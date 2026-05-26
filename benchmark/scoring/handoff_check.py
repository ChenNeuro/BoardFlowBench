"""Structured handoff checks for BoardFlowBench."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = [
    "task_id",
    "agent_id",
    "agent_role",
    "status",
    "files_changed",
    "commands_run",
    "tests",
    "temporary_files_created",
    "temporary_files_removed",
    "decisions",
    "risks",
    "next_recommended_step",
]


def check_handoff(
    repo: str | Path, task: dict[str, Any], changed_files: list[str] | None = None
) -> dict[str, Any]:
    """Score structured handoff quality out of 15."""
    root = Path(repo)
    task_id = str(task.get("task_id") or task.get("id"))
    required = _handoff_required(task)
    handoffs = _load_handoffs(root, task_id)
    warnings: list[str] = []
    violations: list[str] = []
    details: dict[str, Any] = {
        "handoff_required": required,
        "handoff_files": [item["path"] for item in handoffs],
    }

    score = 0

    if handoffs:
        score += 3
        handoff = handoffs[-1]["data"]
    elif required:
        violations.append(f"handoff required for {task_id} but none was found")
        handoff = None
    else:
        score += 3
        warnings.append("handoff is not required for this task")
        handoff = None

    if handoff is None:
        return {
            "score": score,
            "max": 15,
            "violations": violations,
            "warnings": warnings,
            "details": details,
        }

    missing = [field for field in REQUIRED_FIELDS if not _field_complete(handoff, field)]
    details["missing_or_empty_required_fields"] = missing
    if missing:
        violations.append("handoff missing required fields: " + ", ".join(missing))
    else:
        score += 4

    changed_files = changed_files or []
    if changed_files and not handoff.get("files_changed"):
        violations.append("files_changed is empty but repository changes were detected")
    else:
        score += 2

    if isinstance(handoff.get("commands_run"), list) and isinstance(
        handoff.get("tests"), list
    ):
        score += 3
    else:
        violations.append("commands_run and tests fields must both be arrays")

    if handoff.get("risks") is not None and handoff.get("next_recommended_step"):
        score += 3
    else:
        violations.append("risks and next_recommended_step must be present")

    return {
        "score": score,
        "max": 15,
        "violations": violations,
        "warnings": warnings,
        "details": details,
    }


def _handoff_required(task: dict[str, Any]) -> bool:
    value = task.get("handoff_requirement")
    if isinstance(value, dict):
        return bool(value.get("required"))
    return bool(task.get("handoff_required", False))


def _load_handoffs(root: Path, task_id: str) -> list[dict[str, Any]]:
    handoff_dir = root / ".board" / "handoffs"
    if not handoff_dir.exists():
        return []

    matches: list[dict[str, Any]] = []
    for path in sorted(handoff_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if data.get("task_id") == task_id:
            matches.append({"path": str(path.relative_to(root)), "data": data})
    return matches


def _field_complete(handoff: dict[str, Any], field: str) -> bool:
    if field not in handoff:
        return False
    value = handoff[field]
    if isinstance(value, str):
        return bool(value.strip())
    return value is not None
