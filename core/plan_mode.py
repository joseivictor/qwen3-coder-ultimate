"""
QWEN3-CODER ULTIMATE — Plan Mode v1.0
Formal two-phase execution: research-only → present plan → user approves → execute.
Blocks all write/execute tools during planning phase.
"""

import json
from dataclasses import dataclass, field
from typing import Optional


# Tools blocked in plan mode (read-only enforcement)
BLOCKED_IN_PLAN_MODE = {
    "write_file", "edit_file", "create_file", "delete_file",
    "run_command", "run_python", "run_script", "execute_code",
    "git_commit", "git_push", "git_checkout",
    "refactor_rename", "refactor_extract", "refactor_inline",
    "agent_run", "tdd_run", "background_run",
    "install_package", "docker_run",
}

# Always allowed even in plan mode
ALWAYS_ALLOWED = {
    "read_file", "list_directory", "file_tree", "search_in_files",
    "search_web", "fetch_url", "context7_get_docs",
    "analyze_code", "security_scan", "memory_recall",
    "reason", "agent_plan", "list_files",
}


@dataclass
class PlanStep:
    order:       int
    description: str
    tool:        Optional[str] = None
    args:        dict = field(default_factory=dict)
    risk:        str  = "low"   # low | medium | high


@dataclass
class Plan:
    goal:     str
    steps:    list[PlanStep] = field(default_factory=list)
    summary:  str = ""
    approved: bool = False


class PlanMode:
    """
    Formal plan mode. When active:
    - Write/execute tools are blocked (returns explanation instead)
    - Model accumulates a plan
    - /approve executes the plan step by step
    - /reject discards plan and exits plan mode
    """

    def __init__(self, client, model: str):
        self.client   = client
        self.model    = model
        self.active   = False
        self.current_plan: Optional[Plan] = None
        self._research_messages: list = []

    # ── ENTER / EXIT ──────────────────────────────────────────────────────────

    def enter(self, goal: str = "") -> str:
        self.active = True
        self.current_plan = Plan(goal=goal)
        self._research_messages = []
        return (
            f"[PLAN MODE ACTIVE]\n"
            f"Goal: {goal or '(not specified)'}\n\n"
            f"I will now RESEARCH ONLY — no writes or commands will execute.\n"
            f"When ready, I'll present a plan for your approval.\n"
            f"Commands: /approve (execute plan) | /reject (cancel) | /plan-status"
        )

    def exit(self, approved: bool = False) -> str:
        was_active = self.active
        self.active = False
        plan = self.current_plan
        self.current_plan = None
        self._research_messages = []
        if not was_active:
            return "Not in plan mode."
        if approved:
            return "[PLAN MODE EXITED] — Executing approved plan."
        return "[PLAN MODE EXITED] — Plan discarded."

    # ── TOOL GATE ─────────────────────────────────────────────────────────────

    def check_tool(self, tool_name: str, args: dict = None) -> tuple[bool, str]:
        """Returns (allowed, message). Called before every tool execution."""
        if not self.active:
            return True, ""
        if tool_name in ALWAYS_ALLOWED:
            return True, ""
        if tool_name in BLOCKED_IN_PLAN_MODE:
            return False, (
                f"[PLAN MODE] Tool '{tool_name}' blocked during planning.\n"
                f"Add this step to your plan instead. I'm collecting: {tool_name}({json.dumps(args or {})[:80]})"
            )
        # Unknown tool — allow with warning
        return True, f"[PLAN MODE] Warning: tool '{tool_name}' not in blocked list."

    def add_planned_step(self, tool: str, args: dict, description: str = "", risk: str = "low"):
        """Add a step to the current plan (called when blocked tool is attempted)."""
        if not self.current_plan:
            return
        order = len(self.current_plan.steps) + 1
        desc  = description or f"{tool}({', '.join(f'{k}={v!r}' for k,v in list(args.items())[:3])})"
        self.current_plan.steps.append(PlanStep(
            order=order, description=desc, tool=tool, args=args, risk=risk
        ))

    # ── PLAN GENERATION ───────────────────────────────────────────────────────

    def generate_plan(self, context: str = "") -> str:
        """Ask the model to generate a structured plan from research so far."""
        if not self.current_plan:
            return "No active plan."

        prompt = (
            f"Goal: {self.current_plan.goal}\n\n"
            f"Based on your research, create a step-by-step execution plan.\n"
            f"Format each step as:\n"
            f"  STEP N: [description] | TOOL: [tool_name] | RISK: [low/medium/high]\n\n"
            f"Context: {context[:2000]}"
        )
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a planning assistant. Generate a clear execution plan."},
                    {"role": "user",   "content": prompt},
                ],
                max_tokens=600, temperature=0.1, stream=False,
            )
            plan_text = resp.choices[0].message.content or ""
            self.current_plan.summary = plan_text
            return self._format_plan(plan_text)
        except Exception as e:
            return f"Plan generation failed: {e}"

    def _format_plan(self, plan_text: str) -> str:
        steps = self.current_plan.steps if self.current_plan else []
        lines = [
            "╔══════════════════════════════════════════════════════╗",
            f"║  PLAN: {(self.current_plan.goal or 'Task')[:46]:46} ║",
            "╠══════════════════════════════════════════════════════╣",
        ]
        if plan_text:
            for line in plan_text.splitlines()[:20]:
                lines.append(f"║  {line[:52]:52} ║")
        if steps:
            lines.append("╠══════════════════════════════════════════════════════╣")
            lines.append("║  Queued tool calls:                                  ║")
            for s in steps[:10]:
                risk_icon = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(s.risk, "⚪")
                desc = f"{risk_icon} {s.order}. {s.description}"[:52]
                lines.append(f"║  {desc:52} ║")
        lines += [
            "╠══════════════════════════════════════════════════════╣",
            "║  Type /approve to execute | /reject to cancel        ║",
            "╚══════════════════════════════════════════════════════╝",
        ]
        return "\n".join(lines)

    def status(self) -> str:
        if not self.active:
            return "Plan mode: OFF"
        steps = len(self.current_plan.steps) if self.current_plan else 0
        goal  = (self.current_plan.goal or "unspecified")[:40] if self.current_plan else ""
        return f"Plan mode: ON | Goal: {goal} | {steps} queued steps"

    def render(self) -> str:
        if not self.current_plan:
            return "No active plan."
        return self._format_plan(self.current_plan.summary)
