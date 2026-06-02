"""Tests for observable git scope boundaries."""
from __future__ import annotations

import subprocess

import pytest

from repo_manager_core.board.scope_check import check_scope


@pytest.mark.parametrize("path", [".repo_manager/search_rules.json", ".repo_manager/smell_rules.json", "benchmark/results/forged.json"])
def test_scope_does_not_hide_policy_or_workspace_local_result_files(tmp_path, path):
    subprocess.run(["git", "init", "-b", "main"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    tracked = tmp_path / "tracked.txt"
    tracked.write_text("baseline\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "baseline"], cwd=tmp_path, check=True, capture_output=True)
    target = tmp_path / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("{}\n", encoding="utf-8")

    result = check_scope(tmp_path, {"allowed_paths": ["tracked.txt"]})

    assert path in result["details"]["changed_files"]
    assert path in result["details"]["outside_allowed_paths"]
