"""Board consistency checks for the BoardFlow protocol."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .board_io import load_board
from .board_sync import check_board_views
from .evidence import validate_acceptance_evidence
from .task_status import VALID_STATUSES


def check_board_consistency(repo: str | Path, task: dict[str, Any]) -> dict[str, Any]:
    """Score machine-readable board consistency out of 10."""
    board = load_board(repo)
    tid = str(task.get("task_id") or task.get("id"))
    board_task = _find_task(board, tid)
    warnings: list[str] = []
    violations: list[str] = []
    details: dict[str, Any] = {"task_id": tid, "board_task_found": bool(board_task)}
    view_violations = check_board_views(repo, board)
    if view_violations:
        violations.extend(view_violations)

    if board_task is None:
        return {
            "score": 0,
            "max": 10,
            "violations": [f"{tid} is missing from .board/tasks.yaml"],
            "warnings": warnings,
            "details": details,
        }

    score = 0
    status = board_task.get("status")
    owner = board_task.get("owner")
    details["status"] = status
    details["owner"] = owner

    if status in VALID_STATUSES:
        score += 2
    else:
        violations.append(f"invalid task status for {tid}: {status}")

    if _dependencies_respected(board, board_task):
        score += 3
    else:
        violations.append(f"dependencies are not respected for {tid}")

    if status == "DONE":
        # DONE tasks must carry observable evidence so the next agent/scorer is
        # not forced to trust chat history.
        evidence_violations = (
            validate_acceptance_evidence(repo, board_task)
            if board_task.get("require_gate_evidence")
            else []
        )
        if board_task.get("require_gate_evidence") and evidence_violations:
            violations.extend(evidence_violations)
        elif board_task.get("current_handoff") or board_task.get("acceptance_evidence"):
            score += 3
        else:
            violations.append(f"{tid} is DONE without acceptance evidence")
    else:
        score += 3
        warnings.append(f"{tid} is not DONE; acceptance evidence is not required yet")

    if owner is not None and status is not None:
        score += 2
    else:
        violations.append(f"{tid} must include owner and status")

    if view_violations:
        score = max(0, score - 2)
    return {
        "score": score,
        "max": 10,
        "violations": violations,
        "warnings": warnings,
        "details": details,
    }


def _find_task(board: dict[str, Any], task_id: str) -> dict[str, Any] | None:
    for item in board.get("tasks", []):
        if isinstance(item, dict) and item.get("id") == task_id:
            return item
    return None


def _dependencies_respected(board: dict[str, Any], task: dict[str, Any]) -> bool:
    status = task.get("status")
    if status == "TODO":
        return True

    # Any task that has started must wait for dependency tasks to be DONE.
    tasks = {
        item.get("id"): item
        for item in board.get("tasks", [])
        if isinstance(item, dict) and item.get("id")
    }
    for dep_id in task.get("dependencies", []) or []:
        dependency = tasks.get(dep_id)
        if dependency is None or dependency.get("status") != "DONE":
            return False
    return True
