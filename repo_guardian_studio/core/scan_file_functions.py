"""AST-based function scanner for a single Python file."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from .extract_comments import extract_leading_comments


class _CallCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.calls: list[str] = []

    def visit_Call(self, node: ast.Call) -> Any:
        name = self._call_name(node.func)
        if name:
            self.calls.append(name)
        self.generic_visit(node)

    @staticmethod
    def _call_name(node: ast.AST) -> str | None:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        return None


def _argument_names(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    args = [arg.arg for arg in node.args.posonlyargs]
    args.extend(arg.arg for arg in node.args.args)
    args.extend(arg.arg for arg in node.args.kwonlyargs)
    if node.args.vararg:
        args.append("*" + node.args.vararg.arg)
    if node.args.kwarg:
        args.append("**" + node.args.kwarg.arg)
    return args


def _function_info(
    file_path: Path,
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    source_lines: list[str],
    parse_succeeded: bool,
) -> dict[str, Any]:
    collector = _CallCollector()
    collector.visit(node)
    start_line = int(getattr(node, "lineno", 0) or 0)
    end_line = int(getattr(node, "end_lineno", start_line) or start_line)

    return {
        "file_path": str(file_path),
        "function_name": node.name,
        "argument_names": _argument_names(node),
        "start_line": start_line,
        "end_line": end_line,
        "docstring": ast.get_docstring(node) or "",
        "leading_comments": extract_leading_comments(source_lines, start_line),
        "function_length": max(0, end_line - start_line + 1),
        "called_function_names": sorted(set(collector.calls)),
        "parse_succeeded": parse_succeeded,
    }


def scan_file_functions(file_path: str | Path) -> dict[str, Any]:
    """Scan one Python file and return parse status plus function metadata."""
    path = Path(file_path)
    result: dict[str, Any] = {
        "file_path": str(path),
        "parse_succeeded": False,
        "error": "",
        "functions": [],
    }

    try:
        source = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        source = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        result["error"] = str(exc)
        return result

    source_lines = source.splitlines()
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        result["error"] = f"{exc.__class__.__name__}: {exc}"
        return result

    result["parse_succeeded"] = True
    result["functions"] = [
        _function_info(path, node, source_lines, True)
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    result["functions"].sort(key=lambda item: (item["start_line"], item["function_name"]))
    return result

