"""Read-only git workspace inspection for Agent Bridge refresh."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


def inspect_git_state(repo: str | Path) -> dict[str, Any]:
    """Return branch and changed-file groups without modifying the repository."""
    root = Path(repo)
    branch = _git_output(root, ["git", "rev-parse", "--abbrev-ref", "HEAD"])
    status = _git_output(root, ["git", "status", "--porcelain", "--untracked-files=all"])
    if branch is None or status is None:
        return {
            "available": False,
            "branch": "",
            "staged_files": [],
            "unstaged_files": [],
            "untracked_files": [],
            "clean": False,
        }

    staged: set[str] = set()
    unstaged: set[str] = set()
    untracked: set[str] = set()
    for line in status.splitlines():
        if len(line) < 3:
            continue
        code = line[:2]
        path = _destination_path(line[3:])
        if code == "??":
            untracked.add(path)
            continue
        if code[0] != " ":
            staged.add(path)
        if code[1] != " ":
            unstaged.add(path)

    return {
        "available": True,
        "branch": branch.strip(),
        "staged_files": sorted(staged),
        "unstaged_files": sorted(unstaged),
        "untracked_files": sorted(untracked),
        "clean": not (staged or unstaged or untracked),
    }


def _git_output(root: Path, command: list[str]) -> str | None:
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
    return result.stdout if result.returncode == 0 else None


def _destination_path(path: str) -> str:
    return path.split(" -> ", 1)[-1]
