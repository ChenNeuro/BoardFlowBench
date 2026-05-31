#!/usr/bin/env python3
"""Update agent_context.md with latest board state and style profile."""
from __future__ import annotations

import argparse
from pathlib import Path

from repo_manager_core.board.board_io import load_board
from repo_manager_core.style.learn_repo_style import read_json
from repo_manager_core.style.style_profile import build_profile
from repo_manager_core.style.learn_repo_style import learn_repo_style
from repo_manager_core.style.context_writer import write_agent_context


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Repository root.")
    parser.add_argument("--agent-id", default=None, help="Current agent identifier.")
    parser.add_argument("--task-id", default=None, help="Current task identifier.")
    args = parser.parse_args()
    root = Path(args.repo)

    # Build style profile if cache doesn't exist
    style_path = root / ".repo_manager" / "repo_style_profile.json"
    if style_path.exists():
        style_profile = read_json(style_path)
    else:
        profile = build_profile(root)
        style_profile = learn_repo_style(profile)

    try:
        board = load_board(root)
    except Exception:
        board = None

    dest = write_agent_context(root, style_profile, board, args.agent_id, args.task_id)
    print(f"Wrote agent context to {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
