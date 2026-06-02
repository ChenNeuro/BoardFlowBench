"""Tests for signed external benchmark control state."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from repo_manager_core.benchmark.control import load_run_state, write_run_state

BASELINE = "1" * 40
ORACLE = "2" * 40


def _state(tmp_path):
    return {
        "run_id": "run-1",
        "target": "expense_lite",
        "condition": "full_boardflow",
        "workspace": str((tmp_path / "workspace").resolve()),
        "oracle_root": str((tmp_path / "oracle").resolve()),
        "seed_commit": "3" * 40,
        "oracle_commit": ORACLE,
        "results_dir": str((tmp_path / "results").resolve()),
        "tasks": ["B001"],
        "current_task": "B001",
        "baseline_commit": BASELINE,
        "stages": [],
        "status": "awaiting_agent",
        "agent_command": "dangerous-agent --token secret",
        "reviewer_command": "reviewer",
    }


def test_signed_run_state_excludes_executable_commands(tmp_path):
    manifest = write_run_state(tmp_path / "results" / "run-1", _state(tmp_path))
    stored = json.loads(manifest.read_text())
    assert "agent_command" not in stored
    assert "reviewer_command" not in stored
    assert load_run_state(manifest)["current_task"] == "B001"


def test_modified_signed_run_state_is_rejected(tmp_path):
    manifest = write_run_state(tmp_path / "results" / "run-1", _state(tmp_path))
    stored = json.loads(manifest.read_text())
    stored["baseline_commit"] = "9" * 40
    manifest.write_text(json.dumps(stored))
    with pytest.raises(ValueError, match="signature is invalid"):
        load_run_state(manifest)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("condition", "unknown", "condition is invalid"),
        ("status", "DONE", "status is invalid"),
        ("oracle_commit", "moving-tag", "oracle_commit must be"),
        ("seed_commit", "moving-tag", "seed_commit must be"),
        ("baseline_commit", "short", "baseline_commit must be"),
    ],
)
def test_run_state_rejects_invalid_control_fields(tmp_path, field, value, message):
    state = _state(tmp_path)
    state[field] = value
    with pytest.raises(ValueError, match=message):
        write_run_state(tmp_path / "results" / "run-1", state)


@pytest.mark.parametrize("field", ["oracle_root", "results_dir"])
def test_run_state_rejects_control_plane_paths_inside_workspace(tmp_path, field):
    state = _state(tmp_path)
    state[field] = str((tmp_path / "workspace" / field).resolve())
    run_dir = Path(state["results_dir"]) / "run-1"
    with pytest.raises(ValueError, match=f"{field} must be outside the workspace"):
        write_run_state(run_dir, state)
