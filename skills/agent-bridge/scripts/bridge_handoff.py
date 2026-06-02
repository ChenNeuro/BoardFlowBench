#!/usr/bin/env python3
"""Create a structured handoff JSON file for agent transition."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from repo_manager_core.board.handoff_writer import (
    validate_handoff_schema,
    write_handoff,
    write_validated_handoff,
)
from repo_manager_core.board.task_status import VALID_STATUSES


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_id", help="Task identifier (e.g. P001 or B001).")
    parser.add_argument("agent_id", help="Agent creating the handoff.")
    parser.add_argument("agent_role", help="Agent role (e.g. first_worker, reviewer_finisher).")
    parser.add_argument("--status", default="READY_FOR_REVIEW", choices=sorted(VALID_STATUSES))
    parser.add_argument("--repo", default=".", help="Repository root.")
    parser.add_argument("--files", nargs="*", default=[], help="Files changed.")
    parser.add_argument("--risks", default=None, help="Known risks.")
    parser.add_argument("--next-step", default=None, help="Next recommended step.")
    parser.add_argument("--schema", default=".board/handoff.schema.json", help="Path to handoff JSON Schema.")
    parser.add_argument("--input", default=None, help="Validated handoff JSON input. Preferred for formal handoff.")
    args = parser.parse_args()
    root = Path(args.repo)

    schema_path = root / args.schema
    if args.input:
        try:
            data = json.loads(Path(args.input).read_text(encoding="utf-8"))
            path = write_validated_handoff(root, data, schema_path)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(f"Error: {exc}")
            return 1
    else:
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
        if schema_path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            violations = validate_handoff_schema(data, schema_path)
            if violations:
                path.unlink()
                print("Error: handoff schema violations: " + "; ".join(violations))
                return 1

    print("Handoff validated against schema.")
    print(f"Created {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
