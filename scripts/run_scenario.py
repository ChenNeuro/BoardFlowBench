#!/usr/bin/env python3
"""Run or resume a BoardFlowBench scenario."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from repo_manager_core.benchmark.runner import resume_run, start_run  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resume", default=None, help="External run.json checkpoint.")
    parser.add_argument("--target", default="expense_lite")
    parser.add_argument("--condition", default="full_boardflow")
    parser.add_argument("--workspace", default=None)
    parser.add_argument("--oracle-root", default=None)
    parser.add_argument("--results-dir", default=None)
    parser.add_argument("--source-repo", default=None)
    parser.add_argument("--agent-profile", default="codex")
    parser.add_argument("--agent-command", default=None, help="Optional argv template with {workspace}, {prompt_file}, and {task_id}.")
    parser.add_argument("--reviewer-command", default=None, help="Optional non-blocking reviewer argv template with {workspace}, {evidence_file}, and {task_id}.")
    args = parser.parse_args()
    try:
        if args.resume:
            state = resume_run(ROOT, args.resume)
        else:
            for name in ("workspace", "oracle_root", "results_dir"):
                if getattr(args, name) is None:
                    raise ValueError(f"--{name.replace('_', '-')} is required unless --resume is used")
            state = start_run(
                ROOT,
                target=args.target,
                condition=args.condition,
                workspace=args.workspace,
                oracle_root=args.oracle_root,
                results_dir=args.results_dir,
                source_repo=args.source_repo,
                agent_profile=args.agent_profile,
                agent_command=args.agent_command,
                reviewer_command=args.reviewer_command,
            )
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1
    print(json.dumps(state, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
