#!/usr/bin/env python3
"""Scan a Python repository and output a function profile JSON."""
from __future__ import annotations

import argparse
from pathlib import Path

from _bootstrap import bootstrap_repo_manager_core

# Keep global skill usage simple: the script can import the bundled core package
# even when the scanned repository is not BoardFlowBench.
bootstrap_repo_manager_core()

from repo_manager_core.health.scan_repo_functions import scan_repo_functions
from repo_manager_core.health.analyze_repo_structure import analyze_repo_structure
from repo_manager_core.style.learn_repo_style import write_json, resolve_output_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo_path", nargs="?", default=".", help="Repository root to scan. Defaults to the current workspace.")
    parser.add_argument("--output", default="repo_manager_report/repo_profile.json", help="Output path for repo profile JSON.")
    args = parser.parse_args()
    root = Path(args.repo_path)

    # The profile is the shared input for later smell, style, and report steps.
    profile = scan_repo_functions(root)

    # Structure warnings are attached to the same JSON so downstream tools only
    # need one profile artifact.
    structure = analyze_repo_structure(root)
    profile["structure_warnings"] = structure["warnings"]
    profile["structure_feedback_questions"] = structure.get("feedback_questions", [])
    profile["structure"] = structure

    # Relative output paths are written inside the scanned repo, not next to the
    # globally installed skill script.
    output_path = resolve_output_path(root, args.output)
    write_json(profile, output_path)
    print(f"Scanned {profile['python_file_count']} files, {profile['function_count']} functions")
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
