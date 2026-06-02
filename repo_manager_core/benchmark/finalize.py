"""Deterministic sticker finalization and acceptance evidence generation."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any

from repo_manager_core.benchmark.oracle import oracle_pack_commit
from repo_manager_core.benchmark.workspace import (
    commit_all,
    load_target,
    load_task_specs,
    normalize_condition,
    require_task,
    task_path,
)
from repo_manager_core.board.board_io import load_board, load_yaml, save_board
from repo_manager_core.board.board_sync import update_task_status
from tools.benchmark_scorer import score_task, write_score


def finalize_task(
    project_root: str | Path,
    workspace: str | Path,
    task_id: str,
    condition: str,
    oracle_root: str | Path,
    results_dir: str | Path,
    *,
    target: str = "expense_lite",
    owner: str = "agent",
    run_id: str | None = None,
    baseline: str | None = None,
) -> dict[str, Any]:
    """Run the blocking gate, persist evidence, and checkpoint an accepted stage."""
    project = Path(project_root).resolve()
    repo = Path(workspace).resolve()
    normalized = normalize_condition(condition)
    run = _load_run(repo) if normalized == "full_boardflow" else {}
    if normalized == "full_boardflow":
        if run.get("target") != target:
            raise ValueError("workspace target mirror differs from external control state")
        if run.get("assigned_task") != task_id:
            raise ValueError(f"workspace assigned task is {run.get('assigned_task')}, not {task_id}")
        baselines = run.get("stage_baselines") or {}
        if not isinstance(baselines, dict) or baselines.get(task_id) != baseline:
            raise ValueError("workspace baseline mirror differs from external control state")
    if not baseline:
        raise ValueError(f"no baseline commit recorded for {task_id}")

    manifest = load_target(project, target)
    task = require_task(load_task_specs(project, manifest), task_id)
    score = score_task(
        repo,
        task_path(project, manifest, task_id),
        phase="completion",
        condition=normalized,
        baseline=baseline,
        oracle_root=oracle_root,
        target=target,
        seed_commit=str(manifest["seed_commit"]),
        oracle_commit=str(manifest["oracle_commit"]),
        handoff_schema=project / ".board" / "handoff.schema.json",
    )
    stage_dir = _stage_dir(results_dir, run_id or repo.name, task_id)
    stage_dir.mkdir(parents=True, exist_ok=True)
    score_path = stage_dir / "score.json"
    write_score(score, score_path)
    if not score["hard_gate_pass"]:
        raise ValueError(f"finalize gate failed for {task_id}; see {stage_dir / 'score.json'}")

    evaluated_head = _head(repo)
    evidence = {
        "schema_version": 1,
        "task_id": task_id,
        "condition": normalized,
        "gate_pass": True,
        "seed_commit": str(manifest["seed_commit"]),
        "baseline_commit": baseline,
        "evaluated_head": evaluated_head,
        "oracle_pack_commit": oracle_pack_commit(oracle_root),
        "score_file": str(score_path),
        "score_sha256": _sha256(score_path),
        "changed_files": score["scope_control"]["details"].get("changed_files", []),
    }
    if normalized == "full_boardflow":
        evidence_path = repo / ".board" / "evidence" / f"{task_id}.json"
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(
            evidence_path,
            {
                "schema_version": 1,
                "kind": "workspace_mirror",
                "task_id": task_id,
                "condition": normalized,
                "gate_pass": True,
                "seed_commit": str(manifest["seed_commit"]),
                "baseline_commit": baseline,
                "evaluated_head": evaluated_head,
                "oracle_pack_commit": oracle_pack_commit(oracle_root),
            },
        )
        board = load_board(repo)
        board_task = _find_board_task(board, task_id)
        board_task["acceptance_evidence"] = str(evidence_path.relative_to(repo))
        handoffs = score["handoff"]["details"].get("handoff_files", [])
        board_task["current_handoff"] = handoffs[-1] if handoffs else None
        save_board(board, repo)
        update_task_status(repo, task_id, "DONE", owner=owner, completion_validated=True)
    finalized_commit = commit_all(repo, f"Finalize benchmark task {task_id}")
    evidence["finalized_commit"] = finalized_commit
    _write_json(stage_dir / "evidence.json", evidence)
    return evidence


def _load_run(repo: Path) -> dict[str, Any]:
    path = repo / ".board" / "run.yaml"
    if not path.exists():
        raise ValueError("workspace is missing .board/run.yaml")
    run = load_yaml(path)
    if not isinstance(run, dict):
        raise ValueError(".board/run.yaml must contain a mapping")
    return run


def _find_board_task(board: dict[str, Any], task_id: str) -> dict[str, Any]:
    for task in board.get("tasks", []):
        if isinstance(task, dict) and task.get("id") == task_id:
            return task
    raise ValueError(f"task {task_id} is missing from workspace board")


def _stage_dir(results_dir: str | Path, run_id: str, task_id: str) -> Path:
    return Path(results_dir).resolve() / run_id / "stages" / task_id


def _head(repo: Path) -> str:
    from repo_manager_core.benchmark.workspace import run_git
    return run_git(["rev-parse", "HEAD"], cwd=repo).stdout.strip()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
