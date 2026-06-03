"""Tests for expense monthly report generation."""
from __future__ import annotations

import csv
from decimal import Decimal

from expense_report import (
    Expense,
    parse_amount,
    parse_date,
    read_expenses,
    summarize_by_month_category,
    generate_monthly_report,
)


def test_parse_date_supports_common_formats():
    assert parse_date("2026-06-02").isoformat() == "2026-06-02"
    assert parse_date("2026/06/02").isoformat() == "2026-06-02"
    assert parse_date("06/02/2026").isoformat() == "2026-06-02"


def test_parse_amount_supports_currency_commas_and_parentheses():
    assert parse_amount("$1,234.50") == Decimal("1234.50")
    assert parse_amount("(23.10)") == Decimal("-23.10")


def test_summarize_by_month_category():
    rows = summarize_by_month_category(
        [
            Expense(parse_date("2026-06-01"), Decimal("12.25"), "Food"),
            Expense(parse_date("2026-06-02"), Decimal("8.10"), "Food"),
            Expense(parse_date("2026-06-03"), Decimal("40"), "Transport"),
            Expense(parse_date("2026-07-01"), Decimal("5"), "Food"),
        ]
    )

    assert rows == [
        {"month": "2026-06", "category": "Food", "total_amount": "20.35", "count": "2"},
        {
            "month": "2026-06",
            "category": "Transport",
            "total_amount": "40.00",
            "count": "1",
        },
        {"month": "2026-07", "category": "Food", "total_amount": "5.00", "count": "1"},
    ]


def test_generate_monthly_report_writes_csv(tmp_path):
    input_csv = tmp_path / "expenses.csv"
    output_csv = tmp_path / "monthly_report.csv"
    input_csv.write_text(
        "date,category,amount\n"
        "2026-06-01,Food,$12.25\n"
        "2026-06-02,Food,8.10\n"
        "2026-06-03,Transport,40\n",
        encoding="utf-8",
    )

    generate_monthly_report(input_csv, output_csv)

    with output_csv.open(newline="", encoding="utf-8") as output_file:
        rows = list(csv.DictReader(output_file))

    assert rows == [
        {"month": "2026-06", "category": "Food", "total_amount": "20.35", "count": "2"},
        {
            "month": "2026-06",
            "category": "Transport",
            "total_amount": "40.00",
            "count": "1",
        },
    ]


def test_read_expenses_reports_bad_rows(tmp_path):
    input_csv = tmp_path / "expenses.csv"
    input_csv.write_text(
        "date,category,amount\n"
        "bad-date,Food,12.25\n",
        encoding="utf-8",
    )

    try:
        read_expenses(input_csv)
    except ValueError as exc:
        assert "expenses.csv:2" in str(exc)
        assert "unsupported date format" in str(exc)
    else:
        raise AssertionError("read_expenses should reject invalid dates")
