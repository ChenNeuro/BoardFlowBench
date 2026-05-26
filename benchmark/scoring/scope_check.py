"""Scope-control checks for BoardFlowBench."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


def check_scope(repo: str | Path, task: dict[str, Any]) -> dict[str, Any]:
    """Score scope control out of 15."""
    root = Path(repo)
    changed = _changed_files(root)
    warnings: list[str] = []
    violations: list[str] = []
    details: dict[str, Any] = {"changed_files": changed["files"]}
    warnings.extend(changed["warnings"])

    allowed_paths = [str(path) for path in task.get("allowed_paths", [])]
    forbidden_paths = [str(path) for path in task.get("forbidden_paths", [])]

    score = 0

    if changed["baseline_available"]:
        outside_allowed = [
            path for path in changed["files"] if not _matches_any(path, allowed_paths)
        ]
        forbidden_modified = [
            path for path in changed["files"] if _matches_any(path, forbidden_paths)
        ]
        unrelated_docs = [
            path
            for path in changed["files"]
            if path.startswith("docs/") and not _matches_any(path, allowed_paths)
        ]
    else:
        outside_allowed = []
        forbidden_modified = []
        unrelated_docs = []

    details["outside_allowed_paths"] = outside_allowed
    details["forbidden_paths_modified"] = forbidden_modified
    details["unrelated_docs_or_formatting"] = unrelated_docs

    if outside_allowed:
        violations.append(
            "changed files outside allowed_paths: " + ", ".join(outside_allowed)
        )
    else:
        score += 8

    if forbidden_modified:
        violations.append(
            "forbidden_paths modified: " + ", ".join(forbidden_modified)
        )
    else:
        score += 4

    if unrelated_docs:
        violations.append(
            "unrelated docs or formatting churn detected: " + ", ".join(unrelated_docs)
        )
    else:
        score += 3

    return {
        "score": score,
        "max": 15,
        "violations": violations,
        "warnings": warnings,
        "details": details,
    }


def _matches_any(path: str, patterns: list[str]) -> bool:
    return any(_matches_path(path, pattern) for pattern in patterns)


def _matches_path(path: str, pattern: str) -> bool:
    normalized = pattern.rstrip("/")
    if pattern.endswith("/"):
        return path == normalized or path.startswith(normalized + "/")
    return path == normalized


def _changed_files(root: Path) -> dict[str, Any]:
    tracked = _git_lines(root, ["git", "ls-files"])
    if tracked is None:
        return {
            "files": [],
            "baseline_available": False,
            "warnings": ["git is unavailable; skipped changed-file scope check"],
        }
    if not tracked:
        return {
            "files": [],
            "baseline_available": False,
            "warnings": ["git has no tracked baseline; skipped changed-file scope check"],
        }

    status = _git_lines(
        root, ["git", "status", "--porcelain", "--untracked-files=all"]
    )
    if status is None:
        return {
            "files": [],
            "baseline_available": False,
            "warnings": ["git status failed; skipped changed-file scope check"],
        }

    files: list[str] = []
    for line in status:
        if not line.strip():
            continue
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if path.startswith("benchmark/results/"):
            continue
        files.append(path)

    return {
        "files": sorted(set(files)),
        "baseline_available": True,
        "warnings": [],
    }


def _git_lines(root: Path, command: list[str]) -> list[str] | None:
    try:
        result = subprocess.run(
            command,
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return [line for line in result.stdout.splitlines() if line.strip()]
