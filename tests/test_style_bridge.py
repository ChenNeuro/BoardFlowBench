"""Tests for generated style summaries and human record preservation."""
from __future__ import annotations

import json

from repo_manager_core.style.learn_repo_style import learn_repo_style
from repo_manager_core.style.style_profile import build_profile

from .conftest import REPO_ROOT


def test_style_profile_includes_compact_test_summary(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "module.py").write_text("def parse_value(value):\n    return value\n", encoding="utf-8")
    (tmp_path / "tests" / "test_module.py").write_text(
        "def test_parse_value():\n    assert True\n",
        encoding="utf-8",
    )

    style = learn_repo_style(build_profile(tmp_path))

    assert style["test_style"]["test_file_count"] == 1
    assert style["test_style"]["test_function_count"] == 1
    assert style["test_style"]["snake_case_test_function_count"] == 1
    assert style["test_style"]["common_test_directories"] == [("tests", 1)]


def test_repo_human_record_is_verbatim_and_generated_files_are_valid():
    record = (REPO_ROOT / ".repo_manager" / "style_record.md").read_text(encoding="utf-8")
    assert record == (
        "这是在与用户对话中，agent探索用户代码风格，读取用户风格文件，跨agent传承\n"
        "HUMAN TODO: 结构化语言需要\n"
    )
    json.loads((REPO_ROOT / ".repo_manager" / "repo_style_profile.json").read_text(encoding="utf-8"))
    for line in (REPO_ROOT / ".repo_manager" / "user_feedback.jsonl").read_text(encoding="utf-8").splitlines():
        json.loads(line)
