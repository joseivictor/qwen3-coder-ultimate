"""
QWEN3-CODER ULTIMATE — Dream System v1.0
Background memory consolidation — runs while model responds.
Based on Claude Code's internal Dream System:
orient → gather_signals → consolidate → prune_context
"""

import threading
import time
import hashlib
import json
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DreamCycle:
    cycle_id:    int
    signals:     list[str]
    consolidated: str
    pruned_keys: list[str]
    duration_ms: int
    timestamp:   float = field(default_factory=time.time)


class DreamSystem:
    """
    Runs in the background during model response streaming.
    Four phases (mirrors Claude Code internals):
    1. orient      — understand current session state
    2. gather      — collect signals: errors, decisions, todos, patterns
    3. consolidate — compress signals into durable memory entries
    4. prune       — remove stale/redundant entries from memory store

    Calls are non-blocking. Results are available after model responds.
    """

    SIGNAL_PATTERNS = [
        ("error",      ["error", "traceback", "exception", "failed", "❌"]),
        ("decision",   ["decided", "escolhi", "vou usar", "we'll use", "architecture"]),
        ("todo",       ["TODO", "FIXME", "ainda falta", "next step", "precisa"]),
        ("learning",   ["aprendi", "discovered", "insight", "pattern", "noticed"]),
        ("file",       ["write_file", "edit_file", "created", "modified", "saved"]),
        ("test",       ["test passed", "test failed", "✅", "all tests", "pytest"]),
    ]

    def __init__(self, client, model: str, memory_store=None):
        self.client       = client
        self.model        = model
        self.memory       = memory_store   # MemorySystem or MemoryAgent
        self._thread:     Optional[threading.Thread] = None
        self._result:     Optional[DreamCycle] = None
        self._cycle_count = 0
        self._lock        = threading.Lock()
        self._stats       = {"cycles": 0, "signals_found": 0, "entries_pruned": 0}

    # ── TRIGGER ───────────────────────────────────────────────────────────────

    def dream(self, history: list, current_task: str = "") -> threading.Thread:
        """
        Start a dream cycle in background. Returns thread (non-blocking).
        Call while waiting for model response.
        """
        t = threading.Thread(
            target=self._run_cycle,
            args=(list(history), current_task),
            daemon=True,
        )
        t.start()
        self._thread = t
        return t

    def await_dream(self, timeout: float = 3.0) -> Optional[DreamCycle]:
        """Wait for current dream cycle to finish. Returns result."""
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout)
        return self._result

    # ── PHASES ────────────────────────────────────────────────────────────────

    def _run_cycle(self, history: list, task: str):
        start = time.time()
        self._cycle_count += 1
        self._stats["cycles"] += 1

        try:
            # Phase 1: Orient
            session_summary = self._orient(history, task)

            # Phase 2: Gather signals
            signals = self._gather_signals(history)
            self._stats["signals_found"] += len(signals)

            if not signals:
                return  # nothing interesting this cycle

            # Phase 3: Consolidate
            consolidated = self._consolidate(signals, session_summary)

            # Phase 4: Prune
            pruned = self._prune(history)
            self._stats["entries_pruned"] += len(pruned)

            # Save to memory if available
            if consolidated and self.memory:
                self._save_to_memory(consolidated, signals)

            duration_ms = int((time.time() - start) * 1000)
            with self._lock:
                self._result = DreamCycle(
                    cycle_id=self._cycle_count,
                    signals=signals,
                    consolidated=consolidated,
                    pruned_keys=pruned,
                    duration_ms=duration_ms,
                )
        except Exception:
            pass

    def _orient(self, history: list, task: str) -> str:
        """Understand current session state in one sentence."""
        if not history:
            return ""
        recent = history[-4:]
        parts  = []
        for m in recent:
            role    = m.get("role", "")
            content = str(m.get("content", ""))[:200]
            if role in ("user", "assistant") and content.strip():
                parts.append(f"{role}: {content}")
        return "\n".join(parts)

    def _gather_signals(self, history: list) -> list[str]:
        """Extract notable signals from recent history."""
        signals = []
        recent  = history[-10:]  # only recent messages matter

        for msg in recent:
            content = str(msg.get("content", "")).lower()
            for signal_type, keywords in self.SIGNAL_PATTERNS:
                if any(kw.lower() in content for kw in keywords):
                    snippet = str(msg.get("content", ""))[:300].strip()
                    signals.append(f"[{signal_type}] {snippet}")
                    break  # one signal per message

        # Deduplicate by first 80 chars
        seen   = set()
        unique = []
        for s in signals:
            key = s[:80]
            if key not in seen:
                seen.add(key)
                unique.append(s)

        return unique[:8]  # max 8 signals per cycle

    def _consolidate(self, signals: list[str], context: str) -> str:
        """Use LLM to compress signals into a durable memory entry."""
        if not signals or not self.client:
            return "\n".join(signals[:3])

        body = "\n".join(signals)
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": (
                        "Consolidate these session signals into 2-3 concise bullet points "
                        "worth remembering across sessions. Focus on: decisions made, "
                        "bugs found/fixed, patterns discovered, files modified. "
                        "Be specific, preserve technical details. Max 150 words."
                    )},
                    {"role": "user", "content": f"Context:\n{context}\n\nSignals:\n{body}"},
                ],
                max_tokens=200, temperature=0.1, stream=False,
            )
            return resp.choices[0].message.content or ""
        except Exception:
            return "\n".join(signals[:3])

    def _prune(self, history: list) -> list[str]:
        """Identify stale entries to remove (heuristic, no LLM needed)."""
        pruned = []
        # Find messages with file content that appear multiple times
        seen_files: dict[str, int] = {}
        for i, msg in enumerate(history):
            content = str(msg.get("content", ""))
            if "```" in content and len(content) > 800:
                h = hashlib.md5(content[:200].encode()).hexdigest()[:8]
                if h in seen_files:
                    pruned.append(f"dup_file_{i}")
                else:
                    seen_files[h] = i
        return pruned

    def _save_to_memory(self, consolidated: str, signals: list[str]):
        """Persist consolidated insights to memory store."""
        if not consolidated:
            return
        try:
            # Try MemorySystem (simple key/value)
            if hasattr(self.memory, "save"):
                key = f"dream_{self._cycle_count}_{int(time.time())}"
                self.memory.save(key, consolidated, "dream")
            # Try MemoryAgent (semantic)
            elif hasattr(self.memory, "store"):
                self.memory.store(consolidated, tags=["dream", "auto"])
        except Exception:
            pass

    # ── INJECT ────────────────────────────────────────────────────────────────

    def inject_into_context(self, history: list) -> list:
        """
        Inject last dream cycle result into system message.
        Call after dream cycle completes.
        """
        result = self._result
        if not result or not result.consolidated:
            return history

        inject = f"\n\n[DREAM MEMORY — cycle {result.cycle_id}]\n{result.consolidated}"
        msgs   = list(history)
        sys_idx = next((i for i, m in enumerate(msgs) if m.get("role") == "system"), None)
        if sys_idx is not None:
            existing = msgs[sys_idx]["content"]
            # Avoid duplicating if already injected
            if "[DREAM MEMORY" not in existing:
                msgs[sys_idx] = {**msgs[sys_idx], "content": existing + inject}
        return msgs

    def stats(self) -> str:
        return (
            f"DreamSystem: {self._stats['cycles']} cycles | "
            f"{self._stats['signals_found']} signals | "
            f"{self._stats['entries_pruned']} pruned"
        )
