"""Tests for board consistency validation."""
from __future__ import annotations

from repo_manager_core.board.board_validator import check_board_consistency

from .conftest import REPO_ROOT


def test_board_consistency_finds_p001():
    """P001 exists in .board/tasks.yaml with status DONE."""
    result = check_board_consistency(REPO_ROOT, {"task_id": "P001"})
    # P001 has status DONE and owner set — should have reasonable score
    assert result["details"]["board_task_found"] is True
    assert result["details"]["task_id"] == "P001"


def test_board_consistency_missing_task():
    result = check_board_consistency(REPO_ROOT, {"task_id": "T999"})
    assert result["details"]["board_task_found"] is False
    assert result["score"] == 0
