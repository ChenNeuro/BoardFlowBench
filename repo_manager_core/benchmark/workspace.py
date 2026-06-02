"""Create isolated benchmark workspaces from standalone target repositories."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

from repo_manager_core.board.board_io import _dump_yaml, load_board, load_yaml, save_board
from repo_manager_core.board.board_sync import check_board_views
from repo_manager_core.board.evidence import validate_acceptance_evidence
from repo_manager_core.board.handoff_writer import check_handoff

SUPPORTED_CONDITIONS = {
    "no_board_baseline",
    "native_instructions",
    "native_docs_handoff",
    "full_boardflow",
    "boardflow_sequential",
}
CONDITION_ALIASES = {"boardflow_sequential": "full_boardflow"}
NATIVE_INSTRUCTION_FILES = {
    "claude": "CLAUDE.md",
    "codex": "AGENTS.md",
    "cursor": "AGENTS.md",
    "gemini": "GEMINI.md",
}


def initialize_workspace(
    project_root: str | Path,
    target: str,
    condition: str,
    task_id: str,
    workspace: str | Path,
    *,
    source_repo: str | Path | None = None,
    agent_profile: str = "codex",
) -> dict[str, str]:
    """Clone a fixed target seed and inject only condition-owned artifacts."""
    root = Path(project_root).resolve()
    dest = Path(workspace).resolve()
    if dest.exists():
        raise ValueError(f"workspace already exists: {dest}")
    normalized = normalize_condition(condition)
    manifest = load_target(root, target)
    specs = load_task_specs(root, manifest)
    task = require_task(specs, task_id)
    source = str(source_repo or manifest["repo_url"])
    seed_commit = str(manifest["seed_commit"])

    dest.parent.mkdir(parents=True, exist_ok=True)
    run_git(["clone", "--quiet", source, str(dest)], cwd=root)
    if normalized == "no_board_baseline":
        run_git(["switch", "--quiet", "--detach", seed_commit], cwd=dest)
        baseline = seed_commit
    else:
        run_git(["switch", "--quiet", "--create", f"{normalized}-run", seed_commit], cwd=dest)
        if normalized == "native_instructions":
            inject_native_instructions(root, dest, agent_profile)
        elif normalized == "native_docs_handoff":
            inject_native_instructions(root, dest, agent_profile)
            inject_native_docs(dest, specs)
        else:
            inject_boardflow(root, dest, manifest, specs, task)
        baseline = commit_all(dest, f"Initialize {normalized} workspace for {task_id}")
        if normalized == "full_boardflow":
            record_stage_baseline(dest, task_id, baseline)

    return {
        "workspace": str(dest),
        "condition": normalized,
        "target": target,
        "task_id": task_id,
        "seed_commit": seed_commit,
        "baseline_commit": baseline,
        "task_spec": str(task_path(root, manifest, task_id)),
    }


def activate_task(
    project_root: str | Path,
    workspace: str | Path,
    task_id: str,
) -> dict[str, str]:
    """Expose one full-BoardFlow task after deterministic dependency gates pass."""
    root = Path(project_root).resolve()
    dest = Path(workspace).resolve()
    if not dest.is_dir():
        raise ValueError(f"workspace does not exist: {dest}")
    if git_status(dest):
        raise ValueError("workspace must be clean before activating another task")

    run_path = dest / ".board" / "run.yaml"
    if not run_path.exists():
        raise ValueError("workspace is not an initialized full BoardFlow run")
    run = load_yaml(run_path)
    if not isinstance(run, dict) or normalize_condition(str(run.get("condition", ""))) != "full_boardflow":
        raise ValueError("workspace is not an initialized full BoardFlow run")

    manifest = load_target(root, str(run.get("target", "")))
    specs = load_task_specs(root, manifest)
    task = require_task(specs, task_id)
    board = load_board(dest)
    violations = check_board_views(dest, board)
    if violations:
        raise ValueError("taskboard views are inconsistent: " + "; ".join(violations))
    board_tasks = {
        str(item.get("id")): item
        for item in board.get("tasks", [])
        if isinstance(item, dict) and item.get("id")
    }
    if task_id not in board_tasks:
        raise ValueError(f"task {task_id} is missing from workspace board")

    dependency_violations = []
    for dep in task.get("dependencies", []) or []:
        board_task = board_tasks.get(str(dep), {})
        if board_task.get("status") != "DONE":
            dependency_violations.append(f"{dep} is not DONE")
            continue
        dependency_violations.extend(validate_acceptance_evidence(dest, board_task))
        dep_spec = require_task(specs, str(dep))
        handoff_task = dict(dep_spec)
        handoff_task["handoff_required"] = True
        dependency_violations.extend(check_handoff(dest, handoff_task).get("violations", []))
    if dependency_violations:
        raise ValueError("task dependencies are not accepted: " + "; ".join(dependency_violations))

    shutil.copyfile(task_path(root, manifest, task_id), dest / ".board" / "assigned_task.yaml")
    run["assigned_task"] = task_id
    write_yaml(run_path, run)
    baseline = commit_all(dest, f"Activate benchmark task {task_id}")
    record_stage_baseline(dest, task_id, baseline)
    return {
        "workspace": str(dest),
        "task_id": task_id,
        "baseline_commit": baseline,
    }


def inject_boardflow(
    project_root: Path,
    workspace: Path,
    manifest: dict[str, Any],
    specs: list[dict[str, Any]],
    task: dict[str, Any],
) -> None:
    """Inject the full BoardFlow protocol into a demo clone."""
    template_root = project_root / "benchmark" / "templates" / "boardflow"
    shutil.copyfile(template_root / "AGENTS.md", workspace / "AGENTS.md")
    shutil.copyfile(template_root / "AI_CONTRACT.md", workspace / "AI_CONTRACT.md")
    board_dir = workspace / ".board"
    (board_dir / "handoffs").mkdir(parents=True)
    (board_dir / "evidence").mkdir()
    shutil.copyfile(project_root / ".board" / "handoff.schema.json", board_dir / "handoff.schema.json")
    tasks = [
        {
            "id": str(spec["task_id"]),
            "title": str(spec["title"]),
            "status": "TODO",
            "owner": "unassigned",
            "dependencies": list(spec.get("dependencies", []) or []),
            "current_handoff": None,
            "acceptance_evidence": None,
            "require_gate_evidence": True,
            "notes": "Benchmark backlog sticker.",
        }
        for spec in specs
    ]
    board = {
        "schema_version": 1,
        "project": str(manifest["title"]),
        "current_milestone": {
            "id": "BM1",
            "title": "Expense Lite sequential handoff",
            "status": "IN_PROGRESS",
            "goal": "Evaluate sequential coding-agent handoff against an isolated demo workspace.",
        },
        "status_values": ["TODO", "IN_PROGRESS", "BLOCKED", "READY_FOR_REVIEW", "DONE"],
        "tasks": tasks,
    }
    save_board(board, workspace)
    (workspace / "PROJECT_BOARD.md").write_text(render_project_board(board), encoding="utf-8")
    shutil.copyfile(task_path(project_root, manifest, str(task["task_id"])), board_dir / "assigned_task.yaml")
    write_yaml(
        board_dir / "run.yaml",
        {
            "schema_version": 1,
            "target": str(manifest["id"]),
            "condition": "full_boardflow",
            "seed_commit": str(manifest["seed_commit"]),
            "assigned_task": str(task["task_id"]),
            "stage_baselines": {},
        },
    )


def inject_native_instructions(project_root: Path, workspace: Path, agent_profile: str) -> None:
    """Inject only the agent runtime's native repository instruction file."""
    filename = NATIVE_INSTRUCTION_FILES.get(agent_profile)
    if not filename:
        raise ValueError(f"unsupported agent profile: {agent_profile}")
    template = project_root / "benchmark" / "templates" / "native" / "INSTRUCTIONS.md"
    shutil.copyfile(template, workspace / filename)


