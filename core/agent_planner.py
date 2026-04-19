"""
QWEN3-CODER ULTIMATE — Agent Planner v1.0
Goal decomposition, dependency graph, dynamic re-planning, ETA estimation.
"""

import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class TaskStatus(Enum):
    PENDING   = "pending"
    RUNNING   = "running"
    DONE      = "done"
    FAILED    = "failed"
    BLOCKED   = "blocked"
    SKIPPED   = "skipped"


@dataclass
class SubTask:
    id:           str
    title:        str
    description:  str
    depends_on:   list[str] = field(default_factory=list)
    status:       TaskStatus = TaskStatus.PENDING
    result:       str = ""
    error:        str = ""
    started_at:   float = 0.0
    finished_at:  float = 0.0
    estimated_s:  float = 30.0
    retry_count:  int = 0
    max_retries:  int = 2
    agent_role:   str = "coder"

    @property
    def duration(self) -> float:
        if self.started_at and self.finished_at:
            return self.finished_at - self.started_at
        return 0.0

    @property
    def is_terminal(self) -> bool:
        return self.status in (TaskStatus.DONE, TaskStatus.FAILED, TaskStatus.SKIPPED)


class AgentPlanner:
    """
    Decomposes high-level goals into executable sub-tasks,
    builds a dependency graph, dynamically re-plans on failure,
    and tracks progress with ETA estimation.
    """

    DECOMPOSE_PROMPT = """You are a software project planner. Decompose the goal into concrete sub-tasks.

Output ONLY valid JSON (no markdown):
{
  "tasks": [
    {
      "id": "t1",
      "title": "Short title",
      "description": "What exactly to do",
      "depends_on": [],
      "agent_role": "coder|reviewer|tester|documenter|security",
      "estimated_seconds": 30
    }
  ]
}

Rules:
- 3 to 10 tasks max
- Each task must be atomic and achievable by a single LLM call + tools
- depends_on lists task ids that must complete before this one
- No circular dependencies
- agent_role matches the specialist best suited for the task"""

    REPLAN_PROMPT = """A sub-task failed. Analyze and suggest a recovery plan.

Output ONLY valid JSON:
{
  "action": "retry|skip|substitute|abort",
  "new_task": {
    "id": "t_new",
    "title": "...",
    "description": "...",
    "depends_on": [],
    "agent_role": "coder",
    "estimated_seconds": 30
  },
  "reason": "..."
}

If action is "retry" or "skip" or "abort", omit "new_task"."""

    def __init__(self, client, model: str):
        self.client = client
        self.model  = model
        self.tasks:  dict[str, SubTask] = {}
        self.goal:   str = ""
        self._log:   list[str] = []

    def _call(self, messages: list, max_tokens: int = 2048) -> str:
        try:
            resp = self.client.chat.completions.create(
                model=self.model, messages=messages,
                max_tokens=max_tokens, temperature=0.1, stream=False,
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            return f"[PlannerError: {e}]"

    # ── DECOMPOSITION ─────────────────────────────────────────────────────────
    def decompose(self, goal: str, context: str = "") -> list[SubTask]:
        """Break a high-level goal into a list of SubTasks with dependency graph."""
        self.goal  = goal
        self.tasks = {}

        user_msg = f"Goal: {goal}"
        if context:
            user_msg += f"\n\nContext:\n{context[:2000]}"

        messages = [
            {"role": "system", "content": self.DECOMPOSE_PROMPT},
            {"role": "user",   "content": user_msg},
        ]
        raw  = self._call(messages)
        data = self._parse_json(raw)

        if not data or "tasks" not in data:
            return self._fallback_plan(goal)

        tasks = []
        for item in data["tasks"]:
            task = SubTask(
                id           = item.get("id", str(uuid.uuid4())[:8]),
                title        = item.get("title", "Unknown"),
                description  = item.get("description", ""),
                depends_on   = item.get("depends_on", []),
                estimated_s  = float(item.get("estimated_seconds", 30)),
                agent_role   = item.get("agent_role", "coder"),
            )
            self.tasks[task.id] = task
            tasks.append(task)

        self._validate_deps(tasks)
        self._log.append(f"Decomposed '{goal}' into {len(tasks)} tasks.")
        return tasks

    def _fallback_plan(self, goal: str) -> list[SubTask]:
        task = SubTask(
            id          = "t1",
            title       = "Execute goal",
            description = goal,
            depends_on  = [],
        )
        self.tasks["t1"] = task
        return [task]

    def _validate_deps(self, tasks: list[SubTask]):
        ids = {t.id for t in tasks}
        for task in tasks:
            task.depends_on = [d for d in task.depends_on if d in ids]

    # ── GRAPH TRAVERSAL ───────────────────────────────────────────────────────
    def get_ready_tasks(self) -> list[SubTask]:
        """Return tasks that are pending and have all dependencies satisfied."""
        ready = []
        for task in self.tasks.values():
            if task.status != TaskStatus.PENDING:
                continue
            deps_done = all(
                self.tasks[dep].status == TaskStatus.DONE
                for dep in task.depends_on
                if dep in self.tasks
            )
            if deps_done:
                ready.append(task)
        return ready

    def mark_running(self, task_id: str):
        if task_id in self.tasks:
            self.tasks[task_id].status     = TaskStatus.RUNNING
            self.tasks[task_id].started_at = time.time()

    def mark_done(self, task_id: str, result: str = ""):
        if task_id in self.tasks:
            t = self.tasks[task_id]
            t.status      = TaskStatus.DONE
            t.result      = result
            t.finished_at = time.time()
            self._log.append(f"✅ {t.title} ({t.duration:.1f}s)")

    def mark_failed(self, task_id: str, error: str = ""):
        if task_id in self.tasks:
            t = self.tasks[task_id]
            t.status      = TaskStatus.FAILED
            t.error       = error
            t.finished_at = time.time()
            self._log.append(f"❌ {t.title}: {error[:100]}")

    # ── DYNAMIC RE-PLANNING ───────────────────────────────────────────────────
    def replan(self, failed_task_id: str) -> dict:
        """
        Given a failed task, ask the LLM how to recover.
        Returns action dict: {action, new_task?, reason}.
        """
        task = self.tasks.get(failed_task_id)
        if not task:
            return {"action": "abort", "reason": "Task not found"}

        completed_summary = "\n".join(
            f"- [{t.status.value}] {t.title}: {t.result[:100]}"
            for t in self.tasks.values()
        )

        user_msg = (
            f"Goal: {self.goal}\n\n"
            f"Failed task: [{task.id}] {task.title}\n"
            f"Error: {task.error}\n\n"
            f"All tasks status:\n{completed_summary}"
        )
        messages = [
            {"role": "system", "content": self.REPLAN_PROMPT},
            {"role": "user",   "content": user_msg},
        ]
        raw    = self._call(messages)
        data   = self._parse_json(raw)

        if not data:
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.PENDING
                return {"action": "retry", "reason": "Auto-retry (parse failed)"}
            return {"action": "skip", "reason": "Max retries exceeded"}

        action = data.get("action", "retry")

        if action == "retry" and task.retry_count < task.max_retries:
            task.retry_count += 1
            task.status = TaskStatus.PENDING
            task.error  = ""

        elif action == "substitute" and "new_task" in data:
            new_t = data["new_task"]
            new_task = SubTask(
                id          = new_t.get("id", f"t_r{len(self.tasks)}"),
                title       = new_t.get("title", "Recovery task"),
                description = new_t.get("description", ""),
                depends_on  = new_t.get("depends_on", []),
                agent_role  = new_t.get("agent_role", "coder"),
                estimated_s = float(new_t.get("estimated_seconds", 30)),
            )
            self.tasks[new_task.id] = new_task
            self._log.append(f"♻️  Substituted '{task.title}' → '{new_task.title}'")

        elif action == "skip":
            task.status = TaskStatus.SKIPPED
            for dep_task in self.tasks.values():
                if failed_task_id in dep_task.depends_on:
                    dep_task.depends_on.remove(failed_task_id)

        elif action == "abort":
            for t in self.tasks.values():
                if t.status == TaskStatus.PENDING:
                    t.status = TaskStatus.SKIPPED

        return data

    # ── PROGRESS & ETA ────────────────────────────────────────────────────────
    def progress(self) -> dict:
        total   = len(self.tasks)
        done    = sum(1 for t in self.tasks.values() if t.status == TaskStatus.DONE)
        failed  = sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED)
        running = sum(1 for t in self.tasks.values() if t.status == TaskStatus.RUNNING)
        pending = sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING)

        completed_tasks = [t for t in self.tasks.values() if t.duration > 0]
        avg_duration = (
            sum(t.duration for t in completed_tasks) / len(completed_tasks)
            if completed_tasks else 30.0
        )
        eta_seconds = pending * avg_duration

        return {
            "total":    total,
            "done":     done,
            "failed":   failed,
            "running":  running,
            "pending":  pending,
            "pct":      round(done / total * 100, 1) if total else 0,
            "eta_s":    round(eta_seconds, 0),
            "eta_str":  self._format_eta(eta_seconds),
        }

    def _format_eta(self, seconds: float) -> str:
        if seconds < 60:   return f"{int(seconds)}s"
        if seconds < 3600: return f"{int(seconds//60)}m {int(seconds%60)}s"
        return f"{int(seconds//3600)}h {int((seconds%3600)//60)}m"

    def render_plan(self) -> str:
        """Return a rich text representation of the current plan."""
        lines = [f"📋 Plan: {self.goal}", ""]
        status_icons = {
            TaskStatus.PENDING:  "⬜",
            TaskStatus.RUNNING:  "🔄",
            TaskStatus.DONE:     "✅",
            TaskStatus.FAILED:   "❌",
            TaskStatus.BLOCKED:  "🔒",
            TaskStatus.SKIPPED:  "⏭️",
        }
        for task in self.tasks.values():
            icon = status_icons.get(task.status, "?")
            deps = f" (needs: {', '.join(task.depends_on)})" if task.depends_on else ""
            role = f" [{task.agent_role}]"
            lines.append(f"  {icon} [{task.id}]{role} {task.title}{deps}")
            if task.error:
                lines.append(f"       ⚠ {task.error[:80]}")
            if task.result and task.status == TaskStatus.DONE:
                lines.append(f"       → {task.result[:80]}")

        p = self.progress()
        lines += [
            "",
            f"Progress: {p['done']}/{p['total']} ({p['pct']}%) | ETA: {p['eta_str']}",
        ]
        if self._log:
            lines += ["", "Recent events:"] + [f"  {l}" for l in self._log[-5:]]
        return "\n".join(lines)

    # ── HELPERS ───────────────────────────────────────────────────────────────
    def _parse_json(self, raw: str) -> Optional[dict]:
        raw = raw.strip()
        for start_c, end_c in [("{", "}"), ("[", "]")]:
            start = raw.find(start_c)
            end   = raw.rfind(end_c) + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(raw[start:end])
                except Exception:
                    pass
        return None

    def export_plan(self) -> dict:
        return {
            "goal": self.goal,
            "tasks": [
                {
                    "id":          t.id,
                    "title":       t.title,
                    "description": t.description,
                    "depends_on":  t.depends_on,
                    "status":      t.status.value,
                    "agent_role":  t.agent_role,
                    "duration_s":  round(t.duration, 2),
                    "result":      t.result[:200] if t.result else "",
                }
                for t in self.tasks.values()
            ],
            "progress": self.progress(),
        }
