#!/usr/bin/env python3
"""Generate a Markdown code health report for a repository."""
from __future__ import annotations

import argparse
from pathlib import Path

from _bootstrap import bootstrap_repo_manager_core

# Import the bundled core package when this skill is installed globally.
bootstrap_repo_manager_core()

from repo_manager_core.style.learn_repo_style import (
    read_json,
    write_json,
    resolve_output_path,
    learn_repo_style,
)
from repo_manager_core.style.style_profile import build_profile, build_smell_report
from repo_manager_core.health.generate_health_report import render_review_report
from repo_manager_core.smell_learning import record_feedback, update_smell_rules


def _parse_feedback(value: str) -> tuple[str, str, str]:
    """Parse category:keyword=policy or keyword=policy feedback syntax."""
    if "=" not in value:
        raise ValueError("feedback must use keyword=policy or category:keyword=policy")
    left, policy = value.split("=", 1)
    if ":" in left:
        category, keyword = left.split(":", 1)
    else:
        category, keyword = "patch_keywords", left
    if not category or not keyword or not policy:
        raise ValueError("feedback category, keyword, and policy must be non-empty")
    return category, keyword, policy


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo_path", nargs="?", default=".", help="Repository root. Defaults to the current workspace.")
    parser.add_argument("--output-dir", default="repo_manager_report", help="Output directory for all artifacts.")
    parser.add_argument("--question", default=None, help="Optional user question for the review.")
    parser.add_argument(
        "--feedback",
        action="append",
        default=[],
        help="Explicitly record feedback, e.g. fix=contextual or suspicious_directory_keywords:old=allowed.",
    )
    parser.add_argument("--feedback-reason", default="", help="Reason stored with --feedback events.")
    args = parser.parse_args()
    root = Path(args.repo_path)

    for feedback in args.feedback:
        category, keyword, policy = _parse_feedback(feedback)
        record_feedback(
            root,
            category=category,
            keyword=keyword,
            decision=policy,
            reason=args.feedback_reason,
        )
        update_smell_rules(
            root,
            category=category,
            keyword=keyword,
            policy=policy,
            reason=args.feedback_reason,
        )

    output_dir = resolve_output_path(root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    profile_path = output_dir / "repo_profile.json"
    smell_path = output_dir / "smell_report.json"
    style_path = output_dir / "style_profile.json"
    report_path = output_dir / "code_health_report.md"

    # Keep the scan artifact when present; it is the expensive repository walk.
    # Smell/style artifacts below are cheap and depend on mutable learned rules.
    repo_profile = read_json(profile_path) if profile_path.exists() else build_profile(root)
    write_json(repo_profile, profile_path)

    # Derived artifacts are rebuilt on each report run so changed smell_rules.json
    # or newly recorded feedback immediately affects the report.
    smell_report = build_smell_report(repo_profile)
    write_json(smell_report, smell_path)

    style_profile = learn_repo_style(repo_profile)
    write_json(style_profile, style_path)

    # The Markdown report is the human-facing artifact; the JSON files above are
    # kept for follow-up automation and diffing.
    report = render_review_report(repo_profile, smell_report, style_profile, args.question)
    report_path.write_text(report, encoding="utf-8")
    print(f"Wrote code health report to {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
