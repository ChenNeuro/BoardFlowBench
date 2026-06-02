#!/usr/bin/env python3
"""Detect function smells from a repo profile and output a smell report JSON."""
from __future__ import annotations

import argparse
from pathlib import Path

from _bootstrap import bootstrap_repo_manager_core

# Allows this globally installed script to find repo_manager_core without asking
# the user to set PYTHONPATH in every target workspace.
bootstrap_repo_manager_core()

from repo_manager_core.style.style_profile import build_profile, build_smell_report, refresh_structure_profile
from repo_manager_core.style.learn_repo_style import read_json, write_json, resolve_output_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo_path", nargs="?", default=".", help="Repository root. Defaults to the current workspace.")
    parser.add_argument("--profile", default="repo_manager_report/repo_profile.json", help="Path to repo profile JSON (created if missing).")
    parser.add_argument("--output", default="repo_manager_report/smell_report.json", help="Output path for smell report JSON.")
    args = parser.parse_args()
    root = Path(args.repo_path)
    profile_path = resolve_output_path(root, args.profile)

    # Reuse the scan artifact when present so scan -> smell -> report workflows
    # all describe the same repository snapshot.
    if profile_path.exists():
        repo_profile = read_json(profile_path)
    else:
        repo_profile = build_profile(root)
    repo_profile = refresh_structure_profile(repo_profile, root)
    write_json(repo_profile, profile_path)

    smell_report = build_smell_report(repo_profile)
    output_path = resolve_output_path(root, args.output)
    write_json(smell_report, output_path)
    print(f"Detected {len(smell_report['warnings'])} warnings in {smell_report['summary']['function_count']} functions")
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
