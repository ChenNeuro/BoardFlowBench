"""Trusted empty-repository bootstrap through allowlisted external templates."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from repo_manager_core.benchmark.workspace import commit_all
from repo_manager_core.board.board_io import save_board


def recommend_templates(catalog_path: str | Path) -> list[dict[str, Any]]:
    """Return auditable template choices without mutating a repository."""
    catalog = _load_catalog(catalog_path)
    return list(catalog["templates"])


def apply_template(
    repo: str | Path,
    catalog_path: str | Path,
    template_id: str,
    prompt_file: str | Path,
    *,
    allow_template_tasks: bool = False,
) -> dict[str, Any]:
    """Apply one explicitly selected fixed-ref template to an empty repository."""
    root = Path(repo).resolve()
    root.mkdir(parents=True, exist_ok=True)
    if any(path.name != ".git" for path in root.iterdir()):
        raise ValueError(f"repository is not empty: {root}")
    template = _find_template(_load_catalog(catalog_path), template_id)
    if not template.get("vcs_ref"):
        raise ValueError(f"template {template_id} must declare a fixed vcs_ref")
    if not _is_immutable_ref(str(template["vcs_ref"])):
        raise ValueError(f"template {template_id} vcs_ref must be an immutable tag or commit")
    if template.get("allow_tasks") and not allow_template_tasks:
        raise ValueError("template tasks require explicit --allow-template-tasks confirmation")
    prompt = Path(prompt_file).read_text(encoding="utf-8")

    engine = template.get("engine")
    if engine == "copier":
        _run_copier(root, template, allow_template_tasks=allow_template_tasks)
    elif engine == "git-template":
        _run_git_template(root, template)
    else:
        raise ValueError(f"unsupported template engine: {engine}")
    _initialize_protocol(root, template, prompt)
    baseline = commit_all(root, "Bootstrap repository from trusted template")
    record_path = root / ".repo_manager" / "bootstrap_record.json"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    record["baseline_commit"] = baseline
    _write_json(record_path, record)
    commit_all(root, "Record bootstrap baseline")
    return record


def _initialize_protocol(root: Path, template: dict[str, Any], prompt: str) -> None:
    if not (root / ".git").exists():
        _run(["git", "init", "-b", "main"], cwd=root)
    (root / ".repo_manager").mkdir(parents=True, exist_ok=True)
    (root / ".repo_manager" / "user_prompt.md").write_text(prompt, encoding="utf-8")
    _write_json(
        root / ".repo_manager" / "bootstrap_record.json",
        {
            "schema_version": 1,
            "template_id": template["id"],
            "engine": template["engine"],
            "source": template["source"],
            "vcs_ref": template["vcs_ref"],
            "allow_tasks": bool(template.get("allow_tasks")),
            "user_prompt": prompt,
            "baseline_commit": "pending",
        },
    )
    if not (root / "AGENTS.md").exists():
        (root / "AGENTS.md").write_text(
            "# AGENTS.md\n\nRead `.board/tasks.yaml` and `.repo_manager/user_prompt.md` before changing code.\n",
            encoding="utf-8",
        )
    board = {
        "schema_version": 1,
        "project": root.name,
        "current_milestone": {
            "id": "M1",
            "title": "Bootstrap user request",
            "status": "IN_PROGRESS",
            "goal": "Implement the original user prompt from the trusted template baseline.",
        },
        "status_values": ["TODO", "IN_PROGRESS", "BLOCKED", "READY_FOR_REVIEW", "DONE"],
        "tasks": [
            {
                "id": "P001",
                "title": "Implement original user prompt",
                "status": "TODO",
                "owner": "unassigned",
                "dependencies": [],
                "current_handoff": None,
                "notes": "Read .repo_manager/user_prompt.md verbatim.",
            }
        ],
    }
    save_board(board, root)
    shutil.copyfile(
        Path(__file__).with_name("default_handoff.schema.json"),
        root / ".board" / "handoff.schema.json",
    )
    (root / "PROJECT_BOARD.md").write_text(
        "# PROJECT_BOARD.md\n\n"
        "## Current Milestone\n\n"
        "Milestone: M1 - Bootstrap user request\n\n"
        "Status: IN_PROGRESS\n\n"
        "## Task Board\n\n"
        "| Task | Title | Status | Owner | Dependencies | Notes |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        "| P001 | Implement original user prompt | TODO | unassigned | none | Read .repo_manager/user_prompt.md verbatim. |\n",
        encoding="utf-8",
    )


def _run_copier(root: Path, template: dict[str, Any], *, allow_template_tasks: bool) -> None:
    executable = shutil.which("copier")
    if not executable:
        raise ValueError("Copier is not installed. Install Copier explicitly before applying this template.")
    command = [
        executable,
        "copy",
        "--vcs-ref",
        str(template["vcs_ref"]),
        "--defaults",
    ]
    if allow_template_tasks:
        command.append("--trust")
    command.extend([str(template["source"]), str(root)])
    _run(command, cwd=root.parent)


def _run_git_template(root: Path, template: dict[str, Any]) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        checkout = Path(tmp) / "template"
        _run(["git", "clone", "--quiet", str(template["source"]), str(checkout)], cwd=root.parent)
        _run(["git", "switch", "--quiet", "--detach", str(template["vcs_ref"])], cwd=checkout)
        for path in checkout.iterdir():
            if path.name == ".git":
                continue
            target = root / path.name
            if path.is_dir():
                shutil.copytree(path, target)
            else:
                shutil.copyfile(path, target)


def _load_catalog(path: str | Path) -> dict[str, Any]:
    catalog = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(catalog, dict) or not isinstance(catalog.get("templates"), list):
        raise ValueError("template catalog must contain a templates array")
    return catalog


def _find_template(catalog: dict[str, Any], template_id: str) -> dict[str, Any]:
    for template in catalog["templates"]:
        if isinstance(template, dict) and template.get("id") == template_id:
            return template
    raise ValueError(f"template is not allowlisted: {template_id}")


def _is_immutable_ref(value: str) -> bool:
    """Require a commit SHA or release-like tag, not a moving branch."""
    return bool(re.fullmatch(r"[0-9a-fA-F]{7,40}", value) or re.fullmatch(r"v?\d+(?:\.\d+)+(?:[-+._][A-Za-z0-9.-]+)?", value))


def _run(command: list[str], *, cwd: Path) -> None:
    result = subprocess.run(command, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode != 0:
        raise ValueError(result.stderr.strip() or result.stdout.strip() or f"command failed: {command}")


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