def inject_native_docs(workspace: Path, specs: list[dict[str, Any]]) -> None:
    """Inject Markdown-only coordination artifacts without machine-readable state."""
    lines = [
        "# PROJECT_BOARD.md",
        "",
        "Human-readable benchmark backlog. Keep this file current between agents.",
        "",
        "| Task | Title | Dependencies | Status |",
        "| --- | --- | --- | --- |",
    ]
    for task in specs:
        dependencies = ", ".join(task.get("dependencies", []) or []) or "none"
        lines.append(f"| {task['task_id']} | {task['title']} | {dependencies} | TODO |")
    (workspace / "PROJECT_BOARD.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (workspace / "HANDOFF.md").write_text(
        "# HANDOFF.md\n\nRecord completed work, validation, risks, and the next step before transfer.\n",
        encoding="utf-8",
    )


def record_stage_baseline(workspace: Path, task_id: str, baseline: str) -> None:
    """Record the stage baseline while keeping the workspace clean."""
    run_path = workspace / ".board" / "run.yaml"
    run = load_yaml(run_path)
    if not isinstance(run, dict):
        raise ValueError(".board/run.yaml must contain a mapping")
    baselines = run.setdefault("stage_baselines", {})
    if not isinstance(baselines, dict):
        raise ValueError(".board/run.yaml stage_baselines must contain a mapping")
    baselines[task_id] = baseline
    write_yaml(run_path, run)
    commit_all(workspace, f"Record {task_id} baseline")


