#!/usr/bin/env python3
"""Run a non-official SWE-bench Lite patch smoke with a local Ollama model."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_MODEL = "qwen3.5:9b"
DEFAULT_INSTANCE = "astropy__astropy-12907"
DEFAULT_CONTEXT_FILES = (
    "astropy/modeling/separable.py",
    "astropy/modeling/tests/test_separable.py",
)
DEFAULT_EDITABLE_FILES = ("astropy/modeling/separable.py",)
VARIANTS = ("plain", "repoflow_skill")
BLOCKED_PATH_PARTS = {"gold_patch.diff", "test_patch.diff", "oracles", "oracle"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, help="Prepared agent workspace used as an immutable template.")
    parser.add_argument("--results-dir", required=True)
    parser.add_argument("--control-dir", help="Evaluator-only directory containing test_patch.diff.")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--instance-id", default=DEFAULT_INSTANCE)
    parser.add_argument("--variant", action="append", choices=VARIANTS, dest="variants")
    parser.add_argument("--context-file", action="append", dest="context_files")
    parser.add_argument("--editable-file", action="append", dest="editable_files")
    parser.add_argument("--max-format-retries", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--think", action="store_true", help="Enable model reasoning when supported by Ollama.")
    parser.add_argument("--analysis-first", action="store_true", help="Run a separate investigation pass before editing.")
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    results_dir = Path(args.results_dir).resolve()
    control_dir = Path(args.control_dir).resolve() if args.control_dir else None
    variants = tuple(args.variants or VARIANTS)
    context_files = tuple(args.context_files or DEFAULT_CONTEXT_FILES)
    editable_files = tuple(args.editable_files or DEFAULT_EDITABLE_FILES)

    validate_inputs(workspace, control_dir, context_files, editable_files)
    results_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for variant in variants:
        results.append(
            run_variant(
                workspace,
                results_dir,
                control_dir,
                args.model,
                args.instance_id,
                variant,
                context_files,
                editable_files,
                args.max_format_retries,
                args.timeout,
                args.think,
                args.analysis_first,
                args.seed,
                args.temperature,
            )
        )

    summary = {
        "schema_version": 1,
        "instance_id": args.instance_id,
        "model": args.model,
        "official_score": False,
        "docker_used": False,
        "think": args.think,
        "analysis_first": args.analysis_first,
        "seed": args.seed,
        "temperature": args.temperature,
        "variants": results,
    }
    write_json(results_dir / "summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if all(
        item["patch_status"] == "applied" and item["validation_status"] == "passed_non_official"
        for item in results
    ) else 1


def validate_inputs(
    workspace: Path,
    control_dir: Path | None,
    context_files: tuple[str, ...],
    editable_files: tuple[str, ...],
) -> None:
    required = [
        workspace / ".repoflow" / "assigned_task.md",
        *(workspace / path for path in set(context_files) | set(editable_files)),
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise ValueError(f"missing required workspace files: {missing}")
    if control_dir is not None and not (control_dir / "test_patch.diff").is_file():
        raise ValueError(f"missing evaluator test patch: {control_dir / 'test_patch.diff'}")


def run_variant(
    template: Path,
    results_dir: Path,
    control_dir: Path | None,
    model: str,
    instance_id: str,
    variant: str,
    context_files: tuple[str, ...],
    editable_files: tuple[str, ...],
    max_format_retries: int,
    timeout: int,
    think: bool,
    analysis_first: bool,
    seed: int,
    temperature: float,
) -> dict[str, Any]:
    variant_dir = results_dir / variant
    variant_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f"swe-lite-{variant}-") as run_dir_name:
        workspace = Path(run_dir_name) / "workspace"
        copy_workspace(template, workspace)
        create_baseline(workspace)
        prompt = build_prompt(workspace, variant, instance_id, context_files, editable_files)
        base_prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        context_hashes = {
            path: hashlib.sha256((workspace / path).read_bytes()).hexdigest() for path in context_files
        }
        analysis_record = None
        if analysis_first:
            analysis_prompt = build_analysis_prompt(workspace, variant, instance_id, context_files, editable_files)
            analysis_response = ollama_generate(
                model,
                analysis_prompt,
                timeout,
                json_format=False,
                think=think,
                num_predict=768,
                seed=seed,
                temperature=temperature,
            )
            write_json(variant_dir / "analysis-response.json", analysis_response)
            analysis_text = str(analysis_response.get("response") or analysis_response.get("thinking") or "")
            analysis_record = {
                "prompt_sha256": hashlib.sha256(analysis_prompt.encode("utf-8")).hexdigest(),
                "response_sha256": hashlib.sha256(analysis_text.encode("utf-8")).hexdigest(),
                "response_chars": len(analysis_text),
            }
            prompt += f"\nInvestigation from the previous pass (verify it against the source):\n{analysis_text}\n"
        prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()

        response_records = []
        payload = None
        pending_writes = None
        format_error = None
        current_prompt = prompt
        for attempt in range(max_format_retries + 1):
            response = ollama_generate(
                model,
                current_prompt,
                timeout,
                json_format=True,
                think=think,
                seed=seed,
                temperature=temperature,
            )
            write_json(variant_dir / f"response-{attempt}.json", response)
            response_text = str(response.get("response", ""))
            try:
                candidate = parse_replacement_payload(response_text)
                pending = prepare_replacements(
                    workspace,
                    candidate,
                    set(editable_files),
                    expected_invocation(variant),
                )
            except (json.JSONDecodeError, ValueError) as exc:
                format_error = str(exc)
                response_records.append({"attempt": attempt, "status": "rejected", "error": format_error})
                current_prompt = build_format_retry_prompt(prompt, format_error)
                continue
            response_records.append({"attempt": attempt, "status": "accepted"})
            payload = candidate
            pending_writes = pending
            write_json(variant_dir / "accepted-payload.json", payload)
            break

        result: dict[str, Any] = {
            "variant": variant,
            "skill_invocation_required": expected_invocation(variant),
            "base_prompt_sha256": base_prompt_hash,
            "prompt_sha256": prompt_hash,
            "context_sha256": context_hashes,
            "analysis": analysis_record,
            "response_attempts": response_records,
            "patch_status": "format_failure",
            "validation_status": "not_run",
            "failure_category": "model_output_or_patch_format_failure",
        }
        if payload is None or pending_writes is None:
            result["format_error"] = format_error
            write_json(variant_dir / "result.json", result)
            return result

        for path, content in pending_writes.items():
            (workspace / path).write_text(content, encoding="utf-8")
        result["patch_status"] = "applied"

        result["changed_files"] = changed_files(workspace)
        source_diff = run_command(["git", "diff", "--binary"], workspace, timeout=120)
        (variant_dir / "model.patch").write_text(source_diff["stdout"], encoding="utf-8")

        evaluator_apply = None
        if control_dir is not None:
            evaluator_apply = run_command(
                ["git", "apply", "--check", str(control_dir / "test_patch.diff")], workspace, timeout=120
            )
            if evaluator_apply["returncode"] == 0:
                evaluator_apply = run_command(
                    ["git", "apply", str(control_dir / "test_patch.diff")], workspace, timeout=120
                )
        result["evaluator_test_patch"] = (
            "not_provided"
            if control_dir is None
            else "applied"
            if evaluator_apply and evaluator_apply["returncode"] == 0
            else "apply_failure"
        )

        commands = [
            run_command([sys.executable, "-m", "py_compile", "astropy/modeling/separable.py"], workspace, timeout=120),
            run_command(
                [sys.executable, "-m", "pytest", "astropy/modeling/tests/test_separable.py", "-q"],
                workspace,
                timeout=timeout,
            ),
        ]
        result["commands"] = commands
        result["validation_status"], result["failure_category"] = classify_validation(commands, evaluator_apply)
        write_json(variant_dir / "result.json", result)
        write_handoff(workspace, variant, instance_id, result)
        return result


def copy_workspace(source: Path, destination: Path) -> None:
    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", "gold_patch.diff", "test_patch.diff"),
    )


def create_baseline(workspace: Path) -> None:
    run_checked(["git", "init", "--quiet"], workspace)
    run_checked(["git", "add", "-A"], workspace)
    run_checked(
        [
            "git",
            "-c",
            "user.name=BoardFlowBench",
            "-c",
            "user.email=boardflowbench@localhost",
            "commit",
            "--quiet",
            "-m",
            "SWE Lite smoke baseline",
        ],
        workspace,
    )


def build_prompt(
    workspace: Path,
    variant: str,
    instance_id: str,
    context_files: tuple[str, ...],
    editable_files: tuple[str, ...],
) -> str:
    task = (workspace / ".repoflow" / "assigned_task.md").read_text(encoding="utf-8")
    skill = ""
    if variant == "repoflow_skill":
        skill = (workspace / ".repoflow" / "skill_packet.md").read_text(encoding="utf-8")
    context = "\n\n".join(
        f"### {path}\n```python\n{(workspace / path).read_text(encoding='utf-8')}\n```" for path in context_files
    )
    allowed = "\n".join(f"- {path}" for path in editable_files)
    skill_block = f"\nRequired skill packet (apply it before solving):\n{skill}\n" if skill else ""
    return f"""You are a local coding agent solving SWE-bench Lite smoke instance {instance_id}.

