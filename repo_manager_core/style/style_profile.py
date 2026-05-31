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
    profile["structure_warnings"] = structure["warnings"]
    profile["structure"] = structure
    return profile


def build_smell_report(repo_profile: dict[str, Any]) -> dict[str, Any]:
    """Detect function smells from a repo profile and merge structure warnings."""
    smell_report = detect_function_smells(repo_profile.get("functions", []))
    smell_report["warnings"].extend(repo_profile.get("structure_warnings", []))
    smell_report["summary"]["warning_count"] = len(smell_report["warnings"])
    return smell_report
