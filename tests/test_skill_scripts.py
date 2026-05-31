"""Integration tests for skill scripts — migrated from test_repo_guardian_skill_scripts.py."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from repo_manager_core.style.style_profile import build_profile, build_smell_report
from repo_manager_core.style.learn_repo_style import learn_repo_style

from .conftest import FIXTURES, REPO_ROOT

SCRIPTS = REPO_ROOT / "skills" / "code-health-review" / "scripts"
DEMO_MESSY = REPO_ROOT / "template" / "messy_ai_case"


def test_style_module_builds_profile_smells_and_style():
    """Style module functions work against the sample fixture."""
    profile = build_profile(FIXTURES / "sample_repo")
    assert profile["function_count"] == 2

    smell_report = build_smell_report(profile)
    assert isinstance(smell_report["warnings"], list)

    style = learn_repo_style(profile)
    assert style["function_count"] == 2
    assert "snake_case_function_count" in style


def test_health_generate_report_writes_expected_outputs(tmp_path):
    """health_generate_report.py produces expected output files."""
    script = SCRIPTS / "health_generate_report.py"
    result = subprocess.run(
        [sys.executable, str(script), str(DEMO_MESSY), "--output-dir", str(tmp_path / "outputs")],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"Script stderr: {result.stderr}"

    report_path = tmp_path / "outputs" / "code_health_report.md"
    assert report_path.exists()
    report_content = report_path.read_text()
    assert "Repo Manager Code Health Review" in report_content

    profile_path = tmp_path / "outputs" / "repo_profile.json"
    assert profile_path.exists()
    profile = json.loads(profile_path.read_text())
    assert profile["function_count"] >= 1

    smell_path = tmp_path / "outputs" / "smell_report.json"
    assert smell_path.exists()
    smell = json.loads(smell_path.read_text())
    assert len(smell["warnings"]) >= 1
