"""Scope-control checks — prevents agents from modifying files outside allowed paths."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ._git_utils import git_lines


CONTROL_PLANE_PATHS = (
    ".board/evidence/",
    ".board/run.yaml",
    ".repo_manager/agent_context.md",
    ".repo_manager/repo_style_profile.json",
)


def check_scope(
    repo: str | Path,
    task: dict[str, Any],
    *,
    baseline: str | None = None,
) -> dict[str, Any]:
    """Score scope control out of 15."""
    root = Path(repo)
    changed = _changed_files(root, baseline=baseline)
    warnings: list[str] = []
    violations: list[str] = []
    details: dict[str, Any] = {
        "baseline_available": changed["baseline_available"],
        "baseline_commit": baseline,
        "changed_files": changed["files"],
    }
    warnings.extend(changed["warnings"])

    allowed_paths = [str(path) for path in task.get("allowed_paths", [])]
    forbidden_paths = [str(path) for path in task.get("forbidden_paths", [])]

    score = 0

    if not changed["baseline_available"]:
        if baseline:
            violations.extend(warnings or [f"git baseline is unavailable: {baseline}"])
            return {
                "score": 0,
                "max": 15,
                "applicable": True,
                "violations": violations,
                "warnings": warnings,
                "details": details,
            }
        return {
            "score": 0,
            "max": 0,
            "applicable": False,
            "violations": [],
            "warnings": warnings,
            "details": details,
        }
    else:
        # Scope checks are based on observable git state, not agent claims.
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
    details["outside_allowed_paths"] = outside_allowed
    details["forbidden_paths_modified"] = forbidden_modified
    details["unrelated_docs_or_formatting"] = unrelated_docs

    if outside_allowed:
        violations.append("changed files outside allowed_paths: " + ", ".join(outside_allowed))
    else:
        score += 8

    if forbidden_modified:
        violations.append("forbidden_paths modified: " + ", ".join(forbidden_modified))
    else:
        score += 4

    if unrelated_docs:
        violations.append("unrelated docs or formatting churn detected: " + ", ".join(unrelated_docs))
    else:
        score += 3

    return {
        "score": score,
        "max": 15,
        "applicable": True,
        "violations": violations,
        "warnings": warnings,
        "details": details,
    }


def _matches_any(path: str, patterns: list[str]) -> bool:
    return any(_matches_path(path, pattern) for pattern in patterns)


def _matches_path(path: str, pattern: str) -> bool:
    normalized = pattern.rstrip("/")
    if pattern.endswith("/"):
        # Directory patterns apply to everything below that directory.
        return path == normalized or path.startswith(normalized + "/")
    return path == normalized


def _changed_files(root: Path, *, baseline: str | None = None) -> dict[str, Any]:
    tracked = git_lines(root, ["git", "ls-files"])
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

    committed: list[str] = []
    if baseline:
        committed_result = git_lines(root, ["git", "diff", "--name-only", f"{baseline}..HEAD"])
        if committed_result is None:
            return {
                "files": [],
                "baseline_available": False,
                "warnings": [f"git baseline is unavailable: {baseline}"],
            }
        committed = committed_result

    status = git_lines(root, ["git", "status", "--porcelain", "--untracked-files=all"])
    if status is None:
        return {
            "files": [],
            "baseline_available": False,
            "warnings": ["git status failed; skipped changed-file scope check"],
        }

    files: list[str] = list(committed)
    for line in status:
        if not line.strip():
            continue
        path = line[3:]
        if " -> " in path:
            # For renames, score the destination path as the changed file.
            path = path.split(" -> ", 1)[1]
        files.append(path)

    return {
        "files": sorted(
            path
            for path in set(files)
            if not any(path == prefix.rstrip("/") or (prefix.endswith("/") and path.startswith(prefix)) for prefix in CONTROL_PLANE_PATHS)
        ),
        "baseline_available": True,
        "warnings": [],
    }
