"""Recursive Python repository scanning."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from repo_manager_core.search_rules import included_roots, load_search_rules, should_scan_path

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


def iter_python_files(repo_path: str | Path, search_rules: dict[str, Any] | None = None) -> list[Path]:
    root = Path(repo_path)
    search_rules = search_rules or load_search_rules(root)
    files: list[Path] = []
    for search_root in included_roots(root, search_rules):
        if not search_root.exists():
            continue
        for path in search_root.rglob("*"):
            if not path.is_file():
                continue
            if not should_scan_path(path, root, search_rules):
                continue
            # Skip generated/dependency/cache directories so reports focus on code
            # the agent is likely responsible for.
            # 中文说明：
            # health review 的对象是“当前仓库中需要维护的源码”，不是虚拟环境、
            # 构建产物或依赖缓存。忽略这些目录可以减少噪音和误报。
            if any(part in IGNORED_DIRS for part in path.parts):
                continue
            files.append(path)
    return sorted(files)


def scan_repo_functions(repo_path: str | Path) -> dict[str, Any]:
    """Scan every Python file in a repository-like directory."""
    root = Path(repo_path)
    search_rules = load_search_rules(root)
    file_results = [scan_file_functions(path) for path in iter_python_files(root, search_rules)]
    # Flatten function records for smell detection while retaining per-file
    # parse status in "files" for troubleshooting.
    # 中文说明：
    # 同时保留两种视图：
    # - files：定位哪个文件解析失败、文件内有哪些函数；
    # - functions：跨文件统一做重复命名、调用关系、wrapper 等规则检测。
    functions = [fn for result in file_results for fn in result["functions"]]

    return {
        "repo_path": str(root),
        "python_file_count": len(file_results),
        "parsed_file_count": sum(1 for item in file_results if item["parse_succeeded"]),
        "failed_file_count": sum(1 for item in file_results if not item["parse_succeeded"]),
        "function_count": len(functions),
        "search_rules": search_rules,
        "files": file_results,
        "functions": functions,
    }
