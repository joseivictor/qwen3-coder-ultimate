"""
QWEN3-CODER ULTIMATE — Git Worktree Manager v1.0
Parallel isolated sessions in separate git worktrees.
Enter/exit worktrees, run agents in parallel branches.
"""

import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Worktree:
    branch:   str
    path:     str
    base_dir: str
    active:   bool = True


class WorktreeManager:
    """
    Manages git worktrees for isolated parallel sessions.

    Workflow:
        wm = WorktreeManager()
        path = wm.create("feature/my-branch")
        wm.enter(path)          # sets cwd
        # ... work in isolation ...
        wm.exit()               # returns to original cwd
        wm.remove(path)         # cleanup
    """

    def __init__(self):
        self._worktrees: dict[str, Worktree] = {}
        self._original_cwd: Optional[str] = None
        self._current_worktree: Optional[str] = None

    # ── GIT CHECK ─────────────────────────────────────────────────────────────

    def _is_git_repo(self, path: str = ".") -> bool:
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=path, capture_output=True, text=True
        )
        return result.returncode == 0

    def _git(self, *args, cwd: str = None) -> tuple[bool, str]:
        result = subprocess.run(
            ["git"] + list(args),
            cwd=cwd or ".",
            capture_output=True, text=True
        )
        output = (result.stdout + result.stderr).strip()
        return result.returncode == 0, output

    def _get_repo_root(self) -> Optional[str]:
        ok, out = self._git("rev-parse", "--show-toplevel")
        return out if ok else None

    # ── CREATE ────────────────────────────────────────────────────────────────

    def create(self, branch: str = None, base_branch: str = "HEAD") -> tuple[bool, str]:
        """
        Create a new git worktree on a new branch.
        Returns (success, path_or_error).
        """
        if not self._is_git_repo():
            return False, "Not a git repository."

        root = self._get_repo_root()
        if not root:
            return False, "Cannot find repo root."

        # Auto-name branch
        if not branch:
            import time
            branch = f"qwen-session-{int(time.time())}"

        # Sanitize branch name
        branch = re.sub(r"[^a-zA-Z0-9/_.-]", "-", branch)

        # Create worktree in temp dir next to repo
        wt_dir = Path(root).parent / f".qwen-worktrees" / branch.replace("/", "-")
        wt_dir.mkdir(parents=True, exist_ok=True)

        # Create new branch from base
        ok, out = self._git("worktree", "add", "-b", branch, str(wt_dir), base_branch)
        if not ok:
            # Branch may already exist — try without -b
            ok, out = self._git("worktree", "add", str(wt_dir), branch)
            if not ok:
                shutil.rmtree(str(wt_dir), ignore_errors=True)
                return False, f"Failed to create worktree: {out}"

        self._worktrees[str(wt_dir)] = Worktree(
            branch=branch, path=str(wt_dir), base_dir=root
        )
        return True, str(wt_dir)

    # ── ENTER / EXIT ──────────────────────────────────────────────────────────

    def enter(self, path: str) -> tuple[bool, str]:
        """Change working directory to worktree. Returns (success, message)."""
        abs_path = os.path.abspath(path)
        if not os.path.exists(abs_path):
            return False, f"Worktree path does not exist: {abs_path}"

        if self._current_worktree:
            return False, f"Already in worktree: {self._current_worktree}. Exit first."

        self._original_cwd      = os.getcwd()
        self._current_worktree  = abs_path
        os.chdir(abs_path)

        wt = self._worktrees.get(abs_path)
        branch = wt.branch if wt else "unknown"
        return True, f"Entered worktree: {abs_path}\nBranch: {branch}"

    def exit(self) -> tuple[bool, str]:
        """Return to original working directory."""
        if not self._current_worktree:
            return False, "Not in a worktree."

        path = self._current_worktree
        self._current_worktree = None

        if self._original_cwd and os.path.exists(self._original_cwd):
            os.chdir(self._original_cwd)
            self._original_cwd = None
            return True, f"Exited worktree: {path}\nReturned to: {os.getcwd()}"

        return True, f"Exited worktree: {path}"

    # ── REMOVE ────────────────────────────────────────────────────────────────

    def remove(self, path: str = None, force: bool = False) -> tuple[bool, str]:
        """Remove a worktree. If path=None, removes current worktree."""
        target = path or self._current_worktree
        if not target:
            return False, "No worktree to remove."

        abs_path = os.path.abspath(target)

        # Exit first if we're in it
        if self._current_worktree == abs_path:
            self.exit()

        args = ["worktree", "remove"]
        if force:
            args.append("--force")
        args.append(abs_path)

        ok, out = self._git(*args)
        if not ok and not force:
            ok, out = self._git("worktree", "remove", "--force", abs_path)

        self._worktrees.pop(abs_path, None)
        shutil.rmtree(abs_path, ignore_errors=True)

        wt_parent = Path(abs_path).parent
        try:
            if wt_parent.name == ".qwen-worktrees" and not any(wt_parent.iterdir()):
                wt_parent.rmdir()
        except Exception:
            pass

        return True, f"Removed worktree: {abs_path}"

    def remove_all(self) -> str:
        """Remove all QWEN worktrees."""
        results = []
        for path in list(self._worktrees.keys()):
            ok, msg = self.remove(path, force=True)
            results.append(msg)
        # Also cleanup via git
        self._git("worktree", "prune")
        return "\n".join(results) if results else "No worktrees to remove."

    # ── LIST ──────────────────────────────────────────────────────────────────

    def list_worktrees(self) -> str:
        ok, out = self._git("worktree", "list", "--porcelain")
        if not ok:
            return "Not a git repo or git not available."

        lines   = ["Git worktrees:"]
        current = self._current_worktree

        for block in out.split("\n\n"):
            if not block.strip():
                continue
            data = {}
            for line in block.splitlines():
                if " " in line:
                    k, v = line.split(" ", 1)
                    data[k] = v
            path   = data.get("worktree", "")
            branch = data.get("branch", "").replace("refs/heads/", "")
            head   = data.get("HEAD", "")[:7]
            marker = " ◀ current" if path == current else ""
            lines.append(f"  {path} [{branch}] {head}{marker}")

        return "\n".join(lines)

    # ── MERGE / PR ────────────────────────────────────────────────────────────

    def diff_vs_main(self, path: str = None, base: str = "main") -> str:
        """Show diff of worktree vs base branch."""
        cwd = path or self._current_worktree or "."
        ok, out = self._git("diff", f"{base}...HEAD", "--stat", cwd=cwd)
        if not ok:
            ok, out = self._git("diff", "master...HEAD", "--stat", cwd=cwd)
        return out or "No changes."

    def create_pr_description(self, path: str = None) -> str:
        """Generate a PR description from commits in worktree."""
        cwd = path or self._current_worktree or "."
        ok, commits = self._git("log", "--oneline", "HEAD", "--not", "$(git merge-base HEAD main 2>/dev/null || echo HEAD~10)", cwd=cwd)
        if not ok:
            ok, commits = self._git("log", "--oneline", "-10", cwd=cwd)
        return commits or "No commits."

    # ── STATUS ────────────────────────────────────────────────────────────────

    @property
    def in_worktree(self) -> bool:
        return self._current_worktree is not None

    @property
    def current_branch(self) -> str:
        ok, out = self._git("branch", "--show-current")
        return out if ok else "unknown"

    def status(self) -> str:
        if not self.in_worktree:
            return f"WorktreeManager: no active worktree | {len(self._worktrees)} known"
        wt  = self._worktrees.get(self._current_worktree)
        branch = wt.branch if wt else self.current_branch
        return f"WorktreeManager: IN worktree [{branch}] at {self._current_worktree}"
