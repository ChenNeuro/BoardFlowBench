"""Tests for external benchmark result aggregation."""
from __future__ import annotations

import json
import hashlib

import pytest

from repo_manager_core.benchmark.aggregation import aggregate_results
from repo_manager_core.benchmark.control import write_run_state

BASELINE = "1" * 40
ORACLE = "2" * 40
FINALIZED = "3" * 40
EVALUATED = "4" * 40
SEED = "5" * 40


def test_aggregate_external_run_results(tmp_path):
    run = tmp_path / "run-1"
    stage = run / "stages" / "B001"
    stage.mkdir(parents=True)
    score = {
        "task_id": "B001",
        "phase": "completion",
        "condition": "full_boardflow",
        "hard_gate_pass": True,
        "correctness": {"violations": [], "details": {"oracle": {"seed_commit": SEED, "oracle_pack_commit": ORACLE}}},
        "scope_control": {"violations": [], "details": {"baseline_commit": BASELINE}},
        "hygiene": {"violations": []},
        "handoff": {"violations": []},
        "board_consistency": {"violations": []},
    }
    score_path = stage / "score.json"
    score_path.write_text(json.dumps(score))
    evidence = {
        "task_id": "B001",
        "condition": "full_boardflow",
        "gate_pass": True,
        "baseline_commit": BASELINE,
        "evaluated_head": EVALUATED,
        "finalized_commit": FINALIZED,
        "seed_commit": SEED,
        "oracle_pack_commit": ORACLE,
        "score_file": str(score_path),
        "score_sha256": hashlib.sha256(score_path.read_bytes()).hexdigest(),
        "duration_seconds": 1.5,
        "reviewer": {"risk_count": 2},
    }
    (stage / "evidence.json").write_text(json.dumps(evidence))
    write_run_state(
        run,
        {
            "run_id": "run-1",
            "target": "expense_lite",
            "condition": "full_boardflow",
            "workspace": str((tmp_path / "workspace").resolve()),
            "oracle_root": str((tmp_path / "oracle").resolve()),
            "seed_commit": SEED,
            "oracle_commit": ORACLE,
            "results_dir": str(tmp_path.resolve()),
            "tasks": ["B001"],
            "current_task": "B001",
            "baseline_commit": BASELINE,
            "status": "complete",
            "stages": [evidence],
        },
    )
    result = aggregate_results(tmp_path)
    assert result["completed_run_count"] == 1
    assert result["task_pass_rate"] == 1
    assert result["regression_count"] == 0
    assert result["reviewer_risk_count"] == 2
    assert result["duration_seconds"] == 1.5
    assert result["by_condition"]["full_boardflow"]["task_pass_rate"] == 1


def test_aggregate_rejects_unsigned_completed_run(tmp_path):
    run = tmp_path / "run-1"
    run.mkdir()
    (run / "run.json").write_text(json.dumps({"run_id": "run-1", "status": "complete"}))
    result = aggregate_results(tmp_path)
    assert result["run_count"] == 0
    assert result["invalid_run_count"] == 1
    assert result["completed_run_count"] == 0


