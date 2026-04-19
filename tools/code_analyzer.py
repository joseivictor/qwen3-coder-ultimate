"""
QWEN3-CODER ULTIMATE — Code Analyzer v1.0
AST-based static analysis: complexity, dead code, dependencies, duplication.
Supports Python natively; JS/TS via regex heuristics.
"""

import ast
import os
import re
import json
import hashlib
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from collections import defaultdict


@dataclass
class FunctionInfo:
    name:        str
    file:        str
    line:        int
    args:        list[str]
    returns:     str
    complexity:  int
    lines:       int
    docstring:   str
    is_async:    bool = False
    calls:       list[str] = field(default_factory=list)
    decorators:  list[str] = field(default_factory=list)


@dataclass
class ClassInfo:
    name:      str
    file:      str
    line:      int
    methods:   list[str]
    bases:     list[str]
    lines:     int
    docstring: str


@dataclass
class AnalysisResult:
    file:               str
    language:           str
    total_lines:        int
    blank_lines:        int
    comment_lines:      int
    code_lines:         int
    functions:          list[FunctionInfo] = field(default_factory=list)
    classes:            list[ClassInfo]    = field(default_factory=list)
    imports:            list[str]          = field(default_factory=list)
    todos:              list[tuple]        = field(default_factory=list)
    issues:             list[dict]         = field(default_factory=list)
    maintainability:    float = 100.0
    avg_complexity:     float = 0.0
    max_complexity:     int   = 0
    duplicates:         list[dict] = field(default_factory=list)


