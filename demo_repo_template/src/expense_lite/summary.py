"""Monthly summary helpers for Expense Lite."""

from __future__ import annotations


def monthly_summary(expenses: list[dict]) -> dict:
    """Summarize expenses by month and category."""
    totals: dict[str, dict[str, float]] = {}

    for expense in expenses:
        month = str(expense["date"])[:7]
        category = str(expense["category"])
        amount = float(expense["amount"])
        totals.setdefault(month, {})
        totals[month][category] = round(totals[month].get(category, 0.0) + amount, 2)

    return {
        month: {
            category: totals[month][category]
            for category in sorted(totals[month])
        }
        for month in sorted(totals)
    }
