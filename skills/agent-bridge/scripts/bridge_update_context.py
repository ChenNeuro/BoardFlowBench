#!/usr/bin/env python3
"""Update agent_context.md with latest board state and style profile."""
from __future__ import annotations

import argparse
from pathlib import Path

from repo_manager_core.board.board_io import load_board
from repo_manager_core.board.board_sync import check_board_views
from repo_manager_core.board.git_state import inspect_git_state
from repo_manager_core.style.style_profile import build_profile
from repo_manager_core.style.learn_repo_style import learn_repo_style
from repo_manager_core.style.context_writer import write_agent_context, write_style_profile


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Repository root.")
    parser.add_argument("--agent-id", default=None, help="Current agent identifier.")
    parser.add_argument("--task-id", default=None, help="Current task identifier.")
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

    style_profile = learn_repo_style(build_profile(root))
    write_style_profile(root, style_profile)
    dest = write_agent_context(
        root,
        style_profile,
        board,
        args.agent_id,
        args.task_id,
        git_state=inspect_git_state(root),
    )
    print(f"Wrote agent context to {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
