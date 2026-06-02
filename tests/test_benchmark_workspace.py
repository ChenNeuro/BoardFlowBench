"""Tests for isolated standalone demo benchmark workspaces."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from repo_manager_core.benchmark.workspace import activate_task, initialize_workspace
from repo_manager_core.board.board_io import load_board, save_board
from repo_manager_core.board.board_sync import update_task_status


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _fixture(tmp_path: Path) -> tuple[Path, Path]:
    project = tmp_path / "boardflow"
    source = tmp_path / "demo-source"
    project.mkdir()
    source.mkdir()

    _git(source, "init", "-b", "main")
    _git(source, "config", "user.name", "Test")
    _git(source, "config", "user.email", "test@example.com")
    _write(source / "src" / "expense_lite" / "parser.py", "def normalize_date(value):\n    return value\n")
    _write(source / "tests" / "test_parser.py", "def test_seed():\n    assert True\n")
    _git(source, "add", ".")
    _git(source, "commit", "-m", "seed")
    seed = _git(source, "rev-parse", "HEAD")
    _git(source, "tag", "benchmark-seed-v1")

    _write(
        project / "benchmark" / "targets" / "expense_lite.yaml",
        "schema_version: 1\n"
        "id: expense_lite\n"
        "title: Expense Lite Bench Demo\n"
        "repo_url: https://example.invalid/demo.git\n"
        f"seed_commit: {seed}\n"
        "task_directory: benchmark/tasks/expense_lite\n",
    )
    _write(
        project / "benchmark" / "tasks" / "expense_lite" / "b001_date_parser.yaml",
        "task_id: B001\n"
        "title: Date parser\n"
        "description: Assigned parser task.\n"
        "dependencies: []\n"
        "allowed_paths:\n"
        "  - src/expense_lite/parser.py\n",
    )
    _write(
        project / "benchmark" / "tasks" / "expense_lite" / "b002_csv_import.yaml",
        "task_id: B002\n"
        "title: CSV import\n"
        "description: Future CSV details must stay hidden.\n"
        "dependencies:\n"
        "  - B001\n"
        "allowed_paths:\n"
        "  - src/expense_lite/parser.py\n",
    )
    _write(project / "benchmark" / "templates" / "boardflow" / "AGENTS.md", "# Demo agents\n")
    _write(project / "benchmark" / "templates" / "boardflow" / "AI_CONTRACT.md", "# Demo contract\n")
    _write(
        project / ".board" / "handoff.schema.json",
        '{"type":"object","properties":{"task_id":{"pattern":"^[A-Z][0-9]{3}$"}}}\n',
    )
    return project, source


def test_boardflow_init_clones_seed_and_exposes_only_assigned_task(tmp_path):
    project, source = _fixture(tmp_path)
    workspace = tmp_path / "run"

    result = initialize_workspace(
        project,
        "expense_lite",
        "boardflow_sequential",
        "B001",
        workspace,
        source_repo=source,
    )

    board = load_board(workspace)
    assigned = (workspace / ".board" / "assigned_task.yaml").read_text(encoding="utf-8")
    assert [task["id"] for task in board["tasks"]] == ["B001", "B002"]
    assert "P001" not in (workspace / "PROJECT_BOARD.md").read_text(encoding="utf-8")
    assert "Assigned parser task." in assigned
    assert "Future CSV details" not in assigned
    assert result["baseline_commit"] != result["seed_commit"]
    assert _git(workspace, "status", "--porcelain") == ""


def test_no_board_init_keeps_workspace_free_of_boardflow_files(tmp_path):
    project, source = _fixture(tmp_path)
    workspace = tmp_path / "run"

    result = initialize_workspace(
        project,
        "expense_lite",
        "no_board_baseline",
        "B001",
        workspace,
        source_repo=source,
    )

    assert not (workspace / ".board").exists()
    assert not (workspace / "PROJECT_BOARD.md").exists()
    assert not (workspace / "AGENTS.md").exists()
    assert result["task_spec"].endswith("b001_date_parser.yaml")
    assert _git(workspace, "status", "--porcelain") == ""


def test_init_refuses_to_overwrite_existing_workspace(tmp_path):
    project, source = _fixture(tmp_path)
    workspace = tmp_path / "run"
    workspace.mkdir()

    with pytest.raises(ValueError, match="workspace already exists"):
        initialize_workspace(
            project,
            "expense_lite",
            "boardflow_sequential",
            "B001",
            workspace,
            source_repo=source,
        )


def test_activate_task_requires_done_dependencies_and_commits_new_baseline(tmp_path):
    project, source = _fixture(tmp_path)
    workspace = tmp_path / "run"
    initialize_workspace(
        project,
        "expense_lite",
        "boardflow_sequential",
        "B001",
        workspace,
        source_repo=source,
    )

    with pytest.raises(ValueError, match="task dependencies are not DONE: B001"):
        activate_task(project, workspace, "B002")

    handoff = workspace / ".board" / "handoffs" / "B001_test.json"
    handoff.write_text("{}\n", encoding="utf-8")
    board = load_board(workspace)
    board["tasks"][0]["current_handoff"] = ".board/handoffs/B001_test.json"
    save_board(board, workspace)
    update_task_status(workspace, "B001", "DONE", owner="tester")

    result = activate_task(project, workspace, "B002")

    assigned = (workspace / ".board" / "assigned_task.yaml").read_text(encoding="utf-8")
    assert "Future CSV details must stay hidden." in assigned
    assert result["task_id"] == "B002"
    assert _git(workspace, "status", "--porcelain") == ""
