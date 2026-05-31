#!/usr/bin/env python3
"""Compare two repo profiles and report new/resolved warnings and style drift."""
from __future__ import annotations

import argparse
from pathlib import Path

from repo_manager_core.style.learn_repo_style import read_json, write_json, resolve_output_path
from repo_manager_core.style.style_profile import build_profile, build_smell_report
from repo_manager_core.style.learn_repo_style import learn_repo_style


def _warning_key(w: dict) -> str:
    return f"{w.get('type','')}:{w.get('file','')}:{w.get('function','')}:{w.get('reason','')}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", required=True, help="Path to before-profile JSON or repo root.")
    parser.add_argument("--after", required=True, help="Path to after-profile JSON or repo root.")
    parser.add_argument("--output", default="outputs/diff_report.json", help="Output path for diff report.")
    args = parser.parse_args()

    def _load_or_build(path_str: str) -> dict:
        p = Path(path_str)
        if p.is_dir():
            return build_profile(p)
        return read_json(p)

    before_profile = _load_or_build(args.before)
    after_profile = _load_or_build(args.after)

    before_smells = build_smell_report(before_profile)
    after_smells = build_smell_report(after_profile)

    before_keys = {_warning_key(w) for w in before_smells.get("warnings", [])}
    after_keys = {_warning_key(w) for w in after_smells.get("warnings", [])}

    new_warnings = [w for w in after_smells.get("warnings", []) if _warning_key(w) not in before_keys]
    resolved_warnings = [w for w in before_smells.get("warnings", []) if _warning_key(w) not in after_keys]

    before_style = learn_repo_style(before_profile)
    after_style = learn_repo_style(after_profile)

    diff = {
        "before_function_count": before_profile.get("function_count", 0),
        "after_function_count": after_profile.get("function_count", 0),
        "new_warning_count": len(new_warnings),
        "resolved_warning_count": len(resolved_warnings),
        "new_warnings": new_warnings,
        "resolved_warnings": resolved_warnings,
        "style_drift": {
            "before_snake_case": before_style.get("snake_case_function_count", 0),
            "after_snake_case": after_style.get("snake_case_function_count", 0),
            "before_patch_like": before_style.get("patch_like_function_count", 0),
            "after_patch_like": after_style.get("patch_like_function_count", 0),
            "before_docstring": before_style.get("docstring_function_count", 0),
            "after_docstring": after_style.get("docstring_function_count", 0),
        },
    }

    repo_root = Path(args.after) if Path(args.after).is_dir() else Path(".")
    output_path = resolve_output_path(repo_root, args.output)
    write_json(diff, output_path)
    print(f"Diff: +{len(new_warnings)} new, -{len(resolved_warnings)} resolved")
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
