#!/usr/bin/env python3
"""Generate a Markdown code health report for a repository."""
from __future__ import annotations

import argparse
from pathlib import Path

from repo_manager_core.style.learn_repo_style import (
    read_json,
    write_json,
    resolve_output_path,
    learn_repo_style,
)
from repo_manager_core.style.style_profile import build_profile, build_smell_report
from repo_manager_core.health.generate_health_report import render_review_report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo_path", nargs="?", default=".", help="Repository root.")
    parser.add_argument("--output-dir", default="outputs", help="Output directory for all artifacts.")
    parser.add_argument("--question", default=None, help="Optional user question for the review.")
    args = parser.parse_args()
    root = Path(args.repo_path)
    output_dir = resolve_output_path(root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    profile_path = output_dir / "repo_profile.json"
    smell_path = output_dir / "smell_report.json"
    style_path = output_dir / "style_profile.json"
    report_path = output_dir / "code_health_report.md"

    # Build or load from cache
    repo_profile = read_json(profile_path) if profile_path.exists() else build_profile(root)
    write_json(repo_profile, profile_path)

    smell_report = read_json(smell_path) if smell_path.exists() else build_smell_report(repo_profile)
    write_json(smell_report, smell_path)

    style_profile = read_json(style_path) if style_path.exists() else learn_repo_style(repo_profile)
    write_json(style_profile, style_path)

    # Render final report
    report = render_review_report(repo_profile, smell_report, style_profile, args.question)
    report_path.write_text(report, encoding="utf-8")
    print(f"Wrote code health report to {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
