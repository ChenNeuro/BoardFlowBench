#!/usr/bin/env python3
"""Prepare a non-official SWE-bench Lite RepoFlow smoke workspace.

This script fetches public SWE-bench Lite instance metadata, optionally clones
the target repository at the base commit, and writes a RepoFlow task packet.
It does not run Docker and does not produce an official SWE-bench score.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

DATASET = "princeton-nlp/SWE-bench_Lite"
CONFIG = "default"
SPLIT = "test"
DEFAULT_INSTANCE = "astropy__astropy-12907"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instance-id", default=DEFAULT_INSTANCE)
    parser.add_argument("--workspace", default=None, help="Workspace to create. Required unless --metadata-only is used.")
    parser.add_argument("--control-dir", default=None, help="Directory for non-agent metadata and test patches.")
    parser.add_argument("--metadata-only", action="store_true", help="Fetch and write metadata without cloning a repository.")
    parser.add_argument("--force", action="store_true", help="Remove an existing workspace/control dir before writing.")
    parser.add_argument("--dataset", default=DATASET)
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve() if args.workspace else None
    if not args.metadata_only and workspace is None:
        print("Error: --workspace is required unless --metadata-only is used", file=sys.stderr)
        return 2

    control_dir = Path(args.control_dir).resolve() if args.control_dir else Path(
        tempfile.mkdtemp(prefix=f"swe-lite-{safe_name(args.instance_id)}-")
    )
    if control_dir.exists() and args.force:
        shutil.rmtree(control_dir)
    control_dir.mkdir(parents=True, exist_ok=True)

    instance = fetch_instance(args.dataset, args.instance_id)
    write_control_files(control_dir, instance)

    result: dict[str, Any] = {
        "dataset": args.dataset,
        "instance_id": instance["instance_id"],
        "repo": instance["repo"],
        "base_commit": instance["base_commit"],
        "control_dir": str(control_dir),
        "metadata_only": args.metadata_only,
        "official_score": False,
        "notes": [
            "This is a non-official SWE-style smoke scaffold.",
            "Gold patch and test patch are stored only in the control directory, not in the agent workspace.",
            "Run official SWE-bench Lite only after Docker isolation is available.",
        ],
    }

    if not args.metadata_only:
        assert workspace is not None
        prepare_workspace(workspace, control_dir, instance, force=args.force)
        result["workspace"] = str(workspace)
        result["workspace_files"] = [
            "AGENTS.md",
            ".repoflow/assigned_task.json",
            ".repoflow/assigned_task.md",
            ".repoflow/skill_packet.md",
        ]
    else:
        result["workspace"] = None

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def fetch_instance(dataset: str, instance_id: str) -> dict[str, Any]:
    offset = 0
    length = 100
    while True:
        query = urllib.parse.urlencode(
            {
                "dataset": dataset,
                "config": CONFIG,
                "split": SPLIT,
                "offset": offset,
                "length": length,
            }
        )
        url = f"https://datasets-server.huggingface.co/rows?{query}"
        with urllib.request.urlopen(url, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
        rows = payload.get("rows") or []
        for item in rows:
            row = item.get("row") or {}
            if row.get("instance_id") == instance_id:
                return row
        if not rows or len(rows) < length:
            break
        offset += length
    raise ValueError(f"instance not found in {dataset}/{SPLIT}: {instance_id}")


def write_control_files(control_dir: Path, instance: dict[str, Any]) -> None:
    public = public_instance(instance)
    (control_dir / "instance_public.json").write_text(json.dumps(public, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (control_dir / "problem_statement.md").write_text(str(instance["problem_statement"]).rstrip() + "\n", encoding="utf-8")
    (control_dir / "agent_task_packet.md").write_text(render_task_packet(instance), encoding="utf-8")
    (control_dir / "repoflow_skill_packet.md").write_text(render_skill_packet(instance), encoding="utf-8")

    # These are public SWE-bench fields, but they are answer/evaluator material.
    # Keep them outside the agent workspace and do not commit run-specific copies.
    (control_dir / "gold_patch.diff").write_text(str(instance.get("patch") or ""), encoding="utf-8")
    (control_dir / "test_patch.diff").write_text(str(instance.get("test_patch") or ""), encoding="utf-8")
    (control_dir / "DO_NOT_SHOW_AGENT.txt").write_text(
        "gold_patch.diff and test_patch.diff are evaluator/control-plane material.\n"
        "Do not place them in the agent workspace or prompt.\n",
        encoding="utf-8",
    )


def public_instance(instance: dict[str, Any]) -> dict[str, Any]:
    hidden = {"patch", "test_patch"}
    return {key: value for key, value in instance.items() if key not in hidden}


def prepare_workspace(workspace: Path, control_dir: Path, instance: dict[str, Any], *, force: bool) -> None:
    if workspace.exists():
        if not force:
            raise ValueError(f"workspace already exists: {workspace}")
        shutil.rmtree(workspace)
    repo_url = f"https://github.com/{instance['repo']}.git"
    run(["git", "clone", "--quiet", repo_url, str(workspace)], cwd=workspace.parent)
    run(["git", "switch", "--quiet", "--detach", str(instance["base_commit"])], cwd=workspace)

    repoflow = workspace / ".repoflow"
    (repoflow / "handoffs").mkdir(parents=True, exist_ok=True)
    (repoflow / "assigned_task.json").write_text(
        json.dumps(public_instance(instance), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (repoflow / "assigned_task.md").write_text(render_task_packet(instance), encoding="utf-8")
    (repoflow / "skill_packet.md").write_text(render_skill_packet(instance), encoding="utf-8")
    (repoflow / "handoffs" / ".gitkeep").write_text("", encoding="utf-8")
    (workspace / "AGENTS.md").write_text(render_agents_md(instance), encoding="utf-8")

    copy_note = {
        "control_dir": str(control_dir),
        "warning": "Control dir contains evaluator material. Do not expose gold_patch.diff or test_patch.diff to the agent.",
    }
    (repoflow / "control_note.json").write_text(json.dumps(copy_note, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def render_agents_md(instance: dict[str, Any]) -> str:
    return f"""# AGENTS.md

