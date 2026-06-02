#!/usr/bin/env python3
"""Refresh Agent Bridge context before starting or ending a coding turn."""
from __future__ import annotations

import argparse
from pathlib import Path

from repo_manager_core.board.board_io import load_board
from repo_manager_core.board.board_sync import check_board_views
from repo_manager_core.board.git_state import inspect_git_state
from repo_manager_core.board.evidence import validate_acceptance_evidence
from repo_manager_core.board.handoff_writer import check_handoff
from repo_manager_core.style.context_writer import write_agent_context, write_style_profile
from repo_manager_core.style.learn_repo_style import learn_repo_style
from repo_manager_core.style.style_profile import build_profile

ACTIVE_STATUSES = {"IN_PROGRESS", "READY_FOR_REVIEW", "BLOCKED"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", required=True, choices=("start", "end"))
    parser.add_argument("--agent-id", required=True)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--repo", default=".", help="Repository root.")
    parser.add_argument("--override-reason", default=None, help="Reason for continuing a blocked start refresh.")
    args = parser.parse_args()
    root = Path(args.repo)

    try:
        board = load_board(root)
        violations = check_board_views(root, board)
    except Exception as exc:
        print(f"Error: {exc}")
        return 1
    if violations:
        print("Error: taskboard views are inconsistent: " + "; ".join(violations))
        return 1

    current = _find_task(board, args.task_id)
    if current is None:
        print(f"Error: task {args.task_id} not found")
        return 1

    git_state = inspect_git_state(root)
    blockers = _start_blockers(root, board, args.task_id, git_state) if args.phase == "start" else []
    style_profile = learn_repo_style(build_profile(root))
    write_style_profile(root, style_profile)
    context_path = write_agent_context(
        root,
        style_profile,
        board,
        args.agent_id,
        args.task_id,
        phase=args.phase,
        git_state=git_state,
        blockers=blockers,
        override_reason=args.override_reason,
    )
    print(f"Wrote agent context to {context_path}")

    if blockers and not args.override_reason:
        print("Error: start refresh is blocked:")
        for blocker in blockers:
            print(f"- {blocker}")
        print("Use --override-reason to continue and record the reason.")
        return 1
    if blockers:
        print("Start refresh continued with recorded override reason.")
    else:
        print(f"{args.phase.capitalize()} refresh passed.")
    return 0


def _find_task(board: dict, task_id: str) -> dict | None:
    for task in board.get("tasks", []):
        if task.get("id") == task_id:
            return task
    return None


def _start_blockers(root: Path, board: dict, current_task_id: str, git_state: dict) -> list[str]:
    blockers = [
        f"{task.get('id')} remains {task.get('status')}"
        for task in board.get("tasks", [])
        if task.get("id") != current_task_id and task.get("status") in ACTIVE_STATUSES
    ]
    if not git_state.get("available"):
        blockers.append("git workspace status is unavailable")
    elif not git_state.get("clean"):
        blockers.append("git workspace has staged, unstaged, or untracked files")
    current = _find_task(board, current_task_id) or {}
    tasks = {
        task.get("id"): task
        for task in board.get("tasks", [])
        if isinstance(task, dict) and task.get("id")
    }
    for dep_id in current.get("dependencies", []) or []:
        dependency = tasks.get(dep_id, {})
        if dependency.get("status") != "DONE":
            blockers.append(f"{dep_id} dependency is not DONE")
            continue
        if dependency.get("require_gate_evidence"):
            blockers.extend(validate_acceptance_evidence(root, dependency))
        handoff = check_handoff(root, {"task_id": dep_id, "handoff_required": True})
        blockers.extend(handoff.get("violations", []))
    return blockers


if __name__ == "__main__":
    raise SystemExit(main())
