"""Aggregate signed external BoardFlowBench run manifests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from repo_manager_core.benchmark.control import load_run_state, validate_stage_snapshot
from repo_manager_core.board.evidence import validate_acceptance_evidence


def aggregate_results(results_dir: str | Path) -> dict[str, Any]:
    """Aggregate only signed runs with complete trusted stage evidence."""
    root = Path(results_dir).resolve()
    runs: list[dict[str, Any]] = []
    invalid_runs: list[dict[str, Any]] = []
    for path in sorted(root.glob("*/run.json")):
        try:
            runs.append(load_run_state(path))
        except ValueError as exc:
            invalid_runs.append({"run_manifest": str(path), "violation": str(exc)})

    stage_reports: list[dict[str, Any]] = []
    scores: list[dict[str, Any]] = []
    scores_by_run: dict[str, list[dict[str, Any]]] = {}
    stages_by_run: dict[str, list[dict[str, Any]]] = {}
    for run in runs:
        run_id = str(run["run_id"])
        run_dir = root / run_id
        for declared in run.get("stages", []):
            task_id = str(declared.get("task_id", ""))
            evidence_path = run_dir / "stages" / task_id / "evidence.json"
            violations = validate_acceptance_evidence(
                run["workspace"],
                {"id": task_id},
                evidence_path,
                trusted_results_root=run_dir,
            )
            try:
                evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                evidence = None
            violations.extend(validate_stage_snapshot(declared, evidence))
            if isinstance(evidence, dict):
                if evidence.get("condition") != run["condition"]:
                    violations.append(f"{task_id} evidence condition differs from signed run manifest")
                if evidence.get("seed_commit") != run["seed_commit"]:
                    violations.append(f"{task_id} evidence seed differs from signed run manifest")
                if evidence.get("oracle_pack_commit") != run["oracle_commit"]:
                    violations.append(f"{task_id} evidence oracle differs from signed run manifest")
            report = {
                "run_id": run_id,
                "task_id": task_id,
                "accepted": not violations,
                "violations": violations,
            }
            stage_reports.append(report)
            if violations:
                continue
            assert isinstance(evidence, dict)
            score = json.loads(Path(evidence["score_file"]).read_text(encoding="utf-8"))
            stages_by_run.setdefault(run_id, []).append(evidence)
            scores_by_run.setdefault(run_id, []).append(score)
            scores.append(score)

    conditions = sorted({str(run.get("condition")) for run in runs if run.get("condition")})
    accepted_stages = [stage for stage in stage_reports if stage["accepted"]]
    completed = [run for run in runs if _run_complete(run, stages_by_run)]
    return {
        "schema_version": 2,
        "run_count": len(runs),
        "invalid_run_count": len(invalid_runs),
        "invalid_runs": invalid_runs,
        "stage_count": len(stage_reports),
        "accepted_stage_count": len(accepted_stages),
        "invalid_stage_count": len(stage_reports) - len(accepted_stages),
        "stage_violations": [stage for stage in stage_reports if not stage["accepted"]],
        "completed_run_count": len(completed),
        "task_pass_rate": round(len(accepted_stages) / len(stage_reports), 4) if stage_reports else 0,
        "scope_drift_count": _count_violations(scores, "scope_control"),
        "hygiene_violation_count": _count_violations(scores, "hygiene"),
        "handoff_violation_count": _count_violations(scores, "handoff"),
        "board_consistency_violation_count": _count_violations(scores, "board_consistency"),
        "regression_count": _count_matching_violations(scores, "correctness", "regression"),
        "reviewer_risk_count": sum(stage.get("reviewer", {}).get("risk_count", 0) for stages in stages_by_run.values() for stage in stages),
        "duration_seconds": round(sum(stage.get("duration_seconds", 0) for stages in stages_by_run.values() for stage in stages), 3),
        "by_condition": {
            condition: _summarize_runs(
                [run for run in runs if run.get("condition") == condition],
                scores_by_run,
                stages_by_run,
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
                "accepted": _run_complete(run, stages_by_run),
            }
            for run in runs
        ],
    }


def _run_complete(run: dict[str, Any], stages_by_run: dict[str, list[dict[str, Any]]]) -> bool:
    accepted = stages_by_run.get(str(run.get("run_id")), [])
    return run.get("status") == "complete" and [stage.get("task_id") for stage in accepted] == run.get("tasks")


def _count_violations(scores: list[dict[str, Any]], section: str) -> int:
    return sum(len(score.get(section, {}).get("violations", [])) for score in scores)


def _count_matching_violations(scores: list[dict[str, Any]], section: str, needle: str) -> int:
    return sum(
        needle in str(violation).lower()
        for score in scores
        for violation in score.get(section, {}).get("violations", [])
    )


def _summarize_runs(
    runs: list[dict[str, Any]],
    scores_by_run: dict[str, list[dict[str, Any]]],
    stages_by_run: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    stages = [stage for run in runs for stage in stages_by_run.get(str(run.get("run_id")), [])]
    declared_count = sum(len(run.get("stages", [])) for run in runs)
    scores = [score for run in runs for score in scores_by_run.get(str(run.get("run_id")), [])]
    return {
        "run_count": len(runs),
        "completed_run_count": sum(_run_complete(run, stages_by_run) for run in runs),
        "stage_count": declared_count,
        "accepted_stage_count": len(stages),
        "task_pass_rate": round(len(stages) / declared_count, 4) if declared_count else 0,
        "regression_count": _count_matching_violations(scores, "correctness", "regression"),
        "scope_drift_count": _count_violations(scores, "scope_control"),
        "hygiene_violation_count": _count_violations(scores, "hygiene"),
        "handoff_violation_count": _count_violations(scores, "handoff"),
        "board_consistency_violation_count": _count_violations(scores, "board_consistency"),
        "reviewer_risk_count": sum(stage.get("reviewer", {}).get("risk_count", 0) for stage in stages),
        "duration_seconds": round(sum(stage.get("duration_seconds", 0) for stage in stages), 3),
    }