Return one JSON object only, with this exact shape:
{{
  "skill_invocation": "{expected_invocation(variant)}",
  "edits": [
    {{"path": "relative/source.py", "old": "exact existing text", "new": "replacement text"}}
  ],
  "notes": "short explanation"
}}

Do not return prose or Markdown fences. Each `old` string must occur exactly once in its file.
Make the smallest correct replacement. Only these paths may be edited:
{allowed}

Do not seek or use gold patches, evaluator test patches, hidden tests, oracle files, or network access.
{skill_block}
Assigned task:
{task}

Current files:
{context}
"""


def build_format_retry_prompt(original_prompt: str, error: str) -> str:
    return f"""Your previous response was rejected before any patch was applied.

Error: {error}

Regenerate the response as one valid JSON object. Use exact source text for every `old` value.

Original request:
{original_prompt}
"""


def build_analysis_prompt(
    workspace: Path,
    variant: str,
    instance_id: str,
    context_files: tuple[str, ...],
    editable_files: tuple[str, ...],
) -> str:
    task = (workspace / ".repoflow" / "assigned_task.md").read_text(encoding="utf-8")
    skill = ""
    if variant == "repoflow_skill":
        skill = (workspace / ".repoflow" / "skill_packet.md").read_text(encoding="utf-8")
    context = "\n\n".join(
        f"### {path}\n```python\n{(workspace / path).read_text(encoding='utf-8')}\n```" for path in context_files
    )
    allowed = "\n".join(f"- {path}" for path in editable_files)
    skill_block = f"\nRequired skill packet (apply it during investigation):\n{skill}\n" if skill else ""
    return f"""Investigate SWE-bench Lite smoke instance {instance_id} before editing.

