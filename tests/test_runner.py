"""Tests for scenario-runner lifecycle orchestration."""
from __future__ import annotations

import json

from repo_manager_core.benchmark import runner

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
        lambda *args, **kwargs: {"task_id": "B002", "baseline_commit": "next-baseline"},
    )

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