def test_aggregate_rejects_external_evidence_changed_after_signing(tmp_path):
    run = tmp_path / "run-1"
    stage = run / "stages" / "B001"
    stage.mkdir(parents=True)
    score_path = stage / "score.json"
    score_path.write_text(
        json.dumps(
            {
                "task_id": "B001",
                "phase": "completion",
                "condition": "full_boardflow",
                "hard_gate_pass": True,
                "correctness": {"details": {"oracle": {"seed_commit": SEED, "oracle_pack_commit": ORACLE}}},
                "scope_control": {"details": {"baseline_commit": BASELINE}},
            }
        )
    )
    evidence = {
        "task_id": "B001",
        "condition": "full_boardflow",
        "gate_pass": True,
        "baseline_commit": BASELINE,
        "evaluated_head": EVALUATED,
        "finalized_commit": FINALIZED,
        "seed_commit": SEED,
        "oracle_pack_commit": ORACLE,
        "score_file": str(score_path),
        "score_sha256": hashlib.sha256(score_path.read_bytes()).hexdigest(),
    }
    evidence_path = stage / "evidence.json"
    evidence_path.write_text(json.dumps(evidence))
    write_run_state(
        run,
        {
            "run_id": "run-1",
            "target": "expense_lite",
            "condition": "full_boardflow",
            "workspace": str((tmp_path / "workspace").resolve()),
            "oracle_root": str((tmp_path / "oracle").resolve()),
            "seed_commit": SEED,
            "oracle_commit": ORACLE,
            "results_dir": str(tmp_path.resolve()),
            "tasks": ["B001"],
            "current_task": "B001",
            "baseline_commit": BASELINE,
            "status": "complete",
            "stages": [evidence],
        },
    )
    evidence["duration_seconds"] = 99
    evidence_path.write_text(json.dumps(evidence))

    result = aggregate_results(tmp_path)

    assert result["accepted_stage_count"] == 0
    assert result["invalid_stage_count"] == 1
    assert "external stage evidence differs from signed run manifest" in result["stage_violations"][0]["violations"]


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("condition", "native_instructions", "evidence condition differs"),
        ("seed_commit", "6" * 40, "evidence seed differs"),
        ("oracle_pack_commit", "7" * 40, "evidence oracle differs"),
    ],
)
def test_aggregate_rejects_evidence_that_contradicts_signed_run(tmp_path, field, value, message):
    _write_completed_run(tmp_path, evidence_overrides={field: value})

    result = aggregate_results(tmp_path)

    assert result["accepted_stage_count"] == 0
    assert any(message in item for item in result["stage_violations"][0]["violations"])


def test_aggregate_rejects_passing_score_with_violations(tmp_path):
    _write_completed_run(tmp_path, score_overrides={"violations": ["contradictory failure"]})

    result = aggregate_results(tmp_path)

    assert result["accepted_stage_count"] == 0
    assert any("contains violations despite passing" in item for item in result["stage_violations"][0]["violations"])


def _write_completed_run(tmp_path, *, evidence_overrides=None, score_overrides=None):
    run = tmp_path / "run-1"
    stage = run / "stages" / "B001"
    stage.mkdir(parents=True)
    evidence_values = {
        "condition": "full_boardflow",
        "seed_commit": SEED,
        "oracle_pack_commit": ORACLE,
        **(evidence_overrides or {}),
    }
    score = {
        "task_id": "B001",
        "phase": "completion",
        "condition": evidence_values["condition"],
        "hard_gate_pass": True,
        "violations": [],
        "correctness": {"details": {"oracle": {"seed_commit": evidence_values["seed_commit"], "oracle_pack_commit": evidence_values["oracle_pack_commit"]}}},
        "scope_control": {"details": {"baseline_commit": BASELINE}},
        **(score_overrides or {}),
    }
    score_path = stage / "score.json"
    score_path.write_text(json.dumps(score))
    evidence = {
        "task_id": "B001",
        "gate_pass": True,
        "baseline_commit": BASELINE,
        "evaluated_head": EVALUATED,
        "finalized_commit": FINALIZED,
        "score_file": str(score_path),
        "score_sha256": hashlib.sha256(score_path.read_bytes()).hexdigest(),
        **evidence_values,
    }
    (stage / "evidence.json").write_text(json.dumps(evidence))
    write_run_state(
        run,
        {
            "run_id": "run-1",
            "target": "expense_lite",
            "condition": "full_boardflow",
            "workspace": str((tmp_path / "workspace").resolve()),
            "oracle_root": str((tmp_path / "oracle").resolve()),
            "seed_commit": SEED,
            "oracle_commit": ORACLE,
            "results_dir": str(tmp_path.resolve()),
            "tasks": ["B001"],
            "current_task": "B001",
            "baseline_commit": BASELINE,
            "status": "complete",
            "stages": [evidence],
        },
    )
