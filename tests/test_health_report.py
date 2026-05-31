"""Tests for health report generation."""
from __future__ import annotations

from repo_manager_core.health.generate_health_report import (
    generate_review_prompt,
    render_review_report,
    _group_warning_counts,
)


def test_generate_review_prompt_includes_profile():
    profile = {"repo_path": "/test", "python_file_count": 3, "function_count": 10}
    smells = {"warnings": []}
    prompt = generate_review_prompt(profile, smells)
    assert "Repo Manager" in prompt
    assert "/test" in prompt
    assert "3" in prompt


def test_generate_review_prompt_with_question():
    prompt = generate_review_prompt(
        {"repo_path": ".", "python_file_count": 1, "function_count": 1},
        {"warnings": []},
        user_question="How to fix?",
    )
    assert "How to fix?" in prompt


def test_render_review_report_contains_expected_sections():
    profile = {"repo_path": "/test", "python_file_count": 5, "function_count": 20}
    smells = {"warnings": []}
    style = {"patch_like_function_count": 2, "average_function_length": 12.5}

    report = render_review_report(profile, smells, style)

    assert "Repo Manager Code Health Review" in report
    assert "## Summary" in report
    assert "## Warning Counts" in report
    assert "## Findings" in report
    assert "## Style Profile" in report
    assert "## Cleanup Plan" in report


def test_render_review_report_with_warnings():
    profile = {"repo_path": "/test", "python_file_count": 1, "function_count": 1}
    smells = {
        "warnings": [
            {
                "severity": "medium",
                "type": "patch_name_smell",
                "file": "fix.py",
                "function": "parse_date_safe",
                "reason": "Contains 'safe'",
                "suggestion": "Rename it",
            }
        ]
    }
    style = {"patch_like_function_count": 1, "average_function_length": 5.0}

    report = render_review_report(profile, smells, style)
    assert "patch_name_smell" in report
    assert "fix.py" in report


def test_group_warning_counts():
    warnings = [
        {"type": "patch_name_smell"},
        {"type": "patch_name_smell"},
        {"type": "unused_function"},
    ]
    counts = _group_warning_counts(warnings)
    assert counts == {"patch_name_smell": 2, "unused_function": 1}
