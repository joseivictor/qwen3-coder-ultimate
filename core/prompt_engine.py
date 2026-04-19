"""
QWEN3-CODER ULTIMATE — Prompt Engine v1.0
Few-shot database, task-specific system prompts, dynamic optimization.
This is what makes Claude Code's responses consistently high quality.
"""

import json
import re
import sqlite3
import time
import hashlib
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FewShotExample:
    task_type:  str
    user_input: str
    ideal_response: str
    tools_used: list[str]
    score:      float = 1.0
    uses:       int = 0


@dataclass
class PromptTemplate:
    name:        str
    system:      str
    task_types:  list[str]
    few_shots:   list[FewShotExample] = field(default_factory=list)
    priority:    int = 0


# ── TASK CLASSIFIERS ──────────────────────────────────────────────────────────
TASK_PATTERNS = {
    "bug_fix": [
        r"(bug|erro|error|fix|corrig|broken|crash|exception|traceback|not working)",
        r"(TypeError|ValueError|AttributeError|ImportError|SyntaxError)",
    ],
    "code_generation": [
        r"(cria|create|implement|escreva|write|make|build|generate|adiciona|add)",
        r"(função|function|class|api|endpoint|script|component)",
    ],
    "code_review": [
        r"(review|revisa|analisa|analyze|check|verifica|melhora|improve|optimize)",
        r"(code|código|função|function|class|arquivo|file)",
    ],
    "refactoring": [
        r"(refactor|refatora|rename|renomea|extract|reorganize|clean|limpa)",
    ],
    "explanation": [
        r"(explica|explain|what does|como funciona|how does|entende|understand)",
        r"(por que|why|o que é|what is|what's)",
    ],
    "testing": [
        r"(test|teste|tdd|coverage|assert|mock|spec)",
    ],
    "security": [
        r"(security|segurança|vulnerability|vulnerabilidade|auth|jwt|password|inject)",
    ],
    "performance": [
        r"(performance|performan|optimize|otimiza|slow|lento|speed|faster|cache)",
    ],
    "documentation": [
        r"(document|documenta|docstring|readme|comment|comenta)",
    ],
    "architecture": [
        r"(architecture|arquitetura|design|pattern|structure|estrutura|plan|plano)",
    ],
}

# ── TASK-SPECIFIC SYSTEM PROMPTS ──────────────────────────────────────────────
TASK_PROMPTS = {
    "bug_fix": """You are an expert debugger. When fixing bugs:
1. READ the file first with read_file before proposing any fix
2. Identify the ROOT CAUSE, not just the symptom
3. Show the exact diff of what changes
4. Explain WHY this is the fix
5. Suggest a test to verify the fix
Be precise. Never guess — read the actual code.""",

    "code_generation": """You are an expert software engineer. When generating code:
1. Write production-ready code, not examples
2. Handle ALL edge cases and errors
3. Use the project's existing patterns (read nearby files first)
4. Write self-documenting code with clear names
5. Include type hints for Python, proper types for TS
6. Use write_file or edit_file to actually save the code""",

    "code_review": """You are a senior code reviewer. Structure your review as:
## Summary
## Critical Issues (must fix)
## High Priority (should fix)
## Suggestions (nice to have)
## Positives
Be specific: include line numbers and exact fixes, not vague advice.""",

    "refactoring": """You are a refactoring expert. Follow this process:
1. Read the current code with read_file
2. Identify the refactoring opportunity
3. Show before/after with clear explanation
4. Use refactor_rename or refactor_extract_fn tools when available
5. Run tests after refactoring to verify nothing broke
Ensure behavior is PRESERVED — refactoring changes structure, not behavior.""",

    "explanation": """You are a patient technical teacher. When explaining:
1. Start with the high-level concept (1-2 sentences)
2. Then go into technical details
3. Use concrete examples from the actual code
4. Relate to patterns the user likely knows
5. Point out gotchas and non-obvious behavior
Adapt to the user's level — don't over-explain basics or skip details.""",

    "testing": """You are a QA expert. When writing tests:
1. Cover happy path, edge cases, error cases
2. Use the project's existing test framework
3. Tests must be deterministic and isolated
4. Use descriptive test names: test_<function>_<scenario>
5. For async code, use proper async test patterns
Generate tests with generate_tests tool or write them directly.""",

    "security": """You are a security engineer. When reviewing security:
1. Check OWASP Top 10 systematically
2. Look for hardcoded secrets, injection, auth issues
3. Use security_scan tool for automated scanning
4. Provide CWE references and specific remediations
5. Prioritize by exploitability × impact
Never dismiss potential vulnerabilities without analysis.""",

    "performance": """You are a performance engineer. When optimizing:
1. Measure first — identify the actual bottleneck
2. State the complexity before and after (O notation)
3. Consider: algorithmic improvements > caching > micro-optimizations
4. Show benchmarks or estimates of improvement
5. Warn about tradeoffs (memory vs speed, readability vs performance)""",

    "architecture": """You are a software architect. When designing:
1. Consider scalability, maintainability, and testability
2. Recommend established patterns (SOLID, DRY, etc.) when appropriate
3. Show trade-offs of different approaches
4. Plan in phases — what's MVP vs future
5. Use plan_task tool to create executable subtasks""",

    "default": """You are an expert AI coding assistant with direct filesystem access.
Always read files before editing. Use tools proactively.
Be concise but complete. Show diffs for all code changes.""",
}

