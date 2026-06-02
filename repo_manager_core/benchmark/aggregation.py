"""Aggregate external BoardFlowBench run manifests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def aggregate_results(results_dir: str | Path) -> dict[str, Any]:
    """Aggregate observable stage evidence without modifying source repositories."""
    root = Path(results_dir)
    runs = []
    for path in sorted(root.glob("*/run.json")):
        runs.append(json.loads(path.read_text(encoding="utf-8")))
    stages = [stage for run in runs for stage in run.get("stages", [])]
    scores = []
    scores_by_run: dict[str, list[dict[str, Any]]] = {}
    for run in runs:
        for stage in run.get("stages", []):
            path = root / run["run_id"] / "stages" / stage["task_id"] / "score.json"
            if path.exists():
                score = json.loads(path.read_text(encoding="utf-8"))
                scores.append(score)
                scores_by_run.setdefault(str(run["run_id"]), []).append(score)
    conditions = sorted({str(run.get("condition")) for run in runs if run.get("condition")})
    return {
        "schema_version": 1,
        "run_count": len(runs),
        "stage_count": len(stages),
        "completed_run_count": sum(run.get("status") == "complete" for run in runs),
        "task_pass_rate": round(sum(stage.get("gate_pass") is True for stage in stages) / len(stages), 4) if stages else 0,
        "scope_drift_count": _count_violations(scores, "scope_control"),
        "hygiene_violation_count": _count_violations(scores, "hygiene"),
        "handoff_violation_count": _count_violations(scores, "handoff"),
        "board_consistency_violation_count": _count_violations(scores, "board_consistency"),
        "regression_count": _count_matching_violations(scores, "correctness", "regression"),
        "reviewer_risk_count": sum(stage.get("reviewer", {}).get("risk_count", 0) for stage in stages),
        "duration_seconds": round(sum(stage.get("duration_seconds", 0) for stage in stages), 3),
        "by_condition": {
            condition: _summarize_runs(
                [run for run in runs if run.get("condition") == condition],
                scores_by_run,
            )
            for condition in conditions
        },
        "runs": [
            {
                "run_id": run.get("run_id"),
                "target": run.get("target"),
                "condition": run.get("condition"),
                "agent_profile": run.get("agent_profile"),
                "status": run.get("status"),
            }
            for run in runs
        ],
    }


def _count_violations(scores: list[dict[str, Any]], section: str) -> int:
    return sum(len(score.get(section, {}).get("violations", [])) for score in scores)


def _count_matching_violations(scores: list[dict[str, Any]], section: str, needle: str) -> int:
    return sum(
        needle in str(violation).lower()
        for score in scores
        for violation in score.get(section, {}).get("violations", [])
    )


def _summarize_runs(runs: list[dict[str, Any]], scores_by_run: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    stages = [stage for run in runs for stage in run.get("stages", [])]
    scores = [score for run in runs for score in scores_by_run.get(str(run.get("run_id")), [])]
    return {
        "run_count": len(runs),
        "completed_run_count": sum(run.get("status") == "complete" for run in runs),
        "stage_count": len(stages),
        "task_pass_rate": round(sum(stage.get("gate_pass") is True for stage in stages) / len(stages), 4) if stages else 0,
        "regression_count": _count_matching_violations(scores, "correctness", "regression"),
        "scope_drift_count": _count_violations(scores, "scope_control"),
        "hygiene_violation_count": _count_violations(scores, "hygiene"),
        "handoff_violation_count": _count_violations(scores, "handoff"),
        "board_consistency_violation_count": _count_violations(scores, "board_consistency"),
        "reviewer_risk_count": sum(stage.get("reviewer", {}).get("risk_count", 0) for stage in stages),
        "duration_seconds": round(sum(stage.get("duration_seconds", 0) for stage in stages), 3),
    }
