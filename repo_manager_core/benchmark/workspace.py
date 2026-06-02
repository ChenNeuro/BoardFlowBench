"""Create isolated benchmark workspaces from standalone target repositories."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

from repo_manager_core.board.board_io import _dump_yaml, load_board, load_yaml, save_board
from repo_manager_core.board.board_sync import check_board_views

SUPPORTED_CONDITIONS = {"boardflow_sequential", "no_board_baseline"}


def initialize_workspace(
    project_root: str | Path,
    target: str,
    condition: str,
    task_id: str,
    workspace: str | Path,
    *,
    source_repo: str | Path | None = None,
) -> dict[str, str]:
    """Clone a fixed target seed and optionally inject run-local BoardFlow state."""
    root = Path(project_root).resolve()
    dest = Path(workspace).resolve()
    if dest.exists():
        raise ValueError(f"workspace already exists: {dest}")
    if condition not in SUPPORTED_CONDITIONS:
        raise ValueError(f"unsupported condition: {condition}")

    manifest = _load_target(root, target)
    specs = _load_task_specs(root, manifest)
    task = _require_task(specs, task_id)
    source = str(source_repo or manifest["repo_url"])
    seed_commit = str(manifest["seed_commit"])

    dest.parent.mkdir(parents=True, exist_ok=True)
    _run(["git", "clone", "--quiet", source, str(dest)], cwd=root)

    if condition == "boardflow_sequential":
        _run(["git", "switch", "--quiet", "--create", "boardflow-run", seed_commit], cwd=dest)
        _inject_boardflow(root, dest, manifest, specs, task)
        baseline = _commit_all(dest, f"Initialize BoardFlow workspace for {task_id}")
    else:
        _run(["git", "switch", "--quiet", "--detach", seed_commit], cwd=dest)
        baseline = seed_commit

    return {
        "workspace": str(dest),
        "condition": condition,
        "target": target,
        "task_id": task_id,
        "seed_commit": seed_commit,
        "baseline_commit": baseline,
        "task_spec": str(_task_path(root, manifest, task_id)),
    }


def activate_task(
    project_root: str | Path,
    workspace: str | Path,
    task_id: str,
) -> dict[str, str]:
    """Expose one assigned task after its dependencies are complete."""
    root = Path(project_root).resolve()
    dest = Path(workspace).resolve()
    if not dest.is_dir():
        raise ValueError(f"workspace does not exist: {dest}")

    run_path = dest / ".board" / "run.yaml"
    if not run_path.exists():
        raise ValueError("workspace is not an initialized BoardFlow run")
    run = load_yaml(run_path)
    if not isinstance(run, dict):
        raise ValueError(".board/run.yaml must contain a mapping")

    manifest = _load_target(root, str(run.get("target", "")))
    specs = _load_task_specs(root, manifest)
    task = _require_task(specs, task_id)
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
    incomplete = [
        dep
        for dep in task.get("dependencies", []) or []
        if board_tasks.get(str(dep), {}).get("status") != "DONE"
    ]
    if incomplete:
        raise ValueError("task dependencies are not DONE: " + ", ".join(str(dep) for dep in incomplete))

    shutil.copyfile(_task_path(root, manifest, task_id), dest / ".board" / "assigned_task.yaml")
    run["assigned_task"] = task_id
    _write_yaml(run_path, run)
    baseline = _commit_all(dest, f"Activate benchmark task {task_id}")
    return {
        "workspace": str(dest),
        "task_id": task_id,
        "baseline_commit": baseline,
    }


def _inject_boardflow(
    project_root: Path,
    workspace: Path,
    manifest: dict[str, Any],
    specs: list[dict[str, Any]],
    task: dict[str, Any],
) -> None:
    template_root = project_root / "benchmark" / "templates" / "boardflow"
    shutil.copyfile(template_root / "AGENTS.md", workspace / "AGENTS.md")
    shutil.copyfile(template_root / "AI_CONTRACT.md", workspace / "AI_CONTRACT.md")
    board_dir = workspace / ".board"
    (board_dir / "handoffs").mkdir(parents=True)
    shutil.copyfile(project_root / ".board" / "handoff.schema.json", board_dir / "handoff.schema.json")

    tasks = [
        {
            "id": str(spec["task_id"]),
            "title": str(spec["title"]),
            "status": "TODO",
            "owner": "unassigned",
            "dependencies": list(spec.get("dependencies", []) or []),
            "current_handoff": None,
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
    (workspace / "PROJECT_BOARD.md").write_text(_render_project_board(board), encoding="utf-8")
    shutil.copyfile(
        _task_path(project_root, manifest, str(task["task_id"])),
        board_dir / "assigned_task.yaml",
    )
    _write_yaml(
        board_dir / "run.yaml",
        {
            "schema_version": 1,
            "target": str(manifest["id"]),
            "condition": "boardflow_sequential",
            "seed_commit": str(manifest["seed_commit"]),
            "assigned_task": str(task["task_id"]),
        },
    )


def _load_target(project_root: Path, target: str) -> dict[str, Any]:
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


def _load_task_specs(project_root: Path, manifest: dict[str, Any]) -> list[dict[str, Any]]:
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


def _require_task(specs: list[dict[str, Any]], task_id: str) -> dict[str, Any]:
    for task in specs:
        if task.get("task_id") == task_id:
            return task
    raise ValueError(f"unknown benchmark task: {task_id}")


def _task_path(project_root: Path, manifest: dict[str, Any], task_id: str) -> Path:
    task_dir = project_root / str(manifest["task_directory"])
    matches = sorted(task_dir.glob(f"{task_id.lower()}_*.yaml"))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one task spec for {task_id}")
    return matches[0]


def _render_project_board(board: dict[str, Any]) -> str:
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


def _write_yaml(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_dump_yaml(value), encoding="utf-8")


def _commit_all(workspace: Path, message: str) -> str:
    _run(["git", "config", "user.name", "BoardFlowBench"], cwd=workspace)
    _run(["git", "config", "user.email", "boardflowbench@example.invalid"], cwd=workspace)
    _run(["git", "add", "-A"], cwd=workspace)
    _run(["git", "commit", "--quiet", "-m", message], cwd=workspace)
    return _run(["git", "rev-parse", "HEAD"], cwd=workspace).stdout.strip()


def _run(command: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise ValueError(f"command failed ({' '.join(command)}): {detail}")
    return result