# ── FEW-SHOT EXAMPLES DATABASE ────────────────────────────────────────────────
BUILTIN_EXAMPLES: list[FewShotExample] = [
    FewShotExample(
        task_type="bug_fix",
        user_input="meu código está dando AttributeError: 'NoneType' has no attribute 'split'",
        ideal_response=(
            "Vou ler o arquivo para encontrar a causa raiz.\n\n"
            "O erro indica que uma variável é `None` quando deveria ser uma string. "
            "Causas comuns:\n"
            "1. Função retornando `None` implicitamente\n"
            "2. Resultado de dicionário/banco sem verificação\n"
            "3. Argumento opcional sem valor padrão\n\n"
            "Vou ler o arquivo agora..."
        ),
        tools_used=["read_file", "search_in_files"],
        score=0.95,
    ),
    FewShotExample(
        task_type="code_generation",
        user_input="cria uma função que faz validação de email",
        ideal_response=(
            "```python\nimport re\n\nEMAIL_PATTERN = re.compile(\n"
            "    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'\n)\n\n"
            "def validate_email(email: str) -> bool:\n"
            "    if not email or not isinstance(email, str):\n"
            "        return False\n"
            "    return bool(EMAIL_PATTERN.match(email.strip()))\n```"
        ),
        tools_used=["write_file"],
        score=0.9,
    ),
    FewShotExample(
        task_type="code_review",
        user_input="revisa esse código",
        ideal_response=(
            "## Summary\nCódigo funcional mas com pontos de melhoria.\n\n"
            "## Critical Issues\n- Sem tratamento de exceções na linha X\n\n"
            "## High Priority\n- Complexidade ciclomática alta na função Y\n\n"
            "## Suggestions\n- Extrair lógica para função separada\n\n"
            "## Positives\n- Boa nomenclatura de variáveis"
        ),
        tools_used=["read_file", "analyze_code"],
        score=0.92,
    ),
]


