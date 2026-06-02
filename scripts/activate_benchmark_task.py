#!/usr/bin/env python3
"""Expose one benchmark task inside an initialized BoardFlow workspace."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from repo_manager_core.benchmark.workspace import activate_task  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, help="Initialized BoardFlow workspace.")
    parser.add_argument("--task-id", required=True, help="Benchmark task id to expose.")
    args = parser.parse_args()
    try:
        result = activate_task(ROOT, args.workspace, args.task_id)
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1
    for key, value in result.items():
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
