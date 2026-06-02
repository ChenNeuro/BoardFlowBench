"""Tests for reviewdog diagnostic export."""

from __future__ import annotations

import json

from repo_manager_core.health.reviewdog_export import export_diagnostics, main, write_rdjsonl


def test_export_diagnostics_uses_relative_path_and_function_line(tmp_path):
    source = tmp_path / "pkg" / "parser.py"
    source.parent.mkdir()
    source.write_text("\n\ndef parse_date_safe(value):\n    return value\n", encoding="utf-8")
    smells = {
        "warnings": [
            {
                "severity": "medium",
                "type": "patch_name_smell",
                "file": str(source),
                "function": "parse_date_safe",
                "reason": "Function name contains keyword 'safe'.",
                "suggestion": "Review whether the abstraction is durable.",
            }
        ]
    }
    profile = {
        "functions": [
            {
                "file_path": str(source),
                "function_name": "parse_date_safe",
                "start_line": 3,
            }
        ]
    }

    diagnostics = export_diagnostics(smells, repo=tmp_path, repo_profile=profile)

    assert diagnostics == [
        {
            "message": (
                "[patch_name_smell] Function name contains keyword 'safe'. "
                "Suggestion: Review whether the abstraction is durable."
            ),
            "location": {
                "path": "pkg/parser.py",
                "range": {"start": {"line": 3, "column": 1}},
            },
            "severity": "WARNING",
            "code": {"value": "patch_name_smell"},
            "source": {"name": "repo-manager-health"},
        }
    ]


def test_export_diagnostics_skips_non_file_findings(tmp_path):
    smells = {
        "warnings": [
            {
                "severity": "low",
                "type": "suspicious_directory_name",
                "file": str(tmp_path / "old"),
                "function": "",
                "reason": "Directory requires human review.",
            }
        ]
    }

    assert export_diagnostics(smells, repo=tmp_path) == []


def test_write_rdjsonl_and_cli(tmp_path):
    source = tmp_path / "sample.py"
    source.write_text("def sample():\n    return 1\n", encoding="utf-8")
    input_path = tmp_path / "smells.json"
    output_path = tmp_path / "reviewdog" / "diagnostics.rdjsonl"
    input_path.write_text(
        json.dumps(
            {
                "warnings": [
                    {
                        "severity": "low",
                        "type": "unused_function",
                        "file": str(source),
                        "function": "sample",
                        "reason": "No scanned call site.",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    assert main(["--input", str(input_path), "--output", str(output_path), "--repo", str(tmp_path)]) == 0
    diagnostic = json.loads(output_path.read_text(encoding="utf-8"))
    assert diagnostic["location"]["path"] == "sample.py"
    assert diagnostic["location"]["range"]["start"]["line"] == 1
    assert diagnostic["severity"] == "INFO"

    empty_output = tmp_path / "empty.rdjsonl"
    write_rdjsonl([], empty_output)
    assert empty_output.read_text(encoding="utf-8") == ""
