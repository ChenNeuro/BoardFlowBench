"""Markdown report rendering for Expense Lite."""

from __future__ import annotations


def render_markdown(summary: dict) -> str:
    """Render a monthly summary as Markdown."""
    lines = ["# Expense Report", ""]

    grand_total = 0.0
    for month in sorted(summary):
        lines.append(f"## {month}")
        month_total = 0.0
        for category in sorted(summary[month]):
            amount = float(summary[month][category])
            month_total += amount
            lines.append(f"- {category}: ${amount:.2f}")
        grand_total += month_total
        lines.append(f"- Total: ${month_total:.2f}")
        lines.append("")

    lines.append(f"Grand total: ${grand_total:.2f}")
    return "\n".join(lines) + "\n"
