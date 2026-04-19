"""
QWEN3-CODER ULTIMATE — Cron Scheduler v1.0
In-session task scheduling. Schedule prompts to run at intervals.
Similar to Claude Code's CronCreate/CronList/CronDelete.
"""

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class ScheduledTask:
    task_id:    str
    prompt:     str
    interval:   int         # seconds (0 = one-shot)
    callback:   Callable    # called with (prompt) → executes the AI turn
    name:       str  = ""
    max_runs:   int  = 0    # 0 = unlimited
    runs:       int  = 0
    last_run:   float = 0.0
    next_run:   float = 0.0
    active:     bool  = True
    created_at: float = field(default_factory=time.time)

    @property
    def is_one_shot(self) -> bool:
        return self.interval == 0

    @property
    def due(self) -> bool:
        return self.active and time.time() >= self.next_run

    @property
    def expired(self) -> bool:
        return self.max_runs > 0 and self.runs >= self.max_runs


class CronScheduler:
    """
    In-session prompt scheduler.
    Tasks run in a background thread at their intervals.
    """

    def __init__(self):
        self._tasks:   dict[str, ScheduledTask] = {}
        self._thread:  Optional[threading.Thread] = None
        self._running  = False
        self._lock     = threading.Lock()
        self._stats    = {"created": 0, "fired": 0, "completed": 0}

    # ── START / STOP ──────────────────────────────────────────────────────────

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread  = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _loop(self):
        while self._running:
            time.sleep(1)
            with self._lock:
                tasks = list(self._tasks.values())
            for task in tasks:
                if task.due and not task.expired:
                    self._fire(task)
                elif task.expired:
                    self._remove(task.task_id)

    def _fire(self, task: ScheduledTask):
        task.last_run = time.time()
        task.next_run = time.time() + task.interval if task.interval > 0 else float("inf")
        task.runs    += 1
        self._stats["fired"] += 1

        if task.is_one_shot:
            task.active = False
            self._stats["completed"] += 1

        try:
            task.callback(task.prompt)
        except Exception:
            pass

    # ── PUBLIC API ────────────────────────────────────────────────────────────

    def create(self, prompt: str, interval: int, callback: Callable,
               name: str = "", max_runs: int = 0, delay: int = 0) -> str:
        """
        Schedule a prompt.
        interval=0 → one-shot (runs once after delay).
        interval>0 → recurring every N seconds.
        Returns task_id.
        """
        task_id = str(uuid.uuid4())[:8]
        first_run = time.time() + (delay if delay > 0 else (interval if interval > 0 else 1))
        task = ScheduledTask(
            task_id=task_id, prompt=prompt, interval=interval,
            callback=callback, name=name or f"task-{task_id}",
            max_runs=max_runs, next_run=first_run,
        )
        with self._lock:
            self._tasks[task_id] = task
        self._stats["created"] += 1

        if not self._running:
            self.start()

        interval_str = f"every {interval}s" if interval > 0 else "one-shot"
        return task_id

    def delete(self, task_id: str) -> bool:
        return self._remove(task_id)

    def _remove(self, task_id: str) -> bool:
        with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                return True
        return False

    def pause(self, task_id: str) -> bool:
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].active = False
                return True
        return False

    def resume(self, task_id: str) -> bool:
        with self._lock:
            if task_id in self._tasks:
                t = self._tasks[task_id]
                t.active   = True
                t.next_run = time.time() + t.interval
                return True
        return False

    def list_tasks(self) -> str:
        with self._lock:
            tasks = list(self._tasks.values())
        if not tasks:
            return "No scheduled tasks."
        lines = ["Scheduled tasks:"]
        for t in tasks:
            status   = "active" if t.active else "paused"
            interval = f"every {t.interval}s" if t.interval > 0 else "one-shot"
            runs     = f"{t.runs}/{t.max_runs}" if t.max_runs else str(t.runs)
            next_in  = max(0, t.next_run - time.time())
            prompt_p = t.prompt[:40].replace("\n", " ")
            lines.append(
                f"  [{t.task_id}] {t.name} | {interval} | runs={runs} | "
                f"next={next_in:.0f}s | {status}\n"
                f"    prompt: {prompt_p}"
            )
        return "\n".join(lines)

    def run_now(self, task_id: str) -> bool:
        """Trigger a task immediately regardless of schedule."""
        with self._lock:
            task = self._tasks.get(task_id)
        if not task:
            return False
        threading.Thread(target=self._fire, args=(task,), daemon=True).start()
        return True

    def stats(self) -> str:
        active = sum(1 for t in self._tasks.values() if t.active)
        return (f"CronScheduler: {len(self._tasks)} tasks ({active} active) | "
                f"{self._stats['created']} created | "
                f"{self._stats['fired']} fired | "
                f"{self._stats['completed']} completed")
