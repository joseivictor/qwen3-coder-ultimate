"""
QWEN3-CODER ULTIMATE — Security Scanner v1.0
OWASP Top 10, hardcoded secrets, SQL injection, XSS, dependency CVEs.
"""

import re
import os
import json
import subprocess
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class SecurityIssue:
    severity:    str   # critical | high | medium | low | info
    category:    str   # OWASP category
    file:        str
    line:        int
    code:        str
    message:     str
    remediation: str
    cwe:         str = ""
    owasp:       str = ""


class SecurityScanner:
    """
    Multi-layer security scanner:
    - Hardcoded secrets & credentials
    - SQL injection patterns
    - XSS / injection vulnerabilities
    - Insecure deserialization
    - Path traversal
    - Command injection
    - Weak cryptography
    - Dependency vulnerabilities (pip-audit / npm audit)
    """

    # ── SECRET PATTERNS ───────────────────────────────────────────────────────
    SECRET_PATTERNS = [
        (r'(?i)(password|passwd|pwd)\s*=\s*["\'](?!.*placeholder)[^"\']{4,}["\']',
         "Hardcoded password", "A02:Cryptographic Failures", "CWE-259"),
        (r'(?i)(api[_-]?key|apikey)\s*=\s*["\'][A-Za-z0-9+/=_\-]{8,}["\']',
         "Hardcoded API key", "A02:Cryptographic Failures", "CWE-798"),
        (r'(?i)(secret[_-]?key|secret)\s*=\s*["\'][^"\']{8,}["\']',
         "Hardcoded secret", "A02:Cryptographic Failures", "CWE-798"),
        (r'(?i)(access[_-]?token|auth[_-]?token)\s*=\s*["\'][A-Za-z0-9+/=_\-\.]{10,}["\']',
         "Hardcoded token", "A02:Cryptographic Failures", "CWE-798"),
        (r'sk-[A-Za-z0-9]{20,}',
         "OpenAI API key exposed", "A02:Cryptographic Failures", "CWE-798"),
        (r'gh[pousr]_[A-Za-z0-9]{36,}',
         "GitHub token exposed", "A02:Cryptographic Failures", "CWE-798"),
        (r'AKIA[0-9A-Z]{16}',
         "AWS Access Key ID exposed", "A02:Cryptographic Failures", "CWE-798"),
        (r'-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----',
         "Private key in source code", "A02:Cryptographic Failures", "CWE-321"),
        (r'(?i)connectionstring\s*=\s*["\'][^"\']{10,}["\']',
         "Connection string with potential credentials", "A02:Cryptographic Failures", "CWE-259"),
        (r'(?i)(db|database)[_-]?(password|pwd)\s*=\s*["\'][^"\']{3,}["\']',
         "Database password exposed", "A02:Cryptographic Failures", "CWE-259"),
    ]

    # ── INJECTION PATTERNS ────────────────────────────────────────────────────
    SQL_INJECTION_PATTERNS = [
        (r'(?i)execute\s*\(\s*["\'].*%s.*["\'].*%\s*\(',
         "SQL injection via % formatting", "A03:Injection", "CWE-89"),
        (r'(?i)execute\s*\(\s*f["\'].*\{',
         "SQL injection via f-string", "A03:Injection", "CWE-89"),
        (r'(?i)(query|execute)\s*\(\s*"[^"]*"\s*\+',
         "SQL injection via string concatenation", "A03:Injection", "CWE-89"),
        (r'(?i)cursor\.execute\s*\(\s*["\'][^"]*["\'][^,\)]*\+',
         "SQL injection — direct string concat in execute()", "A03:Injection", "CWE-89"),
        (r'(?i)\.raw\s*\(\s*f["\']',
         "Django raw() SQL injection via f-string", "A03:Injection", "CWE-89"),
    ]

    COMMAND_INJECTION_PATTERNS = [
        (r'subprocess\.(run|call|Popen|check_output)\s*\([^,]+shell\s*=\s*True',
         "Command injection via shell=True", "A03:Injection", "CWE-78"),
        (r'os\.system\s*\(',
         "os.system() — prefer subprocess with shell=False", "A03:Injection", "CWE-78"),
        (r'os\.popen\s*\(',
         "os.popen() — prefer subprocess", "A03:Injection", "CWE-78"),
        (r'eval\s*\(',
         "eval() — arbitrary code execution risk", "A03:Injection", "CWE-95"),
        (r'exec\s*\(',
         "exec() — arbitrary code execution risk", "A03:Injection", "CWE-95"),
        (r'__import__\s*\(',
         "Dynamic __import__() — code injection risk", "A03:Injection", "CWE-95"),
    ]

    XSS_PATTERNS = [
        (r'\.innerHTML\s*=(?!=)',
         "XSS via innerHTML assignment", "A03:Injection", "CWE-79"),
        (r'document\.write\s*\(',
         "XSS via document.write()", "A03:Injection", "CWE-79"),
        (r'\.outerHTML\s*=(?!=)',
         "XSS via outerHTML assignment", "A03:Injection", "CWE-79"),
        (r'dangerouslySetInnerHTML',
         "React dangerouslySetInnerHTML — XSS risk", "A03:Injection", "CWE-79"),
        (r'(?i)mark_safe\s*\(',
         "Django mark_safe() — potential XSS", "A03:Injection", "CWE-79"),
    ]

    DESERIALIZATION_PATTERNS = [
        (r'pickle\.loads?\s*\(',
         "Insecure deserialization via pickle", "A08:Software Integrity Failures", "CWE-502"),
        (r'yaml\.load\s*\([^,]+\)',
         "Insecure yaml.load() — use yaml.safe_load()", "A08:Software Integrity Failures", "CWE-502"),
        (r'marshal\.loads?\s*\(',
         "Insecure deserialization via marshal", "A08:Software Integrity Failures", "CWE-502"),
        (r'jsonpickle\.decode\s*\(',
         "Insecure deserialization via jsonpickle", "A08:Software Integrity Failures", "CWE-502"),
    ]

    PATH_TRAVERSAL_PATTERNS = [
        (r'open\s*\([^)]*\+[^)]*\)',
         "Potential path traversal — unvalidated path concatenation", "A01:Broken Access Control", "CWE-22"),
        (r'(?i)os\.path\.join\s*\([^)]*request\.',
         "Path traversal — user input in os.path.join()", "A01:Broken Access Control", "CWE-22"),
        (r'send_file\s*\([^)]*request\.',
         "Path traversal — user input in send_file()", "A01:Broken Access Control", "CWE-22"),
    ]

    CRYPTO_PATTERNS = [
        (r'(?i)(md5|sha1)\s*\(',
         "Weak hash algorithm (MD5/SHA1) — use SHA-256+", "A02:Cryptographic Failures", "CWE-327"),
        (r'(?i)DES\s*\.',
         "Weak encryption (DES) — use AES-256", "A02:Cryptographic Failures", "CWE-327"),
        (r'(?i)random\.(random|randint|choice)\s*\(',
         "Insecure random — use secrets module for security", "A02:Cryptographic Failures", "CWE-338"),
        (r'(?i)verify\s*=\s*False',
         "SSL verification disabled — MITM risk", "A02:Cryptographic Failures", "CWE-295"),
        (r'(?i)ssl\.CERT_NONE',
         "SSL certificate verification disabled", "A02:Cryptographic Failures", "CWE-295"),
        (r"ALLOWED_HOSTS\s*=\s*\[.*['\"]?\*['\"]?.*\]",
         "Django ALLOWED_HOSTS wildcard (*) in production", "A05:Security Misconfiguration", "CWE-183"),
        (r"(?i)DEBUG\s*=\s*True",
         "DEBUG mode enabled — disable in production", "A05:Security Misconfiguration", "CWE-489"),
    ]

    AUTH_PATTERNS = [
        (r"(?i)@app\.route.*methods.*['\"]GET['\"].*password",
         "Password in GET request — use POST", "A07:Auth Failures", "CWE-598"),
        (r"(?i)jwt\.decode\s*\([^)]*verify\s*=\s*False",
         "JWT verification disabled", "A07:Auth Failures", "CWE-347"),
        (r"(?i)login_required\s*=\s*False",
         "Authentication bypassed", "A07:Auth Failures", "CWE-306"),
    ]

    REMEDIATION = {
        "CWE-89":  "Use parameterized queries or ORM methods",
        "CWE-79":  "Sanitize output with escaping libraries (e.g., bleach, DOMPurify)",
        "CWE-78":  "Avoid shell=True; validate/sanitize inputs; use shlex.quote()",
        "CWE-95":  "Never eval/exec user input; use ast.literal_eval for safe parsing",
        "CWE-798": "Use environment variables or a secrets manager (e.g., Vault, AWS Secrets Manager)",
        "CWE-259": "Move credentials to environment variables; use .env files (not committed)",
        "CWE-321": "Never commit private keys; use key management services",
        "CWE-502": "Validate source before deserialization; use safe alternatives",
        "CWE-22":  "Validate and sanitize file paths; use os.path.abspath() and check against allowed roots",
        "CWE-327": "Use SHA-256 or bcrypt for passwords; use AES-256 for encryption",
        "CWE-338": "Use the secrets module for security-critical randomness",
        "CWE-295": "Always verify SSL certificates in production",
        "CWE-347": "Always verify JWT signatures; set algorithm explicitly",
        "CWE-306": "Enforce authentication on all protected routes",
        "CWE-183": "Set ALLOWED_HOSTS explicitly; never use wildcard in production",
        "CWE-489": "Set DEBUG=False in production; use environment variables",
        "CWE-598": "Use POST for sensitive data; never pass credentials in URLs",
    }

    SEVERITY_MAP = {
        "A01:Broken Access Control":          "high",
        "A02:Cryptographic Failures":         "high",
        "A03:Injection":                      "critical",
        "A05:Security Misconfiguration":      "medium",
        "A07:Auth Failures":                  "high",
        "A08:Software Integrity Failures":    "high",
    }

    SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", "test", "tests"}
    SKIP_COMMENTS = re.compile(r"^\s*(#|//|/\*|\*)")

    def scan_file(self, filepath: str) -> list[SecurityIssue]:
        p = Path(filepath)
        if not p.exists():
            return []
        content = p.read_text(encoding="utf-8", errors="replace")
        return self._scan_content(content, filepath)

    def scan_directory(self, dirpath: str = ".") -> dict:
        all_issues: list[SecurityIssue] = []
        scanned = 0

        for fp in Path(dirpath).rglob("*"):
            if not fp.is_file():
                continue
            if any(part in self.SKIP_DIRS for part in fp.parts):
                continue
            if fp.suffix.lower() not in {".py", ".js", ".ts", ".jsx", ".tsx", ".env", ".json", ".yml", ".yaml"}:
                continue
            try:
                issues = self.scan_file(str(fp))
                all_issues.extend(issues)
                scanned += 1
            except Exception:
                pass

        dep_issues = self._scan_dependencies(dirpath)
        all_issues.extend(dep_issues)

        return {
            "files_scanned":  scanned,
            "total_issues":   len(all_issues),
            "critical":       [i for i in all_issues if i.severity == "critical"],
            "high":           [i for i in all_issues if i.severity == "high"],
            "medium":         [i for i in all_issues if i.severity == "medium"],
            "low":            [i for i in all_issues if i.severity == "low"],
            "all_issues":     all_issues,
            "report":         self._render_report(all_issues, scanned),
        }

    def _scan_content(self, content: str, filepath: str) -> list[SecurityIssue]:
        issues = []
        lines  = content.splitlines()

        all_patterns = [
            (self.SECRET_PATTERNS,          "critical"),
            (self.SQL_INJECTION_PATTERNS,   "critical"),
            (self.COMMAND_INJECTION_PATTERNS, "high"),
            (self.XSS_PATTERNS,             "high"),
            (self.DESERIALIZATION_PATTERNS, "high"),
            (self.PATH_TRAVERSAL_PATTERNS,  "medium"),
            (self.CRYPTO_PATTERNS,          "medium"),
            (self.AUTH_PATTERNS,            "high"),
        ]

        for pattern_group, default_sev in all_patterns:
            for pattern, message, owasp, cwe in pattern_group:
                for i, line in enumerate(lines, 1):
                    if self.SKIP_COMMENTS.match(line):
                        continue
                    if re.search(pattern, line):
                        sev = self.SEVERITY_MAP.get(owasp, default_sev)
                        issues.append(SecurityIssue(
                            severity    = sev,
                            category    = owasp,
                            file        = filepath,
                            line        = i,
                            code        = line.strip()[:120],
                            message     = message,
                            remediation = self.REMEDIATION.get(cwe, "Review and fix this security issue."),
                            cwe         = cwe,
                            owasp       = owasp,
                        ))

        return issues

    def _scan_dependencies(self, dirpath: str) -> list[SecurityIssue]:
        issues = []

        req_file = Path(dirpath) / "requirements.txt"
        if req_file.exists():
            try:
                result = subprocess.run(
                    ["pip-audit", "--requirement", str(req_file), "--format", "json"],
                    capture_output=True, text=True, timeout=60
                )
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    for vuln in data.get("vulnerabilities", []):
                        issues.append(SecurityIssue(
                            severity    = "high",
                            category    = "A06:Vulnerable Components",
                            file        = str(req_file),
                            line        = 0,
                            code        = f"{vuln.get('name')}=={vuln.get('version')}",
                            message     = f"CVE: {vuln.get('id')} — {vuln.get('description','')[:100]}",
                            remediation = f"Upgrade to {vuln.get('fix_versions', ['latest'])}",
                            cwe         = "CWE-1035",
                            owasp       = "A06:Vulnerable Components",
                        ))
            except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
                pass

        pkg_file = Path(dirpath) / "package.json"
        if pkg_file.exists():
            try:
                result = subprocess.run(
                    ["npm", "audit", "--json"],
                    capture_output=True, text=True, timeout=60, cwd=dirpath
                )
                if result.stdout:
                    data = json.loads(result.stdout)
                    vulns = data.get("vulnerabilities", {})
                    for name, info in list(vulns.items())[:10]:
                        sev = info.get("severity", "medium")
                        issues.append(SecurityIssue(
                            severity    = sev if sev in ("critical","high","medium","low") else "medium",
                            category    = "A06:Vulnerable Components",
                            file        = str(pkg_file),
                            line        = 0,
                            code        = name,
                            message     = f"npm vulnerability in {name}: {info.get('title','')}",
                            remediation = "Run npm audit fix or upgrade the package",
                            cwe         = "CWE-1035",
                            owasp       = "A06:Vulnerable Components",
                        ))
            except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
                pass

        return issues

    def _render_report(self, issues: list[SecurityIssue], scanned: int) -> str:
        critical = [i for i in issues if i.severity == "critical"]
        high     = [i for i in issues if i.severity == "high"]
        medium   = [i for i in issues if i.severity == "medium"]
        low      = [i for i in issues if i.severity == "low"]

        lines = [
            "🔐 SECURITY SCAN REPORT",
            f"Files scanned: {scanned} | Issues: {len(issues)} "
            f"(🔴 {len(critical)} critical | 🟠 {len(high)} high | 🟡 {len(medium)} medium | 🟢 {len(low)} low)",
            "",
        ]

        for sev, sev_issues, icon in [
            ("CRITICAL", critical, "🔴"),
            ("HIGH",     high,     "🟠"),
            ("MEDIUM",   medium,   "🟡"),
        ]:
            if not sev_issues:
                continue
            lines.append(f"{icon} {sev} ({len(sev_issues)})")
            for issue in sev_issues[:10]:
                lines.append(f"  {issue.file}:{issue.line} [{issue.cwe}] {issue.message}")
                lines.append(f"    Code: {issue.code[:80]}")
                lines.append(f"    Fix:  {issue.remediation}")
            lines.append("")

        if not issues:
            lines.append("✅ No security issues found!")

        return "\n".join(lines)

    def quick_scan(self, filepath: str) -> str:
        """Quick single-file security scan, returns formatted string."""
        issues = self.scan_file(filepath)
        if not issues:
            return f"✅ No security issues found in {filepath}"
        lines = [f"🔐 Security scan: {filepath} — {len(issues)} issues\n"]
        for i in sorted(issues, key=lambda x: {"critical":0,"high":1,"medium":2,"low":3}.get(x.severity,4)):
            icon = {"critical":"🔴","high":"🟠","medium":"🟡","low":"🟢"}.get(i.severity,"⚪")
            lines.append(f"{icon} line {i.line} [{i.cwe}] {i.message}")
            lines.append(f"   {i.code[:80]}")
            lines.append(f"   ➜ {i.remediation}\n")
        return "\n".join(lines)
