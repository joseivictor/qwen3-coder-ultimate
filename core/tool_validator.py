"""
QWEN3-CODER ULTIMATE — Tool Validator v1.0
Zero-hallucination tool use: schema enforcement, arg auto-correction,
retry-with-feedback loop. This is what makes Claude Code reliable.
"""

import json
import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ValidationResult:
    valid:     bool
    args:      dict
    errors:    list[str] = field(default_factory=list)
    corrected: bool = False
    attempts:  int = 1


@dataclass
class ExecutionResult:
    success:   bool
    output:    str
    tool_name: str
    args:      dict
    attempts:  int = 1
    error:     str = ""


# Full type coercers
TYPE_COERCERS = {
    "string":  str,
    "integer": lambda v: int(float(v)) if str(v).strip() else 0,
    "number":  float,
    "boolean": lambda v: str(v).lower() in ("true", "1", "yes", "sim") if isinstance(v, str) else bool(v),
    "array":   lambda v: v if isinstance(v, list) else [v],
    "object":  lambda v: v if isinstance(v, dict) else {},
}


class ToolValidator:
    """
    Validates and auto-corrects tool arguments against their JSON Schema.
    Implements a retry-with-correction loop using LLM feedback.

    This directly solves the #1 reliability gap vs Claude Code:
    Qwen models sometimes produce malformed args → this catches and fixes them.
    """

    def __init__(self, client, model: str, tools: list):
        self.client    = client
        self.model     = model
        self.tools     = {t["function"]["name"]: t["function"] for t in tools if "function" in t}
        self._stats    = {"validated": 0, "corrected": 0, "failed": 0}

    def update_tools(self, tools: list):
        self.tools = {t["function"]["name"]: t["function"] for t in tools if "function" in t}

    # ── MAIN ENTRY POINT ──────────────────────────────────────────────────────
    def validate_and_fix(self, tool_name: str, raw_args: str,
                         max_attempts: int = 3) -> ValidationResult:
        """
        Parse raw_args JSON, validate against schema, auto-correct if needed.
        Returns a ValidationResult with corrected args ready for execution.
        """
        self._stats["validated"] += 1

        # Step 1: Parse JSON
        args, parse_error = self._parse_json(raw_args)
        if parse_error and max_attempts > 1:
            args = self._llm_fix_json(tool_name, raw_args, parse_error)
            if args is None:
                self._stats["failed"] += 1
                return ValidationResult(False, {}, [f"JSON parse failed: {parse_error}"])

        args = args or {}

        # Step 2: Validate against schema
        schema = self.tools.get(tool_name, {}).get("parameters", {})
        errors = self._validate_schema(args, schema)

        if not errors:
            return ValidationResult(True, args, corrected=False)

        # Step 3: Auto-correct type mismatches
        args, remaining = self._auto_correct_types(args, schema)
        if not remaining:
            self._stats["corrected"] += 1
            return ValidationResult(True, args, corrected=True, errors=errors)

        # Step 4: LLM-assisted correction for structural errors
        if max_attempts > 1:
            fixed = self._llm_fix_args(tool_name, args, remaining)
            if fixed:
                final_errors = self._validate_schema(fixed, schema)
                if not final_errors:
                    self._stats["corrected"] += 1
                    return ValidationResult(True, fixed, corrected=True, errors=errors, attempts=2)

        # Step 5: Fill required fields with safe defaults
        args = self._fill_defaults(args, schema)
        final_errors = self._validate_schema(args, schema)

        if final_errors:
            self._stats["failed"] += 1
            return ValidationResult(False, args, errors=final_errors, attempts=max_attempts)

        self._stats["corrected"] += 1
        return ValidationResult(True, args, corrected=True, errors=errors, attempts=max_attempts)

    # ── JSON PARSING ──────────────────────────────────────────────────────────
    def _parse_json(self, raw: str) -> tuple[Optional[dict], Optional[str]]:
        raw = raw.strip()
        if not raw:
            return {}, None

        # Try direct parse
        try:
            return json.loads(raw), None
        except json.JSONDecodeError as e:
            pass

        # Try extracting JSON object from text
        for pattern in [r'\{[^{}]*\}', r'\{.*\}']:
            m = re.search(pattern, raw, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group()), None
                except Exception:
                    pass

        # Try fixing common issues
        fixed = raw
        fixed = re.sub(r',\s*([}\]])', r'\1', fixed)        # trailing commas
        fixed = re.sub(r"'([^']*)'", r'"\1"', fixed)        # single → double quotes
        fixed = re.sub(r'(\w+):', r'"\1":', fixed)           # unquoted keys
        try:
            return json.loads(fixed), None
        except json.JSONDecodeError as e:
            return None, str(e)

    def _llm_fix_json(self, tool_name: str, raw_args: str, error: str) -> Optional[dict]:
        schema = self.tools.get(tool_name, {})
        prompt = (
            f"Fix this malformed JSON for tool '{tool_name}'.\n"
            f"Error: {error}\n"
            f"Schema: {json.dumps(schema.get('parameters', {}), indent=2)[:500]}\n"
            f"Broken JSON: {raw_args[:500]}\n\n"
            "Output ONLY valid JSON, nothing else:"
        )
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300, temperature=0.0, stream=False,
            )
            fixed_raw = resp.choices[0].message.content or ""
            result, err = self._parse_json(fixed_raw)
            return result if not err else None
        except Exception:
            return None

    # ── SCHEMA VALIDATION ─────────────────────────────────────────────────────
    def _validate_schema(self, args: dict, schema: dict) -> list[str]:
        errors = []
        properties = schema.get("properties", {})
        required   = schema.get("required", [])

        for field_name in required:
            if field_name not in args or args[field_name] is None:
                errors.append(f"Missing required field: '{field_name}'")

        for field_name, value in args.items():
            if field_name not in properties:
                continue
            field_schema = properties[field_name]
            expected_type = field_schema.get("type")
            if not expected_type:
                continue
            type_error = self._check_type(field_name, value, expected_type, field_schema)
            if type_error:
                errors.append(type_error)

            if "enum" in field_schema and value not in field_schema["enum"]:
                errors.append(f"Field '{field_name}' must be one of {field_schema['enum']}, got '{value}'")

        return errors

    def _check_type(self, name: str, value, expected: str, schema: dict) -> Optional[str]:
        type_map = {
            "string":  str,
            "integer": int,
            "number":  (int, float),
            "boolean": bool,
            "array":   list,
            "object":  dict,
        }
        expected_py = type_map.get(expected)
        if not expected_py:
            return None
        if not isinstance(value, expected_py):
            return f"Field '{name}' should be {expected}, got {type(value).__name__}"
        return None

    # ── AUTO-CORRECTION ───────────────────────────────────────────────────────
    def _auto_correct_types(self, args: dict, schema: dict) -> tuple[dict, list[str]]:
        """Fix type mismatches automatically (e.g. "3" → 3, "true" → True)."""
        properties = schema.get("properties", {})
        corrected  = dict(args)
        remaining  = []

        errors = self._validate_schema(args, schema)
        for error in errors:
            if "Missing required field" in error:
                remaining.append(error)
                continue

            match = re.search(r"Field '(\w+)' should be (\w+)", error)
            if not match:
                remaining.append(error)
                continue

            field_name  = match.group(1)
            target_type = match.group(2)
            coercer     = TYPE_COERCERS.get(target_type)

            if coercer and field_name in corrected:
                try:
                    corrected[field_name] = coercer(corrected[field_name])
                except Exception:
                    remaining.append(error)
            else:
                remaining.append(error)

        return corrected, remaining

    def _fill_defaults(self, args: dict, schema: dict) -> dict:
        """Fill missing required fields with safe defaults."""
        properties = schema.get("properties", {})
        required   = schema.get("required", [])
        filled     = dict(args)

        for field_name in required:
            if field_name in filled and filled[field_name] is not None:
                continue
            field_schema = properties.get(field_name, {})
            field_type   = field_schema.get("type", "string")
            defaults = {
                "string":  "",
                "integer": 0,
                "number":  0.0,
                "boolean": False,
                "array":   [],
                "object":  {},
            }
            if "default" in field_schema:
                filled[field_name] = field_schema["default"]
            elif "enum" in field_schema:
                filled[field_name] = field_schema["enum"][0]
            else:
                filled[field_name] = defaults.get(field_type, "")

        return filled

    def _llm_fix_args(self, tool_name: str, args: dict, errors: list[str]) -> Optional[dict]:
        schema = self.tools.get(tool_name, {})
        prompt = (
            f"Fix these tool arguments for '{tool_name}'.\n"
            f"Errors: {chr(10).join(errors)}\n"
            f"Schema: {json.dumps(schema.get('parameters', {}), indent=2)[:600]}\n"
            f"Current args: {json.dumps(args, indent=2)[:400]}\n\n"
            "Output ONLY the corrected JSON args, nothing else:"
        )
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400, temperature=0.0, stream=False,
            )
            raw   = resp.choices[0].message.content or ""
            fixed, err = self._parse_json(raw)
            return fixed if not err else None
        except Exception:
            return None

    # ── SAFE EXECUTOR ─────────────────────────────────────────────────────────
    def validated_execute(self, tool_name: str, raw_args: str,
                          executor, max_attempts: int = 3) -> ExecutionResult:
        """
        Validate args, then execute. Retry with correction if execution fails
        due to arg-related errors.
        """
        validation = self.validate_and_fix(tool_name, raw_args, max_attempts)

        if not validation.valid:
            return ExecutionResult(
                success=False, output="", tool_name=tool_name,
                args=validation.args, error=f"Validation failed: {'; '.join(validation.errors)}"
            )

        for attempt in range(1, max_attempts + 1):
            try:
                result = executor.execute(tool_name, validation.args)
                is_error = (
                    result.startswith("Tool error") or
                    result.startswith("Unknown tool") or
                    result.startswith("❌") or
                    "not found" in result.lower() and attempt == 1
                )
                if not is_error or attempt == max_attempts:
                    return ExecutionResult(
                        success=not is_error, output=result,
                        tool_name=tool_name, args=validation.args, attempts=attempt,
                    )
                # Retry with corrected args from error message
                fixed = self._fix_from_error(tool_name, validation.args, result)
                if fixed:
                    validation.args = fixed
            except Exception as e:
                if attempt == max_attempts:
                    return ExecutionResult(
                        success=False, output="", tool_name=tool_name,
                        args=validation.args, attempts=attempt, error=str(e),
                    )

        return ExecutionResult(
            success=False, output="Max retries reached", tool_name=tool_name,
            args=validation.args, attempts=max_attempts,
        )

    def _fix_from_error(self, tool_name: str, args: dict, error_output: str) -> Optional[dict]:
        schema = self.tools.get(tool_name, {})
        prompt = (
            f"Tool '{tool_name}' returned an error. Fix the arguments.\n"
            f"Error: {error_output[:300]}\n"
            f"Schema: {json.dumps(schema.get('parameters', {}), indent=2)[:500]}\n"
            f"Failed args: {json.dumps(args)[:300]}\n\n"
            "Output ONLY the corrected JSON args:"
        )
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300, temperature=0.0, stream=False,
            )
            result, err = self._parse_json(resp.choices[0].message.content or "")
            return result if not err else None
        except Exception:
            return None

    def stats(self) -> str:
        total = self._stats["validated"]
        if not total:
            return "ToolValidator: no calls yet."
        corr_pct = self._stats["corrected"] / total * 100
        fail_pct = self._stats["failed"]    / total * 100
        return (
            f"ToolValidator: {total} calls | "
            f"{self._stats['corrected']} corrected ({corr_pct:.0f}%) | "
            f"{self._stats['failed']} failed ({fail_pct:.0f}%)"
        )
