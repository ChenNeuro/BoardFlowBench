#!/usr/bin/env python3
"""Run a small Ollama/Qwen plain-vs-RepoFlow-skill pilot on Expense Lite."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MODEL = "qwen3.5:9b"
TASKS = ("B001", "B002")
VARIANTS = ("plain", "repoflow_skill")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--source-repo", default=str((ROOT.parent / "ExpenseLiteBenchDemo").resolve()))
    parser.add_argument("--results-dir", default=None)
    parser.add_argument("--tasks", nargs="+", choices=TASKS, default=["B001", "B002"])
    parser.add_argument("--variant", choices=VARIANTS, action="append", default=None)
    parser.add_argument("--max-repairs", type=int, default=1)
    parser.add_argument("--max-format-retries", type=int, default=2)
    args = parser.parse_args()

    variants = args.variant or list(VARIANTS)
    results_dir = Path(args.results_dir).resolve() if args.results_dir else Path(tempfile.mkdtemp(prefix="repoflow-ollama-skill-pilot-"))
    results_dir.mkdir(parents=True, exist_ok=True)
    source_repo = Path(args.source_repo).resolve()
    if not source_repo.is_dir():
        print(f"missing source repo: {source_repo}", file=sys.stderr)
        return 2

    summary: dict[str, Any] = {
        "model": args.model,
        "source_repo": str(source_repo),
        "results_dir": str(results_dir),
        "tasks": args.tasks,
        "variants": {},
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    for variant in variants:
        run = run_variant(
            args.model,
            source_repo,
            results_dir,
            variant,
            args.tasks,
            max_repairs=args.max_repairs,
            max_format_retries=args.max_format_retries,
        )
        summary["variants"][variant] = run
        write_json(results_dir / "summary.json", summary)
    summary["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    write_json(results_dir / "summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def run_variant(
    model: str,
    source_repo: Path,
    results_dir: Path,
    variant: str,
    tasks: list[str],
    *,
    max_repairs: int,
    max_format_retries: int,
) -> dict[str, Any]:
    workspace = results_dir / f"{variant}-workspace"
    if workspace.exists():
        shutil.rmtree(workspace)
    run(["git", "clone", "--quiet", str(source_repo), str(workspace)], cwd=ROOT)
    run(["git", "switch", "--quiet", "--detach", "30ce6f0d76e2338e56d599fd2beb6fe954b96452"], cwd=workspace)
    run(["git", "config", "user.name", "RepoFlow Pilot"], cwd=workspace)
    run(["git", "config", "user.email", "repoflow-pilot@example.invalid"], cwd=workspace)

    run_record: dict[str, Any] = {"workspace": str(workspace), "tasks": {}, "status": "running"}
    for task_id in tasks:
        if task_id == "B002" and not task_passed(run_record, "B001"):
            run_record["tasks"][task_id] = {"status": "skipped", "reason": "B001 did not pass"}
            break
        task_record = run_task(
            model,
            workspace,
            results_dir,
            variant,
            task_id,
            max_repairs=max_repairs,
            max_format_retries=max_format_retries,
        )
        run_record["tasks"][task_id] = task_record
        if task_record["status"] != "passed":
            break
    run_record["status"] = "complete"
    return run_record


def task_passed(run_record: dict[str, Any], task_id: str) -> bool:
    task = run_record.get("tasks", {}).get(task_id)
    return isinstance(task, dict) and task.get("status") == "passed"


def run_task(
    model: str,
    workspace: Path,
    results_dir: Path,
    variant: str,
    task_id: str,
    *,
    max_repairs: int,
    max_format_retries: int,
) -> dict[str, Any]:
    task_yaml = task_path(task_id).read_text(encoding="utf-8")
    prompt = build_prompt(workspace, variant, task_id, task_yaml)
    prompt_path = results_dir / f"{variant}-{task_id}-prompt.md"
    prompt_path.write_text(prompt, encoding="utf-8")

    payload, response_path, format_attempts, format_error = request_payload(
        model,
        prompt,
        results_dir,
        variant,
        task_id,
        phase="initial",
        max_format_retries=max_format_retries,
    )
    if payload is None:
        return {
            "status": "failed",
            "task_id": task_id,
            "prompt_file": str(prompt_path),
            "response_file": str(response_path) if response_path else None,
            "changed_files": git_changed_files(workspace),
            "commands": [],
            "attempts": format_attempts,
            "commit": None,
            "skill_invocation": None,
            "notes": f"model response rejected before editing: {format_error}",
        }

    commands = validation_commands(task_id)
    attempts: list[dict[str, Any]] = format_attempts
    try:
        apply_payload(workspace, payload, task_id)
    except ValueError as exc:
        command_results = [apply_error_result(str(exc))]
        attempts.append({"kind": "initial", "apply_error": str(exc), "commands": command_results})
    else:
        command_results = [run_shell(command, cwd=workspace) for command in commands]
        attempts.append({"kind": "initial", "commands": command_results})
    repairs_used = 0
    while repairs_used < max_repairs and any(item["returncode"] != 0 for item in command_results):
        repairs_used += 1
        repair_prompt = build_repair_prompt(workspace, variant, task_id, command_results)
        repair_payload, _, repair_format_attempts, repair_error = request_payload(
            model,
            repair_prompt,
            results_dir,
            variant,
            task_id,
            phase=f"repair-{repairs_used}",
            max_format_retries=max_format_retries,
        )
        attempts.extend(repair_format_attempts)
        if repair_payload is None:
            attempts.append({"kind": f"repair-{repairs_used}", "format_error": repair_error, "commands": command_results})
            break
        try:
            apply_payload(workspace, repair_payload, task_id)
        except ValueError as exc:
            command_results = [apply_error_result(str(exc))]
            attempts.append({"kind": f"repair-{repairs_used}", "apply_error": str(exc), "commands": command_results})
            continue
        payload = repair_payload
        command_results = [run_shell(command, cwd=workspace) for command in commands]
        attempts.append({"kind": f"repair-{repairs_used}", "commands": command_results})
    changed = git_changed_files(workspace)
    status = "passed" if all(item["returncode"] == 0 for item in command_results) else "failed"
    if variant == "repoflow_skill" and payload.get("skill_invocation") != "repoflow-task-agent":
        status = "failed"
    commit = None
    if changed:
        run(["git", "add", "-A"], cwd=workspace)
        commit_result = run(["git", "commit", "--quiet", "-m", f"{variant} {task_id}"], cwd=workspace, check=False)
        if commit_result.returncode == 0:
            commit = run(["git", "rev-parse", "HEAD"], cwd=workspace).stdout.strip()

    return {
        "status": status,
        "task_id": task_id,
        "prompt_file": str(prompt_path),
        "response_file": str(response_path),
        "changed_files": changed,
        "commands": command_results,
        "attempts": attempts,
        "commit": commit,
        "skill_invocation": payload.get("skill_invocation"),
        "notes": payload.get("notes"),
    }


def build_prompt(workspace: Path, variant: str, task_id: str, task_yaml: str) -> str:
    files = task_files(workspace, task_id)
    skill = ""
    if variant == "repoflow_skill":
        skill = (ROOT / "skills" / "repoflow-task-agent" / "SKILL.md").read_text(encoding="utf-8")
    file_blocks = "\n\n".join(
        f"### {path}\n```python\n{(workspace / path).read_text(encoding='utf-8')}\n```"
        for path in files
        if (workspace / path).exists()
    )
    return f"""You are a local coding agent editing an Expense Lite workspace.

