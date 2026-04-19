"""
QWEN3-CODER ULTIMATE — Checkpoint System v1.0
Per-edit file snapshots. Esc/undo restores to any previous state.
Every write_file/edit_file saves a snapshot before applying.
"""

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class FileSnapshot:
    path:      str
    content:   str
    timestamp: float
    tool_name: str
    turn_id:   int
    checksum:  str = ""

    def __post_init__(self):
        self.checksum = hashlib.md5(self.content.encode()).hexdigest()[:8]


@dataclass
class Checkpoint:
    turn_id:    int
    description: str
    snapshots:  list[FileSnapshot] = field(default_factory=list)
    timestamp:  float = field(default_factory=time.time)

    @property
    def files_changed(self) -> list[str]:
        return list({s.path for s in self.snapshots})


class CheckpointSystem:
    """
    Per-edit file checkpoint system.

    Usage:
    - Call before_edit(path, tool_name) before any file write
    - Call after_edit(path) after writing (optional, for verification)
    - Call undo() to restore last checkpoint
    - Call undo_to(turn_id) to restore to specific turn
    """

    MAX_CHECKPOINTS = 50
    MAX_FILE_SIZE   = 5 * 1024 * 1024  # 5MB — don't snapshot huge files

    def __init__(self):
        self._checkpoints: list[Checkpoint] = []
        self._current_turn: int = 0
        self._current_checkpoint: Optional[Checkpoint] = None
        self._stats = {"snapshots": 0, "restores": 0, "turns": 0}

    # ── SNAPSHOT ──────────────────────────────────────────────────────────────

    def begin_turn(self, description: str = "") -> int:
        """Call at start of each AI turn."""
        self._current_turn += 1
        self._stats["turns"] += 1
        self._current_checkpoint = Checkpoint(
            turn_id=self._current_turn,
            description=description or f"Turn {self._current_turn}",
        )
        return self._current_turn

    def before_edit(self, path: str, tool_name: str = "write_file") -> bool:
        """
        Snapshot file before editing. Returns True if snapshot was saved.
        Must be called before every file write.
        """
        if not self._current_checkpoint:
            self.begin_turn()

        try:
            abs_path = os.path.abspath(path)
            if not os.path.exists(abs_path):
                # New file — snapshot empty content so undo = delete
                content = ""
            else:
                size = os.path.getsize(abs_path)
                if size > self.MAX_FILE_SIZE:
                    return False
                with open(abs_path, encoding="utf-8", errors="replace") as f:
                    content = f.read()

            snap = FileSnapshot(
                path=abs_path, content=content,
                timestamp=time.time(), tool_name=tool_name,
                turn_id=self._current_turn,
            )
            self._current_checkpoint.snapshots.append(snap)
            self._stats["snapshots"] += 1
            return True
        except Exception:
            return False

    def commit_turn(self):
        """Commit current checkpoint (call at end of turn)."""
        if not self._current_checkpoint or not self._current_checkpoint.snapshots:
            self._current_checkpoint = None
            return

        self._checkpoints.append(self._current_checkpoint)
        self._current_checkpoint = None

        # Trim old checkpoints
        if len(self._checkpoints) > self.MAX_CHECKPOINTS:
            self._checkpoints = self._checkpoints[-self.MAX_CHECKPOINTS:]

    # ── RESTORE ───────────────────────────────────────────────────────────────

    def undo(self) -> str:
        """Restore files to state before last turn. Returns status message."""
        if not self._checkpoints:
            return "No checkpoints to undo."
        checkpoint = self._checkpoints.pop()
        return self._restore(checkpoint)

    def undo_to(self, turn_id: int) -> str:
        """Restore to specific turn. All newer checkpoints are discarded."""
        target = next((c for c in reversed(self._checkpoints) if c.turn_id == turn_id), None)
        if not target:
            return f"No checkpoint for turn {turn_id}."

        # Pop all checkpoints after target
        while self._checkpoints and self._checkpoints[-1].turn_id != turn_id:
            self._checkpoints.pop()
        if self._checkpoints:
            self._checkpoints.pop()

        return self._restore(target)

    def _restore(self, checkpoint: Checkpoint) -> str:
        """Restore all files in checkpoint to their saved state."""
        restored = []
        errors   = []

        for snap in checkpoint.snapshots:
            try:
                path = snap.path
                if snap.content == "" and os.path.exists(path):
                    # File was created in this turn — delete it
                    os.remove(path)
                    restored.append(f"  Deleted: {os.path.basename(path)}")
                else:
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(snap.content)
                    restored.append(f"  Restored: {os.path.basename(path)} ({snap.checksum})")
                self._stats["restores"] += 1
            except Exception as e:
                errors.append(f"  Failed {snap.path}: {e}")

        lines = [f"[Checkpoint] Restored to: {checkpoint.description} (turn {checkpoint.turn_id})"]
        lines += restored
        if errors:
            lines += ["Errors:"] + errors
        return "\n".join(lines)

    # ── INSPECTION ────────────────────────────────────────────────────────────

    def list_checkpoints(self) -> str:
        if not self._checkpoints:
            return "No checkpoints."
        lines = ["Checkpoints (oldest → newest):"]
        for cp in self._checkpoints[-10:]:
            ts = time.strftime("%H:%M:%S", time.localtime(cp.timestamp))
            files = ", ".join(os.path.basename(f) for f in cp.files_changed[:3])
            if len(cp.files_changed) > 3:
                files += f" +{len(cp.files_changed)-3} more"
            lines.append(f"  [{cp.turn_id}] {ts} — {cp.description[:30]} | {files}")
        return "\n".join(lines)

    def diff_last(self) -> str:
        """Show what changed in the last turn."""
        if not self._checkpoints:
            return "No checkpoints."
        cp    = self._checkpoints[-1]
        lines = [f"Changes in turn {cp.turn_id} — {cp.description}:"]
        for snap in cp.snapshots:
            current_path = snap.path
            if not os.path.exists(current_path):
                lines.append(f"  {os.path.basename(current_path)}: [deleted]")
                continue
            try:
                with open(current_path, encoding="utf-8", errors="replace") as f:
                    current = f.read()
                old_lines = snap.content.splitlines()
                new_lines = current.splitlines()
                added   = sum(1 for l in new_lines if l not in old_lines)
                removed = sum(1 for l in old_lines if l not in new_lines)
                lines.append(f"  {os.path.basename(current_path)}: +{added}/-{removed} lines")
            except Exception:
                lines.append(f"  {os.path.basename(current_path)}: [unreadable]")
        return "\n".join(lines)

    def stats(self) -> str:
        return (f"Checkpoints: {len(self._checkpoints)} saved | "
                f"{self._stats['snapshots']} snapshots | "
                f"{self._stats['restores']} restores | "
                f"{self._stats['turns']} turns")
