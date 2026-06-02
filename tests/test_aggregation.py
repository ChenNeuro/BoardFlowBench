"""Tests for external benchmark result aggregation."""
from __future__ import annotations

import json

from repo_manager_core.benchmark.aggregation import aggregate_results


def test_aggregate_external_run_results(tmp_path):
    run = tmp_path / "run-1"
    stage = run / "stages" / "B001"
    stage.mkdir(parents=True)
    (run / "run.json").write_text(json.dumps({"run_id": "run-1", "condition": "full_boardflow", "status": "complete", "stages": [{"task_id": "B001", "gate_pass": True, "duration_seconds": 1.5, "reviewer": {"risk_count": 2}}]}))
    (stage / "score.json").write_text(json.dumps({"correctness": {"violations": ["regression command failed"]}, "scope_control": {"violations": []}, "hygiene": {"violations": []}, "handoff": {"violations": []}, "board_consistency": {"violations": []}}))
    result = aggregate_results(tmp_path)
    assert result["completed_run_count"] == 1
    assert result["task_pass_rate"] == 1
    assert result["regression_count"] == 1
    assert result["reviewer_risk_count"] == 2
    assert result["duration_seconds"] == 1.5
    assert result["by_condition"]["full_boardflow"]["task_pass_rate"] == 1