Return a single JSON object only. Do not use Markdown fences.

Required JSON shape:
{{
  "skill_invocation": "{'repoflow-task-agent' if variant == 'repoflow_skill' else 'none'}",
  "files": [
    {{"path": "relative/path.py", "content": "complete file content"}}
  ],
  "notes": "short summary"
}}

Rules:
- Edit only files needed for {task_id}.
- Return complete file content for every changed file.
- Do not create data fixtures, output folders, caches, or scratch files.
- Keep imports valid and use only the Python standard library.
- If adding tests, keep them in existing test files.
- `files[*].path` must match the allowed path list exactly, except allowed prefixes.
- A response that mentions any other path is rejected before tests run.

{allowed_paths_block(task_id)}

{"Required skill packet, apply before editing:\n" + skill if skill else ""}

Assigned task:
```yaml
{task_yaml}
```

Current relevant files:
{file_blocks}
"""


def build_repair_prompt(workspace: Path, variant: str, task_id: str, command_results: list[dict[str, Any]]) -> str:
    task_yaml = task_path(task_id).read_text(encoding="utf-8")
    diagnostics = json.dumps(command_results, indent=2)
    skill = ""
    if variant == "repoflow_skill":
        skill = (ROOT / "skills" / "repoflow-task-agent" / "SKILL.md").read_text(encoding="utf-8")
    skill_block = f"Required skill packet, apply before editing:\n{skill}" if skill else ""
    file_blocks = "\n\n".join(
        f"### {path}\n```python\n{(workspace / path).read_text(encoding='utf-8')}\n```"
        for path in task_files(workspace, task_id)
        if (workspace / path).exists()
    )
    return f"""You are repairing a failed local coding-agent attempt.

Return a single JSON object only. Do not use Markdown fences.

