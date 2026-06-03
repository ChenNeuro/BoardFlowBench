#!/usr/bin/env python3
"""Create a structured handoff JSON file for agent transition."""
from __future__ import annotations

import argparse
from pathlib import Path

from _bootstrap import bootstrap_repo_manager_core

bootstrap_repo_manager_core()

from repo_manager_core.board.handoff_writer import write_handoff, validate_handoff_schema
from repo_manager_core.board.task_status import VALID_STATUSES


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_id", help="Task identifier (e.g. T001).")
    parser.add_argument("agent_id", help="Agent creating the handoff.")
    parser.add_argument("agent_role", help="Agent role (e.g. first_worker, reviewer_finisher).")
    parser.add_argument("--status", default="READY_FOR_REVIEW", choices=sorted(VALID_STATUSES))
    parser.add_argument("--repo", default=".", help="Repository root.")
    parser.add_argument("--files", nargs="*", default=[], help="Files changed.")
    parser.add_argument("--risks", default=None, help="Known risks.")
    parser.add_argument("--next-step", default=None, help="Next recommended step.")
    parser.add_argument("--schema", default=".board/handoff.schema.json", help="Path to handoff JSON Schema.")
    args = parser.parse_args()
    root = Path(args.repo)

    path = write_handoff(
        repo=root,
        task_id=args.task_id,
        agent_id=args.agent_id,
        agent_role=args.agent_role,
        status=args.status,
        files_changed=list(args.files),
        risks=args.risks,
        next_recommended_step=args.next_step,
    )

    schema_path = root / args.schema
    if schema_path.exists():
        with open(path) as f:
            import json
            data = json.load(f)
        missing = validate_handoff_schema(data, schema_path)
        if missing:
            print(f"Warning: handoff missing required fields: {missing}")
        else:
            print("Handoff validated against schema.")

    print(f"Created {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
