#!/usr/bin/env python3
"""Detect function smells from a repo profile and output a smell report JSON."""
from __future__ import annotations

import argparse
from pathlib import Path

from repo_manager_core.style.style_profile import build_profile, build_smell_report
from repo_manager_core.style.learn_repo_style import read_json, write_json, resolve_output_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo_path", nargs="?", default=".", help="Repository root.")
    parser.add_argument("--profile", default="outputs/repo_profile.json", help="Path to repo profile JSON (created if missing).")
    parser.add_argument("--output", default="outputs/smell_report.json", help="Output path for smell report JSON.")
    args = parser.parse_args()
    root = Path(args.repo_path)
    profile_path = resolve_output_path(root, args.profile)
    if profile_path.exists():
        repo_profile = read_json(profile_path)
    else:
        repo_profile = build_profile(root)
        write_json(repo_profile, profile_path)
    smell_report = build_smell_report(repo_profile)
    output_path = resolve_output_path(root, args.output)
    write_json(smell_report, output_path)
    print(f"Detected {len(smell_report['warnings'])} warnings in {smell_report['summary']['function_count']} functions")
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
