"""Tests for allowlisted external repository templates."""
from __future__ import annotations

import json
import subprocess

import pytest

from repo_manager_core.bootstrap import apply_template, recommend_templates
from repo_manager_core.board.board_sync import check_board_views


def _git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()


def _catalog(tmp_path):
    template = tmp_path / "template"
    template.mkdir()
    _git(template, "init", "-b", "main")
    _git(template, "config", "user.name", "Test")
    _git(template, "config", "user.email", "test@example.com")
    (template / "README.md").write_text("# Template\n")
    _git(template, "add", ".")
    _git(template, "commit", "-m", "template")
    commit = _git(template, "rev-parse", "HEAD")
    catalog = tmp_path / "catalog.json"
    catalog.write_text(
        json.dumps(
            {
                "templates": [
                    {
                        "id": "local",
                        "engine": "git-template",
                        "source": str(template),
                        "vcs_ref": commit,
                        "description": "Local test template.",
                        "structure_preview": ["README.md"],
                        "allow_tasks": False,
                    }
                ]
            }
        )
    )
    return catalog


def test_recommend_lists_allowlisted_templates(tmp_path):
    assert recommend_templates(_catalog(tmp_path))[0]["id"] == "local"


def test_apply_template_preserves_prompt_and_records_baseline(tmp_path):
    catalog = _catalog(tmp_path)
    prompt = tmp_path / "prompt.md"
    prompt.write_text("人写的 prompt，逐字保留。\n")
    repo = tmp_path / "repo"
    record = apply_template(repo, catalog, "local", prompt)
    assert record["user_prompt"] == "人写的 prompt，逐字保留。\n"
    assert record["baseline_commit"] != "pending"
    assert (repo / ".board" / "tasks.yaml").exists()
    assert (repo / ".board" / "handoff.schema.json").exists()
    assert check_board_views(repo) == []


def test_apply_rejects_unregistered_template(tmp_path):
    with pytest.raises(ValueError, match="not allowlisted"):
        apply_template(tmp_path / "repo", _catalog(tmp_path), "missing", tmp_path / "missing-prompt")


def test_apply_rejects_moving_template_ref(tmp_path):
    catalog = _catalog(tmp_path)
    data = json.loads(catalog.read_text())
    data["templates"][0]["vcs_ref"] = "main"
    catalog.write_text(json.dumps(data))
    prompt = tmp_path / "prompt.md"
    prompt.write_text("Build a package.\n")
    with pytest.raises(ValueError, match="immutable commit SHA"):
        apply_template(tmp_path / "repo", catalog, "local", prompt)


def test_apply_rejects_catalog_disabled_template_tasks(tmp_path):
    catalog = _catalog(tmp_path)
    prompt = tmp_path / "prompt.md"
    prompt.write_text("Build a package.\n")
    with pytest.raises(ValueError, match="disabled by catalog policy"):
        apply_template(tmp_path / "repo", catalog, "local", prompt, allow_template_tasks=True)


def test_apply_template_accepts_fixed_commit_sha(tmp_path):
    catalog = _catalog(tmp_path)
    data = json.loads(catalog.read_text())
    data["templates"][0]["vcs_ref"] = _git(tmp_path / "template", "rev-parse", "HEAD")
    catalog.write_text(json.dumps(data))
    prompt = tmp_path / "prompt.md"
    prompt.write_text("Build a package.\n")
    record = apply_template(tmp_path / "repo", catalog, "local", prompt)
    assert record["vcs_ref"] == data["templates"][0]["vcs_ref"]
