"""Score observable repository state for a BoardFlowBench task."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from repo_manager_core.benchmark.commands import run_commands
from repo_manager_core.benchmark.oracle import run_oracle
from repo_manager_core.board.board_io import load_task, task_id
from repo_manager_core.board.board_validator import check_board_consistency
from repo_manager_core.board.handoff_writer import check_handoff
from repo_manager_core.board.hygiene import check_hygiene
from repo_manager_core.board.scope_check import check_scope

FULL_BOARD_CONDITIONS = {"boardflow_sequential", "full_boardflow"}


def score_task(
    repo: str | Path,
    task_path: str | Path,
    *,
    phase: str = "completion",
    condition: str = "full_boardflow",
    baseline: str | None = None,
    oracle_root: str | Path | None = None,
    target: str = "expense_lite",
    seed_commit: str | None = None,
    oracle_commit: str | None = None,
    handoff_schema: str | Path | None = None,
) -> dict[str, Any]:
    """Run applicable checks and return a condition-aware score report."""
    root = Path(repo)
    task = load_task(task_path, root)
    tid = task_id(task)
    if phase not in {"seed", "completion"}:
        raise ValueError(f"unsupported score phase: {phase}")

    correctness = (
        _score_seed(root, task, oracle_root=oracle_root, target=target, seed_commit=seed_commit, oracle_commit=oracle_commit)
        if phase == "seed"
        else _score_completion(root, task, oracle_root=oracle_root, target=target, seed_commit=seed_commit, oracle_commit=oracle_commit)
    )
    hygiene = check_hygiene(
        root,
        artifact_dir="artifacts" if (root / "artifacts").exists() else "repo_manager_report/artifacts",
        scratch_dir=".scratch" if (root / ".scratch").exists() else ".repo_manager/scratch",
        allowed_paths=[str(path) for path in task.get("allowed_paths", [])],
    )
    scope_control = check_scope(root, task, baseline=baseline)
    changed_files = scope_control.get("details", {}).get("changed_files", [])
    if phase == "completion" and condition in FULL_BOARD_CONDITIONS:
        handoff = check_handoff(root, task, changed_files, schema_path_override=handoff_schema)
        board_consistency = check_board_consistency(root, task)
        if board_consistency.get("details", {}).get("status") == "TODO":
            board_consistency["violations"].append(f"{tid} remains TODO during completion scoring")
    else:
        handoff = _not_applicable("structured JSON handoff is not part of this condition")
        board_consistency = _not_applicable("machine-readable board is not part of this condition")

    sections = {
        "correctness": correctness,
        "hygiene": hygiene,
        "scope_control": scope_control,
        "handoff": handoff,
        "board_consistency": board_consistency,
    }
    total = sum(int(section["score"]) for section in sections.values())
    applicable_max = sum(int(section["max"]) for section in sections.values())
    violations: list[str] = []
    warnings: list[str] = []
    for name, section in sections.items():
        violations.extend(f"{name}: {item}" for item in section.get("violations", []))
        warnings.extend(f"{name}: {item}" for item in section.get("warnings", []))

    return {
        "task_id": tid,
        "phase": phase,
        "condition": condition,
        "total": total,
        "applicable_max": applicable_max,
        "normalized_score": round((total / applicable_max) * 100, 2) if applicable_max else 0,
        "hard_gate_pass": not violations,
        **sections,
        "violations": violations,
        "warnings": warnings,
    }


def write_score(report: dict[str, Any], output: str | Path) -> None:
    """Write a score report as stable JSON."""
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True, help="Path to task YAML.")
    parser.add_argument("--repo", default=".", help="Repository root to score.")
    parser.add_argument("--output", required=True, help="Path for score JSON output.")
    parser.add_argument("--phase", choices=("seed", "completion"), default="completion")
    parser.add_argument("--condition", default="full_boardflow")
    parser.add_argument("--baseline", default=None, help="Sticker start commit for scope checks.")
    parser.add_argument("--oracle-root", default=None, help="External private oracle pack.")
    parser.add_argument("--target", default="expense_lite")
    parser.add_argument("--seed-commit", default=None, help="Expected fixed target seed SHA.")
    parser.add_argument("--oracle-commit", default=None, help="Expected fixed private oracle-pack SHA.")
    parser.add_argument("--fail-on-violations", action="store_true")
    args = parser.parse_args(argv)

    report = score_task(
        args.repo,
        args.task,
        phase=args.phase,
        condition=args.condition,
        baseline=args.baseline,
        oracle_root=args.oracle_root,
        target=args.target,
        seed_commit=args.seed_commit,
        oracle_commit=args.oracle_commit,
    )
    write_score(report, args.output)
    print(f"wrote {args.output}")
    print(f"task_id={report['task_id']} total={report['total']} gate_pass={report['hard_gate_pass']}")
    return 1 if args.fail_on_violations and not report["hard_gate_pass"] else 0


def _score_seed(
    root: Path,
    task: dict[str, Any],
    *,
    oracle_root: str | Path | None,
    target: str,
    seed_commit: str | None,
    oracle_commit: str | None,
) -> dict[str, Any]:
    expected = task.get("expected_failing_test_initial_state")
    violations: list[str] = []
    warnings: list[str] = []
    details: dict[str, Any] = {}
    score = 0
    maximum = 0
    if isinstance(expected, dict) and expected.get("command") and expected.get("test"):
        maximum += 1
        results = run_commands(root, [expected["command"]])
        details["expected_initial_failure"] = results
        haystack = "\n".join(item["stdout_tail"] + "\n" + item["stderr_tail"] for item in results)
        expected_test = str(expected["test"])
        if results[0]["returncode"] != 0 and (
            expected_test in haystack or expected_test.split(".")[-1] in haystack
        ):
            score += 1
        else:
            violations.append("documented initial failure was not reproduced")
    if oracle_root:
        maximum += 1
        oracle = run_oracle(
            oracle_root,
            target,
            task_id(task),
            root,
            phase="seed",
            expected_seed_commit=seed_commit,
            expected_oracle_commit=oracle_commit,
        )
        details["oracle"] = oracle
        if oracle["passed"]:
            score += 1
        else:
            violations.append("seed oracle did not pass")
    if maximum == 0:
        violations.append("seed validation has no configured checks")
    return _section(score, maximum, violations, warnings, details)


def _score_completion(
    root: Path,
    task: dict[str, Any],
    *,
    oracle_root: str | Path | None,
    target: str,
    seed_commit: str | None,
    oracle_commit: str | None,
) -> dict[str, Any]:
    violations: list[str] = []
    warnings: list[str] = []
    details: dict[str, Any] = {}
    score = 0
    maximum = 0

    score, maximum = _score_command_group(
        root, task.get("acceptance_commands") or [], "acceptance_commands", 20,
        score, maximum, violations, warnings, details,
    )
    score, maximum = _score_command_group(
        root, task.get("regression_commands") or [], "regression_commands", 10,
        score, maximum, violations, warnings, details,
    )
    if oracle_root:
        maximum += 20
        oracle = run_oracle(
            oracle_root,
            target,
            task_id(task),
            root,
            expected_seed_commit=seed_commit,
            expected_oracle_commit=oracle_commit,
        )
        details["oracle"] = oracle
        if oracle["passed"]:
            score += 20
        else:
            violations.append("completion oracle did not pass")
    else:
        warnings.append("no external oracle pack configured")
    if maximum == 0:
        violations.append("completion scoring has no configured checks")
    return _section(score, maximum, violations, warnings, details)


def _score_command_group(
    root: Path,
    commands: list[Any],
    label: str,
    weight: int,
    score: int,
    maximum: int,
    violations: list[str],
    warnings: list[str],
    details: dict[str, Any],
) -> tuple[int, int]:
    if not commands:
        warnings.append(f"no {label} defined")
        return score, maximum
    maximum += weight
    results = run_commands(root, commands)
    details[label] = results
    if all(result["returncode"] == 0 for result in results):
        score += weight
    else:
        violations.append(f"one or more {label} failed")
    return score, maximum


def _not_applicable(reason: str) -> dict[str, Any]:
    return {
        "score": 0,
        "max": 0,
        "applicable": False,
        "violations": [],
        "warnings": [reason],
        "details": {},
    }


def _section(
    score: int,
    maximum: int,
    violations: list[str],
    warnings: list[str],
    details: dict[str, Any],
) -> dict[str, Any]:
    return {
        "score": score,
        "max": maximum,
        "applicable": True,
        "violations": violations,
        "warnings": warnings,
        "details": details,
    }


if __name__ == "__main__":
    raise SystemExit(main())