This is a non-official SWE-bench Lite smoke workspace prepared by BoardFlowBench.

Required reading order:

1. `AGENTS.md`
2. `.repoflow/assigned_task.md`
3. `.repoflow/skill_packet.md`
4. Repository files relevant to the issue

Rules:

- Work only on SWE-bench Lite instance `{instance['instance_id']}`.
- Do not look for or use `gold_patch.diff`, `test_patch.diff`, oracle files, or evaluator artifacts.
- Make the smallest source change that addresses the issue statement.
- Run focused repository tests if the local environment supports them.
- Record changed files, commands, results, risks, and next step in `.repoflow/handoffs/`.
- This workspace is for patch-generation smoke testing only. It is not an official SWE-bench score.
"""


def render_task_packet(instance: dict[str, Any]) -> str:
    return f"""# SWE-bench Lite Task Packet

Instance: `{instance['instance_id']}`
Repository: `{instance['repo']}`
Base commit: `{instance['base_commit']}`

## Problem Statement

{str(instance['problem_statement']).rstrip()}

## Constraints

- Do not use official gold patches or test patches while generating a solution.
- Keep the patch minimal and issue-focused.
- Prefer running targeted tests before broad test suites.
- If dependencies are unavailable, record the exact command and failure.

## Non-Official Status

This packet supports local RepoFlow/SWE-style smoke testing. It is not an official SWE-bench Lite evaluation without Docker isolation and the official harness.
"""


def render_skill_packet(instance: dict[str, Any]) -> str:
    return f"""# RepoFlow SWE Lite Smoke Skill

Use this packet before editing `{instance['repo']}` for `{instance['instance_id']}`.

1. Restate the issue in one sentence before editing.
2. Inspect the smallest plausible set of source files.
3. Do not use evaluator-only artifacts: `gold_patch.diff`, `test_patch.diff`, hidden tests, or oracle directories.
4. Make a minimal patch; avoid broad refactors and unrelated formatting.
5. Run focused tests if available. If not available, run import or unit-level checks that are cheap and relevant.
6. Write a handoff under `.repoflow/handoffs/` with changed files, commands, results, risks, and next step.

Failure categories to record separately:

- model output or patch format failure;
- dependency/environment failure;
- repository test failure;
- suspected harness/evaluator mismatch.
"""


def run(arguments: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(arguments, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(arguments)}\n{result.stderr or result.stdout}")
    return result


def safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in value)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
