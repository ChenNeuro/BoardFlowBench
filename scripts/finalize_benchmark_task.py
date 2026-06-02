#!/usr/bin/env python3
"""Run deterministic acceptance checks and finalize one benchmark sticker."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from repo_manager_core.benchmark.finalize import finalize_task  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--condition", required=True)
    parser.add_argument("--oracle-root", required=True)
    parser.add_argument("--results-dir", required=True)
    parser.add_argument("--target", default="expense_lite")
    parser.add_argument("--owner", default="agent")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--baseline", default=None)
    args = parser.parse_args()
    try:
        evidence = finalize_task(
            ROOT,
            args.workspace,
            args.task_id,
            args.condition,
            args.oracle_root,
            args.results_dir,
            target=args.target,
            owner=args.owner,
            run_id=args.run_id,
            baseline=args.baseline,
        )
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
