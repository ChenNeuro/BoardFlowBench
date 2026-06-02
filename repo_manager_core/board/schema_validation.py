"""Small JSON Schema validator for repository-local protocol documents."""

from __future__ import annotations

import re
from typing import Any


def validate_json_schema(value: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    """Validate the JSON Schema subset used by BoardFlow protocol files."""
    violations: list[str] = []
    expected_type = schema.get("type")
    if expected_type and not _matches_type(value, str(expected_type)):
        return [f"{path} must be {expected_type}"]

    if isinstance(value, dict):
        required = schema.get("required", [])
        for field in required if isinstance(required, list) else []:
            if field not in value:
                violations.append(f"{path}.{field} is required")
        properties = schema.get("properties", {})
        if isinstance(properties, dict):
            for field, item in value.items():
                child = properties.get(field)
                if isinstance(child, dict):
                    violations.extend(validate_json_schema(item, child, f"{path}.{field}"))
                elif schema.get("additionalProperties") is False:
                    violations.append(f"{path}.{field} is not allowed")

    if isinstance(value, list):
        minimum = schema.get("minItems")
        if isinstance(minimum, int) and len(value) < minimum:
            violations.append(f"{path} must contain at least {minimum} items")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                violations.extend(validate_json_schema(item, item_schema, f"{path}[{index}]"))

    if isinstance(value, str):
        minimum = schema.get("minLength")
        if isinstance(minimum, int) and len(value) < minimum:
            violations.append(f"{path} must contain at least {minimum} characters")
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and not re.search(pattern, value):
            violations.append(f"{path} must match {pattern}")
        enum = schema.get("enum")
        if isinstance(enum, list) and value not in enum:
            violations.append(f"{path} must be one of {enum}")
    return violations


def _matches_type(value: Any, expected_type: str) -> bool:
    checks = {
        "array": lambda item: isinstance(item, list),
        "boolean": lambda item: isinstance(item, bool),
        "integer": lambda item: isinstance(item, int) and not isinstance(item, bool),
        "number": lambda item: isinstance(item, (int, float)) and not isinstance(item, bool),
        "object": lambda item: isinstance(item, dict),
        "string": lambda item: isinstance(item, str),
    }
    check = checks.get(expected_type)
    return bool(check and check(value))
