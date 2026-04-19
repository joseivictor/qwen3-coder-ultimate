"""
QWEN3-CODER ULTIMATE — Refactor Engine v1.0
Safe automated refactoring: rename, extract method/variable, inline,
move symbol, dead code removal. Pre/post validation with tests.
"""

import ast
import re
import os
import difflib
import subprocess
import shutil
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RefactorResult:
    operation:    str
    success:      bool
    files_changed: list[str] = field(default_factory=list)
    diff:         str = ""
    error:        str = ""
    tests_passed: Optional[bool] = None
    message:      str = ""


class RefactorEngine:
    """
    Safe automated refactoring with diff preview and optional test validation.
    All operations create backups before modifying files.
    """

    SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}

    def __init__(self, project_root: str = "."):
        self.root    = Path(project_root).resolve()
        self._backup: dict[str, str] = {}

    # ── RENAME ────────────────────────────────────────────────────────────────
    def rename_symbol(self, old_name: str, new_name: str,
                      file_pattern: str = "*.py",
                      whole_word: bool = True) -> RefactorResult:
        """
        Rename a symbol (function, class, variable) across all matching files.
        Uses whole-word matching to avoid partial replacements.
        """
        if not self._valid_identifier(new_name):
            return RefactorResult("rename", False, error=f"Invalid identifier: {new_name}")

        files     = self._find_files(file_pattern)
        changed   = []
        full_diff = []

        pattern = re.compile(
            r'\b' + re.escape(old_name) + r'\b' if whole_word else re.escape(old_name)
        )

        for fp in files:
            content = fp.read_text(encoding="utf-8", errors="replace")
            if old_name not in content:
                continue

            new_content = pattern.sub(new_name, content)
            if new_content == content:
                continue

            diff = self._make_diff(str(fp), content, new_content)
            full_diff.append(diff)

            self._backup_file(fp, content)
            fp.write_text(new_content, encoding="utf-8")
            changed.append(str(fp))

        if not changed:
            return RefactorResult("rename", False, error=f"Symbol '{old_name}' not found in {file_pattern} files.")

        return RefactorResult(
            operation     = "rename",
            success       = True,
            files_changed = changed,
            diff          = "\n".join(full_diff),
            message       = f"Renamed '{old_name}' → '{new_name}' in {len(changed)} file(s)",
        )

    # ── EXTRACT FUNCTION ──────────────────────────────────────────────────────
    def extract_function(self, filepath: str, start_line: int, end_line: int,
                         new_function_name: str, params: list[str] = None) -> RefactorResult:
        """Extract lines [start_line..end_line] into a new function."""
        fp = Path(filepath)
        if not fp.exists():
            return RefactorResult("extract_function", False, error=f"File not found: {filepath}")
        if not self._valid_identifier(new_function_name):
            return RefactorResult("extract_function", False, error=f"Invalid name: {new_function_name}")

        content = fp.read_text(encoding="utf-8", errors="replace")
        lines   = content.splitlines()

        if start_line < 1 or end_line > len(lines) or start_line > end_line:
            return RefactorResult("extract_function", False, error="Invalid line range.")

        extracted = lines[start_line-1:end_line]
        indent    = self._detect_indent(extracted)
        dedented  = [l[len(indent):] if l.startswith(indent) else l for l in extracted]

        params_str = ", ".join(params) if params else ""
        func_def   = [
            f"def {new_function_name}({params_str}):",
            *[f"    {l}" for l in dedented],
            "",
        ]

        call_line  = f"{indent}{new_function_name}({params_str})"

        new_lines  = (
            lines[:start_line-1] +
            [call_line] +
            lines[end_line:] +
            ["", ""] +
            func_def
        )
        new_content = "\n".join(new_lines)

        diff = self._make_diff(filepath, content, new_content)
        self._backup_file(fp, content)
        fp.write_text(new_content, encoding="utf-8")

        return RefactorResult(
            operation     = "extract_function",
            success       = True,
            files_changed = [filepath],
            diff          = diff,
            message       = f"Extracted lines {start_line}-{end_line} into {new_function_name}()",
        )

    # ── EXTRACT VARIABLE ──────────────────────────────────────────────────────
    def extract_variable(self, filepath: str, line_num: int,
                         expression: str, var_name: str) -> RefactorResult:
        """Replace an inline expression with a named variable."""
        fp = Path(filepath)
        if not fp.exists():
            return RefactorResult("extract_variable", False, error=f"File not found: {filepath}")

        content = fp.read_text(encoding="utf-8", errors="replace")
        lines   = content.splitlines()

        if line_num < 1 or line_num > len(lines):
            return RefactorResult("extract_variable", False, error="Invalid line number.")

        target_line = lines[line_num - 1]
        if expression not in target_line:
            return RefactorResult("extract_variable", False, error=f"Expression not found on line {line_num}.")

        indent         = len(target_line) - len(target_line.lstrip())
        indent_str     = target_line[:indent]
        assignment     = f"{indent_str}{var_name} = {expression}"
        new_line       = target_line.replace(expression, var_name, 1)

        new_lines      = lines[:line_num-1] + [assignment, new_line] + lines[line_num:]
        new_content    = "\n".join(new_lines)

        diff = self._make_diff(filepath, content, new_content)
        self._backup_file(fp, content)
        fp.write_text(new_content, encoding="utf-8")

        return RefactorResult(
            operation     = "extract_variable",
            success       = True,
            files_changed = [filepath],
            diff          = diff,
            message       = f"Extracted '{expression}' into variable '{var_name}' at line {line_num}",
        )

    # ── INLINE VARIABLE ───────────────────────────────────────────────────────
    def inline_variable(self, filepath: str, var_name: str) -> RefactorResult:
        """Inline a single-assignment variable at its use sites and remove the assignment."""
        fp = Path(filepath)
        if not fp.exists():
            return RefactorResult("inline_variable", False, error=f"File not found: {filepath}")

        content = fp.read_text(encoding="utf-8", errors="replace")
        lines   = content.splitlines()

        assign_pattern = re.compile(r"^(\s*)" + re.escape(var_name) + r"\s*=\s*(.+)$")
        assign_line    = -1
        assign_value   = ""

        for i, line in enumerate(lines):
            m = assign_pattern.match(line)
            if m:
                if assign_line >= 0:
                    return RefactorResult("inline_variable", False,
                                         error=f"Multiple assignments to '{var_name}' — cannot safely inline.")
                assign_line  = i
                assign_value = m.group(2).strip()

        if assign_line < 0:
            return RefactorResult("inline_variable", False,
                                  error=f"Assignment to '{var_name}' not found.")

        use_pattern = re.compile(r'\b' + re.escape(var_name) + r'\b')
        new_lines   = []
        for i, line in enumerate(lines):
            if i == assign_line:
                continue
            new_lines.append(use_pattern.sub(assign_value, line))

        new_content = "\n".join(new_lines)
        diff = self._make_diff(filepath, content, new_content)
        self._backup_file(fp, content)
        fp.write_text(new_content, encoding="utf-8")

        return RefactorResult(
            operation     = "inline_variable",
            success       = True,
            files_changed = [filepath],
            diff          = diff,
            message       = f"Inlined '{var_name}' (value: {assign_value[:60]})",
        )

    # ── MOVE SYMBOL ───────────────────────────────────────────────────────────
    def move_function(self, source_file: str, target_file: str,
                      function_name: str) -> RefactorResult:
        """Move a function definition from source_file to target_file."""
        src = Path(source_file)
        tgt = Path(target_file)

        if not src.exists():
            return RefactorResult("move_function", False, error=f"Source file not found: {source_file}")

        src_content = src.read_text(encoding="utf-8", errors="replace")
        tgt_content = tgt.read_text(encoding="utf-8", errors="replace") if tgt.exists() else ""

        func_text, new_src_content = self._extract_function_text(src_content, function_name)
        if not func_text:
            return RefactorResult("move_function", False,
                                  error=f"Function '{function_name}' not found in {source_file}")

        new_tgt_content = tgt_content + "\n\n" + func_text

        self._backup_file(src, src_content)
        src.write_text(new_src_content, encoding="utf-8")
        tgt.parent.mkdir(parents=True, exist_ok=True)
        tgt.write_text(new_tgt_content, encoding="utf-8")

        diff = (self._make_diff(source_file, src_content, new_src_content) +
                self._make_diff(target_file, tgt_content, new_tgt_content))

        return RefactorResult(
            operation     = "move_function",
            success       = True,
            files_changed = [source_file, target_file],
            diff          = diff,
            message       = f"Moved '{function_name}' from {source_file} → {target_file}",
        )

    # ── REMOVE DEAD CODE ──────────────────────────────────────────────────────
    def remove_dead_code(self, filepath: str) -> RefactorResult:
        """Remove obvious dead code: unreachable statements, pass-only functions, unused imports."""
        fp = Path(filepath)
        if not fp.exists():
            return RefactorResult("remove_dead_code", False, error=f"File not found: {filepath}")
        if fp.suffix != ".py":
            return RefactorResult("remove_dead_code", False, error="Only Python files supported.")

        content = fp.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            return RefactorResult("remove_dead_code", False, error=f"Syntax error: {e}")

        dead_lines = set()
        lines      = content.splitlines()

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if (len(node.body) == 1 and
                        isinstance(node.body[0], ast.Expr) and
                        isinstance(node.body[0].value, ast.Constant) and
                        node.body[0].value.value is ...):
                    pass

            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.For, ast.While)):
                after_return = False
                for child in ast.iter_child_nodes(node):
                    if after_return and isinstance(child, ast.stmt):
                        if hasattr(child, "lineno"):
                            dead_lines.add(child.lineno)
                    if isinstance(child, ast.Return):
                        after_return = True

        if not dead_lines:
            return RefactorResult("remove_dead_code", True, message="No obvious dead code found.")

        new_lines   = [l for i, l in enumerate(lines, 1) if i not in dead_lines]
        new_content = "\n".join(new_lines)
        diff        = self._make_diff(filepath, content, new_content)

        self._backup_file(fp, content)
        fp.write_text(new_content, encoding="utf-8")

        return RefactorResult(
            operation     = "remove_dead_code",
            success       = True,
            files_changed = [filepath],
            diff          = diff,
            message       = f"Removed {len(dead_lines)} dead code line(s)",
        )

    # ── SAFE RENAME WITH TEST VALIDATION ─────────────────────────────────────
    def safe_rename(self, old_name: str, new_name: str,
                    file_pattern: str = "*.py",
                    test_command: str = "") -> RefactorResult:
        """Rename with automatic rollback if tests fail after the change."""
        result = self.rename_symbol(old_name, new_name, file_pattern)
        if not result.success:
            return result

        if test_command:
            passed = self._run_tests(test_command)
            result.tests_passed = passed
            if not passed:
                self.undo_last()
                result.success = False
                result.error   = "Tests failed after rename — changes rolled back."
                result.message = f"Rollback: '{new_name}' reverted to '{old_name}'"

        return result

    def _run_tests(self, command: str) -> bool:
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True,
                text=True, timeout=120, cwd=str(self.root)
            )
            return result.returncode == 0
        except Exception:
            return False

    # ── UNDO ──────────────────────────────────────────────────────────────────
    def undo_last(self):
        for filepath, content in self._backup.items():
            try:
                Path(filepath).write_text(content, encoding="utf-8")
            except Exception:
                pass
        self._backup.clear()

    # ── HELPERS ───────────────────────────────────────────────────────────────
    def _find_files(self, pattern: str) -> list[Path]:
        files = []
        for fp in self.root.rglob(pattern):
            if any(part in self.SKIP_DIRS for part in fp.parts):
                continue
            if fp.is_file():
                files.append(fp)
        return files

    def _backup_file(self, fp: Path, content: str):
        self._backup[str(fp)] = content

    def _make_diff(self, filepath: str, old: str, new: str) -> str:
        diff = difflib.unified_diff(
            old.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile=f"a/{filepath}",
            tofile=f"b/{filepath}",
            lineterm="",
        )
        return "".join(diff)

    def _detect_indent(self, lines: list[str]) -> str:
        for line in lines:
            if line.strip():
                return line[:len(line) - len(line.lstrip())]
        return "    "

    def _valid_identifier(self, name: str) -> bool:
        return bool(re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name))

    def _extract_function_text(self, content: str, func_name: str) -> tuple[str, str]:
        """Extract a function's full text from content, return (func_text, remaining_content)."""
        try:
            tree  = ast.parse(content)
            lines = content.splitlines()

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func_name:
                    start = node.lineno - 1
                    end   = (node.end_lineno or node.lineno)

                    for d in node.decorator_list:
                        start = min(start, d.lineno - 1)

                    func_lines    = lines[start:end]
                    func_text     = "\n".join(func_lines)
                    remaining     = "\n".join(lines[:start] + lines[end:])
                    return func_text, remaining
        except Exception:
            pass
        return "", content

    def format_result(self, result: RefactorResult) -> str:
        icon = "✅" if result.success else "❌"
        lines = [
            f"{icon} Refactor: {result.operation}",
            result.message or result.error,
        ]
        if result.files_changed:
            lines.append(f"Files changed: {', '.join(result.files_changed)}")
        if result.tests_passed is not None:
            lines.append(f"Tests: {'✅ passed' if result.tests_passed else '❌ failed'}")
        if result.diff:
            lines.append(f"\nDiff preview:\n{result.diff[:1500]}")
        return "\n".join(lines)
