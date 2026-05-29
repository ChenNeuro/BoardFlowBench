"""Prompt generation for repository review."""

from __future__ import annotations

import json
from typing import Any


def generate_review_prompt(
    repo_profile: dict[str, Any],
    smell_report: dict[str, Any],
    user_question: str | None = None,
) -> str:
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
You are RepoGuardian Studio, a reviewer for AI-generated Python repositories.

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

