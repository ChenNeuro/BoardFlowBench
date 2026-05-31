"""Recursive Python repository scanning."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .scan_file_functions import scan_file_functions

IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
    "node_modules",
}


def iter_python_files(repo_path: str | Path) -> list[Path]:
    root = Path(repo_path)
    files: list[Path] = []
    for path in root.rglob("*.py"):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        files.append(path)
    return sorted(files)


def scan_repo_functions(repo_path: str | Path) -> dict[str, Any]:
    """Scan every Python file in a repository-like directory."""
    root = Path(repo_path)
    file_results = [scan_file_functions(path) for path in iter_python_files(root)]
    functions = [fn for result in file_results for fn in result["functions"]]

    return {
        "repo_path": str(root),
        "python_file_count": len(file_results),
        "parsed_file_count": sum(1 for item in file_results if item["parse_succeeded"]),
        "failed_file_count": sum(1 for item in file_results if not item["parse_succeeded"]),
        "function_count": len(functions),
        "files": file_results,
        "functions": functions,
    }
