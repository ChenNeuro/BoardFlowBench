"""Agent context and style profile file writers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from repo_manager_core.board.handoff_writer import handoff_sort_key

from .learn_repo_style import write_json


def write_style_profile(repo_path: str | Path, style_profile: dict[str, Any]) -> Path:
    """Write repo_style_profile.json to .repo_manager/."""
    root = Path(repo_path)
    dest = root / ".repo_manager" / "repo_style_profile.json"
    write_json(style_profile, dest)
    return dest


def write_agent_context(
    repo_path: str | Path,
    style_profile: dict[str, Any],
    board: dict[str, Any] | None = None,
    agent_id: str | None = None,
    task_id: str | None = None,
    *,
    phase: str | None = None,
    git_state: dict[str, Any] | None = None,
    blockers: list[str] | None = None,
    override_reason: str | None = None,
) -> Path:
    """Write agent_context.md summarizing current state for the next agent."""
    root = Path(repo_path)
    dest = root / ".repo_manager" / "agent_context.md"
    dest.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Agent Context",
        "",
        f"> Generated for agent: `{agent_id or 'unknown'}`",
        f"> Last task: `{task_id or 'none'}`",
        "",
        "## Refresh",
        "",
        f"- Phase: `{phase or 'manual'}`",
    ]
    if override_reason:
        lines.append(f"- Override reason: {override_reason}")
    if blockers:
        lines.extend(["- Risks:"])
        lines.extend(f"  - {blocker}" for blocker in blockers)
    else:
        lines.append("- Risks: none")

    milestone = (board or {}).get("current_milestone", {})
    lines.extend(
        [
            "",
            "## Current Milestone",
            "",
            f"- ID: `{milestone.get('id', 'none')}`",
            f"- Title: {milestone.get('title', '')}",
            f"- Status: `{milestone.get('status', 'unknown')}`",
            f"- Goal: {milestone.get('goal', '')}",
            "",
            "## Current Sticker",
            "",
        ]
    )
    current_task = _find_task(board, task_id)
    if current_task:
        lines.extend(
            [
                f"- ID: `{current_task.get('id', '')}`",
                f"- Title: {current_task.get('title', '')}",
                f"- Status: `{current_task.get('status', 'TODO')}`",
                f"- Owner: `{current_task.get('owner', 'unassigned')}`",
                f"- Notes: {current_task.get('notes', '')}",
            ]
        )
    else:
        lines.append("- No current sticker selected.")

    lines.extend(["", "## Unfinished Stickers", ""])
    active = _active_tasks(board, task_id)
    lines.extend(_task_lines(active, empty="- No other active stickers."))

    lines.extend(["", "## Long-Term Backlog", ""])
    backlog = _backlog_tasks(board)
    lines.extend(_task_lines(backlog, empty="- No unfinished stickers."))

    lines.extend(["", "## Git Status", ""])
    lines.extend(_git_lines(git_state or {}))

    lines.extend(
        [
            "",
        "## Repository Style Summary",
        "",
        f"- Functions: {style_profile.get('function_count', 0)}",
        f"- Snake case compliance: {style_profile.get('snake_case_function_count', 0)}/{style_profile.get('function_count', 0)}",
        f"- With docstrings: {style_profile.get('docstring_function_count', 0)}",
        f"- Average function length: {style_profile.get('average_function_length', 0)}",
        f"- Patch-like names: {style_profile.get('patch_like_function_count', 0)}",
        "",
        "## Test Style Summary",
        "",
    ])
    test_style = style_profile.get("test_style", {})
    lines.extend(
        [
            f"- Test files: {test_style.get('test_file_count', 0)}",
            f"- Test functions: {test_style.get('test_function_count', 0)}",
            f"- Snake case test functions: {test_style.get('snake_case_test_function_count', 0)}",
            f"- Common test directories: {json.dumps(test_style.get('common_test_directories', []))}",
            "",
            "## Latest Handoff",
            "",
            f"- {_latest_handoff(root, current_task) or 'No handoff recorded for the current sticker.'}",
            "",
            "## Human Style Record",
            "",
            "- Read `.repo_manager/style_record.md` when it exists. Preserve human-written text verbatim.",
            "",
        ]
    )

    if board and board.get("tasks"):
        # Keep this compact: the detailed source of truth remains .board/tasks.yaml.
        lines.extend(["## Current Task Board", ""])
        for task in board["tasks"]:
            status = task.get("status", "TODO")
            owner = task.get("owner", "-")
            lines.append(f"- **{task.get('id', '?')}** [{status}] — {task.get('title', '')} (owner: {owner})")
        lines.append("")

    lines.extend(
        [
            "## Notes for the Next Agent",
            "",
            "- Read `.board/tasks.yaml` and `.board/handoffs/` for detailed handoff records.",
            "- Read `.repo_manager/repo_style_profile.json` for style conventions.",
            "- Read `.repo_manager/style_record.md` for human-written conventions.",
            "- Match the prevailing naming and docstring style in this codebase.",
        ]
    )

    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return dest


def _find_task(board: dict[str, Any] | None, task_id: str | None) -> dict[str, Any] | None:
    for task in (board or {}).get("tasks", []):
        if task.get("id") == task_id:
            return task
    return None


def _active_tasks(board: dict[str, Any] | None, current_task_id: str | None) -> list[dict[str, Any]]:
    active_statuses = {"IN_PROGRESS", "READY_FOR_REVIEW", "BLOCKED"}
    return [
        task
        for task in (board or {}).get("tasks", [])
        if task.get("id") != current_task_id and task.get("status") in active_statuses
    ]


def _backlog_tasks(board: dict[str, Any] | None) -> list[dict[str, Any]]:
    return [task for task in (board or {}).get("tasks", []) if task.get("status") != "DONE"]


def _task_lines(tasks: list[dict[str, Any]], *, empty: str) -> list[str]:
    if not tasks:
        return [empty]
    return [
        f"- **{task.get('id', '?')}** [{task.get('status', 'TODO')}] - {task.get('title', '')} (owner: {task.get('owner', '-')})"
        for task in tasks
    ]


def _git_lines(git_state: dict[str, Any]) -> list[str]:
    lines = [
        f"- Available: `{git_state.get('available', False)}`",
        f"- Branch: `{git_state.get('branch', '')}`",
        f"- Clean: `{git_state.get('clean', False)}`",
    ]
    for label, key in (
        ("Staged", "staged_files"),
        ("Unstaged", "unstaged_files"),
        ("Untracked", "untracked_files"),
    ):
        values = git_state.get(key, [])
        lines.append(f"- {label}:")
        lines.extend(f"  - `{value}`" for value in values)
        if not values:
            lines.append("  - none")
    return lines


def _latest_handoff(root: Path, current_task: dict[str, Any] | None) -> str | None:
    if not current_task:
        return None
    configured = current_task.get("current_handoff")
    if configured and (root / str(configured)).exists():
        return str(configured)
    handoff_dir = root / ".board" / "handoffs"
    if not handoff_dir.exists():
        return None
    matches = sorted(handoff_dir.glob(f"{current_task.get('id', '')}_*.json"), key=handoff_sort_key)
    return str(matches[-1].relative_to(root)) if matches else None
