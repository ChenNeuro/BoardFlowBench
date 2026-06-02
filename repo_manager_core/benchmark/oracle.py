"""Load and execute private oracle packs outside agent workspaces."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from repo_manager_core.benchmark.commands import run_commands


def run_oracle(
    oracle_root: str | Path,
    target: str,
    task_id: str,
    workspace: str | Path,
    *,
    phase: str = "completion",
    expected_seed_commit: str | None = None,
    expected_oracle_commit: str | None = None,
) -> dict[str, Any]:
    """Run an isolated oracle pack without copying it into the workspace."""
    root = Path(oracle_root).resolve()
    manifest = load_oracle_manifest(root, target)
    seed_commit = str(manifest.get("seed_commit", ""))
    seed_matches_target = not expected_seed_commit or seed_commit == expected_seed_commit
    pack_commit = oracle_pack_commit(root)
    commit_matches_target = bool(expected_oracle_commit) and pack_commit == expected_oracle_commit
    clean = oracle_pack_clean(root)
    variables = {
        "oracle_root": str(root),
        "workspace": str(Path(workspace).resolve()),
    }
    results: list[dict[str, Any]] = []
    if seed_matches_target and commit_matches_target and clean:
        if phase == "seed":
            commands = manifest.get("seed_commands") or []
        else:
            tasks = manifest.get("tasks") or {}
            config = tasks.get(task_id) if isinstance(tasks, dict) else None
            commands = config.get("commands", []) if isinstance(config, dict) else []
        results = _redact_results(run_commands(workspace, commands, variables=variables), variables)
    return {
        "oracle_pack_commit": pack_commit,
        "oracle_commit_matches_target": commit_matches_target,
        "oracle_pack_clean": clean,
        "seed_commit": seed_commit,
        "seed_matches_target": seed_matches_target,
        "task_id": task_id,
        "phase": phase,
        "commands": results,
        "passed": commit_matches_target and clean and seed_matches_target and bool(results) and all(item["returncode"] == 0 for item in results),
    }


def load_oracle_manifest(oracle_root: str | Path, target: str) -> dict[str, Any]:
    """Load a target oracle manifest from an external pack."""
    path = Path(oracle_root) / "targets" / f"{target}.json"
    if not path.exists():
        raise ValueError(f"oracle manifest not found: {path}")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError(f"oracle manifest must contain a mapping: {path}")
    return manifest


def oracle_pack_commit(oracle_root: str | Path) -> str:
    """Return the oracle repository commit, or an explicit unversioned marker."""
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=Path(oracle_root),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "unversioned"


def oracle_pack_clean(oracle_root: str | Path) -> bool:
    """Return whether the private oracle checkout has no local mutations."""
    result = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=Path(oracle_root),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result.returncode == 0 and not result.stdout.strip()


def _redact_results(results: list[dict[str, Any]], variables: dict[str, str]) -> list[dict[str, Any]]:
    """Keep observable command results while hiding private filesystem roots."""
    redacted = []
    for item in results:
        copy = dict(item)
        copy["argv"] = [_redact(str(part), variables) for part in item.get("argv", [])]
        copy["stdout_tail"] = _redact(str(item.get("stdout_tail", "")), variables)
        copy["stderr_tail"] = _redact(str(item.get("stderr_tail", "")), variables)
        redacted.append(copy)
    return redacted


def _redact(value: str, variables: dict[str, str]) -> str:
    for name, replacement in variables.items():
        value = value.replace(replacement, "{" + name + "}")
    return value
