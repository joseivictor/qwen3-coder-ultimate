"""
QWEN3-CODER ULTIMATE — Hooks Engine v1.0
20 events, 4 hook types: command, http, prompt, function.
Deterministic automation layer — the infrastructure backbone.
"""

import json
import os
import re
import subprocess
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional
import urllib.request
import urllib.error


class HookEvent(str, Enum):
    # Session
    SESSION_START        = "SessionStart"
    SESSION_END          = "SessionEnd"
    # User
    USER_PROMPT_SUBMIT   = "UserPromptSubmit"
    NOTIFICATION         = "Notification"
    # Tool
    PRE_TOOL_USE         = "PreToolUse"
    POST_TOOL_USE        = "PostToolUse"
    POST_TOOL_FAILURE    = "PostToolUseFailure"
    PERMISSION_REQUEST   = "PermissionRequest"
    PERMISSION_DENIED    = "PermissionDenied"
    # File
    FILE_CHANGED         = "FileChanged"
    FILE_SAVED           = "FileSaved"
    CWD_CHANGED          = "CwdChanged"
    # Task
    TASK_CREATED         = "TaskCreated"
    TASK_COMPLETED       = "TaskCompleted"
    # Agent
    SUBAGENT_START       = "SubagentStart"
    SUBAGENT_STOP        = "SubagentStop"
    # Context
    PRE_COMPACT          = "PreCompact"
    POST_COMPACT         = "PostCompact"
    # Plan
    PLAN_ENTER           = "PlanEnter"
    PLAN_EXIT            = "PlanExit"
    # Turn
    STOP                 = "Stop"
    STOP_FAILURE         = "StopFailure"


@dataclass
class HookResult:
    blocked:  bool = False
    modified: Any  = None   # modified payload if hook wants to change it
    message:  str  = ""
    exit_code: int = 0


@dataclass
class HookDef:
    event:    str
    type:     str           # command | http | prompt | function
    target:   str           # shell cmd / URL / prompt text / function name
    matcher:  str  = ""     # optional filter (tool name, file pattern, etc.)
    timeout:  int  = 10
    blocking: bool = True   # if True, exit_code=2 blocks the action


