"""Shared git utility extracted to eliminate duplication between hygiene and scope checks."""

from __future__ import annotations

import subprocess
from pathlib import Path


def git_lines(root: Path, command: list[str]) -> list[str] | None:
    """Run a git command and return stripped stdout lines, or None on failure."""
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
