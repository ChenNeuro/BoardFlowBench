"""Integration tests for skill scripts — migrated from test_repo_guardian_skill_scripts.py."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from repo_manager_core.style.style_profile import build_profile, build_smell_report
from repo_manager_core.style.learn_repo_style import learn_repo_style

from .conftest import REPO_ROOT

SCRIPTS = REPO_ROOT / "skills" / "code-health-review" / "scripts"


def test_style_module_builds_profile_smells_and_style(tmp_path):
    """Style module functions work against the sample fixture."""
    workspace = tmp_path / "sample_repo"
    package_dir = workspace / "pkg"
    package_dir.mkdir(parents=True)
    (package_dir / "sample.py").write_text(
        "def outer(value):\n"
        "    return helper(value)\n"
        "\n"
        "\n"
        "def helper(value):\n"
        "    return value.strip()\n",
        encoding="utf-8",
    )

    profile = build_profile(workspace)
    assert profile["function_count"] == 2

    smell_report = build_smell_report(profile)
    assert isinstance(smell_report["warnings"], list)

    style = learn_repo_style(profile)
    assert style["function_count"] == 2
    assert "snake_case_function_count" in style


def test_health_generate_report_writes_expected_outputs(tmp_path):
    """health_generate_report.py produces expected output files."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "parser_patch.py").write_text(
        "def parse_date_safe(value):\n"
        "    return value\n",
        encoding="utf-8",
    )

    script = SCRIPTS / "health_generate_report.py"
    result = subprocess.run(
        [sys.executable, str(script), str(workspace), "--output-dir", str(tmp_path / "outputs")],
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


def test_health_generate_report_defaults_to_current_workspace(tmp_path):
    """Without repo/output args, the script scans cwd and writes repo_manager_report."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "sample.py").write_text(
        "def parse_date_safe(value):\n"
        "    return value\n",
        encoding="utf-8",
    )

    script = SCRIPTS / "health_generate_report.py"
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=workspace,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script stderr: {result.stderr}"

    output_dir = workspace / "repo_manager_report"
    assert (output_dir / "repo_profile.json").exists()
    assert (output_dir / "smell_report.json").exists()
    assert (output_dir / "style_profile.json").exists()
    assert (output_dir / "code_health_report.md").exists()


def test_health_generate_report_records_explicit_feedback(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "sample.py").write_text(
        "def fix_timezone_offset(value):\n"
        "    return value\n",
        encoding="utf-8",
    )

    script = SCRIPTS / "health_generate_report.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            str(workspace),
            "--feedback",
            "fix=contextual",
            "--feedback-reason",
            "Used in public APIs",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script stderr: {result.stderr}"

    rules_path = workspace / ".repo_manager" / "smell_rules.json"
    feedback_path = workspace / ".repo_manager" / "user_feedback.jsonl"
    report_path = workspace / "repo_manager_report" / "code_health_report.md"

    rules = json.loads(rules_path.read_text(encoding="utf-8"))
    feedback = json.loads(feedback_path.read_text(encoding="utf-8").strip())
    report = report_path.read_text(encoding="utf-8")

    assert rules["patch_keywords"]["fix"]["policy"] == "contextual"
    assert feedback["keyword"] == "fix"
    assert "## Learned Repository Policies" in report
    assert "Policy: `contextual`" in report
