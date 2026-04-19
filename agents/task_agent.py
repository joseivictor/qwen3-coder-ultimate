"""
QWEN3-CODER ULTIMATE — Task Agent v1.0
Real sub-agents with fully isolated context, history, and tool scope.
Matches Claude Code's Task tool: spawns an independent agent, collects result.

Usage (as a tool the model can call):
  task_agent.spawn(task="...", context="...", tools=[...], max_turns=20)

Or registered as a tool so the LLM can spawn sub-agents itself.
"""

import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TaskResult:
    task_id:    str
    task:       str
    output:     str
    success:    bool
    turns:      int
    tool_calls: int
    duration_s: float
    error:      str   = ""
    artifacts:  list  = field(default_factory=list)   # files written, etc.


class TaskAgent:
    """
    Isolated sub-agent. Has its own:
    - history (independent of parent)
    - tool scope (subset of parent tools or full set)
    - model (can differ from parent)
    - token budget

    Created by the parent agent via the `task` tool.
    Runs synchronously, returns TaskResult.
    """

    DEFAULT_SYSTEM = (
        "You are a focused sub-agent. Complete exactly the task given. "
        "Use tools as needed. Be concise. When done, output your final result "
        "prefixed with [RESULT]. Do not ask for clarification."
    )

    def __init__(
        self,
        client,
        model:       str,
        all_tools:   list,
        executor,                        # ToolExecutor from parent
        permissions  = None,             # PermissionManager (inherited)
        max_tokens:  int  = 4096,
        max_turns:   int  = 20,
        temperature: float = 0.1,
    ):
        self.client      = client
        self.model       = model
        self.all_tools   = all_tools
        self.executor    = executor
        self.permissions = permissions
        self.max_tokens  = max_tokens
        self.max_turns   = max_turns
        self.temperature = temperature
        self._active_tasks: dict[str, TaskResult] = {}

    # ── SPAWN ─────────────────────────────────────────────────────────────────

    def spawn(
        self,
        task:       str,
        context:    str   = "",
        tools:      list  = None,       # subset of tools; None = all
        system:     str   = "",
        max_turns:  int   = None,
        model:      str   = None,
    ) -> TaskResult:
        """
        Spawn a new isolated sub-agent for the given task.
        Returns TaskResult when complete.
        """
        task_id   = str(uuid.uuid4())[:8]
        start     = time.time()
        turns     = 0
        tool_call_count = 0
        artifacts = []

        # Tool scope
        tool_defs = tools if tools is not None else self.all_tools
        # Filter by name if strings passed
        if tool_defs and isinstance(tool_defs[0], str):
            names = set(tool_defs)
            tool_defs = [t for t in self.all_tools if t.get("function", {}).get("name") in names]

        # Build isolated history
        sys_content = system or self.DEFAULT_SYSTEM
        if context:
            sys_content += f"\n\nContext from parent agent:\n{context[:3000]}"

        history = [
            {"role": "system", "content": sys_content},
            {"role": "user",   "content": task},
        ]

        chosen_model = model or self.model
        output = ""

        try:
            for _ in range(max_turns or self.max_turns):
                turns += 1

                params = {
                    "model":       chosen_model,
                    "messages":    history,
                    "tools":       tool_defs or None,
                    "tool_choice": "auto" if tool_defs else None,
                    "temperature": self.temperature,
                    "max_tokens":  self.max_tokens,
                    "stream":      False,
                }
                if not tool_defs:
                    params.pop("tools", None)
                    params.pop("tool_choice", None)

                resp = self.client.chat.completions.create(**params)
                msg  = resp.choices[0].message

                # Handle tool calls
                if msg.tool_calls:
                    history.append({
                        "role":       "assistant",
                        "content":    msg.content or "",
                        "tool_calls": [
                            {
                                "id":       tc.id,
                                "type":     "function",
                                "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                            }
                            for tc in msg.tool_calls
                        ],
                    })

                    for tc in msg.tool_calls:
                        tool_call_count += 1
                        try:
                            args = json.loads(tc.function.arguments)
                        except Exception:
                            args = {}

                        # Permission gate (inherited from parent)
                        if self.permissions:
                            allowed = self.permissions.prompt_and_check(tc.function.name, args)
                            if not allowed:
                                result = f"[BLOCKED] Tool '{tc.function.name}' was denied by permissions."
                            else:
                                result = str(self.executor.execute(tc.function.name, args))
                        else:
                            result = str(self.executor.execute(tc.function.name, args))

                        # Track artifacts
                        if tc.function.name in ("write_file", "edit_file", "bulk_write"):
                            path = args.get("path") or args.get("filename", "")
                            if path:
                                artifacts.append(path)

                        history.append({
                            "role":         "tool",
                            "tool_call_id": tc.id,
                            "content":      result,
                        })
                    continue

                # Final response
                output = msg.content or ""
                history.append({"role": "assistant", "content": output})

                # Extract [RESULT] tag if present
                if "[RESULT]" in output:
                    output = output[output.index("[RESULT]") + len("[RESULT]"):].strip()

                break

        except Exception as e:
            return TaskResult(
                task_id=task_id, task=task, output="",
                success=False, turns=turns, tool_calls=tool_call_count,
                duration_s=time.time() - start, error=str(e),
            )

        result = TaskResult(
            task_id    = task_id,
            task       = task,
            output     = output,
            success    = bool(output),
            turns      = turns,
            tool_calls = tool_call_count,
            duration_s = time.time() - start,
            artifacts  = artifacts,
        )
        self._active_tasks[task_id] = result
        return result

    # ── PARALLEL SPAWN ────────────────────────────────────────────────────────

    def spawn_parallel(self, tasks: list[dict], max_workers: int = 4) -> list[TaskResult]:
        """
        Spawn multiple independent sub-agents in parallel.
        Each dict: {task, context?, tools?, system?, max_turns?}
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {
                pool.submit(self.spawn, **t): t.get("task", "")
                for t in tasks
            }
            for future in as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as e:
                    results.append(TaskResult(
                        task_id="err", task=futures[future],
                        output="", success=False, turns=0,
                        tool_calls=0, duration_s=0, error=str(e),
                    ))
        return results

    # ── TOOL DEFINITION ───────────────────────────────────────────────────────

    def as_tool_definition(self) -> dict:
        """Returns the JSON schema for registering 'task' as a tool the LLM can call."""
        return {
            "type": "function",
            "function": {
                "name": "spawn_task",
                "description": (
                    "Spawn an isolated sub-agent to complete a specific task. "
                    "The sub-agent has access to all tools and runs independently. "
                    "Use for parallel work, delegation, or complex sub-tasks. "
                    "Returns the sub-agent's final output."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "string",
                            "description": "The complete task description for the sub-agent.",
                        },
                        "context": {
                            "type": "string",
                            "description": "Relevant context to pass to the sub-agent (file contents, prior results, etc.).",
                        },
                        "tools": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional list of tool names to restrict the sub-agent to. Omit for all tools.",
                        },
                        "max_turns": {
                            "type": "integer",
                            "description": "Max turns for the sub-agent (default 20).",
                            "default": 20,
                        },
                    },
                    "required": ["task"],
                },
            },
        }

    # ── STATS ─────────────────────────────────────────────────────────────────

    def stats(self) -> str:
        if not self._active_tasks:
            return "TaskAgent: 0 tasks"
        total    = len(self._active_tasks)
        success  = sum(1 for r in self._active_tasks.values() if r.success)
        avg_time = sum(r.duration_s for r in self._active_tasks.values()) / max(1, total)
        return (
            f"TaskAgent: {total} tasks | {success} ok | "
            f"avg {avg_time:.1f}s | "
            f"{sum(r.tool_calls for r in self._active_tasks.values())} tool calls"
        )

    def list_tasks(self) -> str:
        if not self._active_tasks:
            return "No tasks."
        lines = []
        for r in list(self._active_tasks.values())[-10:]:
            status = "OK" if r.success else "FAIL"
            lines.append(
                f"  [{r.task_id}] {status} | {r.turns}t {r.tool_calls}calls "
                f"{r.duration_s:.1f}s | {r.task[:60]}"
            )
        return "\n".join(lines)
