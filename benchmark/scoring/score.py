"""Score observable repository state for a BoardFlowBench task."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from benchmark.scoring.board_consistency import check_board_consistency
from benchmark.scoring.handoff_check import check_handoff
from benchmark.scoring.hygiene import check_hygiene
from benchmark.scoring.scope_check import check_scope
from benchmark.scoring.task_loader import load_task, task_id


def score_task(repo: str | Path, task_path: str | Path) -> dict[str, Any]:
    """Run all minimal checks and return a score report."""
    root = Path(repo)
    task = load_task(task_path, root)
    tid = task_id(task)

    correctness = _score_correctness(root, task)
    hygiene = check_hygiene(root)
    scope_control = check_scope(root, task)
    changed_files = scope_control.get("details", {}).get("changed_files", [])
    handoff = check_handoff(root, task, changed_files)
    board_consistency = check_board_consistency(root, task)

    sections = {
        "correctness": correctness,
        "hygiene": hygiene,
        "scope_control": scope_control,
        "handoff": handoff,
        "board_consistency": board_consistency,
    }
    total = sum(int(section["score"]) for section in sections.values())

    violations: list[str] = []
    warnings: list[str] = []
    for name, section in sections.items():
        violations.extend(f"{name}: {item}" for item in section.get("violations", []))
        warnings.extend(f"{name}: {item}" for item in section.get("warnings", []))

    return {
        "task_id": tid,
        "total": total,
        "correctness": correctness,
        "hygiene": hygiene,
        "scope_control": scope_control,
        "handoff": handoff,
        "board_consistency": board_consistency,
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
    parser.add_argument("--task", required=True, help="Path to benchmark task YAML.")
    parser.add_argument("--repo", default=".", help="Repository root to score.")
    parser.add_argument("--output", required=True, help="Path for score JSON output.")
    args = parser.parse_args(argv)

    report = score_task(args.repo, args.task)
    write_score(report, args.output)
    print(f"wrote {args.output}")
    print(f"task_id={report['task_id']} total={report['total']}")
    return 0


def _score_correctness(root: Path, task: dict[str, Any]) -> dict[str, Any]:
    score = 0
    violations: list[str] = []
    warnings: list[str] = []
    details: dict[str, Any] = {}

    command_results = [_run_command(root, command) for command in _commands(task)]
    details["acceptance_commands"] = command_results

    if command_results and all(result["returncode"] == 0 for result in command_results):
        score += 20
    elif _expected_failure_captured(task, command_results):
        score += 20
        expected = task.get("expected_failing_test_initial_state", {})
        warnings.append(
            "task-specific acceptance command failed as documented: "
            + str(expected.get("test"))
        )
    else:
        violations.append("task-specific tests did not pass and no expected failure matched")

    regression_commands = task.get("regression_commands") or []
    if regression_commands:
        regression_results = [
            _run_command(root, command) for command in regression_commands
        ]
        details["regression_commands"] = regression_results
        if all(result["returncode"] == 0 for result in regression_results):
            score += 10
        else:
            violations.append("one or more regression commands failed")
    elif task.get("expected_failing_test_initial_state"):
        score += 10
        warnings.append("no regression_commands defined; expected initial failure is documented")
    else:
        violations.append("no regression_commands defined and no documented exception")

    if command_results:
        score += 10
    else:
        violations.append("no acceptance evidence exists because no commands were run")

    return {
        "score": score,
        "max": 40,
        "violations": violations,
        "warnings": warnings,
        "details": details,
    }


def _commands(task: dict[str, Any]) -> list[str]:
    commands = task.get("acceptance_commands") or []
    return [str(command) for command in commands]


def _run_command(root: Path, command: str) -> dict[str, Any]:
    result = subprocess.run(
        command,
        cwd=root,
        shell=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return {
        "command": command,
        "returncode": result.returncode,
        "stdout_tail": _tail(result.stdout),
        "stderr_tail": _tail(result.stderr),
    }


def _tail(text: str, limit: int = 4000) -> str:
    return text[-limit:]


def _expected_failure_captured(
    task: dict[str, Any], command_results: list[dict[str, Any]]
) -> bool:
    expected = task.get("expected_failing_test_initial_state")
    if not isinstance(expected, dict):
        return False
    expected_test = str(expected.get("test", ""))
    if not expected_test:
        return False
    haystack = "\n".join(
        result.get("stdout_tail", "") + "\n" + result.get("stderr_tail", "")
        for result in command_results
    )
    return expected_test in haystack or expected_test.split(".")[-1] in haystack


if __name__ == "__main__":
    raise SystemExit(main())