class ComplexityVisitor(ast.NodeVisitor):
    """McCabe cyclomatic complexity counter."""

    BRANCH_NODES = (
        ast.If, ast.For, ast.While, ast.ExceptHandler,
        ast.With, ast.Assert, ast.comprehension,
    )
    BOOL_OPS = (ast.And, ast.Or)

    def __init__(self):
        self.complexity = 1

    def visit_If(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_For(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_While(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        self.complexity += len(node.values) - 1
        self.generic_visit(node)

    def visit_comprehension(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_With(self, node):
        self.complexity += len(node.items) - 1
        self.generic_visit(node)


class CallVisitor(ast.NodeVisitor):
    """Collects all function calls in a node."""

    def __init__(self):
        self.calls = []

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            self.calls.append(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            self.calls.append(node.func.attr)
        self.generic_visit(node)


class CodeAnalyzer:
    """Static analysis engine for Python (AST) and JS/TS (regex heuristics)."""

    COMPLEXITY_THRESHOLDS = {
        "low":      5,
        "medium":  10,
        "high":    20,
    }

    TODO_PATTERN    = re.compile(r"#\s*(TODO|FIXME|HACK|XXX|BUG|NOTE)[\s:]*(.*)", re.IGNORECASE)
    DEAD_CODE_HINTS = re.compile(r"^\s*(pass\s*$|return\s+None\s*$|\.\.\.)", re.MULTILINE)

    def __init__(self):
        self._chunk_hashes: dict[str, list[str]] = defaultdict(list)

    # ── ENTRY POINTS ──────────────────────────────────────────────────────────
    def analyze_file(self, filepath: str) -> AnalysisResult:
        path = Path(filepath)
        if not path.exists():
            return self._empty(filepath, "not_found")

        content = path.read_text(encoding="utf-8", errors="replace")
        ext     = path.suffix.lower()

        if ext == ".py":
            return self._analyze_python(filepath, content)
        elif ext in (".js", ".ts", ".jsx", ".tsx"):
            return self._analyze_js(filepath, content)
        else:
            return self._analyze_generic(filepath, content)

    def analyze_directory(self, dirpath: str = ".", extensions: list = None) -> dict:
        """Analyze all code files in a directory and return an aggregated report."""
        if extensions is None:
            extensions = [".py", ".js", ".ts", ".jsx", ".tsx"]

        results    = []
        all_issues = []
        total_cc   = []

        for fp in Path(dirpath).rglob("*"):
            if fp.suffix.lower() not in extensions:
                continue
            if any(part in fp.parts for part in {".git", "node_modules", "__pycache__", ".venv", "venv"}):
                continue
            try:
                r = self.analyze_file(str(fp))
                results.append(r)
                all_issues.extend(r.issues)
                total_cc.append(r.avg_complexity)
            except Exception:
                pass

        duplicates = self._find_cross_file_duplicates(results)

        return {
            "files_analyzed":  len(results),
            "total_lines":     sum(r.total_lines for r in results),
            "total_functions": sum(len(r.functions) for r in results),
            "total_classes":   sum(len(r.classes) for r in results),
            "avg_complexity":  round(sum(total_cc) / len(total_cc), 2) if total_cc else 0,
            "issues":          sorted(all_issues, key=lambda i: i.get("severity","low"), reverse=True)[:50],
            "cross_duplicates": duplicates[:10],
            "todos":           self._collect_todos(results),
            "hotspots":        self._identify_hotspots(results),
            "summary":         self._build_summary(results),
        }

    # ── PYTHON ANALYSIS ───────────────────────────────────────────────────────
    def _analyze_python(self, filepath: str, content: str) -> AnalysisResult:
        result = self._count_lines(filepath, content, "python")

        try:
            tree = ast.parse(content, filename=filepath)
        except SyntaxError as e:
            result.issues.append({
                "type": "syntax_error", "severity": "critical",
                "line": e.lineno, "message": str(e), "file": filepath,
            })
            return result

        result.imports  = self._extract_python_imports(tree)
        result.classes  = self._extract_classes(tree, filepath, content)
        result.functions = self._extract_functions(tree, filepath, content)
        result.todos    = self._extract_todos(content, filepath)

        complexities = [f.complexity for f in result.functions]
        if complexities:
            result.avg_complexity = round(sum(complexities) / len(complexities), 2)
            result.max_complexity = max(complexities)

        result.issues   = self._python_issues(result, content)
        result.maintainability = self._maintainability_index(result, content)
        result.duplicates = self._find_duplicates(content, filepath)

        return result

    def _extract_functions(self, tree: ast.AST, filepath: str, content: str) -> list[FunctionInfo]:
        funcs = []
        lines = content.splitlines()

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            cv = ComplexityVisitor()
            cv.visit(node)

            callv = CallVisitor()
            callv.visit(node)

            func_lines = (node.end_lineno or node.lineno) - node.lineno + 1

            docstring = ""
            if (node.body and isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, ast.Constant)):
                docstring = str(node.body[0].value.value)[:300]

            args = [arg.arg for arg in node.args.args]
            ret  = ""
            if node.returns:
                try:
                    ret = ast.unparse(node.returns)
                except Exception:
                    ret = "?"

            decorators = []
            for d in node.decorator_list:
                try:
                    decorators.append(ast.unparse(d))
                except Exception:
                    decorators.append("@?")

            funcs.append(FunctionInfo(
                name       = node.name,
                file       = filepath,
                line       = node.lineno,
                args       = args,
                returns    = ret,
                complexity = cv.complexity,
                lines      = func_lines,
                docstring  = docstring,
                is_async   = isinstance(node, ast.AsyncFunctionDef),
                calls      = list(set(callv.calls)),
                decorators = decorators,
            ))

        return funcs

    def _extract_classes(self, tree: ast.AST, filepath: str, content: str) -> list[ClassInfo]:
        classes = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            methods = [n.name for n in ast.walk(node) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            bases   = []
            for b in node.bases:
                try:
                    bases.append(ast.unparse(b))
                except Exception:
                    bases.append("?")
            cls_lines = (node.end_lineno or node.lineno) - node.lineno + 1
            docstring = ""
            if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant):
                docstring = str(node.body[0].value.value)[:200]
            classes.append(ClassInfo(
                name=node.name, file=filepath, line=node.lineno,
                methods=methods, bases=bases, lines=cls_lines, docstring=docstring,
            ))
        return classes

    def _extract_python_imports(self, tree: ast.AST) -> list[str]:
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                for alias in node.names:
                    imports.append(f"{mod}.{alias.name}")
        return imports

    def _python_issues(self, result: AnalysisResult, content: str) -> list[dict]:
        issues = []
        lines  = content.splitlines()

        for func in result.functions:
            if func.complexity > self.COMPLEXITY_THRESHOLDS["high"]:
                issues.append({
                    "type": "high_complexity", "severity": "high",
                    "file": result.file, "line": func.line,
                    "message": f"Function '{func.name}' has cyclomatic complexity {func.complexity} (threshold: {self.COMPLEXITY_THRESHOLDS['high']})",
                })
            elif func.complexity > self.COMPLEXITY_THRESHOLDS["medium"]:
                issues.append({
                    "type": "medium_complexity", "severity": "medium",
                    "file": result.file, "line": func.line,
                    "message": f"Function '{func.name}' has complexity {func.complexity}",
                })

            if func.lines > 80:
                issues.append({
                    "type": "long_function", "severity": "medium",
                    "file": result.file, "line": func.line,
                    "message": f"Function '{func.name}' is {func.lines} lines long (consider splitting)",
                })

            if not func.docstring and not func.name.startswith("_") and func.lines > 10:
                issues.append({
                    "type": "missing_docstring", "severity": "low",
                    "file": result.file, "line": func.line,
                    "message": f"Public function '{func.name}' has no docstring",
                })

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if re.match(r"except\s*:", stripped) or stripped == "except Exception:":
                issues.append({
                    "type": "bare_except", "severity": "medium",
                    "file": result.file, "line": i,
                    "message": "Bare except clause — catches all exceptions including KeyboardInterrupt",
                })
            if re.match(r"print\s*\(", stripped) and "test" not in result.file.lower():
                issues.append({
                    "type": "debug_print", "severity": "low",
                    "file": result.file, "line": i,
                    "message": "print() in production code — consider using logging",
                })

        return issues

    def _maintainability_index(self, result: AnalysisResult, content: str) -> float:
        import math
        loc = max(result.code_lines, 1)
        avg_cc = result.avg_complexity or 1
        halstead_volume = loc * math.log2(max(loc, 2))
        mi = max(0, (171 - 5.2 * math.log(halstead_volume) - 0.23 * avg_cc - 16.2 * math.log(loc)) * 100 / 171)
        return round(mi, 1)

    # ── JS/TS ANALYSIS ────────────────────────────────────────────────────────
    def _analyze_js(self, filepath: str, content: str) -> AnalysisResult:
        result = self._count_lines(filepath, content, "javascript")

        func_pattern = re.compile(
            r"(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:function|\([^)]*\)\s*=>))",
            re.MULTILINE
        )
        for m in func_pattern.finditer(content):
            name = m.group(1) or m.group(2) or "anonymous"
            line = content[:m.start()].count("\n") + 1
            result.functions.append(FunctionInfo(
                name=name, file=filepath, line=line, args=[], returns="",
                complexity=1, lines=10, docstring="",
            ))

        import_pattern = re.compile(r'(?:import|require)\s*[({]?\s*[\'"]([^\'"]+)[\'"]', re.MULTILINE)
        result.imports = [m.group(1) for m in import_pattern.finditer(content)]

        result.todos = self._extract_todos(content, filepath)
        result.issues = self._js_issues(result, content)
        return result

    def _js_issues(self, result: AnalysisResult, content: str) -> list[dict]:
        issues = []
        lines  = content.splitlines()
        for i, line in enumerate(lines, 1):
            if "eval(" in line and "// safe" not in line.lower():
                issues.append({
                    "type": "eval_usage", "severity": "high",
                    "file": result.file, "line": i,
                    "message": "eval() usage — potential security risk (XSS/code injection)",
                })
            if "innerHTML" in line and "=" in line:
                issues.append({
                    "type": "innerHTML_assignment", "severity": "medium",
                    "file": result.file, "line": i,
                    "message": "innerHTML assignment — potential XSS vulnerability",
                })
            if "console.log(" in line:
                issues.append({
                    "type": "console_log", "severity": "low",
                    "file": result.file, "line": i,
                    "message": "console.log() in production code",
                })
        return issues

    # ── GENERIC ANALYSIS ──────────────────────────────────────────────────────
    def _analyze_generic(self, filepath: str, content: str) -> AnalysisResult:
        result = self._count_lines(filepath, content, "unknown")
        result.todos = self._extract_todos(content, filepath)
        return result

    # ── SHARED UTILITIES ──────────────────────────────────────────────────────
    def _count_lines(self, filepath: str, content: str, lang: str) -> AnalysisResult:
        lines = content.splitlines()
        blank = sum(1 for l in lines if not l.strip())
        comments = sum(1 for l in lines if l.strip().startswith(("#", "//", "/*", "*", "*/", '"""', "'''")))
        code = len(lines) - blank - comments
        return AnalysisResult(
            file=filepath, language=lang,
            total_lines=len(lines), blank_lines=blank,
            comment_lines=comments, code_lines=max(0, code),
        )

    def _extract_todos(self, content: str, filepath: str) -> list[tuple]:
        todos = []
        for i, line in enumerate(content.splitlines(), 1):
            m = self.TODO_PATTERN.search(line)
            if m:
                todos.append((filepath, i, m.group(1).upper(), m.group(2).strip()))
        return todos

    def _find_duplicates(self, content: str, filepath: str, min_lines: int = 6) -> list[dict]:
        """Find duplicate code blocks within a single file."""
        lines   = content.splitlines()
        chunks  = {}
        dups    = []

        for i in range(len(lines) - min_lines):
            chunk = "\n".join(lines[i:i+min_lines]).strip()
            if len(chunk) < 100:
                continue
            h = hashlib.md5(chunk.encode()).hexdigest()
            if h in chunks:
                dups.append({
                    "file": filepath,
                    "first_occurrence":  chunks[h],
                    "duplicate_at_line": i + 1,
                    "lines":             min_lines,
                    "preview":           chunk[:100],
                })
            else:
                chunks[h] = i + 1

        return dups[:5]

    def _find_cross_file_duplicates(self, results: list[AnalysisResult]) -> list[dict]:
        chunk_map: dict[str, list] = defaultdict(list)
        for r in results:
            try:
                content = Path(r.file).read_text(encoding="utf-8", errors="replace")
                lines   = content.splitlines()
                for i in range(len(lines) - 8):
                    chunk = "\n".join(lines[i:i+8]).strip()
                    if len(chunk) < 80:
                        continue
                    h = hashlib.md5(chunk.encode()).hexdigest()
                    chunk_map[h].append({"file": r.file, "line": i+1})
            except Exception:
                pass

        return [
            {"locations": locs, "preview": ""}
            for h, locs in chunk_map.items()
            if len(locs) > 1
        ][:10]

    def _collect_todos(self, results: list[AnalysisResult]) -> list[dict]:
        todos = []
        for r in results:
            for filepath, line, kind, msg in r.todos:
                todos.append({"file": filepath, "line": line, "type": kind, "message": msg})
        return todos[:30]

    def _identify_hotspots(self, results: list[AnalysisResult]) -> list[dict]:
        hotspots = []
        for r in results:
            for func in r.functions:
                if func.complexity > 8 or func.lines > 60:
                    hotspots.append({
                        "file":       func.file,
                        "function":   func.name,
                        "line":       func.line,
                        "complexity": func.complexity,
                        "lines":      func.lines,
                        "score":      func.complexity * 2 + func.lines // 10,
                    })
        return sorted(hotspots, key=lambda h: h["score"], reverse=True)[:10]

    def _build_summary(self, results: list[AnalysisResult]) -> str:
        if not results:
            return "No files analyzed."
        total_issues = sum(len(r.issues) for r in results)
        critical = sum(1 for r in results for i in r.issues if i.get("severity") == "critical")
        high     = sum(1 for r in results for i in r.issues if i.get("severity") == "high")
        avg_mi   = sum(r.maintainability for r in results) / len(results)

        return (
            f"Analyzed {len(results)} files | "
            f"{total_issues} issues ({critical} critical, {high} high) | "
            f"Avg maintainability: {avg_mi:.0f}/100"
        )

    def _empty(self, filepath: str, lang: str) -> AnalysisResult:
        return AnalysisResult(file=filepath, language=lang, total_lines=0, blank_lines=0, comment_lines=0, code_lines=0)

    # ── PUBLIC REPORT ─────────────────────────────────────────────────────────
    def report(self, filepath_or_dir: str) -> str:
        p = Path(filepath_or_dir)
        if p.is_dir():
            data = self.analyze_directory(str(p))
            lines = [
                f"📊 Code Analysis: {filepath_or_dir}",
                f"Files: {data['files_analyzed']} | Lines: {data['total_lines']:,}",
                f"Functions: {data['total_functions']} | Classes: {data['total_classes']}",
                f"Avg complexity: {data['avg_complexity']} | {data['summary']}",
                "",
            ]
            if data["hotspots"]:
                lines.append("🔥 Hotspots (high complexity):")
                for h in data["hotspots"][:5]:
                    lines.append(f"  {h['file']}:{h['line']} {h['function']}() cc={h['complexity']} lines={h['lines']}")
            if data["issues"]:
                lines.append("\n⚠️  Top Issues:")
                for issue in data["issues"][:10]:
                    lines.append(f"  [{issue['severity'].upper()}] {issue['file']}:{issue.get('line','?')} — {issue['message']}")
            if data["todos"]:
                lines.append(f"\n📝 TODOs: {len(data['todos'])} found")
            return "\n".join(lines)

        else:
            r = self.analyze_file(str(p))
            lines = [
                f"📊 {r.file} ({r.language})",
                f"Lines: {r.total_lines} (code: {r.code_lines}, blank: {r.blank_lines}, comments: {r.comment_lines})",
                f"Functions: {len(r.functions)} | Classes: {len(r.classes)}",
                f"Avg complexity: {r.avg_complexity} | Max: {r.max_complexity} | Maintainability: {r.maintainability}/100",
                "",
            ]
            if r.functions:
                lines.append("Functions (sorted by complexity):")
                for f in sorted(r.functions, key=lambda x: x.complexity, reverse=True)[:10]:
                    flag = " ⚠️" if f.complexity > 10 else ""
                    lines.append(f"  line {f.line}: {f.name}() cc={f.complexity} ({f.lines} lines){flag}")
            if r.issues:
                lines.append("\nIssues:")
                for issue in r.issues[:15]:
                    lines.append(f"  [{issue['severity'].upper()}] line {issue.get('line','?')}: {issue['message']}")
            if r.todos:
                lines.append("\nTODOs:")
                for _, line, kind, msg in r.todos[:5]:
                    lines.append(f"  line {line} [{kind}]: {msg}")
            return "\n".join(lines)
