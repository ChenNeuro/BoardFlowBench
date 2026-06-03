"""Command-line entry point for Expense Lite."""

from __future__ import annotations

import argparse
from pathlib import Path

from .parser import load_expenses_json
from .report import render_markdown
from .summary import monthly_summary
from .validator import validate_expense


def main(argv: list[str] | None = None) -> int:
    """Run the Expense Lite CLI."""
    parser = argparse.ArgumentParser(prog="expense-lite")
    parser.add_argument("input_json", help="Path to an expense JSON file.")
    parser.add_argument(
        "--output",
        default=None,
        help="Optional path for a Markdown report artifact.",
    )
    args = parser.parse_args(argv)

    records = load_expenses_json(args.input_json)
    expenses = [validate_expense(record) for record in records]
    rendered = render_markdown(monthly_summary(expenses))

    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")

    return 0
