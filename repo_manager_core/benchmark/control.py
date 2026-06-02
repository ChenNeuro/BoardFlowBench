"""Signed external runner state for benchmark control-plane decisions."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import stat
import re
from pathlib import Path
from typing import Any

SENSITIVE_FIELDS = {"agent_command", "reviewer_command"}
SUPPORTED_CONDITIONS = {
    "no_board_baseline",
    "native_instructions",
    "native_docs_handoff",
    "full_boardflow",
}
SUPPORTED_STATUSES = {"awaiting_agent", "activating_task", "agent_failed", "complete"}
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
REQUIRED_FIELDS = {
    "run_id": str,
    "target": str,
    "condition": str,
    "workspace": str,
    "oracle_root": str,
    "seed_commit": str,
    "oracle_commit": str,
    "results_dir": str,
    "tasks": list,
    "current_task": str,
    "baseline_commit": str,
    "stages": list,
    "status": str,
}


def write_run_state(run_dir: str | Path, state: dict[str, Any]) -> Path:
    """Persist a signed state snapshot without executable adapter commands."""
    directory = Path(run_dir).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    snapshot = {key: value for key, value in state.items() if key not in SENSITIVE_FIELDS}
    snapshot["schema_version"] = 2
    _validate_shape(snapshot, directory)
    key = _load_or_create_key(Path(snapshot["results_dir"]))
    snapshot["state_signature"] = _signature(snapshot, key)
    destination = directory / "run.json"
    temporary = directory / "run.json.tmp"
    temporary.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(destination)
    return destination


def load_run_state(run_manifest: str | Path) -> dict[str, Any]:
    """Load a signed external run manifest and reject modified snapshots."""
    path = Path(run_manifest).resolve()
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise ValueError(f"run manifest is unreadable: {exc}") from exc
    if not isinstance(state, dict):
        raise ValueError("run manifest must contain an object")
    _validate_shape(state, path.parent)
    signature = state.get("state_signature")
    if not isinstance(signature, str) or not signature:
        raise ValueError("run manifest is unsigned")
    key = _load_existing_key(Path(state["results_dir"]))
    if not hmac.compare_digest(signature, _signature(state, key)):
        raise ValueError("run manifest signature is invalid")
    return state


def validate_stage_snapshot(declared: Any, evidence: Any) -> list[str]:
    """Return violations when external evidence differs from signed state."""
    if not isinstance(declared, dict):
        return ["signed run manifest is missing the stage snapshot"]
    if not isinstance(evidence, dict):
        return ["external stage evidence must contain an object"]
    return [] if declared == evidence else ["external stage evidence differs from signed run manifest"]


def find_stage_snapshot(state: dict[str, Any], task_id: str) -> dict[str, Any] | None:
    """Return one signed stage snapshot by task id."""
    for stage in state.get("stages", []):
        if isinstance(stage, dict) and stage.get("task_id") == task_id:
            return stage
    return None


def validate_external_placement(
    workspace: str | Path,
    oracle_root: str | Path,
    results_dir: str | Path,
) -> None:
    """Require trusted inputs and state directories to stay outside the workspace."""
    workspace_path = Path(workspace).resolve()
    for field, value in (("oracle_root", oracle_root), ("results_dir", results_dir)):
        candidate = Path(value).resolve()
        try:
            candidate.relative_to(workspace_path)
        except ValueError:
            continue
        raise ValueError(f"{field} must be outside the workspace")


def _validate_shape(state: dict[str, Any], run_dir: Path) -> None:
    for field, expected_type in REQUIRED_FIELDS.items():
        if not isinstance(state.get(field), expected_type):
            raise ValueError(f"run manifest is missing or invalid {field}")
    if any(field in state for field in SENSITIVE_FIELDS):
        raise ValueError("run manifest must not persist executable adapter commands")
    if Path(state["results_dir"]).resolve() != run_dir.parent.resolve():
        raise ValueError("run manifest results_dir does not match its external directory")
    if str(state["run_id"]) != run_dir.name:
        raise ValueError("run manifest run_id does not match its external directory")
    for field in ("workspace", "oracle_root", "results_dir"):
        if not Path(state[field]).is_absolute():
            raise ValueError(f"run manifest {field} must be an absolute path")
    if state["condition"] not in SUPPORTED_CONDITIONS:
        raise ValueError("run manifest condition is invalid")
    if state["status"] not in SUPPORTED_STATUSES:
        raise ValueError("run manifest status is invalid")
    if not SHA_PATTERN.fullmatch(state["oracle_commit"]):
        raise ValueError("run manifest oracle_commit must be a 40-character lowercase SHA")
    if not SHA_PATTERN.fullmatch(state["seed_commit"]):
        raise ValueError("run manifest seed_commit must be a 40-character lowercase SHA")
    if not SHA_PATTERN.fullmatch(state["baseline_commit"]):
        raise ValueError("run manifest baseline_commit must be a 40-character lowercase SHA")
    if not all(isinstance(task, str) and task for task in state["tasks"]):
        raise ValueError("run manifest tasks must contain task ids")
    if len(set(state["tasks"])) != len(state["tasks"]):
        raise ValueError("run manifest tasks must not contain duplicates")
    if state["current_task"] not in state["tasks"]:
        raise ValueError("run manifest current_task is not listed in tasks")
    stage_ids = []
    for stage in state["stages"]:
        if not isinstance(stage, dict) or not isinstance(stage.get("task_id"), str):
            raise ValueError("run manifest stages must contain task snapshots")
        stage_ids.append(stage["task_id"])
    if stage_ids != state["tasks"][: len(stage_ids)]:
        raise ValueError("run manifest stages must be an ordered task prefix")
    if state["status"] == "complete" and stage_ids != state["tasks"]:
        raise ValueError("complete run manifest must contain every task stage")
    pending_task = state.get("pending_task")
    if state["status"] == "activating_task":
        try:
            expected_pending = state["tasks"][state["tasks"].index(state["current_task"]) + 1]
        except (ValueError, IndexError) as exc:
            raise ValueError("activating run manifest does not have a next task") from exc
        if pending_task != expected_pending:
            raise ValueError("activating run manifest pending_task is invalid")
    elif pending_task is not None:
        raise ValueError("run manifest pending_task is only valid while activating a task")

    validate_external_placement(state["workspace"], state["oracle_root"], state["results_dir"])


def _load_or_create_key(results_dir: Path) -> bytes:
    results_dir.mkdir(parents=True, exist_ok=True)
    path = results_dir / ".boardflowbench.key"
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return _load_existing_key(results_dir)
    key = secrets.token_bytes(32)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(key)
    return key


def _load_existing_key(results_dir: Path) -> bytes:
    path = results_dir / ".boardflowbench.key"
    try:
        mode = stat.S_IMODE(path.stat().st_mode)
        key = path.read_bytes()
    except OSError as exc:
        raise ValueError(f"runner signing key is unavailable: {exc}") from exc
    if mode & 0o077:
        raise ValueError("runner signing key permissions must not allow group or other access")
    if len(key) < 32:
        raise ValueError("runner signing key is invalid")
    return key


def _signature(state: dict[str, Any], key: bytes) -> str:
    unsigned = {name: value for name, value in state.items() if name != "state_signature"}
    payload = json.dumps(unsigned, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hmac.new(key, payload, hashlib.sha256).hexdigest()
