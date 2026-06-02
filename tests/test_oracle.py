"""Tests for private oracle isolation and target binding."""
from __future__ import annotations

import json
import subprocess

from repo_manager_core.benchmark.oracle import run_oracle


def _git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()


def test_oracle_rejects_manifest_for_different_seed(tmp_path):
    oracle = tmp_path / "oracle"
    workspace = tmp_path / "workspace"
    (oracle / "targets").mkdir(parents=True)
    workspace.mkdir()
    _git(oracle, "init", "-b", "main")
    _git(oracle, "config", "user.name", "Test")
    _git(oracle, "config", "user.email", "test@example.com")
    (oracle / "targets" / "demo.json").write_text(
        json.dumps(
            {
                "seed_commit": "wrong-seed",
                "seed_commands": [{"argv": ["python3", "-c", "raise SystemExit(0)"]}],
            }
        )
    )
    _git(oracle, "add", ".")
    _git(oracle, "commit", "-m", "oracle")

    result = run_oracle(
        oracle,
        "demo",
        "B001",
        workspace,
        phase="seed",
        expected_seed_commit="expected-seed",
        expected_oracle_commit=_git(oracle, "rev-parse", "HEAD"),
    )

    assert result["seed_matches_target"] is False
    assert result["passed"] is False


def test_oracle_rejects_dirty_pack_without_running_commands(tmp_path):
    oracle = tmp_path / "oracle"
    workspace = tmp_path / "workspace"
    (oracle / "targets").mkdir(parents=True)
    workspace.mkdir()
    _git(oracle, "init", "-b", "main")
    _git(oracle, "config", "user.name", "Test")
    _git(oracle, "config", "user.email", "test@example.com")
    marker = tmp_path / "executed"
    (oracle / "targets" / "demo.json").write_text(json.dumps({"seed_commit": "seed", "seed_commands": [{"argv": ["python3", "-c", f"open({str(marker)!r}, 'w').write('bad')"]}]}))
    _git(oracle, "add", ".")
    _git(oracle, "commit", "-m", "oracle")
    head = _git(oracle, "rev-parse", "HEAD")
    (oracle / "dirty.txt").write_text("dirty")

    result = run_oracle(oracle, "demo", "B001", workspace, phase="seed", expected_seed_commit="seed", expected_oracle_commit=head)

    assert result["oracle_pack_clean"] is False
    assert result["commands"] == []
    assert not marker.exists()
