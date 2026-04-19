"""
QWEN3-CODER ULTIMATE — GitHub Integration v1.0
Auto-fix PRs, create PRs, watch CI status, comment on issues.
"""

import json
import os
import re
import subprocess
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PRInfo:
    number:  int
    title:   str
    branch:  str
    base:    str
    url:     str
    status:  str  # open | closed | merged
    checks:  list[dict] = field(default_factory=list)
    failing_checks: list[str] = field(default_factory=list)


class GitHubIntegration:
    """
    GitHub API integration for PR management, CI watching, and auto-fix.
    Uses GITHUB_TOKEN env var or token from config.
    """

    API = "https://api.github.com"

    def __init__(self, config: dict, client=None, model: str = ""):
        self.client  = client
        self.model   = model
        self.token   = (config.get("github_token") or os.getenv("GITHUB_TOKEN", ""))
        self._repo   = self._detect_repo()
        self._stats  = {"api_calls": 0, "prs_created": 0, "fixes_applied": 0}

    # ── REPO DETECTION ────────────────────────────────────────────────────────

    def _detect_repo(self) -> Optional[str]:
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                url = result.stdout.strip()
                m = re.search(r"github\.com[:/](.+?)(?:\.git)?$", url)
                if m:
                    return m.group(1)
        except Exception:
            pass
        return None

    @property
    def repo(self) -> str:
        return self._repo or ""

    @property
    def available(self) -> bool:
        return bool(self.token and self._repo)

    # ── HTTP ──────────────────────────────────────────────────────────────────

    def _request(self, method: str, endpoint: str, body: dict = None) -> tuple[int, dict]:
        url = f"{self.API}{endpoint}"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept":        "application/vnd.github+json",
            "User-Agent":    "QWEN3-CODER-Ultimate/1.0",
            "Content-Type":  "application/json",
        }
        data = json.dumps(body).encode() if body else None
        req  = urllib.request.Request(url, data=data, headers=headers, method=method)
        self._stats["api_calls"] += 1
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.status, json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            try:
                return e.code, json.loads(e.read().decode())
            except Exception:
                return e.code, {"message": str(e)}
        except Exception as e:
            return 0, {"message": str(e)}

    def _get(self, endpoint: str) -> tuple[int, dict]:
        return self._request("GET", endpoint)

    def _post(self, endpoint: str, body: dict) -> tuple[int, dict]:
        return self._request("POST", endpoint, body)

    def _patch(self, endpoint: str, body: dict) -> tuple[int, dict]:
        return self._request("PATCH", endpoint, body)

    # ── PR OPERATIONS ─────────────────────────────────────────────────────────

    def create_pr(self, title: str, body: str, head: str = None,
                  base: str = "main", draft: bool = False) -> tuple[bool, str]:
        """Create a pull request."""
        if not self.available:
            return False, "GitHub token or repo not configured."

        if not head:
            result = subprocess.run(["git", "branch", "--show-current"],
                                    capture_output=True, text=True)
            head = result.stdout.strip()

        status, data = self._post(f"/repos/{self.repo}/pulls", {
            "title": title, "body": body,
            "head": head, "base": base, "draft": draft,
        })

        if status == 201:
            self._stats["prs_created"] += 1
            return True, f"PR created: {data.get('html_url', '')}"
        return False, f"Failed ({status}): {data.get('message', '')}"

    def get_pr(self, pr_number: int) -> Optional[PRInfo]:
        """Get PR info including CI check status."""
        status, data = self._get(f"/repos/{self.repo}/pulls/{pr_number}")
        if status != 200:
            return None

        # Get check runs
        head_sha = data.get("head", {}).get("sha", "")
        checks   = []
        failing  = []
        if head_sha:
            _, check_data = self._get(f"/repos/{self.repo}/commits/{head_sha}/check-runs")
            for run in check_data.get("check_runs", []):
                check = {
                    "name":       run.get("name"),
                    "status":     run.get("status"),
                    "conclusion": run.get("conclusion"),
                    "url":        run.get("html_url"),
                }
                checks.append(check)
                if run.get("conclusion") in ("failure", "timed_out", "cancelled"):
                    failing.append(run.get("name", ""))

        return PRInfo(
            number=pr_number,
            title=data.get("title", ""),
            branch=data.get("head", {}).get("ref", ""),
            base=data.get("base", {}).get("ref", ""),
            url=data.get("html_url", ""),
            status=data.get("state", ""),
            checks=checks,
            failing_checks=failing,
        )

    def list_prs(self, state: str = "open") -> str:
        """List PRs for the repo."""
        if not self.available:
            return "GitHub not configured."
        status, data = self._get(f"/repos/{self.repo}/pulls?state={state}&per_page=20")
        if status != 200:
            return f"Error: {data.get('message', '')}"
        if not data:
            return f"No {state} PRs."
        lines = [f"PRs ({state}) in {self.repo}:"]
        for pr in data:
            lines.append(f"  #{pr['number']} {pr['title'][:60]} [{pr['head']['ref']}]")
        return "\n".join(lines)

    def comment_on_pr(self, pr_number: int, comment: str) -> bool:
        """Add a comment to a PR."""
        status, _ = self._post(f"/repos/{self.repo}/issues/{pr_number}/comments",
                               {"body": comment})
        return status == 201

    def get_pr_diff(self, pr_number: int) -> str:
        """Get the diff for a PR."""
        if not self.available:
            return ""
        url = f"{self.API}/repos/{self.repo}/pulls/{pr_number}"
        req = urllib.request.Request(url, headers={
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3.diff",
        })
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.read().decode()
        except Exception:
            return ""

    # ── CI WATCHING ───────────────────────────────────────────────────────────

    def watch_pr_checks(self, pr_number: int, timeout: int = 300) -> dict:
        """
        Poll PR checks until all pass or fail or timeout.
        Returns final status dict.
        """
        start   = time.time()
        interval = 15
        while time.time() - start < timeout:
            pr = self.get_pr(pr_number)
            if not pr:
                return {"error": f"PR #{pr_number} not found"}

            all_done = all(
                c.get("status") == "completed"
                for c in pr.checks
            )
            if pr.checks and all_done:
                passed  = [c for c in pr.checks if c.get("conclusion") == "success"]
                failed  = [c for c in pr.checks if c.get("conclusion") in ("failure","timed_out")]
                return {
                    "pr":      pr_number,
                    "passed":  [c["name"] for c in passed],
                    "failed":  [c["name"] for c in failed],
                    "success": len(failed) == 0,
                }
            time.sleep(interval)

        return {"error": "timeout", "pr": pr_number}

    # ── AUTO-FIX ──────────────────────────────────────────────────────────────

    def get_ci_logs(self, pr_number: int) -> str:
        """Get failing CI logs for a PR (best-effort)."""
        pr = self.get_pr(pr_number)
        if not pr or not pr.failing_checks:
            return ""

        logs = []
        head_sha = ""
        _, pr_data = self._get(f"/repos/{self.repo}/pulls/{pr_number}")
        head_sha   = pr_data.get("head", {}).get("sha", "")

        if head_sha:
            _, check_data = self._get(f"/repos/{self.repo}/commits/{head_sha}/check-runs")
            for run in check_data.get("check_runs", []):
                if run.get("conclusion") in ("failure", "timed_out"):
                    name = run.get("name", "")
                    # Try to get logs URL
                    run_id = run.get("id")
                    if run_id:
                        _, log_data = self._get(f"/repos/{self.repo}/actions/runs/{run_id}/logs")
                        if isinstance(log_data, dict):
                            logs.append(f"=== {name} ===\n{json.dumps(log_data)[:2000]}")

        return "\n\n".join(logs) or f"Failing checks: {', '.join(pr.failing_checks)}"

    def auto_fix_pr(self, pr_number: int) -> str:
        """
        AI-powered PR auto-fix:
        1. Get PR diff + failing CI logs
        2. Ask AI to identify fixes
        3. Return fix suggestions (user must apply)
        """
        if not self.available:
            return "GitHub not configured."
        if not self.client:
            return "No AI client available."

        pr = self.get_pr(pr_number)
        if not pr:
            return f"PR #{pr_number} not found."

        diff  = self.get_pr_diff(pr_number)[:4000]
        logs  = self.get_ci_logs(pr_number)[:2000]

        if not pr.failing_checks:
            return f"PR #{pr_number} has no failing checks."

        prompt = (
            f"PR #{pr_number}: {pr.title}\n"
            f"Branch: {pr.branch} → {pr.base}\n\n"
            f"Failing checks: {', '.join(pr.failing_checks)}\n\n"
            f"CI Logs:\n{logs}\n\n"
            f"Diff:\n{diff}\n\n"
            "Identify the exact files and changes needed to fix the failing CI. "
            "Be specific — file paths and code changes."
        )

        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a CI debugging expert. Identify exact fixes for failing CI checks."},
                    {"role": "user",   "content": prompt},
                ],
                max_tokens=1000, temperature=0.1, stream=False,
            )
            fix = resp.choices[0].message.content or ""
            self._stats["fixes_applied"] += 1
            return f"PR #{pr_number} fix analysis:\n{fix}"
        except Exception as e:
            return f"AI fix failed: {e}"

    # ── ISSUES ────────────────────────────────────────────────────────────────

    def create_issue(self, title: str, body: str, labels: list[str] = None) -> tuple[bool, str]:
        status, data = self._post(f"/repos/{self.repo}/issues", {
            "title": title, "body": body, "labels": labels or []
        })
        if status == 201:
            return True, data.get("html_url", "")
        return False, data.get("message", "")

    def list_issues(self, state: str = "open", labels: str = "") -> str:
        params = f"state={state}&per_page=20"
        if labels:
            params += f"&labels={labels}"
        status, data = self._get(f"/repos/{self.repo}/issues?{params}")
        if status != 200 or not isinstance(data, list):
            return "Error fetching issues."
        lines = [f"Issues ({state}):"]
        for issue in data:
            if "pull_request" in issue:
                continue  # skip PRs
            lines.append(f"  #{issue['number']} {issue['title'][:60]}")
        return "\n".join(lines) if len(lines) > 1 else "No issues."

    # ── STATS ─────────────────────────────────────────────────────────────────

    def stats(self) -> str:
        return (f"GitHub: repo={self.repo or 'none'} | "
                f"{self._stats['api_calls']} calls | "
                f"{self._stats['prs_created']} PRs | "
                f"{'connected' if self.available else 'no token'}")
