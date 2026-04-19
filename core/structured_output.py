"""
QWEN3-CODER ULTIMATE — Structured Output v1.0
Force model to return valid JSON matching a schema.
JSON Schema validation with retry loop.
"""

import json
import re
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class StructuredResult:
    success:  bool
    data:     Any
    attempts: int
    errors:   list[str]
    raw:      str = ""


class StructuredOutput:
    """
    Guarantees valid JSON output matching a JSON Schema.

    Usage:
        so = StructuredOutput(client, model)
        result = so.get(messages, schema={"type":"object","properties":{...}})
        if result.success:
            data = result.data
    """

    def __init__(self, client, model: str):
        self.client = client
        self.model  = model
        self._stats = {"calls": 0, "retries": 0, "failures": 0}

    def get(self, messages: list, schema: dict,
            max_attempts: int = 3, temperature: float = 0.0) -> StructuredResult:
        """
        Get a response that matches the given JSON Schema.
        Retries with correction feedback if schema validation fails.
        """
        self._stats["calls"] += 1
        errors  = []
        raw_out = ""

        # Inject schema instruction into last user message
        schema_str  = json.dumps(schema, indent=2)
        system_inject = (
            f"You MUST respond with ONLY valid JSON matching this schema. No markdown, no explanation:\n{schema_str}"
        )
        msgs = self._inject_schema_instruction(messages, system_inject)

        for attempt in range(1, max_attempts + 1):
            try:
                resp = self.client.chat.completions.create(
                    model=self.model, messages=msgs,
                    max_tokens=2000, temperature=temperature, stream=False,
                )
                raw_out = resp.choices[0].message.content or ""
            except Exception as e:
                errors.append(f"API error: {e}")
                break

            # Extract JSON from response
            data, parse_err = self._extract_json(raw_out)
            if parse_err:
                errors.append(f"Attempt {attempt}: JSON parse error — {parse_err}")
                self._stats["retries"] += 1
                msgs = self._inject_correction(msgs, raw_out, parse_err, schema_str)
                continue

            # Validate against schema
            schema_errors = self._validate(data, schema)
            if not schema_errors:
                return StructuredResult(success=True, data=data,
                                        attempts=attempt, errors=errors, raw=raw_out)

            errors.append(f"Attempt {attempt}: Schema errors — {'; '.join(schema_errors)}")
            self._stats["retries"] += 1
            msgs = self._inject_correction(msgs, raw_out, "; ".join(schema_errors), schema_str)

        self._stats["failures"] += 1
        return StructuredResult(success=False, data=None,
                                attempts=max_attempts, errors=errors, raw=raw_out)

    def get_list(self, messages: list, item_schema: dict, **kwargs) -> StructuredResult:
        """Shortcut for getting a JSON array."""
        schema = {"type": "array", "items": item_schema}
        return self.get(messages, schema, **kwargs)

    def get_typed(self, messages: list, fields: dict[str, str], **kwargs) -> StructuredResult:
        """
        Shortcut: fields = {"name": "string", "count": "integer", "active": "boolean"}
        Builds schema automatically.
        """
        type_map = {
            "str": "string", "string": "string",
            "int": "integer", "integer": "integer",
            "float": "number", "number": "number",
            "bool": "boolean", "boolean": "boolean",
            "list": "array", "dict": "object",
        }
        properties = {
            k: {"type": type_map.get(v.lower(), "string")}
            for k, v in fields.items()
        }
        schema = {
            "type": "object",
            "properties": properties,
            "required": list(fields.keys()),
        }
        return self.get(messages, schema, **kwargs)

    # ── HELPERS ───────────────────────────────────────────────────────────────

    def _extract_json(self, text: str) -> tuple[Any, Optional[str]]:
        text = text.strip()

        # Strip markdown code fences
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()

        # Direct parse
        try:
            return json.loads(text), None
        except json.JSONDecodeError as e:
            pass

        # Find first JSON object or array
        for pattern in [r"\{[\s\S]*\}", r"\[[\s\S]*\]"]:
            m = re.search(pattern, text)
            if m:
                try:
                    return json.loads(m.group()), None
                except Exception:
                    pass

        # Try fixing trailing commas + single quotes
        fixed = re.sub(r",\s*([}\]])", r"\1", text)
        fixed = re.sub(r"'([^']*)'", r'"\1"', fixed)
        try:
            return json.loads(fixed), None
        except json.JSONDecodeError as e:
            return None, str(e)

    def _validate(self, data: Any, schema: dict) -> list[str]:
        """Minimal JSON Schema validation (subset)."""
        errors = []
        schema_type = schema.get("type")

        TYPE_MAP = {
            "string": str, "integer": int, "number": (int, float),
            "boolean": bool, "array": list, "object": dict, "null": type(None),
        }

        if schema_type and schema_type != "null":
            expected = TYPE_MAP.get(schema_type)
            if expected and not isinstance(data, expected):
                errors.append(f"Expected {schema_type}, got {type(data).__name__}")
                return errors

        if schema_type == "object" and isinstance(data, dict):
            for req in schema.get("required", []):
                if req not in data:
                    errors.append(f"Missing required field: '{req}'")
            for prop, prop_schema in schema.get("properties", {}).items():
                if prop in data:
                    sub_errors = self._validate(data[prop], prop_schema)
                    errors += [f"{prop}: {e}" for e in sub_errors]

        elif schema_type == "array" and isinstance(data, list):
            item_schema = schema.get("items", {})
            min_items   = schema.get("minItems", 0)
            if len(data) < min_items:
                errors.append(f"Array too short: {len(data)} < {min_items}")
            for i, item in enumerate(data[:5]):  # validate first 5
                sub_errors = self._validate(item, item_schema)
                errors += [f"[{i}]: {e}" for e in sub_errors]

        if "enum" in schema and data not in schema["enum"]:
            errors.append(f"Value {data!r} not in enum {schema['enum']}")

        return errors

    def _inject_schema_instruction(self, messages: list, instruction: str) -> list:
        msgs = list(messages)
        # Add/update system message
        if msgs and msgs[0]["role"] == "system":
            msgs[0] = {**msgs[0], "content": msgs[0]["content"] + f"\n\n{instruction}"}
        else:
            msgs.insert(0, {"role": "system", "content": instruction})
        return msgs

    def _inject_correction(self, messages: list, bad_output: str,
                           error: str, schema_str: str) -> list:
        msgs = list(messages)
        msgs.append({"role": "assistant", "content": bad_output})
        msgs.append({"role": "user", "content": (
            f"Your response was invalid.\nError: {error}\n"
            f"Schema required:\n{schema_str}\n\n"
            "Respond with ONLY valid JSON, nothing else:"
        )})
        return msgs

    def stats(self) -> str:
        return (f"StructuredOutput: {self._stats['calls']} calls | "
                f"{self._stats['retries']} retries | "
                f"{self._stats['failures']} failures")