def load_target(project_root: Path, target: str) -> dict[str, Any]:
    path = project_root / "benchmark" / "targets" / f"{target}.yaml"
    if not path.exists():
        raise ValueError(f"unknown benchmark target: {target}")
    manifest = load_yaml(path)
    if not isinstance(manifest, dict):
        raise ValueError(f"target manifest must contain a mapping: {path}")
    for field in ("id", "title", "repo_url", "seed_commit", "task_directory"):
        if not manifest.get(field):
            raise ValueError(f"target manifest is missing {field}: {path}")
    return manifest


def load_task_specs(project_root: Path, manifest: dict[str, Any]) -> list[dict[str, Any]]:
    task_dir = project_root / str(manifest["task_directory"])
    specs = []
    for path in sorted(task_dir.glob("*.yaml")):
        task = load_yaml(path)
        if not isinstance(task, dict) or not task.get("task_id"):
            raise ValueError(f"task spec must contain task_id: {path}")
        specs.append(task)
    if not specs:
        raise ValueError(f"no benchmark tasks found under {task_dir}")
    return specs


def require_task(specs: list[dict[str, Any]], task_id: str) -> dict[str, Any]:
    for task in specs:
        if task.get("task_id") == task_id:
            return task
    raise ValueError(f"unknown benchmark task: {task_id}")


def task_path(project_root: Path, manifest: dict[str, Any], task_id: str) -> Path:
    task_dir = project_root / str(manifest["task_directory"])
    matches = sorted(task_dir.glob(f"{task_id.lower()}_*.yaml"))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one task spec for {task_id}")
    return matches[0]


def normalize_condition(condition: str) -> str:
    """Normalize compatibility aliases while rejecting unknown conditions."""
    if condition not in SUPPORTED_CONDITIONS:
        raise ValueError(f"unsupported condition: {condition}")
    return CONDITION_ALIASES.get(condition, condition)


def render_project_board(board: dict[str, Any]) -> str:
    milestone = board["current_milestone"]
    lines = [
        "# PROJECT_BOARD.md",
        "",
        "Human-readable board for this isolated benchmark workspace.",
        "",
        "## Current Milestone",
        "",
        f"Milestone: {milestone['id']} - {milestone['title']}",
        "",
        f"Goal: {milestone['goal']}",
        "",
        f"Status: {milestone['status']}",
        "",
        "## Task Board",
        "",
        "| Task | Title | Status | Owner | Dependencies | Notes |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for task in board["tasks"]:
        dependencies = ", ".join(task.get("dependencies", [])) or "none"
        lines.append(
            f"| {task['id']} | {task['title']} | {task['status']} | {task['owner']} | "
            f"{dependencies} | {task['notes']} |"
        )
    return "\n".join(lines) + "\n"


def write_yaml(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_dump_yaml(value), encoding="utf-8")


def commit_all(workspace: Path, message: str) -> str:
    """Commit workspace state when needed and return the resulting HEAD."""
    run_git(["config", "user.name", "BoardFlowBench"], cwd=workspace)
    run_git(["config", "user.email", "boardflowbench@example.invalid"], cwd=workspace)
    if git_status(workspace):
        run_git(["add", "-A"], cwd=workspace)
        run_git(["commit", "--quiet", "-m", message], cwd=workspace)
    return run_git(["rev-parse", "HEAD"], cwd=workspace).stdout.strip()


def git_status(workspace: Path) -> str:
    return run_git(["status", "--porcelain", "--untracked-files=all"], cwd=workspace).stdout.strip()


def run_git(arguments: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *arguments],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise ValueError(f"command failed (git {' '.join(arguments)}): {detail}")
    return result
