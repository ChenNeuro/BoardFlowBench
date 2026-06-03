#!/usr/bin/env python3
"""Update task status in .board/tasks.yaml."""
from __future__ import annotations

import argparse
from pathlib import Path

from _bootstrap import bootstrap_repo_manager_core

bootstrap_repo_manager_core()

from repo_manager_core.board.board_io import load_board, save_board
from repo_manager_core.board.task_status import VALID_STATUSES


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_id", help="Task identifier (e.g. T001).")
    parser.add_argument("status", choices=sorted(VALID_STATUSES), help="New status.")
    parser.add_argument("--repo", default=".", help="Repository root.")
    parser.add_argument("--owner", default=None, help="Agent who owns the task.")
    args = parser.parse_args()
    root = Path(args.repo)
    board = load_board(root)
    for task in board.get("tasks", []):
        if task.get("id") == args.task_id:
            task["status"] = args.status
            if args.owner:
                task["owner"] = args.owner
            break
    else:
        print(f"Task {args.task_id} not found")
        return 1
    save_board(board, root)
    print(f"Updated {args.task_id} to {args.status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
