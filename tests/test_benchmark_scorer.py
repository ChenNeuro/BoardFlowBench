"""Mutation fixtures for condition-aware benchmark scoring."""
from __future__ import annotations

import subprocess

from repo_manager_core.board.scope_check import check_scope
from repo_manager_core.benchmark.workspace import initialize_workspace
from tools.benchmark_scorer import score_task

from .test_benchmark_workspace import _fixture


def _git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()


def test_scope_uses_committed_diff_from_sticker_baseline(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "config", "user.email", "test@example.com")
    (repo / "allowed.py").write_text("x = 1\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "baseline")
    baseline = _git(repo, "rev-parse", "HEAD")
    (repo / "outside.py").write_text("x = 2\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "outside")

    result = check_scope(repo, {"allowed_paths": ["allowed.py"]}, baseline=baseline)

    assert "outside.py" in result["details"]["outside_allowed_paths"]
    assert result["score"] < result["max"]


def test_scope_without_git_baseline_is_not_evaluated(tmp_path):
    result = check_scope(tmp_path, {"allowed_paths": []})
    assert result["max"] == 0
    assert result["applicable"] is False


def test_no_board_score_does_not_require_board_files(tmp_path):
    project, source = _fixture(tmp_path)
    task = project / "benchmark" / "tasks" / "expense_lite" / "b001_date_parser.yaml"
    result = score_task(source, task, condition="no_board_baseline", baseline=_git(source, "rev-parse", "HEAD"))
    assert result["handoff"]["applicable"] is False
    assert result["board_consistency"]["applicable"] is False


def test_full_boardflow_completion_rejects_todo_sticker(tmp_path):
    project, source = _fixture(tmp_path)
    workspace = tmp_path / "run"
    initialized = initialize_workspace(
        project,
        "expense_lite",
        "full_boardflow",
        "B001",
        workspace,
        source_repo=source,
    )
    task = project / "benchmark" / "tasks" / "expense_lite" / "b001_date_parser.yaml"

    result = score_task(workspace, task, condition="full_boardflow", baseline=initialized["baseline_commit"])

    assert "B001 remains TODO during completion scoring" in result["board_consistency"]["violations"]
