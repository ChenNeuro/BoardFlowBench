"""Tests for shell-free benchmark command normalization."""
from __future__ import annotations

import pytest

from repo_manager_core.benchmark.commands import normalize_command


def test_string_command_preserves_placeholder_path_with_spaces():
    argv, env = normalize_command(
        "PYTHONPATH={workspace}/src python3 -m unittest discover -s {oracle_root}/tests",
        variables={"workspace": "/tmp/work space", "oracle_root": "/tmp/oracle space"},
    )
    assert env["PYTHONPATH"] == "/tmp/work space/src"
    assert argv[-1] == "/tmp/oracle space/tests"


def test_command_rejects_unresolved_placeholder():
    with pytest.raises(ValueError, match="unresolved placeholder"):
        normalize_command("python3 {missing}")
