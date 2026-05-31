"""Prompt generation and report rendering for code health review."""

from __future__ import annotations

import json
from collections import Counter
from typing import Any


def generate_review_prompt(
    repo_profile: dict[str, Any],
    smell_report: dict[str, Any],
    user_question: str | None = None,
) -> str:
    """Build a compact LLM prompt from the repo profile and smell report."""
    compact_profile = {
        "repo_path": repo_profile.get("repo_path"),
        "python_file_count": repo_profile.get("python_file_count"),
        "function_count": repo_profile.get("function_count"),
        "parsed_file_count": repo_profile.get("parsed_file_count"),
        "failed_file_count": repo_profile.get("failed_file_count"),
        "structure_warnings": repo_profile.get("structure_warnings", []),
    }
    compact_smells = smell_report.get("warnings", [])[:80]

    prompt = f"""
You are Repo Manager Code Health Review, a reviewer for AI-generated Python repositories.

Write a concise, human-readable review. Treat findings as suspicious signals, not absolute errors.

Focus on:
- patch function bloat
- duplicate-like helper functions
- unused functions
- wrapper functions
- messy repository structure
- a practical cleanup plan

Repository profile:
{json.dumps(compact_profile, indent=2)}

Function smell warnings:
{json.dumps(compact_smells, indent=2)}
""".strip()

    if user_question:
        prompt += f"\n\nUser question:\n{user_question.strip()}"

    return prompt


def _group_warning_counts(warnings: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(warning.get("type", "unknown") for warning in warnings).items()))


def render_review_report(
    repo_profile: dict[str, Any],
    smell_report: dict[str, Any],
    style_profile: dict[str, Any],
    user_question: str | None = None,
) -> str:
    """Generate a full Markdown health review report."""
    warnings = smell_report.get("warnings", [])
    warning_counts = _group_warning_counts(warnings)
    top_warnings = warnings[:20]

    lines = [
        "# Repo Manager Code Health Review",
        "",
        "## Summary",
        "",
        "Findings are suspicious signals, not absolute defects. Confirm public entry points before removing or inlining code.",
        "",
        f"- Repository: `{repo_profile.get('repo_path', '')}`",
        f"- Python files scanned: {repo_profile.get('python_file_count', 0)}",
        f"- Functions scanned: {repo_profile.get('function_count', 0)}",
        f"- Total warnings: {len(warnings)}",
        f"- Patch-like function names: {style_profile.get('patch_like_function_count', 0)}",
        f"- Average function length: {style_profile.get('average_function_length', 0)}",
        "",
        "## Warning Counts",
        "",
    ]

    if warning_counts:
        lines.extend(f"- {name}: {count}" for name, count in warning_counts.items())
    else:
        lines.append("- No suspicious signals found.")

    lines.extend(["", "## Findings", ""])
    if top_warnings:
        for index, warning in enumerate(top_warnings, start=1):
            target = warning.get("function") or "(module/repo)"
            file_path = warning.get("file") or "(repository)"
            lines.extend(
                [
                    f"{index}. `{warning.get('type', 'unknown')}` ({warning.get('severity', 'unknown')})",
                    f"   - Location: `{file_path}` / `{target}`",
                    f"   - Reason: {warning.get('reason', '')}",
                    f"   - Suggestion: {warning.get('suggestion', '')}",
                ]
            )
    else:
        lines.append("No suspicious function or structure warnings were detected.")

    style_warnings = style_profile.get("style_warnings", [])
    lines.extend(["", "## Style Profile", ""])
    lines.extend(
        [
            f"- Snake case functions: {style_profile.get('snake_case_function_count', 0)}",
            f"- Functions with docstrings: {style_profile.get('docstring_function_count', 0)}",
            f"- Median function length: {style_profile.get('median_function_length', 0)}",
            f"- Max function length: {style_profile.get('max_function_length', 0)}",
        ]
    )
    if style_warnings:
        lines.append("- Style warnings:")
        for warning in style_warnings:
            lines.append(f"  - {warning.get('type')}: {warning.get('reason')}")

    lines.extend(
        [
            "",
            "## Cleanup Plan",
            "",
            "1. Confirm public entry points, framework hooks, CLI commands, tests, and plugin callbacks.",
            "2. Merge duplicate-like helpers only after behavior is covered by tests.",
            "3. Inline thin wrappers when they do not validate input, document an API boundary, or improve readability.",
            "4. Rename or remove temporary files after stable code is moved into clear modules.",
            "5. Re-run Code Health Review and the repository's normal test suite.",
        ]
    )

    if user_question:
        lines.extend(["", "## User Question", "", user_question.strip()])

    return "\n".join(lines) + "\n"
