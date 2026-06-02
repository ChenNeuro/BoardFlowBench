"""Keep the human and machine BoardFlow taskboard views synchronized."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .board_io import _dump_yaml, load_board
from .evidence import has_valid_acceptance_evidence
from .task_status import VALID_STATUSES

PROJECT_BOARD_PATH = "PROJECT_BOARD.md"
TASKS_PATH = ".board/tasks.yaml"
SYNCED_TASK_FIELDS = ("title", "status", "owner", "dependencies", "notes")


def check_board_views(repo: str | Path, board: dict[str, Any] | None = None) -> list[str]:
    """Return taskboard view differences without modifying either file."""
    root = Path(repo)
    machine = board or load_board(root)
    human = read_project_board(root)
    violations: list[str] = []

    machine_milestone = machine.get("current_milestone", {})
    human_milestone = human.get("current_milestone", {})
    for field in ("id", "title", "status"):
        if str(machine_milestone.get(field, "")) != str(human_milestone.get(field, "")):
            violations.append(f"milestone {field} differs between taskboard views")

    machine_tasks = _tasks_by_id(machine.get("tasks", []))
    human_tasks = _tasks_by_id(human.get("tasks", []))
    if set(machine_tasks) != set(human_tasks):
        violations.append("task ids differ between taskboard views")

    for task_id in sorted(set(machine_tasks) & set(human_tasks)):
        for field in SYNCED_TASK_FIELDS:
            if str(machine_tasks[task_id].get(field, "")) != str(human_tasks[task_id].get(field, "")):
                violations.append(f"{task_id} {field} differs between taskboard views")
    return violations


def update_task_status(
    repo: str | Path,
    task_id: str,
    status: str,
    *,
    owner: str | None = None,
) -> None:
    """Update status and owner in both taskboard views after consistency checks."""
    root = Path(repo)
    if status not in VALID_STATUSES:
        raise ValueError(f"invalid status: {status}")
    board = load_board(root)
    violations = check_board_views(root, board)
    if violations:
        raise ValueError("taskboard views are inconsistent: " + "; ".join(violations))

    task = _find_task(board, task_id)
    if task is None:
        raise ValueError(f"task {task_id} not found")
    if status == "DONE" and not _has_completion_evidence(root, task):
        raise ValueError(f"task {task_id} cannot be marked DONE without handoff or acceptance evidence")

    task["status"] = status
    if owner:
        task["owner"] = owner

    markdown_path = root / PROJECT_BOARD_PATH
    markdown = _update_markdown_task(markdown_path.read_text(encoding="utf-8"), task_id, status, owner)
    (root / TASKS_PATH).write_text(_dump_yaml(board), encoding="utf-8")
    markdown_path.write_text(markdown, encoding="utf-8")


def read_project_board(repo: str | Path) -> dict[str, Any]:
    """Parse the synchronized fields from PROJECT_BOARD.md."""
    text = (Path(repo) / PROJECT_BOARD_PATH).read_text(encoding="utf-8")
    milestone_match = re.search(r"^Milestone:\s*(.*?)\s+-\s+(.*?)\s*$", text, re.MULTILINE)
    status_match = re.search(
        r"## Current Milestone.*?^Status:\s*(.*?)\s*$",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if not milestone_match or not status_match:
        raise ValueError(f"{PROJECT_BOARD_PATH} is missing current milestone fields")

    tasks = []
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 6 or cells[0] in {"Task", "---"}:
            continue
        tasks.append(
            {
                "id": cells[0],
                "title": cells[1],
                "status": cells[2],
                "owner": cells[3],
                "dependencies": [] if cells[4] == "none" else [item.strip() for item in cells[4].split(",")],
                "notes": "|".join(cells[5:]).strip(),
            }
        )

    return {
        "current_milestone": {
            "id": milestone_match.group(1).strip(),
            "title": milestone_match.group(2).strip(),
            "status": status_match.group(1).strip(),
        },
        "tasks": tasks,
    }


def _tasks_by_id(tasks: list[Any]) -> dict[str, dict[str, Any]]:
    return {
        str(task.get("id")): task
        for task in tasks
        if isinstance(task, dict) and task.get("id")
    }


def _find_task(board: dict[str, Any], task_id: str) -> dict[str, Any] | None:
    return _tasks_by_id(board.get("tasks", [])).get(task_id)


def _has_completion_evidence(root: Path, task: dict[str, Any]) -> bool:
    if task.get("require_gate_evidence"):
        return has_valid_acceptance_evidence(root, task)
    if task.get("acceptance_evidence"):
        return True
    handoff = task.get("current_handoff")
    return bool(handoff and (root / str(handoff)).exists())


def _update_markdown_task(text: str, task_id: str, status: str, owner: str | None) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if not line.startswith("|"):
            continue
        parts = line.split("|")
        if len(parts) < 8 or parts[1].strip() != task_id:
            continue
        parts[3] = f" {status} "
        if owner:
            parts[4] = f" {owner} "
        lines[index] = "|".join(parts)
        return "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    raise ValueError(f"task {task_id} not found in {PROJECT_BOARD_PATH}")
