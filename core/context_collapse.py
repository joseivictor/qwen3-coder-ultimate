"""
QWEN3-CODER ULTIMATE — Context Collapse v1.0
Reversible context compression with collapse commits.
Based on Claude Code's 4-tier compaction strategy:
  Proactive → Reactive → Snip → Context Collapse (reversible)
"""

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CollapseCommit:
    """A reversible compression point — can be restored."""
    commit_id:  str
    summary:    str
    full_msgs:  list[dict]   # original messages before collapse
    token_before: int
    token_after:  int
    timestamp:  float = field(default_factory=time.time)

    @property
    def savings(self) -> int:
        return self.token_before - self.token_after

    @property
    def ratio(self) -> float:
        return self.token_after / max(1, self.token_before)


class ContextCollapse:
    """
    4-tier context compaction matching Claude Code's strategy:

    Tier 1 — Proactive: trim before API call if >75% full
    Tier 2 — Reactive:  compress after token limit error
    Tier 3 — Snip:      remove oldest tool outputs (fast, no LLM)
    Tier 4 — Collapse:  full LLM compression → stored as CollapseCommit (reversible)

    CollapseCommit = the original is kept, can be restored with revert().
    """

    PROACTIVE_THRESHOLD = 0.75   # compress at 75% context
    REACTIVE_THRESHOLD  = 0.92   # emergency compress at 92%
    CACHE_BOUNDARY      = "__SYSTEM_PROMPT_DYNAMIC_BOUNDARY__"

    def __init__(self, client, model: str, max_tokens: int = 200_000):
        self.client     = client
        self.model      = model
        self.max_tokens = max_tokens
        self._commits:  list[CollapseCommit] = []
        self._stats     = {
            "proactive": 0, "reactive": 0, "snip": 0,
            "collapse": 0, "reverts": 0, "tokens_saved": 0
        }

    def _estimate_tokens(self, messages: list) -> int:
        return sum(len(str(m.get("content", ""))) // 4 for m in messages)

    def _token_pct(self, messages: list) -> float:
        return self._estimate_tokens(messages) / max(1, self.max_tokens)

    # ── TIER 1: PROACTIVE ─────────────────────────────────────────────────────

    def proactive(self, messages: list) -> list:
        """Trim before API call if context is getting full."""
        if self._token_pct(messages) < self.PROACTIVE_THRESHOLD:
            return messages
        self._stats["proactive"] += 1
        return self.snip(messages, keep_recent=12)

    # ── TIER 2: REACTIVE ──────────────────────────────────────────────────────

    def reactive(self, messages: list, error: str = "") -> list:
        """Emergency compression after token limit error."""
        self._stats["reactive"] += 1
        # Aggressive snip first
        trimmed = self.snip(messages, keep_recent=6)
        if self._token_pct(trimmed) > 0.70:
            trimmed = self.collapse(trimmed)
        return trimmed

    # ── TIER 3: SNIP ─────────────────────────────────────────────────────────

    def snip(self, messages: list, keep_recent: int = 10) -> list:
        """
        Fast snip — no LLM needed.
        1. Remove duplicate file contents
        2. Truncate long tool outputs
        3. Keep system + keep_recent messages
        """
        self._stats["snip"] += 1
        if not messages:
            return messages

        result     = list(messages)
        sys_msgs   = [m for m in result if m.get("role") == "system"]
        non_sys    = [m for m in result if m.get("role") != "system"]

        # Truncate large tool results (keep first 400 chars)
        for i, m in enumerate(non_sys):
            if m.get("role") == "tool":
                content = str(m.get("content", ""))
                if len(content) > 800:
                    non_sys[i] = {**m, "content": content[:400] + "\n[...snipped]"}

        # Keep only recent non-system
        kept = non_sys[-keep_recent:]

        # Add snip marker
        if len(non_sys) > keep_recent:
            dropped = len(non_sys) - keep_recent
            kept = [{"role": "system", "content": f"[{dropped} older messages snipped]"}] + kept

        return sys_msgs + kept

    # ── TIER 4: COLLAPSE (REVERSIBLE) ─────────────────────────────────────────

    def collapse(self, messages: list, focus: str = "") -> list:
        """
        Full LLM compression. Stores original as CollapseCommit.
        Can be reverted with revert(commit_id).
        """
        if not messages:
            return messages

        sys_msgs = [m for m in messages if m.get("role") == "system"]
        non_sys  = [m for m in messages if m.get("role") != "system"]
        recent   = non_sys[-8:]
        middle   = non_sys[:-8]

        if not middle:
            return messages

        # Generate summary of middle
        body = "\n".join(
            f"[{m['role'].upper()}] {str(m.get('content',''))[:300]}"
            for m in middle[:30]
        )

        focus_inst = f"\nFocus on: {focus}" if focus else ""
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": (
                        "Create a dense technical summary of this conversation history.\n"
                        "Preserve: decisions made, files modified, bugs found/fixed, "
                        "code written, errors, current task state.\n"
                        f"Max 200 words.{focus_inst}"
                    )},
                    {"role": "user", "content": body[:5000]},
                ],
                max_tokens=280, temperature=0.1, stream=False,
            )
            summary = resp.choices[0].message.content or ""
        except Exception:
            summary = f"[{len(middle)} messages compressed]"

        # Build collapsed history
        collapsed = sys_msgs + [
            {"role": "system", "content": (
                f"[CONTEXT COLLAPSE — {len(middle)} messages compressed]\n{summary}"
            )}
        ] + recent

        # Store as reversible commit
        commit_id = hashlib.md5(body[:500].encode()).hexdigest()[:8]
        commit    = CollapseCommit(
            commit_id    = commit_id,
            summary      = summary,
            full_msgs    = messages,
            token_before = self._estimate_tokens(messages),
            token_after  = self._estimate_tokens(collapsed),
        )
        self._commits.append(commit)
        self._stats["collapse"] += 1
        self._stats["tokens_saved"] += commit.savings

        return collapsed

    # ── REVERT ────────────────────────────────────────────────────────────────

    def revert(self, commit_id: str = None) -> Optional[list]:
        """
        Restore history to state before a collapse commit.
        If commit_id=None, reverts the most recent collapse.
        """
        if not self._commits:
            return None

        if commit_id:
            commit = next((c for c in reversed(self._commits) if c.commit_id == commit_id), None)
        else:
            commit = self._commits[-1]

        if not commit:
            return None

        self._commits.remove(commit)
        self._stats["reverts"] += 1
        return commit.full_msgs

    def list_commits(self) -> str:
        if not self._commits:
            return "No collapse commits."
        lines = ["Context collapse commits (oldest → newest):"]
        for c in self._commits:
            ts   = time.strftime("%H:%M:%S", time.localtime(c.timestamp))
            pct  = f"{(1 - c.ratio)*100:.0f}%"
            lines.append(
                f"  [{c.commit_id}] {ts} — saved {c.savings:,} tokens ({pct}) | "
                f"{c.summary[:60]}..."
            )
        return "\n".join(lines)

    # ── SMART DISPATCH ────────────────────────────────────────────────────────

    def smart_compress(self, messages: list, error: str = "",
                       focus: str = "") -> list:
        """
        Dispatch to correct tier based on current state.
        This is the single entry point — call this instead of individual tiers.
        """
        pct = self._token_pct(messages)

        if error and ("context" in error.lower() or "token" in error.lower()):
            return self.reactive(messages, error)

        if pct >= 0.92:
            return self.reactive(messages)

        if pct >= self.PROACTIVE_THRESHOLD:
            # Try snip first (cheap)
            snipped = self.snip(messages, keep_recent=12)
            if self._token_pct(snipped) < 0.65:
                return snipped
            # Need full collapse
            return self.collapse(snipped, focus=focus)

        return messages

    # ── CACHE BOUNDARY ────────────────────────────────────────────────────────

    @staticmethod
    def inject_cache_boundary(messages: list) -> list:
        """
        Insert __SYSTEM_PROMPT_DYNAMIC_BOUNDARY__ into system prompt.
        Static part (before marker) gets cached globally across users.
        Dynamic part (after marker) is per-session.
        Based on Claude Code's prompt caching optimization.
        """
        msgs = list(messages)
        for i, m in enumerate(msgs):
            if m.get("role") == "system":
                content = m.get("content", "")
                if ContextCollapse.CACHE_BOUNDARY not in content:
                    # Find the boundary: after static instructions, before dynamic context
                    # Heuristic: split at first occurrence of "[" (where dynamic content starts)
                    static_end = content.find("\n\n[")
                    if static_end > 200:
                        static  = content[:static_end]
                        dynamic = content[static_end:]
                        msgs[i] = {**m, "content": (
                            f"{static}\n{ContextCollapse.CACHE_BOUNDARY}\n{dynamic}"
                        )}
                break
        return msgs

    def stats(self) -> str:
        s = self._stats
        return (
            f"ContextCollapse: P={s['proactive']} R={s['reactive']} "
            f"S={s['snip']} C={s['collapse']} rev={s['reverts']} | "
            f"~{s['tokens_saved']:,} tokens saved | "
            f"{len(self._commits)} commits"
        )
