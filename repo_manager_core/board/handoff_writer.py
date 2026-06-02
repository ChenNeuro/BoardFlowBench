"""Structured handoff writing and validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from repo_manager_core.board.schema_validation import validate_json_schema
from repo_manager_core.board.task_status import VALID_STATUSES

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
    tid = str(task.get("task_id") or task.get("id"))
    required = _handoff_required(task)
    handoffs = _load_handoffs(root, tid)
    warnings: list[str] = []
    violations: list[str] = []
    details: dict[str, Any] = {
        "handoff_required": required,
        "handoff_files": [item["path"] for item in handoffs],
    }

    score = 0

    if handoffs:
        # Use the latest matching handoff as the active transition record.
        score += 3
        handoff = handoffs[-1]["data"]
    elif required:
        violations.append(f"handoff required for {tid} but none was found")
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

    schema_path = _schema_path(root, task)
    schema_violations = validate_handoff_schema(handoff, schema_path)
    details["schema_violations"] = schema_violations
    if schema_violations:
        violations.append("handoff schema violations: " + "; ".join(schema_violations))
    else:
        score += 4

    missing = [field for field in REQUIRED_FIELDS if not _field_complete(handoff, field)]
    details["missing_or_empty_required_fields"] = missing
    if missing:
        violations.append("handoff missing required fields: " + ", ".join(missing))
    else:
        score += 2

    changed_files = changed_files or []
    if changed_files and not handoff.get("files_changed"):
        # If git observed changes, the handoff should tell the next agent where
        # to look first.
        violations.append("files_changed is empty but repository changes were detected")
    else:
        score += 1

    if isinstance(handoff.get("commands_run"), list) and isinstance(
        handoff.get("tests"), list
    ):
        score += 2
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


def write_handoff(
    repo: str | Path,
    task_id: str,
    agent_id: str,
    agent_role: str,
    status: str,
    files_changed: list[str] | None = None,
    commands_run: list[dict[str, str]] | None = None,
    tests: list[dict[str, str]] | None = None,
    temporary_files_created: list[str] | None = None,
    temporary_files_removed: list[str] | None = None,
    decisions: list[str] | None = None,
    risks: list[str] | str | None = None,
    next_recommended_step: str | None = None,
) -> Path:
    """Create a structured handoff JSON file under .board/handoffs/."""
    if status not in VALID_STATUSES:
        raise ValueError(f"invalid status '{status}', must be one of {VALID_STATUSES}")

    root = Path(repo)
    handoff_dir = root / ".board" / "handoffs"
    handoff_dir.mkdir(parents=True, exist_ok=True)

    data: dict[str, Any] = {
        "task_id": task_id,
        "agent_id": agent_id,
        "agent_role": agent_role,
        "status": status,
        "files_changed": files_changed or [],
        "commands_run": commands_run or [],
        "tests": tests or [],
        "temporary_files_created": temporary_files_created or [],
        "temporary_files_removed": temporary_files_removed or [],
        "decisions": decisions or [],
        "risks": _normalize_risks(risks),
        "next_recommended_step": next_recommended_step,
    }

    # Generate unique filename: <task_id>_<agent_id>_<timestamp>.json
    import time
    ts = time.time_ns()
    path = handoff_dir / f"{task_id}_{agent_id}_{ts}.json"
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_validated_handoff(
    repo: str | Path,
    handoff_data: dict[str, Any],
    schema_path: str | Path,
) -> Path:
    """Write a caller-supplied handoff only after full schema validation."""
    root = Path(repo)
    violations = validate_handoff_schema(handoff_data, schema_path)
    if violations:
        raise ValueError("handoff schema violations: " + "; ".join(violations))
    handoff_dir = root / ".board" / "handoffs"
    handoff_dir.mkdir(parents=True, exist_ok=True)
    import time
    path = handoff_dir / f"{handoff_data['task_id']}_{handoff_data['agent_id']}_{time.time_ns()}.json"
    path.write_text(json.dumps(handoff_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def validate_handoff_schema(handoff_data: dict[str, Any], schema_path: str | Path) -> list[str]:
    """Validate handoff data against the repository-local JSON Schema."""
    schema_path = Path(schema_path)
    if not schema_path.exists():
        return ["schema not found"]

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    return validate_json_schema(handoff_data, schema)


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
    for p in sorted(handoff_dir.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            # Ignore malformed handoffs rather than breaking the whole score.
            continue
        if data.get("task_id") == task_id:
            matches.append({"path": str(p.relative_to(root)), "data": data})
    return matches


def _field_complete(handoff: dict[str, Any], field: str) -> bool:
    if field not in handoff:
        return False
    value = handoff[field]
    if isinstance(value, str):
        return bool(value.strip())
    return value is not None


def _schema_path(root: Path, task: dict[str, Any]) -> Path:
    requirement = task.get("handoff_requirement")
    if isinstance(requirement, dict) and requirement.get("schema"):
        return root / str(requirement["schema"])
    return root / ".board" / "handoff.schema.json"


def _normalize_risks(value: list[str] | str | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return list(value)
