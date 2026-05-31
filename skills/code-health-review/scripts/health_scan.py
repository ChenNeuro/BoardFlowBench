#!/usr/bin/env python3
"""Scan a Python repository and output a function profile JSON."""
from __future__ import annotations

import argparse
from pathlib import Path

from repo_manager_core.health.scan_repo_functions import scan_repo_functions
from repo_manager_core.health.analyze_repo_structure import analyze_repo_structure
from repo_manager_core.style.learn_repo_style import write_json, resolve_output_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo_path", nargs="?", default=".", help="Repository root to scan.")
    parser.add_argument("--output", default="outputs/repo_profile.json", help="Output path for repo profile JSON.")
    args = parser.parse_args()
    root = Path(args.repo_path)
    profile = scan_repo_functions(root)
    structure = analyze_repo_structure(root)
    profile["structure_warnings"] = structure["warnings"]
    profile["structure"] = structure
    output_path = resolve_output_path(root, args.output)
    write_json(profile, output_path)
    print(f"Scanned {profile['python_file_count']} files, {profile['function_count']} functions")
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
