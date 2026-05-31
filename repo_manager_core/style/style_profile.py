"""Profile builders that compose scan and smell-detection steps."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from repo_manager_core.health.scan_repo_functions import scan_repo_functions
from repo_manager_core.health.analyze_repo_structure import analyze_repo_structure
from repo_manager_core.health.detect_function_smells import detect_function_smells


def build_profile(repo_path: str | Path) -> dict[str, Any]:
    """Scan a repo and build a complete profile (functions + structure)."""
    profile = scan_repo_functions(repo_path)
    structure = analyze_repo_structure(repo_path)
    # Attach structure warnings to the same profile so downstream scripts only
    # need one JSON input.
    profile["structure_warnings"] = structure["warnings"]
    profile["structure_feedback_questions"] = structure.get("feedback_questions", [])
    profile["structure"] = structure
    return profile


def build_smell_report(repo_profile: dict[str, Any]) -> dict[str, Any]:
    """Detect function smells from a repo profile and merge structure warnings."""
    smell_report = detect_function_smells(
        repo_profile.get("functions", []),
        repo_path=repo_profile.get("repo_path", "."),
    )
    # Structure warnings share the same report format as function warnings.
    smell_report["warnings"].extend(repo_profile.get("structure_warnings", []))
    smell_report["feedback_questions"] = _merge_feedback_questions(
        smell_report.get("feedback_questions", []),
        repo_profile.get("structure_feedback_questions", []),
    )
    smell_report["summary"]["warning_count"] = len(smell_report["warnings"])
    return smell_report


def _merge_feedback_questions(
    first: list[dict[str, Any]],
    second: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for question in [*first, *second]:
        key = (str(question.get("category", "")), str(question.get("keyword", "")))
        if key not in by_key:
            by_key[key] = dict(question)
            by_key[key]["observed"] = list(question.get("observed", []))
            continue
        observed = set(by_key[key].get("observed", []))
        observed.update(question.get("observed", []))
        by_key[key]["observed"] = sorted(observed)[:10]
    return [by_key[key] for key in sorted(by_key)]
