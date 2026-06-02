"""Tests for synchronized human and machine taskboard updates."""
from __future__ import annotations

import json
import pytest

from repo_manager_core.board.board_io import load_board, save_board
from repo_manager_core.board.board_sync import check_board_views, update_task_status
from .conftest import REPO_ROOT


def _write_board(repo, *, status="TODO", owner="unassigned", notes="Human note stays exact.", evidence=None):
    task = {
        "id": "P002",
        "title": "Bridge lifecycle refresh",
        "status": status,
        "owner": owner,
        "dependencies": [],
        "notes": notes,
    }
    if evidence:
        task["acceptance_evidence"] = evidence
    save_board(
        {
            "schema_version": 1,
            "project": "Test",
            "current_milestone": {
                "id": "M1",
                "title": "Test milestone",
                "status": "IN_PROGRESS",
                "goal": "Test sync.",
            },
            "tasks": [task],
        },
        repo,
    )
    schema = repo / ".board" / "handoff.schema.json"
    schema.write_text((REPO_ROOT / ".board" / "handoff.schema.json").read_text(encoding="utf-8"), encoding="utf-8")
    if evidence:
        path = repo / evidence
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "task_id": "P002",
                    "agent_id": "test",
                    "agent_role": "tester",
                    "status": "DONE",
                    "files_changed": [],
                    "commands_run": [{"command": "pytest", "result": "PASS", "notes": "passed"}],
                    "tests": [{"name": "pytest", "result": "PASS", "notes": "passed"}],
                    "temporary_files_created": [],
                    "temporary_files_removed": [],
                    "decisions": [],
                    "risks": [],
                    "next_recommended_step": "Continue.",
                }
            ),
            encoding="utf-8",
        )
    (repo / "PROJECT_BOARD.md").write_text(
        "# Project Board\n\n"
        "## Current Milestone\n\n"
        "Milestone: M1 - Test milestone\n\n"
        "Goal: Test sync.\n\n"
        "Status: IN_PROGRESS\n\n"
        "## Task Board\n\n"
        "| Task | Title | Status | Owner | Dependencies | Notes |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        f"| P002 | Bridge lifecycle refresh | {status} | {owner} | none | {notes} |\n",
        encoding="utf-8",
    )


def test_update_task_status_updates_both_views_and_preserves_notes(tmp_path):
    _write_board(tmp_path, notes="人写的 note stays exact.")

    update_task_status(tmp_path, "P002", "IN_PROGRESS", owner="codex")

    board = load_board(tmp_path)
    markdown = (tmp_path / "PROJECT_BOARD.md").read_text(encoding="utf-8")
    assert board["tasks"][0]["status"] == "IN_PROGRESS"
    assert board["tasks"][0]["owner"] == "codex"
    assert board["tasks"][0]["notes"] == "人写的 note stays exact."
    assert "| P002 | Bridge lifecycle refresh | IN_PROGRESS | codex | none | 人写的 note stays exact. |" in markdown
    assert check_board_views(tmp_path) == []


def test_update_task_status_stops_when_views_disagree(tmp_path):
    _write_board(tmp_path)
    path = tmp_path / "PROJECT_BOARD.md"
    path.write_text(path.read_text(encoding="utf-8").replace("| TODO |", "| BLOCKED |"), encoding="utf-8")

    with pytest.raises(ValueError, match="taskboard views are inconsistent"):
        update_task_status(tmp_path, "P002", "IN_PROGRESS", owner="codex")


def test_done_requires_handoff_or_acceptance_evidence(tmp_path):
    _write_board(tmp_path)

    with pytest.raises(ValueError, match="cannot be marked DONE"):
        update_task_status(tmp_path, "P002", "DONE", owner="codex")


def test_done_accepts_existing_evidence_field(tmp_path):
    _write_board(tmp_path, evidence=".board/handoffs/P002_test.json")

    update_task_status(tmp_path, "P002", "DONE", owner="codex")

    assert load_board(tmp_path)["tasks"][0]["status"] == "DONE"
