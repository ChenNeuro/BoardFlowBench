#!/usr/bin/env python3
"""Recover a runner-authored signed benchmark activation transition."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from repo_manager_core.benchmark.runner import resume_activation  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-manifest", required=True, help="Signed external run.json checkpoint.")
    args = parser.parse_args()
    try:
        result = resume_activation(ROOT, args.run_manifest)
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1
    for key, value in result.items():
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
