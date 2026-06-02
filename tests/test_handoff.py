"""Tests for handoff writing and validation."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from repo_manager_core.board.handoff_writer import check_handoff, write_handoff, write_validated_handoff

from .conftest import REPO_ROOT


def test_check_handoff_finds_p001_handoffs():
    """P001 has a handoff file from the completed project task."""
    task = {"task_id": "P001", "handoff_required": True}
    result = check_handoff(REPO_ROOT, task)
    assert result["score"] >= 3  # at least "handoff exists" points
    assert len(result["details"]["handoff_files"]) >= 1


def test_write_and_check_handoff_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / ".board" / "handoffs").mkdir(parents=True)

        path = write_handoff(
            repo=root,
            task_id="P001",
            agent_id="test-agent",
            agent_role="tester",
            status="READY_FOR_REVIEW",
            files_changed=["src/module.py"],
            commands_run=[{"command": "pytest", "result": "PASS", "notes": "passed"}],
            tests=[{"name": "pytest", "result": "PASS", "notes": "passed"}],
            risks="No known risks",
            next_recommended_step="Run tests and review",
        )
        assert path.exists()

        task = {"task_id": "P001", "handoff_required": True}
        result = check_handoff(root, task)
        assert result["score"] >= 3


def test_write_handoff_rejects_empty_validation_records(tmp_path):
    with pytest.raises(ValueError, match="commands_run must include at least one PASS"):
        write_handoff(
            repo=tmp_path,
            task_id="P001",
            agent_id="test-agent",
            agent_role="tester",
            status="READY_FOR_REVIEW",
            risks="No known risks",
            next_recommended_step="Run tests and review",
        )


def test_check_handoff_reports_non_object_json_as_malformed(tmp_path):
    handoff_dir = tmp_path / ".board" / "handoffs"
    handoff_dir.mkdir(parents=True)
    (handoff_dir / "P001_test_1.json").write_text("[]\n", encoding="utf-8")

    result = check_handoff(tmp_path, {"task_id": "P001", "handoff_required": True})

    assert result["details"]["malformed_handoff_files"] == [".board/handoffs/P001_test_1.json"]


def test_check_handoff_orders_latest_record_by_timestamp_not_agent_id(tmp_path):
    handoff_dir = tmp_path / ".board" / "handoffs"
    handoff_dir.mkdir(parents=True)
    handoff = {
        "task_id": "P001",
        "agent_id": "z-agent",
        "agent_role": "tester",
        "status": "READY_FOR_REVIEW",
        "files_changed": [],
        "commands_run": [{"command": "pytest", "result": "PASS", "notes": "passed"}],
        "tests": [{"name": "pytest", "result": "PASS", "notes": "passed"}],
        "temporary_files_created": [],
        "temporary_files_removed": [],
        "decisions": [],
        "risks": [],
        "next_recommended_step": "Continue.",
    }
    (handoff_dir / "P001_z-agent_1.json").write_text(json.dumps(handoff), encoding="utf-8")
    handoff["agent_id"] = "a-agent"
    (handoff_dir / "P001_a-agent_2.json").write_text(json.dumps(handoff), encoding="utf-8")

    result = check_handoff(tmp_path, {"task_id": "P001", "handoff_required": True})

    assert result["details"]["handoff_files"][-1] == ".board/handoffs/P001_a-agent_2.json"


def test_write_validated_handoff_rejects_non_object_json(tmp_path):
    with pytest.raises(ValueError, match="handoff JSON must contain an object"):
        write_validated_handoff(tmp_path, [], REPO_ROOT / ".board" / "handoff.schema.json")
