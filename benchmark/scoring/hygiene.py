"""Repository hygiene checks for BoardFlowBench."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


FORBIDDEN_ROOT_NAMES = {
    "result.txt",
    "output.txt",
    "final.md",
    "tmp.py",
    "debug.py",
}

CACHE_NAMES = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".DS_Store",
}


def check_hygiene(repo: str | Path) -> dict[str, Any]:
    """Score repository hygiene out of 20."""
    root = Path(repo)
    score = 0
    violations: list[str] = []
    warnings: list[str] = []
    details: dict[str, Any] = {}

    forbidden_root = [
        path.name
        for path in root.iterdir()
        if path.is_file() and _is_forbidden_root_name(path.name)
    ]
    details["forbidden_root_files"] = forbidden_root
    if forbidden_root:
        violations.append(f"forbidden root files found: {', '.join(forbidden_root)}")
    else:
        score += 6

    artifact_issues = _artifact_issues(root)
    details["artifact_issues"] = artifact_issues
    if artifact_issues:
        violations.extend(artifact_issues)
    else:
        score += 5

    scratch_entries = _scratch_entries(root)
    details["scratch_entries"] = scratch_entries
    if scratch_entries:
        violations.append(
            "demo_repo_template/.scratch contains files not justified by scorer"
        )
    else:
        score += 4

    cache_files = _cache_files(root)
    details["cache_files"] = cache_files
    if cache_files:
        violations.append(f"cache or temp files found: {', '.join(cache_files)}")
    else:
        score += 3

    untracked = _unexpected_untracked(root)
    details["unexpected_untracked_files"] = untracked["files"]
    warnings.extend(untracked["warnings"])
    if untracked["files"]:
        violations.append(
            "unexpected untracked files found: " + ", ".join(untracked["files"])
        )
    else:
        score += 2

    return {
        "score": score,
        "max": 20,
        "violations": violations,
        "warnings": warnings,
        "details": details,
    }


def _is_forbidden_root_name(name: str) -> bool:
    lower = name.lower()
    return lower in FORBIDDEN_ROOT_NAMES or lower.startswith(("tmp.", "debug."))


def _artifact_issues(root: Path) -> list[str]:
    artifact_dir = root / "demo_repo_template" / "artifacts"
    if not artifact_dir.exists():
        return []

    issues: list[str] = []
    for path in artifact_dir.iterdir():
        if path.name == ".gitkeep":
            continue
        if path.is_dir():
            issues.append(f"artifact directory is not expected: {path}")
        elif path.suffix != ".md":
            issues.append(f"artifact should be a Markdown file: {path}")
        elif _is_forbidden_root_name(path.name):
            issues.append(f"artifact has generic temporary name: {path}")
    return issues


def _scratch_entries(root: Path) -> list[str]:
    scratch = root / "demo_repo_template" / ".scratch"
    if not scratch.exists():
        return []
    return [
        str(path.relative_to(root))
        for path in scratch.iterdir()
        if path.name != ".gitkeep"
    ]


def _cache_files(root: Path) -> list[str]:
    matches: list[str] = []
    for path in root.rglob("*"):
        if ".git" in path.parts:
            continue
        if path.name in CACHE_NAMES or path.suffix in {".pyc", ".pyo"}:
            matches.append(str(path.relative_to(root)))
    return sorted(matches)


def _unexpected_untracked(root: Path) -> dict[str, Any]:
    tracked = _git_lines(root, ["git", "ls-files"])
    if tracked is None:
        return {
            "files": [],
            "warnings": ["git is unavailable; skipped unexpected untracked check"],
        }
    if not tracked:
        return {
            "files": [],
            "warnings": [
                "git has no tracked baseline; skipped unexpected untracked check"
            ],
        }

    status = _git_lines(
        root, ["git", "status", "--porcelain", "--untracked-files=all"]
    )
    if status is None:
        return {
            "files": [],
            "warnings": ["git status failed; skipped unexpected untracked check"],
        }

    files = []
    for line in status:
        if not line.startswith("?? "):
            continue
        path = line[3:]
        if path.startswith("benchmark/results/"):
            continue
        files.append(path)

    return {"files": sorted(files), "warnings": []}


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
