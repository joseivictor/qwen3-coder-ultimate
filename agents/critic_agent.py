"""
QWEN3-CODER ULTIMATE — Critic Agent v1.0
Reviews all generated code before delivery. Configurable strictness.
Checks: correctness, style, security, performance, completeness.
"""

import re
import json
from dataclasses import dataclass, field
from enum import Enum


class Strictness(Enum):
    LAX     = "lax"      # Only critical issues
    NORMAL  = "normal"   # Critical + high
    STRICT  = "strict"   # All issues
    PEDANTIC = "pedantic" # Including style nits


@dataclass
class CritiqueIssue:
    severity: str    # critical | high | medium | low | style
    category: str    # correctness | security | performance | style | completeness
    message:  str
    line:     int = 0
    fix:      str = ""


@dataclass
class CritiqueResult:
    approved:   bool
    score:      int           # 0-100
    issues:     list[CritiqueIssue] = field(default_factory=list)
    summary:    str = ""
    revised:    str = ""      # Revised code if auto-fix was applied
    iterations: int = 1


class CriticAgent:
    """
    Autonomous code review agent that:
    1. Analyzes code for issues at configurable strictness
    2. Requests revisions with specific feedback
    3. Iterates until the code meets the quality bar
    4. Returns approved code or detailed rejection report
    """

    CRITIC_SYSTEM = """You are a world-class code reviewer with expertise in:
- Software correctness and logic errors
- Security vulnerabilities (OWASP Top 10)
- Performance anti-patterns
- Code style and readability
- API completeness and edge cases

Analyze code and output ONLY valid JSON:
{
  "score": <0-100>,
  "approved": <true/false>,
  "issues": [
    {
      "severity": "critical|high|medium|low|style",
      "category": "correctness|security|performance|style|completeness",
      "message": "Clear description of the issue",
      "line": <line number or 0>,
      "fix": "Specific fix suggestion"
    }
  ],
  "summary": "Overall assessment in 1-2 sentences"
}

Severity thresholds:
- critical: Logic errors, data loss risk, security holes → score 0-40
- high: Missing error handling, potential crashes, perf issues → score 41-65
- medium: Poor practices, missing validation → score 66-80
- low: Minor improvements → score 81-90
- style: Naming, formatting → score 91-100"""

    REVISION_SYSTEM = """You are an expert programmer. Fix the code based on the reviewer's feedback.
Output ONLY the corrected, complete code with no markdown fences, no explanations.
Apply ALL critical and high severity fixes. Apply medium fixes if reasonable."""

    STRICTNESS_THRESHOLDS = {
        Strictness.LAX:      40,
        Strictness.NORMAL:   65,
        Strictness.STRICT:   80,
        Strictness.PEDANTIC: 90,
    }

    def __init__(self, client, model: str,
                 strictness: Strictness = Strictness.NORMAL):
        self.client     = client
        self.model      = model
        self.strictness = strictness
        self.threshold  = self.STRICTNESS_THRESHOLDS[strictness]

    def _call(self, messages: list, max_tokens: int = 3000, json_mode: bool = False) -> str:
        try:
            kwargs = {
                "model":       self.model,
                "messages":    messages,
                "max_tokens":  max_tokens,
                "temperature": 0.1,
                "stream":      False,
            }
            resp = self.client.chat.completions.create(**kwargs)
            return resp.choices[0].message.content or ""
        except Exception as e:
            return f"[CriticError: {e}]"

    # ── SINGLE REVIEW ─────────────────────────────────────────────────────────
    def review(self, code: str, task_context: str = "",
               language: str = "python") -> CritiqueResult:
        """Review code and return a CritiqueResult."""
        user_msg = (
            f"Language: {language}\n"
            f"{'Task context: ' + task_context[:500] + chr(10) if task_context else ''}"
            f"Code to review:\n```{language}\n{code[:4000]}\n```"
        )
        raw = self._call(
            [{"role": "system", "content": self.CRITIC_SYSTEM},
             {"role": "user",   "content": user_msg}],
        )
        return self._parse_critique(raw, code)

    def _parse_critique(self, raw: str, original_code: str) -> CritiqueResult:
        try:
            start = raw.find("{")
            end   = raw.rfind("}") + 1
            data  = json.loads(raw[start:end])

            issues = [
                CritiqueIssue(
                    severity = i.get("severity", "medium"),
                    category = i.get("category", "correctness"),
                    message  = i.get("message", ""),
                    line     = i.get("line", 0),
                    fix      = i.get("fix", ""),
                )
                for i in data.get("issues", [])
            ]

            score    = max(0, min(100, int(data.get("score", 50))))
            approved = score >= self.threshold and not any(
                i.severity == "critical" for i in issues
            )

            return CritiqueResult(
                approved = approved,
                score    = score,
                issues   = issues,
                summary  = data.get("summary", ""),
            )
        except Exception:
            return CritiqueResult(
                approved = False,
                score    = 0,
                summary  = f"Review parse error. Raw: {raw[:200]}",
            )

    # ── ITERATIVE REVIEW + REVISION ───────────────────────────────────────────
    def review_and_revise(self, code: str, task_context: str = "",
                          language: str = "python",
                          max_iterations: int = 3) -> CritiqueResult:
        """
        Review code, request revisions if needed, iterate until approved
        or max_iterations reached.
        """
        current = code

        for i in range(max_iterations):
            result = self.review(current, task_context, language)
            result.iterations = i + 1

            if result.approved:
                result.revised = current if current != code else ""
                return result

            critical_high = [iss for iss in result.issues
                             if iss.severity in ("critical", "high")]

            if not critical_high and i > 0:
                result.approved = True
                result.revised  = current
                return result

            feedback = self._format_feedback(result.issues)
            revision_prompt = (
                f"Original task: {task_context[:300]}\n\n"
                f"Current code:\n```{language}\n{current[:3000]}\n```\n\n"
                f"Reviewer feedback:\n{feedback}\n\n"
                "Fix ALL critical and high severity issues. Return ONLY the corrected code:"
            )

            revised = self._call(
                [{"role": "system", "content": self.REVISION_SYSTEM},
                 {"role": "user",   "content": revision_prompt}],
                max_tokens=4000,
            )
            revised = self._clean_code(revised, language)

            if revised and revised != current and len(revised) > 20:
                current = revised
            else:
                break

        final = self.review(current, task_context, language)
        final.iterations = max_iterations
        final.revised    = current if current != code else ""
        return final

    # ── QUICK CHECKS ──────────────────────────────────────────────────────────
    def quick_check(self, code: str, language: str = "python") -> str:
        """Fast, non-iterative review returning a formatted string."""
        result = self.review(code, language=language)
        return self.format_report(result)

    def gate(self, code: str, task_context: str = "", language: str = "python") -> tuple[bool, str]:
        """
        Quality gate: returns (approved, reason).
        Use before delivering code to user.
        """
        result = self.review_and_revise(code, task_context, language, max_iterations=2)
        approved_code = result.revised or code
        return result.approved, approved_code

    # ── SPECIALIZED REVIEWS ───────────────────────────────────────────────────
    def security_review(self, code: str, language: str = "python") -> CritiqueResult:
        """Security-focused review (overrides system prompt)."""
        system = (
            "You are a security engineer. Focus ONLY on security vulnerabilities. "
            "Check for: injection, auth bypass, crypto issues, sensitive data, insecure dependencies. "
            "Output JSON same format as before."
        )
        raw = self._call(
            [{"role": "system", "content": system},
             {"role": "user",   "content": f"Security audit:\n```{language}\n{code[:4000]}\n```"}]
        )
        return self._parse_critique(raw, code)

    def performance_review(self, code: str, language: str = "python") -> CritiqueResult:
        """Performance-focused review."""
        system = (
            "You are a performance engineer. Focus ONLY on performance issues. "
            "Check for: O(n²) algorithms, unnecessary loops, missing caching, blocking I/O, "
            "memory leaks, inefficient data structures. "
            "Output JSON same format as before."
        )
        raw = self._call(
            [{"role": "system", "content": system},
             {"role": "user",   "content": f"Performance review:\n```{language}\n{code[:4000]}\n```"}]
        )
        return self._parse_critique(raw, code)

    # ── HELPERS ───────────────────────────────────────────────────────────────
    def _format_feedback(self, issues: list[CritiqueIssue]) -> str:
        lines = []
        for i, iss in enumerate(issues, 1):
            line_ref = f" (line {iss.line})" if iss.line else ""
            lines.append(
                f"{i}. [{iss.severity.upper()}] {iss.category}{line_ref}: {iss.message}"
                + (f"\n   Fix: {iss.fix}" if iss.fix else "")
            )
        return "\n".join(lines)

    def _clean_code(self, raw: str, language: str) -> str:
        raw = re.sub(rf"```{language}\n?", "", raw)
        raw = re.sub(r"```\n?", "", raw)
        return raw.strip()

    def format_report(self, result: CritiqueResult) -> str:
        status = "✅ APPROVED" if result.approved else "❌ NEEDS REVISION"
        sev_icons = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢", "style": "⚪"}

        lines = [
            f"{status} | Score: {result.score}/100 | Strictness: {self.strictness.value}",
            f"Summary: {result.summary}",
            "",
        ]

        if result.issues:
            lines.append(f"Issues ({len(result.issues)}):")
            for iss in sorted(result.issues, key=lambda x: {"critical":0,"high":1,"medium":2,"low":3,"style":4}.get(x.severity,5)):
                icon    = sev_icons.get(iss.severity, "⚪")
                line_ref = f" line {iss.line}" if iss.line else ""
                lines.append(f"  {icon} [{iss.severity}]{line_ref}: {iss.message}")
                if iss.fix:
                    lines.append(f"     Fix: {iss.fix}")

        if result.iterations > 1:
            lines.append(f"\nIterations: {result.iterations}")

        if result.revised:
            lines.append(f"\nRevised code available ({len(result.revised)} chars).")

        return "\n".join(lines)

    def set_strictness(self, level: str):
        try:
            self.strictness = Strictness(level.lower())
            self.threshold  = self.STRICTNESS_THRESHOLDS[self.strictness]
        except ValueError:
            pass
