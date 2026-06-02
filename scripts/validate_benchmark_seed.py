#!/usr/bin/env python3
"""Validate that a benchmark seed reproduces its intentional initial gap."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from repo_manager_core.benchmark.workspace import load_target, run_git, task_path  # noqa: E402
from tools.benchmark_scorer import score_task, write_score  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--oracle-root", required=True)
    parser.add_argument("--target", default="expense_lite")
    parser.add_argument("--task-id", default="B001")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    workspace = Path(args.workspace).resolve()
    manifest = load_target(ROOT, args.target)
    baseline = run_git(["rev-parse", "HEAD"], cwd=workspace).stdout.strip()
    if baseline != manifest["seed_commit"]:
        print("Error: workspace HEAD does not match the fixed target seed commit")
        return 1
    result = score_task(
        workspace,
        task_path(ROOT, manifest, args.task_id),
        phase="seed",
        condition="no_board_baseline",
        baseline=baseline,
        oracle_root=args.oracle_root,
        target=args.target,
        seed_commit=str(manifest["seed_commit"]),
        oracle_commit=str(manifest["oracle_commit"]),
    )
    if args.output:
        write_score(result, args.output)
    print(f"task_id={result['task_id']} total={result['total']} gate_pass={result['hard_gate_pass']}")
    return 0 if result["hard_gate_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
