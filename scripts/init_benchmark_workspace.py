#!/usr/bin/env python3
"""Clone a fixed standalone demo seed into an isolated benchmark workspace."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from repo_manager_core.benchmark.workspace import initialize_workspace  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, help="Benchmark target id.")
    parser.add_argument(
        "--condition",
        required=True,
        choices=("boardflow_sequential", "full_boardflow", "native_instructions", "native_docs_handoff", "no_board_baseline"),
    )
    parser.add_argument("--task-id", required=True, help="Assigned benchmark task id.")
    parser.add_argument("--workspace", required=True, help="New workspace directory.")
    parser.add_argument("--source-repo", default=None, help="Optional local clone source for offline validation.")
    parser.add_argument("--agent-profile", default="codex", help="Native instructions profile.")
    args = parser.parse_args()
    try:
        result = initialize_workspace(
            ROOT,
            args.target,
            args.condition,
            args.task_id,
            args.workspace,
            source_repo=args.source_repo,
            agent_profile=args.agent_profile,
        )
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1
    for key, value in result.items():
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
