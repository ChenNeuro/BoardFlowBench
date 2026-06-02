"""Scenario orchestration around external coding-agent command adapters."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from repo_manager_core.benchmark.control import (
    find_stage_snapshot,
    load_run_state,
    validate_external_placement,
    write_run_state,
)
from repo_manager_core.benchmark.finalize import finalize_task
from repo_manager_core.benchmark.workspace import (
    activate_task,
    commit_all,
    initialize_workspace,
    git_status,
    load_target,
    load_task_specs,
    normalize_condition,
    run_git,
    task_path,
)
from tools.benchmark_scorer import score_task, write_score


def start_run(
    project_root: str | Path,
    *,
    target: str,
    condition: str,
    workspace: str | Path,
    oracle_root: str | Path,
    results_dir: str | Path,
    source_repo: str | Path | None = None,
    agent_profile: str = "codex",
    agent_command: str | None = None,
    reviewer_command: str | None = None,
    allow_unisolated_agent_command: bool = False,
) -> dict[str, Any]:
    """Initialize, validate seed, and either run all tasks or pause for an agent."""
    project = Path(project_root).resolve()
    normalized = normalize_condition(condition)
    manifest = load_target(project, target)
    validate_external_placement(workspace, oracle_root, results_dir)
    if agent_command and not allow_unisolated_agent_command:
        raise ValueError("agent commands require explicit --allow-unisolated-agent-command acknowledgement")
    specs = load_task_specs(project, manifest)
    first = str(specs[0]["task_id"])
    init = initialize_workspace(
        project, target, normalized, first, workspace,
        source_repo=source_repo, agent_profile=agent_profile,
    )
    run_id = f"{target}-{normalized}-{time.time_ns()}"
    run_dir = Path(results_dir).resolve() / run_id
    run_dir.mkdir(parents=True)
    seed_score = score_task(
        init["workspace"],
        task_path(project, manifest, first),
        phase="seed",
        condition=normalized,
        baseline=init["baseline_commit"],
        oracle_root=oracle_root,
        target=target,
        seed_commit=str(manifest["seed_commit"]),
        oracle_commit=str(manifest["oracle_commit"]),
    )
    write_score(seed_score, run_dir / "seed-score.json")
    if not seed_score["hard_gate_pass"]:
        raise ValueError(f"seed validation failed; see {run_dir / 'seed-score.json'}")
    state = {
        "schema_version": 1,
        "run_id": run_id,
        "target": target,
        "condition": normalized,
        "workspace": str(Path(workspace).resolve()),
        "oracle_root": str(Path(oracle_root).resolve()),
        "seed_commit": str(manifest["seed_commit"]),
        "oracle_commit": str(manifest["oracle_commit"]),
        "results_dir": str(Path(results_dir).resolve()),
        "agent_profile": agent_profile,
        "agent_command": agent_command,
        "reviewer_command": reviewer_command,
        "tasks": [str(task["task_id"]) for task in specs],
        "current_task": first,
        "baseline_commit": init["baseline_commit"],
        "stages": [],
        "status": "awaiting_agent",
    }
    _write_state(run_dir, state)
    return _advance(project, run_dir, state) if agent_command else _await_agent(project, run_dir, state)


def resume_run(
    project_root: str | Path,
    run_manifest: str | Path,
    *,
    reviewer_command: str | None = None,
) -> dict[str, Any]:
    """Finalize the current manual checkpoint and continue to the next sticker."""
    project = Path(project_root).resolve()
    path = Path(run_manifest).resolve()
    state = load_run_state(path)
    if state["status"] not in {"awaiting_agent", "activating_task"}:
        raise ValueError(f"run manifest cannot resume from status {state['status']}")
    state["reviewer_command"] = reviewer_command
    if state["status"] == "activating_task" or find_stage_snapshot(state, str(state["current_task"])):
        return _continue_after_finalization(project, path.parent, state)
    return _finalize_and_continue(project, path.parent, state)


def resume_activation(project_root: str | Path, run_manifest: str | Path) -> dict[str, Any]:
    """Resume only a runner-authored signed activation transition."""
    project = Path(project_root).resolve()
    path = Path(run_manifest).resolve()
    state = load_run_state(path)
    if state["status"] != "activating_task":
        raise ValueError("run manifest is not waiting for activation recovery")
    return _continue_after_finalization(project, path.parent, state)


def _advance(project: Path, run_dir: Path, state: dict[str, Any]) -> dict[str, Any]:
    command = state.get("agent_command")
    if not command:
        return _await_agent(project, run_dir, state)
    while state["status"] != "complete":
        state = _prepare_stage(project, run_dir, state)
        prompt = _write_prompt(project, run_dir, state)
        argv = _expand_command(
            str(command),
            workspace=state["workspace"],
            prompt_file=str(prompt),
            task_id=state["current_task"],
        )
        result = subprocess.run(
            argv,
            cwd=state["workspace"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env=_agent_environment(),
        )
        (run_dir / "agent-output").mkdir(exist_ok=True)
        (run_dir / "agent-output" / f"{state['current_task']}.json").write_text(
            json.dumps({"adapter": _adapter_summary(argv), "returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}, indent=2) + "\n",
            encoding="utf-8",
        )
        if result.returncode != 0:
            state["status"] = "agent_failed"
            _write_state(run_dir, state)
            raise ValueError(f"agent command failed for {state['current_task']}")
        state = _finalize_and_continue(project, run_dir, state)
    return state


def _finalize_and_continue(project: Path, run_dir: Path, state: dict[str, Any]) -> dict[str, Any]:
    task_id = str(state["current_task"])
    if state["condition"] == "full_boardflow":
        _run_refresh(project, state, "end")
    evidence = finalize_task(
        project,
        state["workspace"],
        task_id,
        state["condition"],
        state["oracle_root"],
        state["results_dir"],
        target=state["target"],
        run_id=state["run_id"],
        baseline=state["baseline_commit"],
        owner=state["agent_profile"],
    )
    started_at = state.get("stage_started_at", {}).get(task_id)
    if started_at:
        evidence["duration_seconds"] = round(time.time() - float(started_at), 3)
    _write_json(run_dir / "stages" / task_id / "evidence.json", evidence)
    trusted_control = _trusted_control_snapshot(run_dir)
    evidence["reviewer"] = _run_reviewer(run_dir, state, evidence)
    _assert_trusted_control_unchanged(run_dir, trusted_control)
    _assert_finalized_workspace(state, evidence)
    _write_json(run_dir / "stages" / task_id / "evidence.json", evidence)
    state["stages"].append(evidence)
    _write_state(run_dir, state)
    return _continue_after_finalization(project, run_dir, state)


def _continue_after_finalization(project: Path, run_dir: Path, state: dict[str, Any]) -> dict[str, Any]:
    """Advance a signed finalized stage, including interrupted activation recovery."""
    task_id = str(state["current_task"])
    index = state["tasks"].index(task_id)
    if index == len(state["tasks"]) - 1:
        state.pop("pending_task", None)
        state["status"] = "complete"
        _write_state(run_dir, state)
        return state
    next_task = state["tasks"][index + 1]
    if state.get("status") == "activating_task" and state.get("pending_task") != next_task:
        raise ValueError("run manifest pending activation differs from the next benchmark task")
    state["status"] = "activating_task"
    state["pending_task"] = next_task
    _write_state(run_dir, state)
    if state["condition"] == "full_boardflow":
        activation = activate_task(
            project,
            state["workspace"],
            next_task,
            run_manifest=run_dir / "run.json",
        )
        baseline = activation["baseline_commit"]
    else:
        baseline = commit_all(Path(state["workspace"]), f"Checkpoint before {next_task}")
    state["current_task"] = next_task
    state["baseline_commit"] = baseline
    state.pop("pending_task", None)
    state["status"] = "awaiting_agent"
    _write_state(run_dir, state)
    return _advance(project, run_dir, state) if state.get("agent_command") else _await_agent(project, run_dir, state)


def _await_agent(project: Path, run_dir: Path, state: dict[str, Any]) -> dict[str, Any]:
    state = _prepare_stage(project, run_dir, state)
    state["status"] = "awaiting_agent"
    _write_state(run_dir, state)
    return state


def _prepare_stage(project: Path, run_dir: Path, state: dict[str, Any]) -> dict[str, Any]:
    task_id = str(state["current_task"])
    started = state.setdefault("stage_started_at", {})
    if task_id not in started:
        if state["condition"] == "full_boardflow":
            _run_refresh(project, state, "start")
        started[task_id] = time.time()
    _write_prompt(project, run_dir, state)
    _write_state(run_dir, state)
    return state


def _run_refresh(project: Path, state: dict[str, Any], phase: str) -> None:
    command = [
        sys.executable,
        str(project / "skills" / "agent-bridge" / "scripts" / "bridge_refresh.py"),
        "--phase",
        phase,
        "--agent-id",
        str(state["agent_profile"]),
        "--task-id",
        str(state["current_task"]),
        "--repo",
        str(state["workspace"]),
    ]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(project)
    result = subprocess.run(command, cwd=project, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode != 0:
        raise ValueError(result.stdout.strip() or result.stderr.strip() or f"{phase} refresh failed")


def _run_reviewer(run_dir: Path, state: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    task_id = str(evidence["task_id"])
    report_path = run_dir / "stages" / task_id / "reviewer-report.json"
    command = state.get("reviewer_command")
    report: dict[str, Any] = {"blocking": False, "configured": bool(command), "risks": []}
    if command:
        evidence_path = run_dir / "stages" / task_id / "evidence.json"
        argv = _expand_command(
            str(command),
            workspace=state["workspace"],
            evidence_file=str(evidence_path),
            task_id=task_id,
        )
        result = subprocess.run(
            argv,
            cwd=state["workspace"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env=_agent_environment(),
        )
        report.update({"adapter": _adapter_summary(argv), "returncode": result.returncode, "stderr": result.stderr})
        if result.returncode == 0:
            try:
                parsed = json.loads(result.stdout)
                if isinstance(parsed, dict):
                    report.update(parsed)
                else:
                    report["warning"] = "reviewer output must be a JSON object"
            except json.JSONDecodeError:
                report["warning"] = "reviewer output was not valid JSON"
                report["stdout"] = result.stdout
        else:
            report["warning"] = "reviewer command failed; findings remain non-blocking"
            report["stdout"] = result.stdout
    risks = report.get("risks")
    report["risk_count"] = len(risks) if isinstance(risks, list) else 0
    _write_json(report_path, report)
    return {"report_file": str(report_path), "risk_count": report["risk_count"], "blocking": False}


def _write_prompt(project: Path, run_dir: Path, state: dict[str, Any]) -> Path:
    manifest = load_target(project, state["target"])
    path = task_path(project, manifest, state["current_task"])
    prompt = run_dir / "prompts" / f"{state['current_task']}.md"
    prompt.parent.mkdir(exist_ok=True)
    prompt.write_text(
        "# Assigned Benchmark Task\n\n"
        f"Workspace: `{state['workspace']}`\n\n"
        f"Condition: `{state['condition']}`\n\n"
        "Implement only this task. Do not read external oracle files.\n\n"
        "```yaml\n" + path.read_text(encoding="utf-8") + "```\n",
        encoding="utf-8",
    )
    return prompt


def _write_state(run_dir: Path, state: dict[str, Any]) -> None:
    write_run_state(run_dir, state)


def _expand_command(template: str, **variables: Any) -> list[str]:
    """Expand only documented tokens so command literals may contain braces."""
    argv = shlex.split(template)
    for name, value in variables.items():
        argv = [part.replace("{" + name + "}", str(value)) for part in argv]
    if any(re.search(r"\{[A-Za-z_][A-Za-z0-9_]*\}", part) for part in argv):
        raise ValueError("adapter command contains an unresolved placeholder")
    return argv


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _agent_environment() -> dict[str, str]:
    """Provide a narrow environment to explicitly enabled unsandboxed adapters."""
    allowed = ("HOME", "LANG", "LC_ALL", "PATH", "TMPDIR")
    return {name: os.environ[name] for name in allowed if name in os.environ}


def _adapter_summary(argv: list[str]) -> dict[str, Any]:
    """Record adapter shape without persisting literal arguments or secrets."""
    return {"executable": argv[0], "argument_count": len(argv) - 1}


def _assert_finalized_workspace(state: dict[str, Any], evidence: dict[str, Any]) -> None:
    """Reject reviewer-side workspace mutations after deterministic acceptance."""
    workspace = Path(state["workspace"])
    if git_status(workspace):
        raise ValueError("reviewer modified the workspace after deterministic acceptance")
    head = run_git(["rev-parse", "HEAD"], cwd=workspace).stdout.strip()
    if head != evidence.get("finalized_commit"):
        raise ValueError("workspace HEAD changed after deterministic acceptance")


def _trusted_control_snapshot(run_dir: Path) -> dict[str, str]:
    """Hash trusted files that a qualitative reviewer must not modify."""
    paths = [
        run_dir.parent / ".boardflowbench.key",
        run_dir / "run.json",
        run_dir / "seed-score.json",
        *sorted((run_dir / "stages").glob("*/score.json")),
        *sorted((run_dir / "stages").glob("*/evidence.json")),
    ]
    return {
        str(path.resolve()): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths
        if path.exists()
    }


def _assert_trusted_control_unchanged(run_dir: Path, expected: dict[str, str]) -> None:
    """Reject reviewer-side mutations to signed state or deterministic evidence."""
    if _trusted_control_snapshot(run_dir) != expected:
        raise ValueError("reviewer modified trusted control-plane files after deterministic acceptance")
