"""Tests for board I/O: loading and saving task boards."""
from __future__ import annotations

import tempfile
from pathlib import Path

from repo_manager_core.board.board_io import load_board, save_board, load_yaml, task_id

from .conftest import REPO_ROOT


def test_task_id_extraction():
    assert task_id({"task_id": "P001"}) == "P001"
    assert task_id({"id": "B002"}) == "B002"


def test_load_board_from_dot_board():
    board = load_board(REPO_ROOT)
    assert isinstance(board, dict)
    assert "tasks" in board
    assert isinstance(board["tasks"], list)


def test_save_and_load_board_roundtrip():
    board = {
        "schema_version": 1,
        "tasks": [
            {"id": "P001", "title": "Test", "status": "TODO", "owner": "agent-a"}
        ],
    }
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / ".board").mkdir()
        saved = save_board(board, root)
        assert saved.exists()

        loaded = load_board(root)
        assert loaded["tasks"][0]["id"] == "P001"
        assert loaded["tasks"][0]["status"] == "TODO"


def test_load_yaml_fallback():
    yaml_text = "key1: value1\nkey2: true\nitems:\n  - a\n  - b\n"
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "test.yaml"
        p.write_text(yaml_text)
        result = load_yaml(p)
        assert result["key1"] == "value1"
        assert result["key2"] is True
        assert result["items"] == ["a", "b"]
