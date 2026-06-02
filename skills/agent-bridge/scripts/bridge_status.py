#!/usr/bin/env python3
"""Update task status in both BoardFlow taskboard views."""
from __future__ import annotations

import argparse
from pathlib import Path

from repo_manager_core.board.board_sync import update_task_status
from repo_manager_core.board.task_status import VALID_STATUSES


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_id", help="Task identifier (e.g. P001 or B001).")
    parser.add_argument("status", choices=sorted(VALID_STATUSES), help="New status.")
    parser.add_argument("--repo", default=".", help="Repository root.")
    parser.add_argument("--owner", default=None, help="Agent who owns the task.")
    args = parser.parse_args()
    root = Path(args.repo)
    try:
        update_task_status(root, args.task_id, args.status, owner=args.owner)
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1
    print(f"Updated {args.task_id} to {args.status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
