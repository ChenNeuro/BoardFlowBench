"""Build a simple name-based function call graph."""

from __future__ import annotations

from typing import Any


def build_call_graph(functions: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Return a lightweight graph keyed by file:function:start_line."""
    graph: dict[str, list[str]] = {}
    for fn in functions:
        key = f"{fn['file_path']}:{fn['function_name']}:{fn['start_line']}"
        graph[key] = list(fn.get("called_function_names", []))
    return graph


def called_function_names(functions: list[dict[str, Any]]) -> set[str]:
    names: set[str] = set()
    for fn in functions:
        names.update(fn.get("called_function_names", []))
    return names

