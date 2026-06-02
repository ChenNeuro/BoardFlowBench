#!/usr/bin/env python3
"""Run deterministic acceptance checks and finalize one benchmark sticker."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from repo_manager_core.benchmark.runner import resume_run  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-manifest", required=True, help="Signed external run.json checkpoint.")
    args = parser.parse_args()
    try:
        state = resume_run(ROOT, args.run_manifest)
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1
    print(json.dumps(state, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
