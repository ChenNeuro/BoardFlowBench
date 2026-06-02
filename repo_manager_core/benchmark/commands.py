"""Structured command execution for observable benchmark checks."""

from __future__ import annotations

import os
import re
import shlex
import subprocess
from pathlib import Path
from typing import Any


def run_commands(
    repo: str | Path,
    commands: list[Any],
    *,
    variables: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Run shell-free argv commands and return stable observable results."""
    return [run_command(repo, command, variables=variables) for command in commands]


def run_command(
    repo: str | Path,
    command: Any,
    *,
    variables: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Run one string-compatible or structured command without shell=True."""
    argv, command_env = normalize_command(command, variables=variables)
    env = os.environ.copy()
    env.update(command_env)
    result = subprocess.run(
        argv,
        cwd=Path(repo),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return {
        "argv": argv,
        "returncode": result.returncode,
        "stdout_tail": _tail(result.stdout),
        "stderr_tail": _tail(result.stderr),
    }


def normalize_command(
    command: Any,
    *,
    variables: dict[str, str] | None = None,
) -> tuple[list[str], dict[str, str]]:
    """Normalize legacy command strings and structured argv mappings."""
    values = variables or {}
    if isinstance(command, str):
        parts = [_format(part, values) for part in shlex.split(command)]
        env: dict[str, str] = {}
        while parts and "=" in parts[0] and not parts[0].startswith("="):
            key, value = parts[0].split("=", 1)
            if not key.replace("_", "").isalnum():
                break
            env[key] = value
            parts.pop(0)
        if not parts:
            raise ValueError("command must include an executable")
        return parts, env
    if not isinstance(command, dict) or not isinstance(command.get("argv"), list):
        raise ValueError("command must be a string or an object with argv")
    argv = [_format(str(part), values) for part in command["argv"]]
    env = {
        str(key): _format(str(value), values)
        for key, value in (command.get("env") or {}).items()
    }
    if not argv:
        raise ValueError("command argv must not be empty")
    return argv, env


def _format(value: str, variables: dict[str, str]) -> str:
    for key, replacement in variables.items():
        value = value.replace("{" + key + "}", replacement)
    if re.search(r"\{[A-Za-z_][A-Za-z0-9_]*\}", value):
        raise ValueError(f"command contains an unresolved placeholder: {value}")
    return value


def _tail(text: str, limit: int = 4000) -> str:
    return text[-limit:]
