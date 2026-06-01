"""Validation helpers for Expense Lite records."""

from __future__ import annotations

from .parser import normalize_date


REQUIRED_FIELDS = ("date", "description", "category", "amount")


def validate_expense(record: dict) -> dict:
    """Validate and normalize a single expense record."""
    if not isinstance(record, dict):
        raise ValueError("expense record must be an object")

    missing = [field for field in REQUIRED_FIELDS if field not in record]
    if missing:
        raise ValueError(f"missing required fields: {', '.join(missing)}")

    amount = record["amount"]
    if isinstance(amount, bool) or not isinstance(amount, (int, float)):
        raise ValueError("amount must be a number")

    return {
        "date": normalize_date(record["date"]),
        "description": str(record["description"]).strip(),
        "category": str(record["category"]).strip(),
        "amount": float(amount),
    }
