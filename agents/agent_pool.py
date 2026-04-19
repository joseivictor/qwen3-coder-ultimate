"""
QWEN3-CODER ULTIMATE — Agent Pool v1.0
Spawn N specialized worker agents in parallel with role-based system prompts.
Roles: Coder, Reviewer, Tester, Documenter, Security, Planner, Optimizer.
"""

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class AgentRole(Enum):
    CODER      = "coder"
    REVIEWER   = "reviewer"
    TESTER     = "tester"
    DOCUMENTER = "documenter"
    SECURITY   = "security"
    PLANNER    = "planner"
    OPTIMIZER  = "optimizer"
    DEBUGGER   = "debugger"


ROLE_PROMPTS = {
    AgentRole.CODER: (
        "You are an expert software engineer. Write clean, efficient, production-ready code. "
        "Follow best practices, handle edge cases, and include error handling. "
        "Output complete, working implementations."
    ),
    AgentRole.REVIEWER: (
        "You are a senior code reviewer. Analyze code for: correctness, readability, performance, "
        "maintainability, edge cases, and best practice violations. "
        "Provide specific, actionable feedback with line references. "
        "Rate severity: critical/high/medium/low."
    ),
    AgentRole.TESTER: (
        "You are a QA expert and test engineer. Write comprehensive tests covering: "
        "happy paths, edge cases, error conditions, boundary values, and integration scenarios. "
        "Use pytest for Python, Jest for JS. Prioritize test coverage and determinism."
    ),
    AgentRole.DOCUMENTER: (
        "You are a technical writer. Create clear, comprehensive documentation including: "
        "function docstrings, module-level docs, usage examples, parameter descriptions, "
        "return values, exceptions raised. Follow Google/NumPy docstring style."
    ),
    AgentRole.SECURITY: (
        "You are a security engineer specialized in application security. "
        "Identify vulnerabilities: OWASP Top 10, injection, auth issues, crypto failures, "
        "sensitive data exposure, insecure dependencies. Provide CVE references and remediations."
    ),
    AgentRole.PLANNER: (
        "You are a software architect. Design systems, plan implementations, decompose tasks, "
        "identify risks, estimate complexity, suggest design patterns. "
        "Think about scalability, maintainability, and trade-offs."
    ),
    AgentRole.OPTIMIZER: (
        "You are a performance engineer. Analyze and optimize code for: time complexity, "
        "space complexity, I/O efficiency, caching opportunities, algorithmic improvements. "
        "Provide before/after comparisons with complexity analysis."
    ),
    AgentRole.DEBUGGER: (
        "You are an expert debugger. Analyze errors, stack traces, and unexpected behavior. "
        "Identify root causes, not just symptoms. Propose precise fixes with explanations. "
        "Check for common pitfalls: off-by-one, race conditions, null dereferences, type errors."
    ),
}


@dataclass
class AgentTask:
    id:       str
    role:     AgentRole
    task:     str
    context:  str = ""
    priority: int = 0


@dataclass
class AgentResult:
    task_id:   str
    role:      AgentRole
    output:    str
    elapsed:   float = 0.0
    success:   bool = True
    error:     str = ""
    tokens:    int = 0


@dataclass
class PoolResult:
    results:     list[AgentResult] = field(default_factory=list)
    merged:      str = ""
    total_time:  float = 0.0
    success_pct: float = 0.0


class WorkerAgent:
    """A single specialized agent with a fixed role and tool access."""

    def __init__(self, client, model: str, role: AgentRole, all_tools: list, executor):
        self.client    = client
        self.model     = model
        self.role      = role
        self.all_tools = all_tools
        self.executor  = executor
        self.system    = ROLE_PROMPTS.get(role, "You are a helpful assistant.")

    def run(self, task: AgentTask, max_steps: int = 8) -> AgentResult:
        start   = time.time()
        history = [
            {"role": "system", "content": self.system},
            {"role": "user",   "content": self._build_prompt(task)},
        ]

        for step in range(max_steps):
            try:
                kwargs = {
                    "model":       self.model,
                    "messages":    history,
                    "max_tokens":  4096,
                    "temperature": 0.1,
                    "stream":      False,
                }
                if self.all_tools:
                    kwargs["tools"]       = self.all_tools
                    kwargs["tool_choice"] = "auto"

                resp = self.client.chat.completions.create(**kwargs)
                msg  = resp.choices[0].message

                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    tc_list = [{
                        "id": tc.id, "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments}
                    } for tc in msg.tool_calls]
                    history.append({
                        "role": "assistant", "content": msg.content or "", "tool_calls": tc_list
                    })
                    for tc in msg.tool_calls:
                        try:
                            args = json.loads(tc.function.arguments)
                        except Exception:
                            args = {}
                        tool_result = self.executor.execute(tc.function.name, args)
                        history.append({
                            "role": "tool", "tool_call_id": tc.id, "content": str(tool_result)
                        })
                else:
                    return AgentResult(
                        task_id = task.id,
                        role    = self.role,
                        output  = msg.content or "",
                        elapsed = round(time.time() - start, 2),
                        success = True,
                    )

            except Exception as e:
                return AgentResult(
                    task_id = task.id,
                    role    = self.role,
                    output  = "",
                    elapsed = round(time.time() - start, 2),
                    success = False,
                    error   = str(e),
                )

        return AgentResult(
            task_id = task.id,
            role    = self.role,
            output  = "(max steps reached)",
            elapsed = round(time.time() - start, 2),
            success = False,
        )

    def _build_prompt(self, task: AgentTask) -> str:
        parts = [f"Task: {task.task}"]
        if task.context:
            parts.append(f"\nContext:\n{task.context[:2000]}")
        return "\n".join(parts)


