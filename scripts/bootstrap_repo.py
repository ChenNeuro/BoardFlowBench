#!/usr/bin/env python3
"""Recommend or apply an allowlisted repository scaffold."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from repo_manager_core.bootstrap import apply_template, recommend_templates  # noqa: E402

CATALOG = ROOT / "benchmark" / "bootstrap_templates" / "catalog.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("recommend", "apply"))
    parser.add_argument("--repo", default=None)
    parser.add_argument("--prompt-file", default=None)
    parser.add_argument("--template-id", default=None)
    parser.add_argument("--catalog", default=str(CATALOG))
    parser.add_argument("--allow-template-tasks", action="store_true")
    args = parser.parse_args()
    if args.action == "recommend":
        print(json.dumps(recommend_templates(args.catalog), indent=2, sort_keys=True))
        return 0
    missing = [name for name in ("repo", "prompt_file", "template_id") if not getattr(args, name)]
    if missing:
        print("Error: " + ", ".join(f"--{name.replace('_', '-')}" for name in missing) + " required for apply")
        return 1
    try:
        record = apply_template(
            args.repo,
            args.catalog,
            args.template_id,
            args.prompt_file,
            allow_template_tasks=args.allow_template_tasks,
        )
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1
    print(json.dumps(record, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
