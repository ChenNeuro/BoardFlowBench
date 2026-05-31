"""Tests for repository hygiene checks."""
from __future__ import annotations

import tempfile
from pathlib import Path

from repo_manager_core.board.hygiene import check_hygiene


def test_clean_repo_scores_full():
    """A clean temp directory should score full hygiene points."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # Create a minimal artifact directory with a markdown file
        artifacts = root / "template" / "expense_lite" / "artifacts"
        artifacts.mkdir(parents=True)
        (artifacts / "report.md").write_text("# Report")
        # Create scratch with just .gitkeep
        scratch = root / "template" / "expense_lite" / ".scratch"
        scratch.mkdir(parents=True)
        (scratch / ".gitkeep").write_text("")

        result = check_hygiene(root)
        assert result["score"] == result["max"]  # full marks
        assert not result["violations"]


def test_forbidden_root_file_detected():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "tmp.py").write_text("x = 1")
        artifacts = root / "template" / "expense_lite" / "artifacts"
        artifacts.mkdir(parents=True)
        (artifacts / "report.md").write_text("# Report")
        scratch = root / "template" / "expense_lite" / ".scratch"
        scratch.mkdir(parents=True)
        (scratch / ".gitkeep").write_text("")

        result = check_hygiene(root)
        assert result["score"] < result["max"]
        assert result["details"]["forbidden_root_files"] == ["tmp.py"]


def test_cache_file_detected():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "__pycache__").mkdir()
        artifacts = root / "template" / "expense_lite" / "artifacts"
        artifacts.mkdir(parents=True)
        (artifacts / "report.md").write_text("# Report")
        scratch = root / "template" / "expense_lite" / ".scratch"
        scratch.mkdir(parents=True)
        (scratch / ".gitkeep").write_text("")

        result = check_hygiene(root)
        assert len(result["details"]["cache_files"]) >= 1