class HooksEngine:
    """
    Deterministic automation layer.
    Hooks run synchronously before/after key events.
    Exit code 2 from command hook = block the action.
    """

    def __init__(self, config: dict, client=None, model: str = ""):
        self.config  = config
        self.client  = client
        self.model   = model
        self._hooks: dict[str, list[HookDef]] = {}
        self._functions: dict[str, Callable] = {}
        self._stats  = {"fired": 0, "blocked": 0, "errors": 0}
        self._load_from_config(config.get("hooks_v2", {}))

    # ── REGISTRATION ──────────────────────────────────────────────────────────

    def register(self, event: str, hook_type: str, target: str,
                 matcher: str = "", timeout: int = 10, blocking: bool = True):
        hd = HookDef(event=event, type=hook_type, target=target,
                     matcher=matcher, timeout=timeout, blocking=blocking)
        self._hooks.setdefault(event, []).append(hd)

    def register_function(self, name: str, fn: Callable):
        """Register a Python callable as a hook target."""
        self._functions[name] = fn

    def _load_from_config(self, hooks_cfg: dict):
        """Load hooks from config dict:
        {"PreToolUse": [{"type": "command", "target": "...", "matcher": "..."}]}
        """
        for event, defs in hooks_cfg.items():
            if isinstance(defs, list):
                for d in defs:
                    self.register(
                        event    = event,
                        hook_type= d.get("type", "command"),
                        target   = d.get("target", ""),
                        matcher  = d.get("matcher", ""),
                        timeout  = d.get("timeout", 10),
                        blocking = d.get("blocking", True),
                    )
            elif isinstance(defs, str) and defs.strip():
                # Legacy: simple string = shell command
                self.register(event=event, hook_type="command", target=defs)

    # ── FIRE ──────────────────────────────────────────────────────────────────

    def fire(self, event: str, payload: dict = None) -> HookResult:
        """Fire all hooks for event. Returns HookResult (blocked=True stops action)."""
        payload = payload or {}
        hooks   = self._hooks.get(event, [])
        if not hooks:
            return HookResult()

        self._stats["fired"] += len(hooks)
        for hook in hooks:
            if hook.matcher and not self._matches(hook.matcher, payload):
                continue
            try:
                result = self._run_hook(hook, event, payload)
                if result.blocked and hook.blocking:
                    self._stats["blocked"] += 1
                    return result
                if result.modified is not None:
                    payload.update(result.modified if isinstance(result.modified, dict) else {})
            except Exception as e:
                self._stats["errors"] += 1
                # Non-blocking errors
        return HookResult(modified=payload if payload else None)

    def fire_async(self, event: str, payload: dict = None):
        """Fire hooks in background (non-blocking)."""
        threading.Thread(target=self.fire, args=(event, payload), daemon=True).start()

    # ── HOOK RUNNERS ──────────────────────────────────────────────────────────

    def _run_hook(self, hook: HookDef, event: str, payload: dict) -> HookResult:
        if hook.type == "command":
            return self._run_command(hook, event, payload)
        elif hook.type == "http":
            return self._run_http(hook, event, payload)
        elif hook.type == "prompt":
            return self._run_prompt(hook, event, payload)
        elif hook.type == "function":
            return self._run_function(hook, event, payload)
        return HookResult()

    def _run_command(self, hook: HookDef, event: str, payload: dict) -> HookResult:
        env = {**os.environ, "HOOK_EVENT": event, "HOOK_PAYLOAD": json.dumps(payload)}
        try:
            proc = subprocess.run(
                hook.target, shell=True, env=env,
                capture_output=True, text=True, timeout=hook.timeout,
            )
            blocked = proc.returncode == 2
            msg     = (proc.stdout + proc.stderr).strip()
            # Try parsing JSON output for payload modification
            modified = None
            if proc.stdout.strip().startswith("{"):
                try:
                    modified = json.loads(proc.stdout.strip())
                except Exception:
                    pass
            return HookResult(blocked=blocked, modified=modified,
                              message=msg, exit_code=proc.returncode)
        except subprocess.TimeoutExpired:
            return HookResult(message=f"Hook timeout ({hook.timeout}s)")
        except Exception as e:
            return HookResult(message=str(e))

    def _run_http(self, hook: HookDef, event: str, payload: dict) -> HookResult:
        body = json.dumps({"event": event, "payload": payload}).encode()
        req  = urllib.request.Request(
            hook.target, data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=hook.timeout) as resp:
                raw      = resp.read().decode()
                status   = resp.status
                blocked  = status == 403
                modified = None
                if raw.strip().startswith("{"):
                    try:
                        modified = json.loads(raw)
                    except Exception:
                        pass
                return HookResult(blocked=blocked, modified=modified,
                                  message=raw[:200], exit_code=status)
        except Exception as e:
            return HookResult(message=str(e))

    def _run_prompt(self, hook: HookDef, event: str, payload: dict) -> HookResult:
        if not self.client:
            return HookResult()
        prompt = hook.target.format(event=event, **payload)
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a hook evaluator. Respond with JSON: {\"allow\": true/false, \"reason\": \"...\"}"},
                    {"role": "user",   "content": prompt},
                ],
                max_tokens=100, temperature=0.0, stream=False,
            )
            raw = resp.choices[0].message.content or "{}"
            try:
                result  = json.loads(raw)
                blocked = not result.get("allow", True)
                return HookResult(blocked=blocked, message=result.get("reason", ""))
            except Exception:
                return HookResult()
        except Exception as e:
            return HookResult(message=str(e))

    def _run_function(self, hook: HookDef, event: str, payload: dict) -> HookResult:
        fn = self._functions.get(hook.target)
        if not fn:
            return HookResult(message=f"Function hook '{hook.target}' not registered")
        try:
            result = fn(event, payload)
            if isinstance(result, HookResult):
                return result
            if isinstance(result, bool):
                return HookResult(blocked=not result)
            if isinstance(result, dict):
                return HookResult(modified=result)
            return HookResult()
        except Exception as e:
            return HookResult(message=str(e))

    # ── BUILT-IN HOOKS ────────────────────────────────────────────────────────

    def setup_builtin_hooks(self):
        """Register useful built-in hooks from legacy config."""
        hooks_cfg = self.config.get("hooks", {})

        if hooks_cfg.get("pre_tool"):
            self.register(HookEvent.PRE_TOOL_USE, "command", hooks_cfg["pre_tool"])
        if hooks_cfg.get("post_tool"):
            self.register(HookEvent.POST_TOOL_USE, "command", hooks_cfg["post_tool"])
        if hooks_cfg.get("on_start"):
            self.register(HookEvent.SESSION_START, "command", hooks_cfg["on_start"])
        if hooks_cfg.get("on_exit"):
            self.register(HookEvent.SESSION_END, "command", hooks_cfg["on_exit"])

        # Built-in: auto-lint Python files on save
        self.register_function("_builtin_lint_check", self._builtin_lint)
        self.register(HookEvent.FILE_SAVED, "function", "_builtin_lint_check",
                      matcher="*.py", blocking=False)

    def _builtin_lint(self, event: str, payload: dict) -> HookResult:
        path = payload.get("path", "")
        if not path.endswith(".py") or not os.path.exists(path):
            return HookResult()
        try:
            result = subprocess.run(
                ["python", "-m", "py_compile", path],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode != 0:
                return HookResult(message=f"Syntax error in {path}: {result.stderr.strip()}")
        except Exception:
            pass
        return HookResult()

    # ── HELPERS ───────────────────────────────────────────────────────────────

    def _matches(self, matcher: str, payload: dict) -> bool:
        """Check if payload matches the hook's matcher pattern."""
        payload_str = json.dumps(payload)
        # Glob-style match on tool name or file path
        import fnmatch
        for val in [payload.get("tool_name",""), payload.get("path",""),
                    payload.get("file",""), str(payload)]:
            if val and fnmatch.fnmatch(str(val), matcher):
                return True
        # Regex fallback
        try:
            return bool(re.search(matcher, payload_str))
        except re.error:
            return False

    def list_hooks(self) -> str:
        if not self._hooks:
            return "No hooks registered."
        lines = []
        for event, hooks in self._hooks.items():
            for h in hooks:
                matcher = f" [{h.matcher}]" if h.matcher else ""
                lines.append(f"  {event:25} {h.type:10} {h.target[:50]}{matcher}")
        return "\n".join(lines)

    def stats(self) -> str:
        return (f"HooksEngine: {self._stats['fired']} fired | "
                f"{self._stats['blocked']} blocked | "
                f"{self._stats['errors']} errors | "
                f"{sum(len(v) for v in self._hooks.values())} registered")
