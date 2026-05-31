"""Rule-based function smell detection."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from repo_manager_core.board.task_status import ENTRY_POINT_NAMES

PATCH_NAME_KEYWORDS = ("fix", "patch", "temp", "workaround", "quick", "hack", "debug", "safe")
HELPER_KEYWORDS = ("helper", "util", "parse", "normalize", "convert", "format")
SUSPICIOUS_FILE_KEYWORDS = ("final", "old", "backup", "temp", "fixed", "patch", "debug")


def called_function_names(functions: list[dict[str, Any]]) -> set[str]:
    """Return the set of all function names called by any scanned function."""
    names: set[str] = set()
    for fn in functions:
        names.update(fn.get("called_function_names", []))
    return names


def _warning(
    severity: str,
    smell_type: str,
    file_path: str,
    function_name: str,
    reason: str,
    suggestion: str,
) -> dict[str, str]:
    return {
        "severity": severity,
        "type": smell_type,
        "file": file_path,
        "function": function_name,
        "reason": reason,
        "suggestion": suggestion,
    }


def detect_function_smells(functions: list[dict[str, Any]]) -> dict[str, Any]:
    """Detect suspicious patterns. Findings are warnings, not proof of defects."""
    warnings: list[dict[str, str]] = []
    called_names = called_function_names(functions)
    definitions = Counter(fn["function_name"] for fn in functions)
    functions_by_file: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for fn in functions:
        functions_by_file[fn["file_path"]].append(fn)

    for fn in functions:
        name = fn["function_name"]
        lowered = name.lower()
        file_path = fn["file_path"]

        if any(keyword in lowered for keyword in PATCH_NAME_KEYWORDS):
            warnings.append(
                _warning(
                    "medium",
                    "patch_name_smell",
                    file_path,
                    name,
                    f"Function name '{name}' contains patch-like wording.",
                    "Review whether this function is a durable abstraction or a temporary patch that should be merged.",
                )
            )

        if (
            name not in called_names
            and not name.startswith("__")
            and name not in ENTRY_POINT_NAMES
        ):
            warnings.append(
                _warning(
                    "low",
                    "unused_function",
                    file_path,
                    name,
                    "The function is defined but not called by another scanned function.",
                    "Confirm whether it is an external entry point; otherwise remove it or add a clear call path.",
                )
            )

        calls = fn.get("called_function_names", [])
        if fn.get("function_length", 0) <= 5 and len(calls) == 1:
            warnings.append(
                _warning(
                    "low",
                    "wrapper_function",
                    file_path,
                    name,
                    f"Very short function mostly delegates to '{calls[0]}'.",
                    "Inline the wrapper or keep it only if it provides a meaningful public API boundary.",
                )
            )

        if definitions[name] > 1:
            warnings.append(
                _warning(
                    "low",
                    "duplicate_function_name",
                    file_path,
                    name,
                    f"Function name '{name}' appears {definitions[name]} times in the scanned repo.",
                    "Check for duplicate-like helpers and consolidate behavior when practical.",
                )
            )

        if any(keyword in Path(file_path).name.lower() for keyword in SUSPICIOUS_FILE_KEYWORDS):
            warnings.append(
                _warning(
                    "medium",
                    "suspicious_file_name",
                    file_path,
                    name,
                    "This function lives in a file whose name looks temporary, patched, or archived.",
                    "Review the file role and fold stable code into the main module structure.",
                )
            )

    for file_path, file_functions in functions_by_file.items():
        short_helpers = [
            fn
            for fn in file_functions
            if fn.get("function_length", 0) <= 8
            and any(keyword in fn["function_name"].lower() for keyword in HELPER_KEYWORDS)
        ]
        if len(short_helpers) >= 4:
            warnings.append(
                _warning(
                    "medium",
                    "fragmented_helpers",
                    file_path,
                    "",
                    f"File contains {len(short_helpers)} short helper-like functions.",
                    "Group related helpers, remove duplicates, and prefer clearer domain-level functions.",
                )
            )

    severity_order = {"high": 0, "medium": 1, "low": 2}
    warnings.sort(key=lambda item: (severity_order.get(item["severity"], 9), item["file"], item["function"]))
    return {
        "summary": {
            "function_count": len(functions),
            "warning_count": len(warnings),
            "called_name_count": len(called_names),
        },
        "warnings": warnings,
    }