Required JSON shape:
{{
  "skill_invocation": "{'repoflow-task-agent' if variant == 'repoflow_skill' else 'none'}",
  "files": [
    {{"path": "relative/path.py", "content": "complete file content"}}
  ],
  "notes": "short repair summary"
}}

Fix only the validation failures below. Keep changes inside allowed task files.

{allowed_paths_block(task_id)}

{skill_block}

Assigned task:
```yaml
{task_yaml}
```

Validation failures:
```json
{diagnostics}
```

Current relevant files:
{file_blocks}
"""


def build_format_regeneration_prompt(original_prompt: str, task_id: str, error: str) -> str:
    return f"""Your previous response was rejected before any files were written.

Rejection:
{error}

Return a corrected single JSON object only. Do not use Markdown fences.

Hard boundary:
{allowed_paths_block(task_id)}

If a previous response included a disallowed path, omit that file completely. Do not rename it, export it, or replace it with another unlisted path.

Original request:
{original_prompt}
"""


def task_files(workspace: Path, task_id: str) -> list[str]:
    common = ["src/expense_lite/parser.py", "src/expense_lite/validator.py", "tests/test_parser.py", "tests/test_validator.py"]
    if task_id == "B001":
        return common
    return common


def task_path(task_id: str) -> Path:
    matches = sorted((ROOT / "benchmark" / "tasks" / "expense_lite").glob(f"{task_id.lower()}_*.yaml"))
    if len(matches) != 1:
        raise RuntimeError(f"expected one task file for {task_id}")
    return matches[0]


def validation_commands(task_id: str) -> list[str]:
    if os.name == "nt":
        commands = [
            "python -m unittest discover -s tests -p test_parser.py",
            "python -m unittest discover -s tests -p test_validator.py",
        ]
        if task_id == "B002":
            commands.append("__B002_CSV_SMOKE__")
        return commands
    commands = [
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_parser.py'",
        "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_validator.py'",
    ]
    if task_id == "B002":
        commands.append("__B002_CSV_SMOKE__")
    return commands


def request_payload(
    model: str,
    prompt: str,
    results_dir: Path,
    variant: str,
    task_id: str,
    *,
    phase: str,
    max_format_retries: int,
) -> tuple[dict[str, Any] | None, str | None, list[dict[str, Any]], str | None]:
    attempts: list[dict[str, Any]] = []
    current_prompt = prompt
    response_path: Path | None = None
    last_error: str | None = None
    for retry in range(max_format_retries + 1):
        label = phase if retry == 0 else f"{phase}-format-{retry}"
        response = ollama_generate(model, current_prompt)
        response_path = results_dir / f"{variant}-{task_id}-{label}-response.json"
        write_json(response_path, response)
        attempt: dict[str, Any] = {"kind": label, "response_file": str(response_path)}
        try:
            payload = parse_json_response(str(response.get("response", "")))
        except (json.JSONDecodeError, ValueError) as exc:
            last_error = f"invalid JSON: {exc}"
            attempt["format_error"] = last_error
            attempts.append(attempt)
            current_prompt = build_format_regeneration_prompt(prompt, task_id, last_error)
            continue

        parsed_path = results_dir / f"{variant}-{task_id}-{label}-parsed.json"
        write_json(parsed_path, payload)
        attempt["parsed_file"] = str(parsed_path)
        validation_errors = validate_payload(payload, task_id, variant)
        if not validation_errors:
            attempt["format_status"] = "accepted"
            attempts.append(attempt)
            return payload, str(response_path), attempts, None
        last_error = "; ".join(validation_errors)
        attempt["format_error"] = last_error
        attempts.append(attempt)
        current_prompt = build_format_regeneration_prompt(prompt, task_id, last_error)
    return None, str(response_path) if response_path else None, attempts, last_error


def ollama_generate(model: str, prompt: str) -> dict[str, Any]:
    body = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "think": False,
            "format": "json",
            "options": {"temperature": 0, "num_ctx": 8192, "num_predict": 8192},
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        "http://127.0.0.1:11434/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(f"ollama request failed: {exc}") from exc


def parse_json_response(text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise
        parsed = json.loads(match.group(0))
    if not isinstance(parsed, dict):
        raise ValueError("model response must be a JSON object")
    return parsed


def apply_payload(workspace: Path, payload: dict[str, Any], task_id: str) -> None:
    validation_errors = validate_payload(payload, task_id, variant=None)
    if validation_errors:
        raise ValueError("; ".join(validation_errors))
    writes: list[tuple[str, str]] = []
    for item in payload["files"]:
        path = str(item.get("path", ""))
        content = item.get("content")
        writes.append((path, content))
    for path, content in writes:
        target = workspace / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


def validate_payload(payload: dict[str, Any], task_id: str, variant: str | None) -> list[str]:
    errors: list[str] = []
    if variant is not None:
        expected_skill = "repoflow-task-agent" if variant == "repoflow_skill" else "none"
        if payload.get("skill_invocation") != expected_skill:
            errors.append(f"skill_invocation must be {expected_skill!r}")
    allowed, allowed_prefixes = allowed_paths(task_id)
    files = payload.get("files")
    if not isinstance(files, list):
        return errors + ["payload.files must be a list"]
    for index, item in enumerate(files):
        if not isinstance(item, dict):
            errors.append(f"file entry {index} must be an object")
            continue
        path = str(item.get("path", ""))
        content = item.get("content")
        if not path:
            errors.append(f"file entry {index} has empty path")
        if "\\" in path or path.startswith("/") or re.match(r"^[A-Za-z]:", path) or ".." in path.split("/"):
            errors.append(f"model attempted unsafe path: {path}")
        elif path not in allowed and not any(path.startswith(prefix) for prefix in allowed_prefixes):
            errors.append(f"model attempted disallowed path: {path}")
        if not isinstance(content, str):
            errors.append(f"model content must be a string: {path}")
    return errors


def allowed_paths(task_id: str) -> tuple[set[str], tuple[str, ...]]:
    if task_id == "B001":
        return {"src/expense_lite/parser.py", "tests/test_parser.py", "PROJECT_BOARD.md", ".board/tasks.yaml"}, (".board/handoffs/",)
    if task_id == "B002":
        return {
            "src/expense_lite/parser.py",
            "src/expense_lite/validator.py",
            "tests/test_parser.py",
            "tests/test_validator.py",
            "PROJECT_BOARD.md",
            ".board/tasks.yaml",
        }, (".board/handoffs/",)
    raise ValueError(f"unsupported task: {task_id}")


def allowed_paths_block(task_id: str) -> str:
    allowed, prefixes = allowed_paths(task_id)
    exact = "\n".join(f"- {path}" for path in sorted(allowed))
    prefix_text = "\n".join(f"- {prefix}" for prefix in prefixes) if prefixes else "- none"
    return f"""Exact allowed file paths:
{exact}

