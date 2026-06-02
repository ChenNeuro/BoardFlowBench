#!/usr/bin/env python3
"""Create a structured handoff JSON file for agent transition."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from repo_manager_core.board.handoff_writer import (
    write_validated_handoff,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Repository root.")
    parser.add_argument("--schema", default=".board/handoff.schema.json", help="Path to handoff JSON Schema.")
    parser.add_argument("--input", required=True, help="Complete handoff JSON input.")
    args = parser.parse_args()
    root = Path(args.repo)

    schema_path = root / args.schema
    try:
        data = json.loads(Path(args.input).read_text(encoding="utf-8"))
        path = write_validated_handoff(root, data, schema_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Error: {exc}")
        return 1

    print("Handoff validated against schema.")
    print(f"Created {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
