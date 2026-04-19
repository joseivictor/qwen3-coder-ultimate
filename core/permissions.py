"""
QWEN3-CODER ULTIMATE — Permissions Engine v1.0
Granular tool permissions: allowedTools, deniedTools, per-tool prompting, modes.
Matches Claude Code's --allowedTools / --permission-mode flags.
"""

import json
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class PermissionMode(str, Enum):
    DEFAULT     = "default"       # ask for dangerous tools
    ACCEPT_EDITS= "acceptEdits"   # auto-approve file edits, ask for shell
    PLAN        = "plan"          # read-only, no writes
    AUTO        = "auto"          # approve everything automatically
    DONT_ASK    = "dontAsk"       # never ask, use allowed/denied lists only
    BYPASS      = "bypass"        # skip all checks (dangerous)


@dataclass
class PermissionResult:
    allowed:      bool
    needs_prompt: bool   = False
    reason:       str    = ""
    auto_approved:bool   = False


ALWAYS_SAFE = {
    "read_file", "list_directory", "file_tree", "search_in_files",
    "search_web", "get_file_info", "show_diff", "git_log", "git_diff",
    "git_status", "get_diagnostics", "get_weather", "get_time",
    "count_tokens", "memory_read", "memory_list", "session_info",
}

WRITE_TOOLS = {
    "write_file", "edit_file", "delete_file", "bulk_write",
    "copy_file", "move_file", "regex_replace", "apply_patch",
    "create_directory", "rename_file",
}

SHELL_TOOLS = {
    "run_shell", "run_command", "execute_script", "bash",
    "run_tests", "run_background",
}

NETWORK_TOOLS = {
    "http_request", "fetch_url", "post_data", "github_create_pr",
    "github_merge_pr", "send_webhook",
}

DESTRUCTIVE_PATTERNS = [
    r"rm\s+-[rf]", r"del\s+/[sfq]", r"DROP\s+TABLE",
    r"TRUNCATE", r"format\s+[a-zA-Z]:", r"shutdown", r"git\s+push\s+--force",
    r"git\s+reset\s+--hard", r"mkfs", r"> /dev/sd",
]