class PromptEngine:
    """
    Intelligent prompt construction engine:
    - Classifies task type from user input
    - Selects optimal system prompt for the task
    - Injects relevant few-shot examples
    - Tracks prompt performance and self-optimizes
    - Builds context-aware prompts from project state
    """

    DB_PATH = "qwen_prompt_engine.db"

    def __init__(self, client, model: str):
        self.client   = client
        self.model    = model
        self._db      = None
        self._cache:  dict[str, str] = {}
        self._init_db()

    def _init_db(self):
        self._db = sqlite3.connect(self.DB_PATH, check_same_thread=False)
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS examples (
                id          TEXT PRIMARY KEY,
                task_type   TEXT,
                user_input  TEXT,
                response    TEXT,
                tools_used  TEXT,
                score       REAL DEFAULT 1.0,
                uses        INTEGER DEFAULT 0,
                created_at  REAL
            )
        """)
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS prompt_scores (
                prompt_hash TEXT PRIMARY KEY,
                task_type   TEXT,
                score       REAL,
                uses        INTEGER DEFAULT 1,
                created_at  REAL
            )
        """)
        self._db.commit()
        self._seed_examples()

    def _seed_examples(self):
        for ex in BUILTIN_EXAMPLES:
            ex_id = hashlib.md5(ex.user_input.encode()).hexdigest()[:12]
            self._db.execute(
                "INSERT OR IGNORE INTO examples VALUES (?,?,?,?,?,?,?,?)",
                (ex_id, ex.task_type, ex.user_input, ex.ideal_response,
                 json.dumps(ex.tools_used), ex.score, 0, time.time())
            )
        self._db.commit()

    # ── TASK CLASSIFICATION ───────────────────────────────────────────────────
    def classify_task(self, user_input: str) -> str:
        """Classify user input into a task type using pattern matching."""
        low    = user_input.lower()
        scores = {}

        for task_type, patterns in TASK_PATTERNS.items():
            score = sum(
                len(re.findall(p, low, re.IGNORECASE))
                for p in patterns
            )
            if score > 0:
                scores[task_type] = score

        if not scores:
            return "default"
        return max(scores, key=lambda k: scores[k])

    def classify_task_llm(self, user_input: str) -> str:
        """LLM-based task classification for ambiguous inputs."""
        task_types = list(TASK_PATTERNS.keys()) + ["default"]
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": (
                        f"Classify this coding task into ONE category: {', '.join(task_types)}\n"
                        f"Task: {user_input[:200]}\n\n"
                        "Reply with ONLY the category name, nothing else."
                    )
                }],
                max_tokens=20, temperature=0.0, stream=False,
            )
            result = (resp.choices[0].message.content or "").strip().lower()
            return result if result in task_types else "default"
        except Exception:
            return self.classify_task(user_input)

    # ── PROMPT BUILDING ───────────────────────────────────────────────────────
    def build_system_prompt(self, user_input: str, base_prompt: str = "",
                             project_context: str = "", memory_context: str = "") -> str:
        """
        Build an optimized system prompt for the given task.
        Combines: base_prompt + task-specific overlay + few-shots + project/memory context.
        """
        task_type    = self.classify_task(user_input)
        task_overlay = TASK_PROMPTS.get(task_type, TASK_PROMPTS["default"])
        few_shots    = self._get_few_shots(task_type, user_input, n=2)

        parts = []
        if base_prompt:
            parts.append(base_prompt)

        parts.append(f"\n## TASK MODE: {task_type.upper().replace('_', ' ')}")
        parts.append(task_overlay)

        if few_shots:
            parts.append("\n## EXAMPLES OF IDEAL RESPONSES")
            for ex in few_shots:
                parts.append(f"User: {ex['user_input'][:150]}")
                parts.append(f"Assistant: {ex['response'][:400]}")
                parts.append("---")

        if memory_context:
            parts.append(f"\n## MEMORY FROM PAST SESSIONS\n{memory_context}")

        if project_context:
            parts.append(f"\n## PROJECT CONTEXT\n{project_context}")

        return "\n\n".join(parts)

    def _get_few_shots(self, task_type: str, user_input: str, n: int = 2) -> list[dict]:
        """Retrieve relevant few-shot examples for the task type."""
        rows = self._db.execute(
            "SELECT user_input, response, score FROM examples WHERE task_type=? ORDER BY score DESC, uses DESC LIMIT ?",
            (task_type, n * 2)
        ).fetchall()

        if not rows:
            return []

        q_words = set(re.findall(r'\w+', user_input.lower()))
        scored  = []
        for row in rows:
            ex_words = set(re.findall(r'\w+', row[0].lower()))
            overlap  = len(q_words & ex_words) / max(len(q_words), 1)
            scored.append((overlap * float(row[2]), row))

        scored.sort(reverse=True)
        return [
            {"user_input": r[0], "response": r[1]}
            for _, r in scored[:n]
        ]

    # ── DYNAMIC INJECTION ─────────────────────────────────────────────────────
    def inject_task_hints(self, user_input: str, task_type: str = "") -> str:
        """
        Generate a short hint block to prepend to the user message.
        Guides the model toward the right approach without changing the user's words.
        """
        if not task_type:
            task_type = self.classify_task(user_input)

        hints = {
            "bug_fix":        "→ Read the file first. Find root cause. Show the exact fix.",
            "code_generation":"→ Write production-ready code. Handle edge cases. Save with write_file.",
            "code_review":    "→ Analyze with analyze_code. Structure: Critical/High/Suggestions.",
            "refactoring":    "→ Read code. Ensure behavior preserved. Use refactor tools. Run tests.",
            "testing":        "→ Use generate_tests or fill_coverage_gaps. Cover happy+edge+error cases.",
            "security":       "→ Use security_scan first. Check OWASP Top 10. Provide CWE references.",
            "performance":    "→ State O() before/after. Measure first, optimize second.",
            "architecture":   "→ Use plan_task to decompose. State trade-offs. Plan MVP first.",
            "explanation":    "→ High-level first, then details. Use concrete code examples.",
        }
        hint = hints.get(task_type, "")
        if not hint:
            return user_input
        return f"[Task: {task_type}] {hint}\n\n{user_input}"

    # ── LEARNING FROM FEEDBACK ────────────────────────────────────────────────
    def record_example(self, user_input: str, response: str,
                       tools_used: list[str], score: float = 1.0):
        """Save a successful interaction as a future few-shot example."""
        task_type = self.classify_task(user_input)
        ex_id     = hashlib.md5(f"{user_input}{time.time()}".encode()).hexdigest()[:12]
        self._db.execute(
            "INSERT OR REPLACE INTO examples VALUES (?,?,?,?,?,?,?,?)",
            (ex_id, task_type, user_input[:500], response[:1000],
             json.dumps(tools_used), score, 0, time.time())
        )
        self._db.commit()

    def record_score(self, prompt_hash: str, task_type: str, score: float):
        """Record prompt performance for future optimization."""
        self._db.execute("""
            INSERT INTO prompt_scores VALUES (?,?,?,1,?)
            ON CONFLICT(prompt_hash) DO UPDATE SET
                score = (score * uses + ?) / (uses + 1),
                uses  = uses + 1
        """, (prompt_hash, task_type, time.time(), score))
        self._db.commit()

    # ── PROMPT OPTIMIZER ──────────────────────────────────────────────────────
    def optimize_prompt(self, task_type: str) -> Optional[str]:
        """
        Use LLM to generate an improved system prompt based on recorded performance.
        Called periodically to self-improve.
        """
        low_score_rows = self._db.execute(
            "SELECT prompt_hash, score FROM prompt_scores WHERE task_type=? AND score < 0.7 ORDER BY uses DESC LIMIT 5",
            (task_type,)
        ).fetchall()

        if not low_score_rows:
            return None

        current = TASK_PROMPTS.get(task_type, "")
        prompt  = (
            f"The current system prompt for '{task_type}' tasks is underperforming.\n"
            f"Current prompt:\n{current}\n\n"
            "Generate an improved version that will lead to better code generation results. "
            "Focus on: precision, edge case handling, and concrete actionable instructions. "
            "Output ONLY the improved prompt text:"
        )
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600, temperature=0.3, stream=False,
            )
            return resp.choices[0].message.content
        except Exception:
            return None

    def get_task_type(self, user_input: str) -> str:
        return self.classify_task(user_input)

    def stats(self) -> str:
        total_ex = self._db.execute("SELECT COUNT(*) FROM examples").fetchone()[0]
        by_type  = self._db.execute(
            "SELECT task_type, COUNT(*) FROM examples GROUP BY task_type"
        ).fetchall()
        lines = [f"PromptEngine: {total_ex} examples in database"]
        for t, c in by_type:
            lines.append(f"  {t}: {c}")
        return "\n".join(lines)

    def close(self):
        if self._db:
            self._db.close()
