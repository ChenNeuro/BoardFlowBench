"""Tests for repo-local smell-rule learning."""
from __future__ import annotations

import json

from repo_manager_core.health.detect_function_smells import detect_function_smells
from repo_manager_core.search_rules import load_search_rules
from repo_manager_core.smell_learning import (
    load_default_smell_rules,
    load_smell_rules,
    record_feedback,
    update_smell_rules,
)


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


def test_learned_allowed_policy_suppresses_patch_keyword(tmp_path):
    rules = load_default_smell_rules()
    rules["patch_keywords"]["safe"] = {
        "policy": "allowed",
        "source": "user_feedback",
        "reason": "Repository naming convention",
    }

    report = detect_function_smells([_fn("safe_parse")], smell_rules=rules)

    assert not any(warning["type"] == "patch_name_smell" for warning in report["warnings"])
    assert report["learned_policies"][0]["keyword"] == "safe"
    assert report["learned_policies"][0]["policy"] == "allowed"


def test_contextual_policy_warns_only_when_unused(tmp_path):
    rules = load_default_smell_rules()
    rules["patch_keywords"]["fix"] = {"policy": "contextual", "source": "user_feedback"}

    used_report = detect_function_smells(
        [_fn("fix_timezone_offset"), _fn("caller", calls=["fix_timezone_offset"])],
        smell_rules=rules,
    )
    unused_report = detect_function_smells([_fn("fix_timezone_offset")], smell_rules=rules)

    assert not any(warning["type"] == "patch_name_smell" for warning in used_report["warnings"])
    assert any(warning["type"] == "patch_name_smell" for warning in unused_report["warnings"])


def test_feedback_is_recorded_and_loaded_as_rules(tmp_path):
    record_feedback(
        tmp_path,
        category="patch_keywords",
        keyword="fix",
        decision="contextual",
        reason="Used in public APIs",
    )
    update_smell_rules(
        tmp_path,
        category="patch_keywords",
        keyword="fix",
        policy="contextual",
        reason="Used in public APIs",
    )

    feedback_path = tmp_path / ".repo_manager" / "user_feedback.jsonl"
    rules_path = tmp_path / ".repo_manager" / "smell_rules.json"
    event = json.loads(feedback_path.read_text(encoding="utf-8").strip())
    loaded = load_smell_rules(tmp_path)

    assert rules_path.exists()
    assert event["keyword"] == "fix"
    assert event["policy"] == "contextual"
    assert loaded["patch_keywords"]["fix"]["policy"] == "contextual"


def test_default_rules_are_loaded_from_json():
    rules = load_default_smell_rules()

    assert "safe" in rules["patch_keywords"]
    assert "parse" in rules["helper_keywords"]
    assert "old" in rules["suspicious_file_keywords"]


def test_missing_rule_files_are_created_from_defaults(tmp_path):
    smell_rules = load_smell_rules(tmp_path)
    search_rules = load_search_rules(tmp_path)

    assert (tmp_path / ".repo_manager" / "smell_rules.json").exists()
    assert (tmp_path / ".repo_manager" / "search_rules.json").exists()
    assert "safe" in smell_rules["patch_keywords"]
    assert ".py" in search_rules["file_suffixes"]
