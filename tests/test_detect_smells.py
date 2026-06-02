"""Tests for function smell detection — migrated from repo_guardian_studio tests."""
from __future__ import annotations

from repo_manager_core.health.detect_function_smells import detect_function_smells


def _fn(name, calls=None, file_path="module.py", length=3):
    return {
        "file_path": file_path,
        "function_name": name,
        "argument_names": [],
        "start_line": 1,
        "end_line": length,
        "docstring": "",
        "function_length": length,
        "called_function_names": calls or [],
        "parse_succeeded": True,
    }


def test_detects_patch_name_smell():
    report = detect_function_smells([_fn("parse_date_safe")])

    assert any(warning["type"] == "patch_name_smell" for warning in report["warnings"])


def test_patch_name_smell_in_tests_is_low_severity():
    report = detect_function_smells([_fn("test_detects_patch_name_smell", file_path="tests/test_detect_smells.py")])

    warning = next(warning for warning in report["warnings"] if warning["type"] == "patch_name_smell")
    assert warning["severity"] == "low"


def test_detects_unused_function():
    report = detect_function_smells([_fn("used"), _fn("caller", calls=["used"])])

    unused = [warning for warning in report["warnings"] if warning["type"] == "unused_function"]
    assert any(warning["function"] == "caller" for warning in unused)
    assert not any(warning["function"] == "used" for warning in unused)
