"""Review markdown writer for the BoardFlow protocol."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def write_review(
    repo: str | Path,
    task_id: str,
    agent_id: str,
    summary: str,
    findings: list[dict[str, str]] | None = None,
    score_data: dict[str, Any] | None = None,
) -> Path:
    """Create a review Markdown file under .board/reviews/."""
    root = Path(repo)
    review_dir = root / ".board" / "reviews"
    review_dir.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# Review: {task_id}",
        "",
        f"**Reviewer:** {agent_id}",
        "",
        "## Summary",
        "",
        summary,
        "",
    ]

    if findings:
        lines.extend(["## Findings", ""])
        for i, finding in enumerate(findings, start=1):
            severity = finding.get("severity", "info")
            lines.append(f"{i}. **[{severity}]** {finding.get('title', '')}")
            if finding.get("detail"):
                lines.append(f"   - {finding['detail']}")
            if finding.get("suggestion"):
                lines.append(f"   - Suggestion: {finding['suggestion']}")
        lines.append("")

    if score_data:
        lines.extend(
            [
                "## Score",
                "",
                f"- **Total:** {score_data.get('total', 'N/A')} / {score_data.get('max_total', 100)}",
                f"- Correctness: {score_data.get('correctness', {}).get('score', '?')} / 40",
                f"- Hygiene: {score_data.get('hygiene', {}).get('score', '?')} / 20",
                f"- Scope Control: {score_data.get('scope_control', {}).get('score', '?')} / 15",
                f"- Handoff: {score_data.get('handoff', {}).get('score', '?')} / 15",
                f"- Board Consistency: {score_data.get('board_consistency', {}).get('score', '?')} / 10",
                "",
            ]
        )

    lines.extend(["## Notes", "", "Continue from repository-local state, not from chat memory.", ""])

    path = review_dir / f"{task_id}_review.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