Identify the concrete root cause in the supplied source. Trace the failing nested composition through the relevant
operator branches and compare primitive inputs with intermediate computed inputs. Respond in at most 12 lines using
only these labels: `ROOT_CAUSE`, `OLD`, `NEW`, and `FOCUSED_TEST`. Quote the exact smallest existing source text and
its replacement. Do not use network access, gold patches, evaluator test patches, hidden tests, or oracle files. Do
not edit files in this pass.

Editable paths for the later pass:
{allowed}
{skill_block}
Assigned task:
{task}

Current files:
{context}
"""


def expected_invocation(variant: str) -> str:
    return "repoflow-task-agent" if variant == "repoflow_skill" else "none"


def parse_replacement_payload(response: str) -> dict[str, Any]:
    payload = json.loads(response)
    if not isinstance(payload, dict):
        raise ValueError("model response must be a JSON object")
    return payload


def prepare_replacements(
    workspace: Path,
    payload: dict[str, Any],
    allowed_paths: set[str],
    invocation: str,
) -> dict[str, str]:
    if payload.get("skill_invocation") != invocation:
        raise ValueError(f"skill_invocation must be {invocation!r}")
    edits = payload.get("edits")
    if not isinstance(edits, list) or not edits:
        raise ValueError("payload.edits must be a non-empty list")
    pending: dict[str, str] = {}
    for index, edit in enumerate(edits):
        if not isinstance(edit, dict):
            raise ValueError(f"edit {index} must be an object")
        path = str(edit.get("path", "")).replace("\\", "/")
        old = edit.get("old")
        new = edit.get("new")
        parts = set(path.lower().split("/"))
        if path.startswith("/") or ".." in path.split("/"):
            raise ValueError(f"unsafe edit path: {path}")
        if parts & BLOCKED_PATH_PARTS:
            raise ValueError(f"evaluator path is forbidden: {path}")
        if path not in allowed_paths:
            raise ValueError(f"edit path is outside the allowed set: {path}")
        if not isinstance(old, str) or not old:
            raise ValueError(f"edit {index} old value must be a non-empty string")
        if not isinstance(new, str):
            raise ValueError(f"edit {index} new value must be a string")
        if new == old:
            raise ValueError(f"edit {index} is a no-op because old and new are identical")
        current = pending.get(path)
        if current is None:
            current = (workspace / path).read_text(encoding="utf-8")
        count = current.count(old)
        if count != 1:
            raise ValueError(f"edit {index} old value occurs {count} times in {path}; expected exactly once")
        pending[path] = current.replace(old, new, 1)
    return pending


def ollama_generate(
    model: str,
    prompt: str,
    timeout: int,
    *,
    json_format: bool = False,
    think: bool = False,
    num_predict: int = 4096,
    seed: int = 7,
    temperature: float = 0.0,
) -> dict[str, Any]:
    body = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "think": think,
            **({"format": "json"} if json_format else {}),
            "options": {
                "temperature": temperature,
                "num_ctx": 16384,
                "num_predict": num_predict,
                "seed": seed,
            },
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        "http://127.0.0.1:11434/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"Ollama request failed: {exc}") from exc
    payload["client_elapsed_seconds"] = round(time.monotonic() - started, 3)
    payload.pop("context", None)
    return payload


def changed_files(workspace: Path) -> list[str]:
    result = run_command(["git", "status", "--porcelain", "--untracked-files=all"], workspace, timeout=120)
    return [line[3:] for line in result["stdout"].splitlines() if line]


def classify_validation(
    commands: list[dict[str, Any]], evaluator_apply: dict[str, Any] | None
) -> tuple[str, str | None]:
    if evaluator_apply is not None and evaluator_apply["returncode"] != 0:
        return "not_run_with_evaluator_tests", "suspected_harness_or_evaluator_mismatch"
    failures = [item for item in commands if item["returncode"] != 0]
    if not failures:
        return "passed_non_official", None
    text = "\n".join(f"{item['stdout']}\n{item['stderr']}" for item in failures).lower()
    environment_signals = (
        "modulenotfounderror",
        "no module named",
        "importerror: cannot import",
        "failed to import the required dependency",
        "microsoft visual c++",
    )
    if any(signal in text for signal in environment_signals):
        return "dependency_environment_failure", "dependency_or_environment_failure"
    return "failed", "repository_test_failure"


def run_command(arguments: list[str], cwd: Path, *, timeout: int) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        result = subprocess.run(
            arguments,
            cwd=cwd,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        return {
            "command": subprocess.list2cmdline(arguments),
            "returncode": result.returncode,
            "stdout": result.stdout[-8000:],
            "stderr": result.stderr[-8000:],
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": subprocess.list2cmdline(arguments),
            "returncode": 124,
            "stdout": str(exc.stdout or "")[-8000:],
            "stderr": f"timeout after {timeout}s\n{str(exc.stderr or '')[-8000:]}",
        }


def run_checked(arguments: list[str], cwd: Path) -> None:
    result = run_command(arguments, cwd, timeout=120)
    if result["returncode"] != 0:
        raise RuntimeError(f"command failed: {result}")


def write_handoff(workspace: Path, variant: str, instance_id: str, result: dict[str, Any]) -> None:
    handoff = {
        "task_id": instance_id,
        "agent_id": f"ollama-{variant}",
        "role": "local-model-smoke",
        "status": result["validation_status"],
        "files_changed": result.get("changed_files", []),
        "commands_run": [item["command"] for item in result.get("commands", [])],
        "tests": result.get("commands", []),
        "temporary_files_created": [],
        "temporary_files_removed": [],
        "decisions": ["Generated a bounded unified diff without evaluator material in model context."],
        "risks": ["This is not an official SWE-bench score; Docker was not used."],
        "next_recommended_step": "Repeat in the official SWE-bench Docker harness when Docker is available.",
    }
    write_json(workspace / ".repoflow" / "handoffs" / f"{variant}.json", handoff)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