class AgentPool:
    """
    Manages a pool of specialized agents running in parallel.
    Supports: parallel execution, result merging, priority queues.
    """

    def __init__(self, client, model: str, all_tools: list, executor,
                 max_workers: int = 4):
        self.client      = client
        self.model       = model
        self.all_tools   = all_tools
        self.executor    = executor
        self.max_workers = max_workers
        self._agents:  dict[AgentRole, WorkerAgent] = {}

    def _get_agent(self, role: AgentRole) -> WorkerAgent:
        if role not in self._agents:
            self._agents[role] = WorkerAgent(
                self.client, self.model, role, self.all_tools, self.executor
            )
        return self._agents[role]

    def run_single(self, task: str, role: AgentRole = AgentRole.CODER,
                   context: str = "") -> AgentResult:
        """Run a single task with the specified agent role."""
        agent_task = AgentTask(id="t0", role=role, task=task, context=context)
        return self._get_agent(role).run(agent_task)

    def run_parallel(self, tasks: list[AgentTask]) -> PoolResult:
        """Execute multiple tasks in parallel, one agent per task."""
        start   = time.time()
        results = []

        tasks_sorted = sorted(tasks, key=lambda t: -t.priority)

        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(tasks))) as pool:
            future_map: dict[Future, AgentTask] = {}
            for task in tasks_sorted:
                agent  = self._get_agent(task.role)
                future = pool.submit(agent.run, task)
                future_map[future] = task

            for future in as_completed(future_map):
                try:
                    results.append(future.result(timeout=300))
                except Exception as e:
                    t = future_map[future]
                    results.append(AgentResult(
                        task_id=t.id, role=t.role, output="", success=False, error=str(e)
                    ))

        success_pct = sum(1 for r in results if r.success) / len(results) * 100 if results else 0

        return PoolResult(
            results     = results,
            merged      = self._merge_results(results, tasks),
            total_time  = round(time.time() - start, 2),
            success_pct = round(success_pct, 1),
        )

    def pipeline(self, task: str, context: str = "",
                 roles: list[AgentRole] = None) -> PoolResult:
        """
        Sequential pipeline: each agent refines the previous agent's output.
        Default pipeline: PLANNER → CODER → REVIEWER → TESTER → SECURITY
        """
        if roles is None:
            roles = [AgentRole.PLANNER, AgentRole.CODER, AgentRole.REVIEWER, AgentRole.TESTER]

        start    = time.time()
        results  = []
        current  = context or ""
        original = task

        for i, role in enumerate(roles):
            prompt = original if i == 0 else f"Refine/extend the previous output for: {original}"
            agent_task = AgentTask(id=f"p{i}", role=role, task=prompt, context=current)
            result     = self._get_agent(role).run(agent_task)
            results.append(result)
            if result.success and result.output:
                current = result.output

        return PoolResult(
            results     = results,
            merged      = current,
            total_time  = round(time.time() - start, 2),
            success_pct = sum(1 for r in results if r.success) / len(results) * 100,
        )

    def multi_review(self, code: str, filepath: str = "") -> str:
        """Run REVIEWER + SECURITY + OPTIMIZER on code simultaneously."""
        tasks = [
            AgentTask(id="rev",  role=AgentRole.REVIEWER,  task="Review this code thoroughly", context=code, priority=2),
            AgentTask(id="sec",  role=AgentRole.SECURITY,   task="Security audit this code", context=code, priority=2),
            AgentTask(id="opt",  role=AgentRole.OPTIMIZER,  task="Optimize this code for performance", context=code, priority=1),
        ]
        pool_result = self.run_parallel(tasks)
        return self._merge_results(pool_result.results, tasks)

    def _merge_results(self, results: list[AgentResult], tasks: list[AgentTask]) -> str:
        task_map = {t.id: t for t in tasks}
        lines    = ["=== AGENT POOL RESULTS ===\n"]
        for r in results:
            role_name = r.role.value.upper()
            status    = "✅" if r.success else "❌"
            task_desc = task_map.get(r.task_id, AgentTask("?", r.role, "?")).task[:60]
            lines.append(f"{status} [{role_name}] ({r.elapsed:.1f}s) — {task_desc}")
            lines.append("-" * 60)
            if r.success:
                lines.append(r.output[:1500])
            else:
                lines.append(f"Error: {r.error}")
            lines.append("")
        return "\n".join(lines)

    def status(self) -> str:
        return (
            f"AgentPool: {len(self._agents)} active agents | "
            f"Max workers: {self.max_workers}\n"
            f"Active roles: {', '.join(r.value for r in self._agents)}"
        )
