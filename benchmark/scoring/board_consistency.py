"""Board consistency checks for BoardFlowBench."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from benchmark.scoring.task_loader import load_board


VALID_STATUSES = {"TODO", "IN_PROGRESS", "BLOCKED", "READY_FOR_REVIEW", "DONE"}


def check_board_consistency(repo: str | Path, task: dict[str, Any]) -> dict[str, Any]:
    """Score machine-readable board consistency out of 10."""
    board = load_board(repo)
    task_id = str(task.get("task_id") or task.get("id"))
    board_task = _find_task(board, task_id)
    warnings: list[str] = []
    violations: list[str] = []
    details: dict[str, Any] = {"task_id": task_id, "board_task_found": bool(board_task)}

    if board_task is None:
        return {
            "score": 0,
            "max": 10,
            "violations": [f"{task_id} is missing from .board/tasks.yaml"],
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
        violations.append(f"invalid task status for {task_id}: {status}")

    if _dependencies_respected(board, board_task):
        score += 3
    else:
        violations.append(f"dependencies are not respected for {task_id}")

    if status == "DONE":
        if board_task.get("current_handoff") or board_task.get("acceptance_evidence"):
            score += 3
        else:
            violations.append(f"{task_id} is DONE without acceptance evidence")
    else:
        score += 3
        warnings.append(f"{task_id} is not DONE; acceptance evidence is not required yet")

    if owner is not None and status is not None:
        score += 2
    else:
        violations.append(f"{task_id} must include owner and status")

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
