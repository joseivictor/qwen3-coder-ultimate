"""
QWEN3-CODER ULTIMATE — Memory Agent v1.0
Long-term project memory: learns preferences, tracks tech debt,
semantic search over past decisions, cross-session continuity.
"""

import sqlite3
import json
import time
import hashlib
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class MemoryEntry:
    id:         str
    type:       str       # decision | preference | bug | debt | fact | snippet
    content:    str
    tags:       list[str]
    project:    str
    created_at: float
    updated_at: float
    access_count: int = 0
    importance: float = 1.0
    related_ids: list[str] = field(default_factory=list)


MEMORY_TYPES = {
    "decision": "Architectural or technical decisions made",
    "preference": "User preferences and working style",
    "bug": "Known bugs, workarounds, and gotchas",
    "debt": "Technical debt items to address later",
    "fact": "Project facts: stack, conventions, team, APIs",
    "snippet": "Useful code snippets and patterns",
    "lesson": "Lessons learned from past mistakes",
}


class MemoryAgent:
    """
    Persistent cross-session memory backed by SQLite.
    Supports semantic-ish search (keyword scoring), auto-tagging,
    importance decay, and LLM-powered recall synthesis.
    """

    DB_PATH = "qwen_memory_agent.db"

    def __init__(self, client, model: str, project: str = "default"):
        self.client  = client
        self.model   = model
        self.project = project
        self._db     = None
        self._init_db()

    def _init_db(self):
        self._db = sqlite3.connect(self.DB_PATH, check_same_thread=False)
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id          TEXT PRIMARY KEY,
                type        TEXT NOT NULL,
                content     TEXT NOT NULL,
                tags        TEXT DEFAULT '[]',
                project     TEXT DEFAULT 'default',
                created_at  REAL,
                updated_at  REAL,
                access_count INTEGER DEFAULT 0,
                importance  REAL DEFAULT 1.0,
                related_ids TEXT DEFAULT '[]'
            )
        """)
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                id          TEXT PRIMARY KEY,
                user_msg    TEXT,
                agent_resp  TEXT,
                tools_used  TEXT,
                project     TEXT,
                created_at  REAL
            )
        """)
        self._db.commit()

    def _call(self, messages: list, max_tokens: int = 1024) -> str:
        try:
            resp = self.client.chat.completions.create(
                model=self.model, messages=messages,
                max_tokens=max_tokens, temperature=0.1, stream=False,
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            return f"[MemoryAgentError: {e}]"

    # ── SAVE ──────────────────────────────────────────────────────────────────
    def remember(self, content: str, type: str = "fact",
                 tags: list = None, importance: float = 1.0) -> str:
        """Store a new memory entry."""
        if type not in MEMORY_TYPES:
            type = "fact"

        auto_tags = self._auto_tag(content)
        all_tags  = list(set((tags or []) + auto_tags))

        entry_id  = hashlib.md5(f"{content}{time.time()}".encode()).hexdigest()[:12]
        now       = time.time()

        existing  = self._find_duplicate(content)
        if existing:
            self._db.execute(
                "UPDATE memories SET content=?, updated_at=?, access_count=access_count+1, importance=? WHERE id=?",
                (content, now, min(importance * 1.1, 5.0), existing)
            )
            self._db.commit()
            return f"✅ Memory updated: '{content[:60]}...'"

        self._db.execute(
            "INSERT INTO memories VALUES (?,?,?,?,?,?,?,?,?,?)",
            (entry_id, type, content, json.dumps(all_tags), self.project,
             now, now, 0, importance, "[]")
        )
        self._db.commit()
        return f"✅ Remembered [{type}]: '{content[:80]}'"

    def learn_from_interaction(self, user_msg: str, agent_resp: str,
                                tools_used: list = None):
        """Extract learnable facts from an interaction and auto-save them."""
        system = """Analyze this AI interaction and extract memorable facts.
Output JSON: {"memories": [{"content": "...", "type": "decision|preference|bug|debt|fact|lesson", "importance": 0.5-3.0}]}
Only extract genuinely useful, reusable information. Max 3 items. If nothing notable, return {"memories": []}."""

        context = (
            f"User: {user_msg[:500]}\n"
            f"Agent: {agent_resp[:800]}\n"
            f"Tools used: {', '.join(tools_used or [])}"
        )
        raw  = self._call(
            [{"role": "system", "content": system},
             {"role": "user",   "content": context}],
            max_tokens=400,
        )
        try:
            start = raw.find("{")
            end   = raw.rfind("}") + 1
            data  = json.loads(raw[start:end])
            for m in data.get("memories", []):
                self.remember(
                    content    = m.get("content", ""),
                    type       = m.get("type", "fact"),
                    importance = float(m.get("importance", 1.0)),
                )
        except Exception:
            pass

        iid = hashlib.md5(f"{user_msg}{time.time()}".encode()).hexdigest()[:12]
        self._db.execute(
            "INSERT INTO interactions VALUES (?,?,?,?,?,?)",
            (iid, user_msg[:1000], agent_resp[:2000],
             json.dumps(tools_used or []), self.project, time.time())
        )
        self._db.commit()

    # ── RECALL ────────────────────────────────────────────────────────────────
    def recall(self, query: str, top_k: int = 8, type_filter: str = "") -> list[MemoryEntry]:
        """Retrieve relevant memories using keyword scoring."""
        sql = "SELECT * FROM memories WHERE project=?"
        params: list = [self.project]

        if type_filter:
            sql += " AND type=?"
            params.append(type_filter)

        rows = self._db.execute(sql, params).fetchall()
        if not rows:
            return []

        query_words = set(re.findall(r'\w+', query.lower()))
        scored      = []
        for row in rows:
            content = row[2].lower()
            tags    = json.loads(row[3])
            score   = 0.0

            for word in query_words:
                if word in content:
                    score += content.count(word) * 1.0
                for tag in tags:
                    if word in tag.lower():
                        score += 2.0

            score  *= row[8]
            score  /= (1 + (time.time() - row[5]) / 86400 / 30)

            if score > 0:
                scored.append((score, row))

        scored.sort(reverse=True)
        results = []
        for _, row in scored[:top_k]:
            self._db.execute("UPDATE memories SET access_count=access_count+1 WHERE id=?", (row[0],))
            results.append(MemoryEntry(
                id           = row[0],
                type         = row[1],
                content      = row[2],
                tags         = json.loads(row[3]),
                project      = row[4],
                created_at   = row[5],
                updated_at   = row[6],
                access_count = row[7],
                importance   = row[8],
                related_ids  = json.loads(row[9]),
            ))
        self._db.commit()
        return results

    def recall_formatted(self, query: str, top_k: int = 6, type_filter: str = "") -> str:
        """Recall and return formatted string for injection into LLM context."""
        entries = self.recall(query, top_k, type_filter)
        if not entries:
            return f"No relevant memories for: {query}"

        lines = [f"📚 Relevant memories ({len(entries)} found):"]
        for e in entries:
            age     = self._age_str(e.created_at)
            tags_s  = f" [{', '.join(e.tags[:3])}]" if e.tags else ""
            lines.append(f"\n[{e.type.upper()}]{tags_s} ({age})")
            lines.append(f"  {e.content}")

        return "\n".join(lines)

    def synthesize(self, query: str) -> str:
        """LLM-powered synthesis of relevant memories into a coherent answer."""
        entries = self.recall(query, top_k=10)
        if not entries:
            return "No relevant memories to synthesize."

        memories_text = "\n".join(
            f"- [{e.type}] {e.content}" for e in entries
        )
        raw = self._call(
            [{"role": "system", "content": "You synthesize project memory into actionable context. Be concise."},
             {"role": "user",   "content": f"Query: {query}\n\nMemories:\n{memories_text}"}],
            max_tokens=600,
        )
        return raw

    # ── LEARN USER PREFERENCES ────────────────────────────────────────────────
    def note_preference(self, preference: str):
        """Explicitly note a user preference."""
        return self.remember(preference, type="preference", importance=2.0)

    def note_decision(self, decision: str, rationale: str = ""):
        """Record an architectural decision."""
        content = f"{decision}" + (f" | Rationale: {rationale}" if rationale else "")
        return self.remember(content, type="decision", importance=2.5)

    def note_bug(self, bug: str, workaround: str = ""):
        """Record a known bug or gotcha."""
        content = f"BUG: {bug}" + (f" | Workaround: {workaround}" if workaround else "")
        return self.remember(content, type="bug", importance=2.0)

    def note_debt(self, item: str, priority: str = "medium"):
        """Track technical debt."""
        content = f"[{priority.upper()}] {item}"
        return self.remember(content, type="debt", importance=1.5)

    # ── HOUSEKEEPING ──────────────────────────────────────────────────────────
    def forget(self, memory_id: str) -> str:
        self._db.execute("DELETE FROM memories WHERE id=?", (memory_id,))
        self._db.commit()
        return f"✅ Forgotten: {memory_id}"

    def list_all(self, type_filter: str = "", limit: int = 30) -> str:
        sql = "SELECT id, type, content, importance, created_at FROM memories WHERE project=?"
        params: list = [self.project]
        if type_filter:
            sql += " AND type=?"
            params.append(type_filter)
        sql += " ORDER BY importance DESC, updated_at DESC LIMIT ?"
        params.append(limit)

        rows = self._db.execute(sql, params).fetchall()
        if not rows:
            return "Memory is empty."

        lines = [f"📚 All memories ({len(rows)}):"]
        for r in rows:
            age = self._age_str(r[4])
            lines.append(f"  [{r[0]}] [{r[1].upper()}] ⭐{r[3]:.1f} ({age}) {r[2][:80]}")
        return "\n".join(lines)

    def stats(self) -> str:
        total    = self._db.execute("SELECT COUNT(*) FROM memories WHERE project=?", (self.project,)).fetchone()[0]
        by_type  = self._db.execute(
            "SELECT type, COUNT(*) FROM memories WHERE project=? GROUP BY type", (self.project,)
        ).fetchall()
        int_cnt  = self._db.execute(
            "SELECT COUNT(*) FROM interactions WHERE project=?", (self.project,)
        ).fetchone()[0]

        lines = [f"MemoryAgent stats (project: {self.project})", f"Total memories: {total}", f"Interactions logged: {int_cnt}"]
        for typ, cnt in by_type:
            lines.append(f"  {typ}: {cnt}")
        return "\n".join(lines)

    def export(self, filepath: str = "qwen_memory_export.json"):
        rows = self._db.execute("SELECT * FROM memories WHERE project=?", (self.project,)).fetchall()
        data = [{"id":r[0],"type":r[1],"content":r[2],"tags":json.loads(r[3]),"created_at":r[5],"importance":r[8]} for r in rows]
        Path(filepath).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return f"✅ Exported {len(data)} memories → {filepath}"

    def get_context_block(self, current_task: str, max_chars: int = 2000) -> str:
        """Build a memory context block to inject into system prompt."""
        entries = self.recall(current_task, top_k=6)
        if not entries:
            return ""

        parts = ["### MEMORY CONTEXT (from past sessions)"]
        total = 0
        for e in entries:
            line  = f"- [{e.type}] {e.content}"
            if total + len(line) > max_chars:
                break
            parts.append(line)
            total += len(line)
        return "\n".join(parts)

    # ── HELPERS ───────────────────────────────────────────────────────────────
    def _auto_tag(self, content: str) -> list[str]:
        tags = []
        tech_keywords = {
            "python": ["python","def","class","import","pytest","django","fastapi","flask"],
            "javascript": ["javascript","const","let","async","await","react","node","jest"],
            "database": ["sql","database","db","query","table","migration","orm"],
            "security": ["security","auth","jwt","password","token","encrypt","hash"],
            "performance": ["performance","optimize","cache","speed","latency","memory"],
            "api": ["api","endpoint","rest","graphql","request","response","webhook"],
            "docker": ["docker","container","kubernetes","k8s","compose"],
            "git": ["git","commit","branch","merge","pr","pull request"],
            "testing": ["test","pytest","jest","mock","fixture","coverage","tdd"],
        }
        c_lower = content.lower()
        for tag, keywords in tech_keywords.items():
            if any(kw in c_lower for kw in keywords):
                tags.append(tag)
        return tags[:4]

    def _find_duplicate(self, content: str, threshold: float = 0.85) -> Optional[str]:
        words_new = set(re.findall(r'\w+', content.lower()))
        rows      = self._db.execute(
            "SELECT id, content FROM memories WHERE project=?", (self.project,)
        ).fetchall()
        for row_id, row_content in rows:
            words_existing = set(re.findall(r'\w+', row_content.lower()))
            if not words_existing:
                continue
            overlap = len(words_new & words_existing)
            jaccard = overlap / len(words_new | words_existing)
            if jaccard >= threshold:
                return row_id
        return None

    def _age_str(self, ts: float) -> str:
        delta = time.time() - ts
        if delta < 3600:   return f"{int(delta//60)}m ago"
        if delta < 86400:  return f"{int(delta//3600)}h ago"
        return f"{int(delta//86400)}d ago"

    def close(self):
        if self._db:
            self._db.close()
