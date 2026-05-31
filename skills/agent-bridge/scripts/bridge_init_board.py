#!/usr/bin/env python3
"""Initialize .board/tasks.yaml and handoffs/reviews directories."""
from __future__ import annotations

import argparse
from pathlib import Path

from repo_manager_core.board.board_io import save_board

DEFAULT_BOARD = {
    "schema_version": 1,
    "project": "Repo Manager",
    "status_values": ["TODO", "IN_PROGRESS", "BLOCKED", "READY_FOR_REVIEW", "DONE"],
    "tasks": [],
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Repository root.")
    args = parser.parse_args()
    root = Path(args.repo)
    board_dir = root / ".board"
    board_dir.mkdir(parents=True, exist_ok=True)
    (board_dir / "handoffs").mkdir(exist_ok=True)
    (board_dir / "reviews").mkdir(exist_ok=True)
    board_path = board_dir / "tasks.yaml"
    if not board_path.exists():
        save_board(DEFAULT_BOARD, root)
        print(f"Created {board_path}")
    else:
        print(f"{board_path} already exists")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
