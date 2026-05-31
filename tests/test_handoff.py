"""Tests for handoff writing and validation."""
from __future__ import annotations

import tempfile
from pathlib import Path

from repo_manager_core.board.handoff_writer import check_handoff, write_handoff

from .conftest import REPO_ROOT


def test_check_handoff_finds_t001_handoffs():
    """T001 has handoff files from the completed demo run."""
    task = {"task_id": "T001", "handoff_required": True}
    result = check_handoff(REPO_ROOT, task)
    assert result["score"] >= 3  # at least "handoff exists" points
    assert len(result["details"]["handoff_files"]) >= 1


def test_write_and_check_handoff_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / ".board" / "handoffs").mkdir(parents=True)

        path = write_handoff(
            repo=root,
            task_id="T001",
            agent_id="test-agent",
            agent_role="tester",
            status="READY_FOR_REVIEW",
            files_changed=["src/module.py"],
            risks="No known risks",
            next_recommended_step="Run tests and review",
        )
        assert path.exists()

        task = {"task_id": "T001", "handoff_required": True}
        result = check_handoff(root, task)
        assert result["score"] >= 3
