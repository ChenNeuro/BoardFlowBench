"""Integration tests for start and end Agent Bridge refresh."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from repo_manager_core.board.board_io import load_board, save_board

from .conftest import REPO_ROOT

SCRIPT = REPO_ROOT / "skills" / "agent-bridge" / "scripts" / "bridge_refresh.py"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def _workspace(tmp_path: Path, *, active_other=False) -> Path:
    root = tmp_path / "workspace"
    root.mkdir()
    (root / ".board" / "handoffs").mkdir(parents=True)
    (root / "pkg").mkdir()
    (root / "tests").mkdir()
    (root / "pkg" / "module.py").write_text("def parse_value(value):\n    return value\n", encoding="utf-8")
    (root / "tests" / "test_module.py").write_text(
        "def test_parse_value():\n    assert True\n",
        encoding="utf-8",
    )
    tasks = [
        {
            "id": "P001",
            "title": "Existing task",
            "status": "IN_PROGRESS" if active_other else "DONE",
            "owner": "agent-a",
            "dependencies": [],
            "notes": "Existing note.",
        },
        {
            "id": "P002",
            "title": "Bridge lifecycle refresh",
            "status": "TODO",
            "owner": "unassigned",
            "dependencies": [],
            "notes": "Refresh note.",
        },
    ]
    save_board(
        {
            "schema_version": 1,
            "project": "Test",
            "current_milestone": {
                "id": "M1",
                "title": "Test milestone",
                "status": "IN_PROGRESS",
                "goal": "Keep long-term tasks visible.",
            },
            "tasks": tasks,
        },
        root,
    )
    (root / "PROJECT_BOARD.md").write_text(
        "# Project Board\n\n"
        "## Current Milestone\n\n"
        "Milestone: M1 - Test milestone\n\n"
        "Goal: Keep long-term tasks visible.\n\n"
        "Status: IN_PROGRESS\n\n"
        "## Task Board\n\n"
        "| Task | Title | Status | Owner | Dependencies | Notes |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        f"| P001 | Existing task | {'IN_PROGRESS' if active_other else 'DONE'} | agent-a | none | Existing note. |\n"
        "| P002 | Bridge lifecycle refresh | TODO | unassigned | none | Refresh note. |\n",
        encoding="utf-8",
    )
    _git(root, "init")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "Test")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "baseline")
    return root


def _refresh(root: Path, phase: str, *extra: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--phase",
            phase,
            "--agent-id",
            "codex",
            "--task-id",
            "P002",
            "--repo",
            str(root),
            *extra,
        ],
        env=env,
        capture_output=True,
        text=True,
    )


def test_start_refresh_blocks_dirty_workspace_and_records_context(tmp_path):
    root = _workspace(tmp_path)
    (root / "pkg" / "module.py").write_text("def parse_value(value):\n    return value.strip()\n", encoding="utf-8")

    result = _refresh(root, "start")

    context = (root / ".repo_manager" / "agent_context.md").read_text(encoding="utf-8")
    assert result.returncode == 1
    assert "git workspace has staged, unstaged, or untracked files" in result.stdout
    assert "## Current Milestone" in context
    assert "## Long-Term Backlog" in context
    assert "## Git Status" in context
    assert "## Test Style Summary" in context


def test_start_refresh_override_reason_is_preserved_verbatim(tmp_path):
    root = _workspace(tmp_path)
    (root / "pkg" / "module.py").write_text("def parse_value(value):\n    return value.strip()\n", encoding="utf-8")
    reason = "保留现有改动，不覆盖。"

    result = _refresh(root, "start", "--override-reason", reason)

    context = (root / ".repo_manager" / "agent_context.md").read_text(encoding="utf-8")
    assert result.returncode == 0
    assert f"- Override reason: {reason}" in context


def test_start_refresh_blocks_other_active_sticker(tmp_path):
    root = _workspace(tmp_path, active_other=True)

    result = _refresh(root, "start")

    assert result.returncode == 1
    assert "P001 remains IN_PROGRESS" in result.stdout


def test_end_refresh_does_not_change_task_status(tmp_path):
    root = _workspace(tmp_path)

    result = _refresh(root, "end")

    assert result.returncode == 0
    assert load_board(root)["tasks"][1]["status"] == "TODO"


def test_refresh_stops_when_taskboard_views_disagree(tmp_path):
    root = _workspace(tmp_path)
    path = root / "PROJECT_BOARD.md"
    path.write_text(path.read_text(encoding="utf-8").replace("| P002 | Bridge lifecycle refresh | TODO |", "| P002 | Bridge lifecycle refresh | BLOCKED |"), encoding="utf-8")

    result = _refresh(root, "end")

    assert result.returncode == 1
    assert "taskboard views are inconsistent" in result.stdout


def test_start_refresh_accepts_completed_dependency_evidence_mirror(tmp_path):
    root = _workspace(tmp_path)
    board = load_board(root)
    board["tasks"][0]["require_gate_evidence"] = True
    board["tasks"][0]["acceptance_evidence"] = ".board/evidence/P001.json"
    board["tasks"][0]["current_handoff"] = ".board/handoffs/P001_test.json"
    board["tasks"][1]["dependencies"] = ["P001"]
    save_board(board, root)
    project_board = root / "PROJECT_BOARD.md"
    project_board.write_text(
        project_board.read_text(encoding="utf-8").replace(
            "| P002 | Bridge lifecycle refresh | TODO | unassigned | none |",
            "| P002 | Bridge lifecycle refresh | TODO | unassigned | P001 |",
        ),
        encoding="utf-8",
    )
    (root / ".board" / "evidence").mkdir()
    (root / ".board" / "evidence" / "P001.json").write_text(
        json.dumps(
            {
                "kind": "workspace_mirror",
                "task_id": "P001",
                "condition": "full_boardflow",
                "gate_pass": True,
                "baseline_commit": "1" * 40,
                "evaluated_head": "2" * 40,
                "seed_commit": "3" * 40,
                "oracle_pack_commit": "4" * 40,
            }
        ),
        encoding="utf-8",
    )
    (root / ".board" / "handoff.schema.json").write_text(
        (REPO_ROOT / ".board" / "handoff.schema.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (root / ".board" / "handoffs" / "P001_test.json").write_text(
        json.dumps(
            {
                "task_id": "P001",
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
    _git(root, "add", ".")
    _git(root, "commit", "-m", "accepted dependency mirror")

    result = _refresh(root, "start")

    assert result.returncode == 0
