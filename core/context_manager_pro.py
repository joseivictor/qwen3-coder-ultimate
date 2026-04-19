"""
QWEN3-CODER ULTIMATE — Context Manager Pro v1.0
Semantic priority windowing: keeps the MOST RELEVANT messages,
not just the most recent. This is how Claude Code handles long contexts.
"""

import json
import re
import time
import hashlib
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MessageScore:
    index:     int
    role:      str
    content:   str
    score:     float
    is_system: bool = False
    has_tools: bool = False
    pinned:    bool = False


class ContextManagerPro:
    """
    Intelligent context window manager:

    1. Semantic relevance scoring — keeps messages relevant to current task
    2. Priority pinning — always keeps: system, recent N, tool results, errors
    3. Hierarchical compression — summarizes old chunks, not individual messages
    4. Token budget enforcement — hard ceiling with graceful degradation
    5. File content deduplication — don't repeat the same file content twice
    """

    # Messages always kept regardless of score
    ALWAYS_KEEP_ROLES = {"system"}
    PIN_KEYWORDS = {
        "error", "erro", "exception", "traceback", "failed", "critical",
        "decision", "decisão", "architecture", "important", "importante",
        "bug", "fix", "breaking",
    }

    def __init__(self, client, model: str, config: dict):
        self.client          = client
        self.model           = model
        self.config          = config
        self.max_tokens      = config.get("max_context_tokens", 32000)
        self.recent_n        = config.get("context_recent_n", 8)
        self.compress_at     = config.get("compress_threshold", 40)
        self._file_cache:    dict[str, str] = {}
        self._summary_cache: dict[str, str] = {}
        self._stats = {"compressions": 0, "tokens_saved": 0}

    def _call(self, messages: list, max_tokens: int = 800) -> str:
        try:
            resp = self.client.chat.completions.create(
                model=self.model, messages=messages,
                max_tokens=max_tokens, temperature=0.1, stream=False,
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            return f"[ContextError: {e}]"

    def _estimate_tokens(self, text: str) -> int:
        return max(1, len(text) // 4)

    def _total_tokens(self, messages: list) -> int:
        return sum(self._estimate_tokens(str(m.get("content", ""))) for m in messages)

    # ── MAIN ENTRY: SMART TRIM ────────────────────────────────────────────────
    def smart_trim(self, history: list, current_task: str = "") -> list:
        """
        Main entry point. Returns a trimmed history that:
        - Fits within token budget
        - Keeps the most relevant messages for current_task
        - Always keeps system + recent N + pinned messages
        """
        if len(history) <= self.recent_n + 2:
            return history

        total_msgs = len(history)
        user_msgs  = sum(1 for m in history if m["role"] == "user")

        # Only compress if needed
        if user_msgs <= self.compress_at and self._total_tokens(history) < self.max_tokens:
            return self._deduplicate_file_content(history)

        self._stats["compressions"] += 1

        scored   = self._score_messages(history, current_task)
        trimmed  = self._select_messages(scored, history)
        deduped  = self._deduplicate_file_content(trimmed)

        tokens_before = self._total_tokens(history)
        tokens_after  = self._total_tokens(deduped)
        self._stats["tokens_saved"] += max(0, tokens_before - tokens_after)

        return deduped

    # ── SCORING ───────────────────────────────────────────────────────────────
    def _score_messages(self, history: list, current_task: str) -> list[MessageScore]:
        task_words = set(re.findall(r'\w+', current_task.lower())) if current_task else set()
        n          = len(history)
        scored     = []

        for i, msg in enumerate(history):
            role    = msg.get("role", "")
            content = str(msg.get("content", ""))
            score   = 0.0

            # Base score: recency (exponential decay)
            recency = (i / max(n - 1, 1))
            score  += recency * 3.0

            # Role bonuses
            if role == "system":
                score += 100.0  # always keep
            elif role == "tool":
                score += 1.5    # tool results are context

            # Tool call presence
            has_tools = bool(msg.get("tool_calls"))
            if has_tools:
                score += 1.0

            # Task relevance
            if task_words:
                content_words = set(re.findall(r'\w+', content.lower()))
                overlap = len(task_words & content_words)
                score  += overlap * 0.5

            # Pin keywords
            content_low = content.lower()
            if any(kw in content_low for kw in self.PIN_KEYWORDS):
                score += 2.0

            # Error messages are critical
            if any(err in content_low for err in ["traceback", "error:", "exception:", "❌"]):
                score += 3.0

            # File reads with actual content
            if "```" in content and len(content) > 200:
                score += 1.0

            # Decisions / architectural notes
            if any(kw in content_low for kw in ["decided", "escolhi", "vamos usar", "architecture", "pattern"]):
                score += 2.5

            pinned = role == "system" or i >= n - self.recent_n
            scored.append(MessageScore(
                index=i, role=role, content=content,
                score=score, is_system=(role == "system"),
                has_tools=has_tools, pinned=pinned,
            ))

        return scored

    def _select_messages(self, scored: list[MessageScore], original: list) -> list:
        """Select messages by score until token budget is met."""
        # Always keep: system + last recent_n
        pinned_indices = {s.index for s in scored if s.pinned}

        # Sort non-pinned by score descending
        non_pinned = sorted(
            [s for s in scored if not s.pinned],
            key=lambda x: x.score, reverse=True
        )

        token_budget = self.max_tokens
        selected     = set(pinned_indices)
        tokens_used  = sum(
            self._estimate_tokens(str(original[i].get("content", "")))
            for i in pinned_indices
        )

        # Fill budget with highest-scored non-pinned messages
        for msg_score in non_pinned:
            msg_tokens = self._estimate_tokens(msg_score.content)
            if tokens_used + msg_tokens <= token_budget:
                selected.add(msg_score.index)
                tokens_used += msg_tokens
            if tokens_used >= token_budget * 0.9:
                break

        # Reconstruct in original order
        result = [original[i] for i in sorted(selected)]

        # Add compression marker if we dropped messages
        dropped = len(original) - len(result)
        if dropped > 0:
            # Insert a summary after system message
            summary = self._build_dropped_summary(
                [original[i] for i in range(len(original)) if i not in selected and original[i]["role"] != "system"]
            )
            sys_msgs = [m for m in result if m.get("role") == "system"]
            rest     = [m for m in result if m.get("role") != "system"]
            result   = sys_msgs + [{"role": "system", "content": f"[CONTEXT SUMMARY — {dropped} older messages compressed]\n{summary}"}] + rest

        return result

    def _build_dropped_summary(self, dropped_msgs: list) -> str:
        if not dropped_msgs:
            return ""
        body = "\n".join(
            f"{m['role'].upper()}: {str(m.get('content',''))[:300]}"
            for m in dropped_msgs[:20]
        )
        chunk_hash = hashlib.md5(body.encode()).hexdigest()[:8]
        if chunk_hash in self._summary_cache:
            return self._summary_cache[chunk_hash]

        summary = self._call(
            [{"role": "system", "content": "Summarize this conversation history in ≤150 words. Preserve: decisions made, code written, errors found, key context."},
             {"role": "user",   "content": body[:4000]}],
            max_tokens=200,
        )
        self._summary_cache[chunk_hash] = summary
        return summary

    # ── FILE CONTENT DEDUPLICATION ────────────────────────────────────────────
    def _deduplicate_file_content(self, history: list) -> list:
        """
        If the same file content appears multiple times in history,
        keep only the most recent occurrence and replace older ones
        with a reference marker.
        """
        file_last_seen: dict[str, int] = {}
        result = list(history)

        # Find last occurrence of each file content
        for i, msg in enumerate(result):
            content = str(msg.get("content", ""))
            matches = re.findall(r'(?:read_file|open|arquivo)[^\n]*?([a-zA-Z0-9_/\\.-]+\.[a-zA-Z]{2,4})', content)
            for fname in matches:
                file_last_seen[fname] = i

        # Replace earlier occurrences
        for i, msg in enumerate(result):
            content = str(msg.get("content", ""))
            for fname, last_idx in file_last_seen.items():
                if i < last_idx and fname in content and "```" in content:
                    # Truncate large file content in older messages
                    if len(content) > 500:
                        result[i] = {**msg, "content": f"[File {fname} shown — see more recent version below]"}
                        break

        return result

    # ── SMART COMPRESS ────────────────────────────────────────────────────────
    def compress_conversation(self, history: list, keep_recent: int = 10) -> list:
        """
        Compress middle of conversation into a structured summary.
        Keeps: system + first 2 messages (context setting) + summary + last keep_recent.
        """
        if len(history) < keep_recent + 4:
            return history

        sys_msgs   = [m for m in history if m.get("role") == "system"]
        rest       = [m for m in history if m.get("role") != "system"]
        recent     = rest[-keep_recent:]
        middle     = rest[:-keep_recent]

        if not middle:
            return history

        # Build structured summary
        summary_body = "\n".join(
            f"[{m['role']}] {str(m.get('content',''))[:300]}"
            for m in middle
        )
        summary = self._call(
            [{"role": "system", "content": (
                "Create a structured summary of this conversation. Include:\n"
                "- Files read/written\n- Code generated\n- Bugs found/fixed\n"
                "- Decisions made\n- Current task state\n"
                "Be concise (≤200 words). Preserve technical details."
            )},
             {"role": "user", "content": summary_body[:5000]}],
            max_tokens=250,
        )

        compressed = sys_msgs + [
            {"role": "system", "content": f"[CONVERSATION HISTORY — {len(middle)} messages]\n{summary}"}
        ] + recent

        self._stats["compressions"] += 1
        return compressed

    # ── CONTEXT INJECTION ─────────────────────────────────────────────────────
    def build_context_for_task(self, task: str, history: list,
                                project_files: dict = None,
                                memory_context: str = "") -> list:
        """
        Build an optimized context window for a specific task.
        Injects relevant file snippets and memory without blowing the budget.
        """
        trimmed = self.smart_trim(history, current_task=task)

        # Inject memory context into system message
        if memory_context and trimmed:
            sys_idx = next((i for i, m in enumerate(trimmed) if m.get("role") == "system"), None)
            if sys_idx is not None:
                trimmed[sys_idx] = {
                    **trimmed[sys_idx],
                    "content": trimmed[sys_idx]["content"] + f"\n\n{memory_context}"
                }

        # Inject relevant project files
        if project_files:
            task_words = set(re.findall(r'\w+', task.lower()))
            relevant   = []
            for fname, content in project_files.items():
                file_words = set(re.findall(r'\w+', fname.lower()))
                if task_words & file_words:
                    relevant.append((fname, content[:1000]))

            if relevant:
                file_block = "\n\n".join(f"### {f}\n```\n{c}\n```" for f, c in relevant[:3])
                trimmed.append({
                    "role":    "system",
                    "content": f"[RELEVANT PROJECT FILES]\n{file_block}"
                })

        return trimmed

    # ── TOKEN BUDGET ENFORCEMENT ──────────────────────────────────────────────
    def enforce_token_budget(self, messages: list, budget: int = None) -> list:
        """Hard ceiling: truncate content of large messages to fit budget."""
        budget = budget or self.max_tokens
        result = []
        tokens = 0

        for msg in messages:
            content = str(msg.get("content", ""))
            msg_tokens = self._estimate_tokens(content)

            if tokens + msg_tokens > budget:
                remaining = budget - tokens
                if remaining < 50:
                    break
                # Truncate content to fit
                truncated  = content[:remaining * 4]
                result.append({**msg, "content": truncated + "\n[...truncated for context budget]"})
                tokens += remaining
                break

            result.append(msg)
            tokens += msg_tokens

        return result

    def should_compress(self, history: list) -> bool:
        user_count = sum(1 for m in history if m.get("role") == "user")
        return (
            user_count > self.compress_at or
            self._total_tokens(history) > self.max_tokens * 0.8
        )

    def stats(self) -> str:
        return (
            f"ContextManagerPro: {self._stats['compressions']} compressions | "
            f"~{self._stats['tokens_saved']:,} tokens saved | "
            f"File cache: {len(self._file_cache)} entries"
        )
