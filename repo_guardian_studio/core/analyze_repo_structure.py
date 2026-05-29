"""Repository layout heuristics."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .scan_repo_functions import IGNORED_DIRS, iter_python_files

SUSPICIOUS_DIR_KEYWORDS = {"old", "temp", "backup", "final"}
SUSPICIOUS_FILE_KEYWORDS = {"final", "old", "backup", "temp", "fixed", "patch", "debug"}
OUTPUT_DIR_KEYWORDS = {"output", "outputs", "artifact", "artifacts", "result", "results"}


def _contains_keyword(value: str, keywords: set[str]) -> bool:
    lowered = value.lower()
    return any(keyword in lowered for keyword in keywords)


def analyze_repo_structure(repo_path: str | Path) -> dict[str, Any]:
    root = Path(repo_path)
    warnings: list[dict[str, Any]] = []
    python_files = iter_python_files(root)
    top_level_files = [path for path in python_files if path.parent == root]

    if len(top_level_files) > 8:
        warnings.append(
            {
                "severity": "medium",
                "type": "too_many_top_level_python_files",
                "file": "",
                "function": "",
                "reason": f"Found {len(top_level_files)} top-level Python files.",
                "suggestion": "Group related modules into packages instead of leaving many scripts at the repo root.",
            }
        )

    for path in root.rglob("*"):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        if path.is_dir() and _contains_keyword(path.name, SUSPICIOUS_DIR_KEYWORDS):
            warnings.append(
                {
                    "severity": "low",
                    "type": "suspicious_directory_name",
                    "file": str(path),
                    "function": "",
                    "reason": f"Directory name '{path.name}' looks like a temporary or archived workspace.",
                    "suggestion": "Move archived code outside the active repo or rename the directory to reflect its purpose.",
                }
            )

    for path in python_files:
        if _contains_keyword(path.name, SUSPICIOUS_FILE_KEYWORDS):
            warnings.append(
                {
                    "severity": "medium",
                    "type": "suspicious_file_name",
                    "file": str(path),
                    "function": "",
                    "reason": f"File name '{path.name}' suggests patch, debug, backup, or final-copy code.",
                    "suggestion": "Rename or consolidate the file after reviewing whether it is still needed.",
                }
            )
        if any(_contains_keyword(part, OUTPUT_DIR_KEYWORDS) for part in path.parts):
            warnings.append(
                {
                    "severity": "medium",
                    "type": "python_file_inside_output_directory",
                    "file": str(path),
                    "function": "",
                    "reason": "Python source appears inside an output/artifact/result-like directory.",
                    "suggestion": "Keep generated outputs separate from source code unless this is intentional.",
                }
            )

    return {
        "repo_path": str(root),
        "python_file_count": len(python_files),
        "top_level_python_file_count": len(top_level_files),
        "warnings": warnings,
    }

