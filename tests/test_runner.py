"""Tests for scenario-runner lifecycle orchestration."""
from __future__ import annotations

import json
import subprocess

import pytest
from repo_manager_core.benchmark import runner
from repo_manager_core.benchmark.control import write_run_state

from .test_benchmark_workspace import _fixture


def _passing_seed(*args, **kwargs):
    return {"hard_gate_pass": True, "task_id": "B001"}


def test_manual_runner_calls_refresh_around_full_boardflow_stickers(tmp_path, monkeypatch):
    project, source = _fixture(tmp_path)
    calls = []
    monkeypatch.setattr(runner, "score_task", _passing_seed)
    monkeypatch.setattr(runner, "_run_refresh", lambda project, state, phase: calls.append((phase, state["current_task"])))

    state = runner.start_run(
        project,
        target="expense_lite",
        condition="full_boardflow",
        workspace=tmp_path / "run",
        oracle_root=tmp_path / "oracles",
        results_dir=tmp_path / "results",
        source_repo=source,
    )
    manifest = next((tmp_path / "results").glob("*/run.json"))
    monkeypatch.setattr(
        runner,
        "finalize_task",
        lambda *args, **kwargs: {"task_id": "B001", "gate_pass": True},
    )
    monkeypatch.setattr(
        runner,
        "activate_task",
        lambda *args, **kwargs: {"task_id": "B002", "baseline_commit": "6" * 40},
    )
    monkeypatch.setattr(runner, "_assert_finalized_workspace", lambda *args, **kwargs: None)

    state = runner.resume_run(project, manifest)

    assert calls == [("start", "B001"), ("end", "B001"), ("start", "B002")]
    assert state["current_task"] == "B002"
    assert state["status"] == "awaiting_agent"


def test_reviewer_adapter_records_non_blocking_risks(tmp_path):
    run_dir = tmp_path / "results" / "run"
    report = runner._run_reviewer(
        run_dir,
        {
            "workspace": str(tmp_path),
            "reviewer_command": "python3 -c 'import json, os; print(json.dumps({\"risks\": [\"inspect edge case\"], \"cwd\": os.getcwd()}))'",
        },
        {"task_id": "B001"},
    )

    stored = json.loads((run_dir / "stages" / "B001" / "reviewer-report.json").read_text())
    assert report["blocking"] is False
    assert report["risk_count"] == 1
    assert stored["risks"] == ["inspect edge case"]
    assert stored["cwd"] == str(tmp_path)


def test_reviewer_adapter_does_not_inherit_unrelated_secrets(tmp_path, monkeypatch):
    monkeypatch.setenv("BOARD_FLOW_TEST_SECRET", "must-not-leak")
    run_dir = tmp_path / "results" / "run"
    runner._run_reviewer(
        run_dir,
        {
            "workspace": str(tmp_path),
            "reviewer_command": "python3 -c 'import json, os; print(json.dumps({\"risks\": [], \"secret\": os.getenv(\"BOARD_FLOW_TEST_SECRET\")}))'",
        },
        {"task_id": "B001"},
    )
    stored = json.loads((run_dir / "stages" / "B001" / "reviewer-report.json").read_text())
    assert stored["secret"] is None


def test_reviewer_adapter_does_not_persist_literal_arguments(tmp_path):
    run_dir = tmp_path / "results" / "run"
    runner._run_reviewer(
        run_dir,
        {
            "workspace": str(tmp_path),
            "reviewer_command": "python3 -c 'import json; print(json.dumps({\"risks\": []}))' --token must-not-persist",
        },
        {"task_id": "B001"},
    )

    stored = (run_dir / "stages" / "B001" / "reviewer-report.json").read_text()

    assert "must-not-persist" not in stored
    assert '"executable": "python3"' in stored


@pytest.mark.parametrize("mutation", ["dirty", "commit"])
def test_post_reviewer_guard_rejects_workspace_mutation(tmp_path, mutation):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _git(workspace, "init", "-b", "main")
    _git(workspace, "config", "user.name", "Test")
    _git(workspace, "config", "user.email", "test@example.com")
    (workspace / "tracked.txt").write_text("baseline\n")
    _git(workspace, "add", ".")
    _git(workspace, "commit", "-m", "baseline")
    finalized = _git(workspace, "rev-parse", "HEAD")
    (workspace / "tracked.txt").write_text("reviewer mutation\n")
    if mutation == "commit":
        _git(workspace, "add", ".")
        _git(workspace, "commit", "-m", "reviewer commit")

    with pytest.raises(ValueError, match="reviewer modified|workspace HEAD changed"):
        runner._assert_finalized_workspace(
            {"workspace": str(workspace)},
            {"finalized_commit": finalized},
        )


@pytest.mark.parametrize("relative_path", [".boardflowbench.key", "run-1/stages/B001/score.json"])
def test_post_reviewer_guard_rejects_trusted_control_mutation(tmp_path, relative_path):
    results = tmp_path / "results"
    run_dir = results / "run-1"
    (run_dir / "stages" / "B001").mkdir(parents=True)
    (results / ".boardflowbench.key").write_text("k" * 32, encoding="utf-8")
    (run_dir / "run.json").write_text("{}\n", encoding="utf-8")
    (run_dir / "stages" / "B001" / "score.json").write_text("{}\n", encoding="utf-8")
    expected = runner._trusted_control_snapshot(run_dir)

    (results / relative_path).write_text("mutated\n", encoding="utf-8")

    with pytest.raises(ValueError, match="reviewer modified trusted control-plane"):
        runner._assert_trusted_control_unchanged(run_dir, expected)


def test_final_stage_still_checks_reviewer_workspace_guard(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "finalize_task", lambda *args, **kwargs: {"task_id": "B001", "gate_pass": True})
    monkeypatch.setattr(runner, "_run_reviewer", lambda *args, **kwargs: {"risk_count": 0, "blocking": False})
    monkeypatch.setattr(runner, "_assert_finalized_workspace", lambda *args, **kwargs: (_ for _ in ()).throw(ValueError("reviewer modified the workspace")))
    state = {
        "condition": "no_board_baseline",
        "current_task": "B001",
        "workspace": str(tmp_path / "workspace"),
        "oracle_root": str(tmp_path / "oracle"),
        "results_dir": str(tmp_path / "results"),
        "target": "expense_lite",
        "run_id": "run-1",
        "baseline_commit": "1" * 40,
        "agent_profile": "codex",
        "tasks": ["B001"],
        "stages": [],
    }

    with pytest.raises(ValueError, match="reviewer modified the workspace"):
        runner._finalize_and_continue(tmp_path, tmp_path / "results" / "run-1", state)


def test_resume_rejects_complete_signed_run(tmp_path):
    run_dir = tmp_path / "results" / "run-1"
    manifest = write_run_state(
        run_dir,
        {
            "run_id": "run-1",
            "target": "expense_lite",
            "condition": "full_boardflow",
            "workspace": str((tmp_path / "workspace").resolve()),
            "oracle_root": str((tmp_path / "oracle").resolve()),
            "seed_commit": "3" * 40,
            "oracle_commit": "1" * 40,
            "results_dir": str((tmp_path / "results").resolve()),
            "tasks": ["B001"],
            "current_task": "B001",
            "baseline_commit": "2" * 40,
            "stages": [{"task_id": "B001"}],
            "status": "complete",
        },
    )

    with pytest.raises(ValueError, match="cannot resume from status complete"):
        runner.resume_run(tmp_path, manifest)


def _git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()
