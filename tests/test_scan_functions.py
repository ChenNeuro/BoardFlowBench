"""Tests for function scanning — migrated from repo_guardian_studio tests."""
from __future__ import annotations

import json
from pathlib import Path

from repo_manager_core.health.analyze_repo_structure import analyze_repo_structure
from repo_manager_core.health.scan_file_functions import scan_file_functions
from repo_manager_core.health.scan_repo_functions import scan_repo_functions

from .conftest import FIXTURES


def _write_sample_repo(root: Path) -> None:
    package_dir = root / "pkg"
    package_dir.mkdir(parents=True)
    (package_dir / "sample.py").write_text(
        "# prepares value\n"
        "def outer(value):\n"
        "    \"\"\"Example docstring.\"\"\"\n"
        "    return helper(value)\n"
        "\n"
        "\n"
        "def helper(value):\n"
        "    return value.strip()\n",
        encoding="utf-8",
    )


def test_scan_file_extracts_function_metadata():
    sample = FIXTURES / "sample_repo" / "pkg" / "sample.py"
    result = scan_file_functions(sample)

    assert result["parse_succeeded"] is True
    assert [fn["function_name"] for fn in result["functions"]] == ["outer", "helper"]
    outer = result["functions"][0]
    assert outer["argument_names"] == ["value"]
    assert outer["docstring"] == "Example docstring."
    assert outer["leading_comments"] == "prepares value"
    assert outer["called_function_names"] == ["helper"]


def test_scan_file_records_default_argument_names(tmp_path):
    sample = tmp_path / "defaults.py"
    sample.write_text(
        "def configure(path, retries=3, *, timeout=None, required):\n"
        "    return path, retries, timeout, required\n",
        encoding="utf-8",
    )

    result = scan_file_functions(sample)

    assert result["parse_succeeded"] is True
    assert result["functions"][0]["argument_names"] == ["path", "retries", "timeout", "required"]
    assert result["functions"][0]["default_argument_names"] == ["retries", "timeout"]


def test_scan_repo_skips_ignored_directories(tmp_path):
    _write_sample_repo(tmp_path)
    ignored_dir = tmp_path / ".venv"
    ignored_dir.mkdir()
    (ignored_dir / "ignored.py").write_text("def ignored():\n    return None\n", encoding="utf-8")

    result = scan_repo_functions(Path(tmp_path))

    assert result["python_file_count"] == 1
    assert result["function_count"] == 2
    assert {fn["function_name"] for fn in result["functions"]} == {"outer", "helper"}
    assert (tmp_path / ".repo_manager" / "search_rules.json").exists()


def test_scan_repo_uses_repo_local_search_rules(tmp_path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "keep.py").write_text("def keep():\n    return 1\n", encoding="utf-8")
    experiment_dir = tmp_path / "experiments"
    experiment_dir.mkdir()
    (experiment_dir / "skip.py").write_text("def skip():\n    return 2\n", encoding="utf-8")
    rules_dir = tmp_path / ".repo_manager"
    rules_dir.mkdir()
    (rules_dir / "search_rules.json").write_text(
        json.dumps({"include_paths": ["src"], "file_suffixes": [".py"]}),
        encoding="utf-8",
    )

    result = scan_repo_functions(tmp_path)

    assert result["python_file_count"] == 1
    assert [fn["function_name"] for fn in result["functions"]] == ["keep"]
    assert result["search_rules"]["include_paths"] == ["src"]
    assert ".venv" in result["search_rules"]["exclude_dirs"]


def test_scan_repo_excludes_specific_files(tmp_path):
    (tmp_path / "keep.py").write_text("def keep():\n    return 1\n", encoding="utf-8")
    (tmp_path / "main_rocopar.py").write_text("def main_rocopar():\n    return 2\n", encoding="utf-8")
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "main_rocopar_test.py").write_text(
        "def main_rocopar_test():\n    return 3\n",
        encoding="utf-8",
    )
    rules_dir = tmp_path / ".repo_manager"
    rules_dir.mkdir()
    (rules_dir / "search_rules.json").write_text(
        json.dumps(
            {
                "exclude_files": [
                    "main_rocopar.py",
                    "tests/main_rocopar_test.py",
                ],
                "file_suffixes": [".py"],
            }
        ),
        encoding="utf-8",
    )

    result = scan_repo_functions(tmp_path)

    assert result["python_file_count"] == 1
    assert [fn["function_name"] for fn in result["functions"]] == ["keep"]
    assert result["search_rules"]["exclude_files"] == ["main_rocopar.py", "tests/main_rocopar_test.py"]


def test_scan_repo_excludes_globbed_files(tmp_path):
    (tmp_path / "keep.py").write_text("def keep():\n    return 1\n", encoding="utf-8")
    (tmp_path / "main_debug.py").write_text("def main_debug():\n    return 2\n", encoding="utf-8")
    generated_dir = tmp_path / "generated"
    generated_dir.mkdir()
    (generated_dir / "artifact.py").write_text("def artifact():\n    return 3\n", encoding="utf-8")
    rules_dir = tmp_path / ".repo_manager"
    rules_dir.mkdir()
    (rules_dir / "search_rules.json").write_text(
        json.dumps(
            {
                "exclude_globs": [
                    "main_*.py",
                    "generated/*.py",
                ],
                "file_suffixes": [".py"],
            }
        ),
        encoding="utf-8",
    )

    result = scan_repo_functions(tmp_path)

    assert result["python_file_count"] == 1
    assert [fn["function_name"] for fn in result["functions"]] == ["keep"]


def test_structure_scan_respects_search_rules(tmp_path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "keep.py").write_text("def keep():\n    return 1\n", encoding="utf-8")
    old_dir = tmp_path / "old"
    old_dir.mkdir()
    (old_dir / "legacy.py").write_text("def legacy():\n    return 2\n", encoding="utf-8")
    rules_dir = tmp_path / ".repo_manager"
    rules_dir.mkdir()
    (rules_dir / "search_rules.json").write_text(
        json.dumps({"include_paths": ["src"], "file_suffixes": [".py"]}),
        encoding="utf-8",
    )

    structure = analyze_repo_structure(tmp_path)

    assert structure["python_file_count"] == 1
    assert not any(warning["type"] == "suspicious_directory_name" for warning in structure["warnings"])