Allowed path prefixes:
{prefix_text}

Do not include `src/expense_lite/__init__.py` unless it appears above."""


def git_changed_files(workspace: Path) -> list[str]:
    result = run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=workspace)
    changed = []
    for line in result.stdout.splitlines():
        if line:
            changed.append(line[3:])
    return changed


def run_shell(command: str, *, cwd: Path) -> dict[str, Any]:
    if command == "__B002_CSV_SMOKE__":
        return run_b002_csv_smoke(cwd)
    env = dict(os.environ)
    env["PYTHONPATH"] = "src"
    result = subprocess.run(
        command,
        cwd=cwd,
        shell=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=120,
        env=env,
    )
    return {
        "command": command,
        "returncode": result.returncode,
        "stdout_tail": result.stdout[-2000:],
        "stderr_tail": result.stderr[-2000:],
    }


def apply_error_result(message: str) -> dict[str, Any]:
    return {
        "command": "__APPLY_PAYLOAD__",
        "returncode": 1,
        "stdout_tail": "",
        "stderr_tail": message,
    }


def run_b002_csv_smoke(cwd: Path) -> dict[str, Any]:
    source = """
import os
import tempfile
from expense_lite import parser

good = tempfile.NamedTemporaryFile("w", delete=False, newline="")
try:
    good.write("date,description,category,amount\\n2026/01/03,Notebook,office,12.5\\n")
    good.close()
    records = parser.load_expenses_csv(good.name)
    assert records == [
        {"date": "2026-01-03", "description": "Notebook", "category": "office", "amount": 12.5}
    ], records
finally:
    try:
        os.unlink(good.name)
    except OSError:
        pass

bad = tempfile.NamedTemporaryFile("w", delete=False, newline="")
try:
    bad.write("date,amount\\n2026/01/03,12.5\\n")
    bad.close()
    try:
        parser.load_expenses_csv(bad.name)
    except ValueError as exc:
        assert "missing required CSV columns" in str(exc), str(exc)
    else:
        raise AssertionError("missing columns accepted")
finally:
    try:
        os.unlink(bad.name)
    except OSError:
        pass
"""
    env = dict(os.environ)
    env["PYTHONPATH"] = "src"
    executable = "python" if os.name == "nt" else "python3"
    result = subprocess.run(
        [executable, "-c", source],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=120,
        env=env,
    )
    return {
        "command": "__B002_CSV_SMOKE__",
        "returncode": result.returncode,
        "stdout_tail": result.stdout[-2000:],
        "stderr_tail": result.stderr[-2000:],
    }


def run(arguments: list[str], *, cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(arguments, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if check and result.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(arguments)}\n{result.stderr or result.stdout}")
    return result


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
