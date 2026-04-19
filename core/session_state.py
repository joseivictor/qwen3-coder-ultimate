"""
QWEN3-CODER ULTIMATE — Session State v1.0
Centralized mutable singleton for session-wide state.
Based on Claude Code's internal session state (~80 infrastructure fields).
Rarely changed, frequently read — optimized for reads.
"""

import os
import time
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class SessionState:
    """
    Single source of truth for all session-level state.
    All modules read from here instead of storing their own copies.
    """

    # ── Identity ──────────────────────────────────────────────────────────────
    session_id:       str  = ""
    session_name:     str  = ""
    started_at:       float = field(default_factory=time.time)

    # ── Model ─────────────────────────────────────────────────────────────────
    model:            str  = ""
    provider:         str  = ""
    temperature:      float = 0.2
    max_tokens:       int  = 8192
    effort_level:     str  = "medium"  # low|medium|high|xhigh|max
    thinking_mode:    bool = False
    fast_mode:        bool = False

    # ── Context ───────────────────────────────────────────────────────────────
    cwd:              str  = field(default_factory=os.getcwd)
    project_type:     str  = ""
    stack:            list = field(default_factory=list)
    tokens_used:      int  = 0
    tokens_budget:    int  = 200_000
    context_pct:      float = 0.0    # 0.0–1.0
    compaction_count: int  = 0
    turn_count:       int  = 0

    # ── Permissions ───────────────────────────────────────────────────────────
    permission_mode:  str  = "default"   # default|acceptEdits|plan|auto|dontAsk|bypass
    safe_mode:        bool = True
    allowed_tools:    list = field(default_factory=list)
    denied_tools:     list = field(default_factory=list)

    # ── Features active ───────────────────────────────────────────────────────
    plan_mode_active: bool = False
    dream_active:     bool = True
    kairos_active:    bool = True
    speculative_exec: bool = True
    web_ui_port:      Optional[int] = None
    vscode_connected: bool = False

    # ── Git ───────────────────────────────────────────────────────────────────
    git_repo:         bool = False
    git_branch:       str  = ""
    git_dirty:        bool = False
    worktree_active:  bool = False
    worktree_path:    str  = ""

    # ── Performance ───────────────────────────────────────────────────────────
    avg_turn_ms:      float = 0.0
    speculative_ms_saved: int = 0
    dream_cycles:     int  = 0
    kairos_signals:   int  = 0
    tool_calls_total: int  = 0
    tool_errors:      int  = 0

    # ── Extras ────────────────────────────────────────────────────────────────
    tags:             list = field(default_factory=list)
    notes:            dict = field(default_factory=dict)

    def update_context_pct(self):
        if self.tokens_budget > 0:
            self.context_pct = self.tokens_used / self.tokens_budget

    def record_turn(self, tokens: int, duration_ms: float):
        self.turn_count   += 1
        self.tokens_used  += tokens
        # Rolling average
        self.avg_turn_ms = (self.avg_turn_ms * (self.turn_count - 1) + duration_ms) / self.turn_count
        self.update_context_pct()

    def to_dict(self) -> dict:
        import dataclasses
        return dataclasses.asdict(self)

    def summary(self) -> str:
        uptime = int(time.time() - self.started_at)
        h, m   = divmod(uptime // 60, 60)
        s      = uptime % 60
        uptime_str = f"{h:02d}:{m:02d}:{s:02d}"
        ctx_pct = f"{self.context_pct * 100:.0f}%"
        return (
            f"Session: {self.session_id or 'unnamed'} | "
            f"Model: {self.model.split('/')[-1]} | "
            f"Turns: {self.turn_count} | "
            f"Context: {ctx_pct} | "
            f"Uptime: {uptime_str} | "
            f"Branch: {self.git_branch or 'none'}"
        )


class SessionManager:
    """Manages the global session state singleton."""

    _instance: Optional[SessionState] = None

    @classmethod
    def get(cls) -> SessionState:
        if cls._instance is None:
            cls._instance = cls._init_state()
        return cls._instance

    @classmethod
    def reset(cls):
        cls._instance = None

    @classmethod
    def _init_state(cls) -> SessionState:
        import uuid
        import subprocess

        state = SessionState(
            session_id = str(uuid.uuid4())[:8],
            cwd        = os.getcwd(),
        )

        # Detect git
        try:
            r = subprocess.run(["git", "branch", "--show-current"],
                               capture_output=True, text=True, cwd=state.cwd)
            if r.returncode == 0:
                state.git_repo   = True
                state.git_branch = r.stdout.strip()
            d = subprocess.run(["git", "status", "--porcelain"],
                               capture_output=True, text=True, cwd=state.cwd)
            state.git_dirty = bool(d.stdout.strip()) if d.returncode == 0 else False
        except Exception:
            pass

        return state

    @classmethod
    def update(cls, **kwargs):
        state = cls.get()
        for k, v in kwargs.items():
            if hasattr(state, k):
                setattr(state, k, v)
