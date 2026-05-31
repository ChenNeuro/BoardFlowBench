"""Agent context and style profile file writers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

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
        "## Repository Style Summary",
        "",
        f"- Functions: {style_profile.get('function_count', 0)}",
        f"- Snake case compliance: {style_profile.get('snake_case_function_count', 0)}/{style_profile.get('function_count', 0)}",
        f"- With docstrings: {style_profile.get('docstring_function_count', 0)}",
        f"- Average function length: {style_profile.get('average_function_length', 0)}",
        f"- Patch-like names: {style_profile.get('patch_like_function_count', 0)}",
        "",
    ]

    if board and board.get("tasks"):
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
            "- Match the prevailing naming and docstring style in this codebase.",
        ]
    )

    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return dest
