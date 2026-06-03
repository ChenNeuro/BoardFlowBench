#!/usr/bin/env python3
"""Learn repository code style and write profile to .repo_manager/."""
from __future__ import annotations

import argparse
from pathlib import Path

from _bootstrap import bootstrap_repo_manager_core

bootstrap_repo_manager_core()

from repo_manager_core.style.learn_repo_style import learn_repo_style, write_json, resolve_output_path
from repo_manager_core.style.style_profile import build_profile


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo_path", nargs="?", default=".", help="Repository root to analyze.")
    parser.add_argument("--output", default=".repo_manager/repo_style_profile.json", help="Output path for style profile.")
    args = parser.parse_args()
    root = Path(args.repo_path)
    profile = build_profile(root)
    style = learn_repo_style(profile)
    output_path = resolve_output_path(root, args.output)
    write_json(style, output_path)
    print(f"Wrote style profile to {output_path} ({style['function_count']} functions)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
