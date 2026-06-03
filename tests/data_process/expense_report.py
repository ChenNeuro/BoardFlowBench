"""Generate a monthly expense report from an expense CSV file."""
from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable


DATE_FORMATS = (
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%m/%d/%Y",
    "%d/%m/%Y",
    "%Y-%m-%d %H:%M:%S",
)

REQUIRED_COLUMNS = {"date", "amount", "category"}


@dataclass(frozen=True)
class Expense:
    """A normalized expense row."""

    spent_on: date
    amount: Decimal
    category: str


def normalize_header(header: str) -> str:
    return header.strip().lower().replace(" ", "_")


def parse_date(value: str) -> date:
    """Parse common CSV date formats into a date."""
    text = value.strip()
    if not text:
        raise ValueError("date is empty")

    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue

    try:
        return datetime.fromisoformat(text).date()
    except ValueError as exc:
        raise ValueError(f"unsupported date format: {value!r}") from exc


def parse_amount(value: str) -> Decimal:
    """Parse an amount such as '$1,234.50' or '(23.10)'."""
    text = value.strip()
    if not text:
        raise ValueError("amount is empty")

    is_negative = text.startswith("(") and text.endswith(")")
    if is_negative:
        text = text[1:-1]

    text = re.sub(r"[^0-9.+-]", "", text)
    if not text:
        raise ValueError(f"amount has no numeric value: {value!r}")

    try:
        amount = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"invalid amount: {value!r}") from exc

    return -amount if is_negative else amount


def read_expenses(csv_path: str | Path) -> list[Expense]:
    """Read and normalize expenses from a CSV file."""
    path = Path(csv_path)
    expenses: list[Expense] = []

    with path.open("r", newline="", encoding="utf-8-sig") as input_file:
        reader = csv.DictReader(input_file)
        if reader.fieldnames is None:
            raise ValueError("CSV file has no header row")

        field_map = {normalize_header(name): name for name in reader.fieldnames}
        missing = REQUIRED_COLUMNS - set(field_map)
        if missing:
            missing_text = ", ".join(sorted(missing))
            raise ValueError(f"CSV missing required column(s): {missing_text}")

        for line_number, row in enumerate(reader, start=2):
            try:
                category = row[field_map["category"]].strip()
                if not category:
                    raise ValueError("category is empty")

                expenses.append(
                    Expense(
                        spent_on=parse_date(row[field_map["date"]]),
                        amount=parse_amount(row[field_map["amount"]]),
                        category=category,
                    )
                )
            except ValueError as exc:
                raise ValueError(f"{path}:{line_number}: {exc}") from exc

    return expenses


def summarize_by_month_category(expenses: Iterable[Expense]) -> list[dict[str, str]]:
    """Aggregate expenses by month and category."""
    totals: dict[tuple[str, str], dict[str, Decimal | int]] = defaultdict(
        lambda: {"total_amount": Decimal("0"), "count": 0}
    )

    for expense in expenses:
        month = expense.spent_on.strftime("%Y-%m")
        key = (month, expense.category)
        totals[key]["total_amount"] += expense.amount
        totals[key]["count"] += 1

    report_rows: list[dict[str, str]] = []
    for month, category in sorted(totals):
        total = totals[(month, category)]["total_amount"]
        count = totals[(month, category)]["count"]
        report_rows.append(
            {
                "month": month,
                "category": category,
                "total_amount": format_money(total),
                "count": str(count),
            }
        )

    return report_rows


def format_money(value: Decimal | int) -> str:
    amount = Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{amount:.2f}"


def export_monthly_report(rows: Iterable[dict[str, str]], output_path: str | Path) -> None:
    """Write monthly report rows to CSV."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=("month", "category", "total_amount", "count"),
        )
        writer.writeheader()
        writer.writerows(rows)


def generate_monthly_report(input_path: str | Path, output_path: str | Path) -> None:
    expenses = read_expenses(input_path)
    rows = summarize_by_month_category(expenses)
    export_monthly_report(rows, output_path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a monthly category expense report from a CSV file."
    )
    parser.add_argument("input_csv", help="Expense CSV with date, amount, and category columns.")
    parser.add_argument(
        "-o",
        "--output",
        default="monthly_report.csv",
        help="Output CSV path. Defaults to monthly_report.csv.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    generate_monthly_report(args.input_csv, args.output)


if __name__ == "__main__":
    main()
