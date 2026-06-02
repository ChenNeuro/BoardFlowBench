"""Acceptance evidence validation for completed BoardFlow stickers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def validate_acceptance_evidence(
    repo: str | Path,
    task: dict[str, Any],
    evidence_path: str | Path | None = None,
) -> list[str]:
    """Return violations for a task's deterministic finalize evidence."""
    root = Path(repo)
    tid = str(task.get("task_id") or task.get("id") or "")
    configured = evidence_path or task.get("acceptance_evidence")
    if not configured:
        return [f"{tid} has no acceptance evidence"]
    path = Path(configured)
    if not path.is_absolute():
        path = root / path
    if not path.exists():
        return [f"{tid} acceptance evidence does not exist: {configured}"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return [f"{tid} acceptance evidence is unreadable: {exc}"]
    if not isinstance(data, dict):
        return [f"{tid} acceptance evidence must be an object"]

    violations = []
    if data.get("task_id") != tid:
        violations.append(f"{tid} acceptance evidence task_id differs")
    if data.get("gate_pass") is not True:
        violations.append(f"{tid} acceptance evidence gate_pass is not true")
    for field in ("condition", "baseline_commit", "evaluated_head", "seed_commit", "oracle_pack_commit", "score_file"):
        if not isinstance(data.get(field), str) or not data[field]:
            violations.append(f"{tid} acceptance evidence is missing {field}")
    score_file = data.get("score_file")
    if isinstance(score_file, str) and score_file:
        score_path = Path(score_file)
        if not score_path.is_absolute():
            score_path = root / score_path
        try:
            score_path.resolve().relative_to(root.resolve())
        except ValueError:
            pass
        else:
            violations.append(f"{tid} acceptance score must be stored outside the workspace")
        violations.extend(_validate_score_file(score_path, tid, data))
    return violations


def has_valid_acceptance_evidence(repo: str | Path, task: dict[str, Any]) -> bool:
    """Return whether deterministic acceptance evidence exists and passes."""
    return not validate_acceptance_evidence(repo, task)


def _validate_score_file(path: Path, task_id: str, evidence: dict[str, Any]) -> list[str]:
    if not path.exists():
        return [f"{task_id} acceptance score does not exist: {path}"]
    try:
        score = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return [f"{task_id} acceptance score is unreadable: {exc}"]
    if not isinstance(score, dict):
        return [f"{task_id} acceptance score must be an object"]

    violations = []
    if score.get("task_id") != task_id:
        violations.append(f"{task_id} acceptance score task_id differs")
    if score.get("phase") != "completion":
        violations.append(f"{task_id} acceptance score phase is not completion")
    if score.get("hard_gate_pass") is not True:
        violations.append(f"{task_id} acceptance score hard_gate_pass is not true")
    if score.get("condition") != evidence.get("condition"):
        violations.append(f"{task_id} acceptance score condition differs")
    scope = score.get("scope_control")
    baseline = scope.get("details", {}).get("baseline_commit") if isinstance(scope, dict) else None
    if baseline != evidence.get("baseline_commit"):
        violations.append(f"{task_id} acceptance score baseline differs")
    correctness = score.get("correctness")
    oracle = correctness.get("details", {}).get("oracle") if isinstance(correctness, dict) else None
    if not isinstance(oracle, dict):
        violations.append(f"{task_id} acceptance score is missing oracle details")
    else:
        if oracle.get("seed_commit") != evidence.get("seed_commit"):
            violations.append(f"{task_id} acceptance score seed_commit differs")
        if oracle.get("oracle_pack_commit") != evidence.get("oracle_pack_commit"):
            violations.append(f"{task_id} acceptance score oracle_pack_commit differs")
    return violations