class PermissionManager:
    """
    Single authority for tool permission decisions.
    Reads allowed/denied lists, respects mode, prompts user when needed.
    """

    def __init__(
        self,
        mode:         PermissionMode = PermissionMode.DEFAULT,
        allowed_tools: list[str]     = None,
        denied_tools:  list[str]     = None,
        prompt_fn=None,
    ):
        self.mode          = mode
        self._allowed:  set = set(allowed_tools or [])
        self._denied:   set = set(denied_tools  or [])
        self._session_grants: set = set()   # granted for this session
        self._session_denies: set = set()   # denied for this session
        self._prompt_fn       = prompt_fn   # callable(tool, args) -> bool
        self._stats = {
            "checked": 0, "auto_allowed": 0, "auto_denied": 0,
            "prompted": 0, "user_allowed": 0, "user_denied": 0,
        }
        self._audit_log: list[dict] = []

    # ── MAIN CHECK ────────────────────────────────────────────────────────────

    def check(self, tool_name: str, args: dict = None) -> PermissionResult:
        """
        Central permission gate. Returns PermissionResult.
        """
        args = args or {}
        self._stats["checked"] += 1
        ts = time.time()

        # BYPASS — skip everything
        if self.mode == PermissionMode.BYPASS:
            self._log(tool_name, "bypass", True, ts)
            return PermissionResult(allowed=True, auto_approved=True, reason="bypass mode")

        # Explicit session deny (user said no this session)
        if tool_name in self._session_denies:
            self._stats["auto_denied"] += 1
            self._log(tool_name, "session_deny", False, ts)
            return PermissionResult(allowed=False, reason="denied this session")

        # Explicit deny list
        if tool_name in self._denied:
            self._stats["auto_denied"] += 1
            self._log(tool_name, "denylist", False, ts)
            return PermissionResult(allowed=False, reason=f"'{tool_name}' is in denied list")

        # Session grant (user already said yes this session)
        if tool_name in self._session_grants:
            self._stats["auto_allowed"] += 1
            self._log(tool_name, "session_grant", True, ts)
            return PermissionResult(allowed=True, auto_approved=True, reason="granted this session")

        # Explicit allow list
        if tool_name in self._allowed:
            self._stats["auto_allowed"] += 1
            self._log(tool_name, "allowlist", True, ts)
            return PermissionResult(allowed=True, auto_approved=True, reason="in allowed list")

        # Always-safe tools
        if tool_name in ALWAYS_SAFE:
            self._stats["auto_allowed"] += 1
            self._log(tool_name, "safe", True, ts)
            return PermissionResult(allowed=True, auto_approved=True, reason="read-only safe tool")

        # PLAN mode — only reads allowed
        if self.mode == PermissionMode.PLAN:
            allowed = tool_name in ALWAYS_SAFE
            reason = "plan mode: only read-only tools allowed" if not allowed else "safe"
            self._log(tool_name, "plan_mode", allowed, ts)
            return PermissionResult(allowed=allowed, reason=reason)

        # AUTO mode — approve everything
        if self.mode == PermissionMode.AUTO:
            self._stats["auto_allowed"] += 1
            self._log(tool_name, "auto", True, ts)
            return PermissionResult(allowed=True, auto_approved=True, reason="auto mode")

        # ACCEPT_EDITS — auto-approve file edits, prompt for shell/network
        if self.mode == PermissionMode.ACCEPT_EDITS:
            if tool_name in WRITE_TOOLS:
                self._stats["auto_allowed"] += 1
                self._log(tool_name, "accept_edits", True, ts)
                return PermissionResult(allowed=True, auto_approved=True, reason="acceptEdits mode")

        # Check for destructive content in args
        if self._is_destructive(args):
            if self.mode == PermissionMode.DONT_ASK:
                self._log(tool_name, "destructive_blocked", False, ts)
                return PermissionResult(allowed=False, reason="destructive command blocked (dontAsk mode)")
            # Prompt user for destructive commands regardless of mode
            return PermissionResult(allowed=False, needs_prompt=True,
                                    reason="destructive command detected — requires explicit approval")

        # Shell/network tools need approval in DEFAULT mode
        if tool_name in SHELL_TOOLS or tool_name in NETWORK_TOOLS:
            if self.mode == PermissionMode.DONT_ASK:
                self._log(tool_name, "dont_ask_block", False, ts)
                return PermissionResult(allowed=False, reason=f"'{tool_name}' requires approval (dontAsk mode)")
            return PermissionResult(allowed=False, needs_prompt=True,
                                    reason=f"'{tool_name}' requires user approval")

        # DEFAULT — allow everything else
        self._stats["auto_allowed"] += 1
        self._log(tool_name, "default_allow", True, ts)
        return PermissionResult(allowed=True, auto_approved=True)

    # ── PROMPT USER ───────────────────────────────────────────────────────────

    def prompt_and_check(self, tool_name: str, args: dict = None) -> bool:
        """
        Check permission and prompt user if needed. Returns True if allowed.
        """
        result = self.check(tool_name, args)

        if result.allowed:
            return True

        if not result.needs_prompt:
            return False

        # Prompt user
        self._stats["prompted"] += 1
        allowed = self._do_prompt(tool_name, args or {}, result.reason)

        if allowed:
            self._stats["user_allowed"] += 1
            self._session_grants.add(tool_name)
        else:
            self._stats["user_denied"] += 1
            self._session_denies.add(tool_name)

        self._log(tool_name, "user_prompt", allowed, time.time())
        return allowed

    def _do_prompt(self, tool_name: str, args: dict, reason: str) -> bool:
        if self._prompt_fn:
            return self._prompt_fn(tool_name, args)

        # Default: terminal prompt
        args_preview = json.dumps(args, ensure_ascii=False)[:200]
        print(f"\n[PERMISSION] Tool: {tool_name}")
        print(f"  Reason: {reason}")
        print(f"  Args:   {args_preview}")
        try:
            ans = input("  Allow? [y/N/session] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            ans = "n"

        if ans in ("y", "yes"):
            return True
        if ans in ("session", "s"):
            self._session_grants.add(tool_name)
            return True
        return False

    # ── MANAGEMENT ────────────────────────────────────────────────────────────

    def grant(self, tool_name: str):
        self._allowed.add(tool_name)
        self._session_denies.discard(tool_name)

    def deny(self, tool_name: str):
        self._denied.add(tool_name)
        self._session_grants.discard(tool_name)

    def grant_session(self, tool_name: str):
        self._session_grants.add(tool_name)
        self._session_denies.discard(tool_name)

    def deny_session(self, tool_name: str):
        self._session_denies.add(tool_name)
        self._session_grants.discard(tool_name)

    def set_mode(self, mode: str):
        try:
            self.mode = PermissionMode(mode)
        except ValueError:
            pass

    def set_allowed_tools(self, tools: list[str]):
        self._allowed = set(tools)

    def set_denied_tools(self, tools: list[str]):
        self._denied = set(tools)

    # ── INTROSPECTION ─────────────────────────────────────────────────────────

    def _is_destructive(self, args: dict) -> bool:
        content = json.dumps(args).lower()
        return any(re.search(p, content, re.IGNORECASE) for p in DESTRUCTIVE_PATTERNS)

    def _log(self, tool: str, decision: str, allowed: bool, ts: float):
        self._audit_log.append({
            "tool": tool, "decision": decision,
            "allowed": allowed, "ts": ts,
        })
        if len(self._audit_log) > 500:
            self._audit_log = self._audit_log[-500:]

    def audit_log(self, last: int = 20) -> list[dict]:
        return self._audit_log[-last:]

    def stats(self) -> str:
        s = self._stats
        return (
            f"Permissions[{self.mode.value}]: "
            f"checked={s['checked']} auto_ok={s['auto_allowed']} "
            f"auto_deny={s['auto_denied']} prompted={s['prompted']} "
            f"user_ok={s['user_allowed']} user_deny={s['user_denied']}"
        )

    def status(self) -> str:
        lines = [f"Permission mode: {self.mode.value}"]
        if self._allowed:
            lines.append(f"  Allowed: {', '.join(sorted(self._allowed))}")
        if self._denied:
            lines.append(f"  Denied:  {', '.join(sorted(self._denied))}")
        if self._session_grants:
            lines.append(f"  Session grants: {', '.join(sorted(self._session_grants))}")
        if self.mode == PermissionMode.AUTO:
            lines.append("  WARNING: auto mode — all tools approved automatically")
        return "\n".join(lines)


def from_cli_args(
    allowed: str = "",
    denied:  str = "",
    mode:    str = "default",
    prompt_fn=None,
) -> PermissionManager:
    """
    Build PermissionManager from CLI-style string args.
    allowed = "read_file,write_file" (comma-separated)
    mode    = "default" | "acceptEdits" | "plan" | "auto" | "dontAsk" | "bypass"
    """
    allowed_list = [t.strip() for t in allowed.split(",") if t.strip()] if allowed else []
    denied_list  = [t.strip() for t in denied.split(",")  if t.strip()] if denied  else []
    try:
        pm = PermissionMode(mode)
    except ValueError:
        pm = PermissionMode.DEFAULT
    return PermissionManager(mode=pm, allowed_tools=allowed_list,
                             denied_tools=denied_list, prompt_fn=prompt_fn)
