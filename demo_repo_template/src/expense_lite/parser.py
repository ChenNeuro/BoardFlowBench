"""Parsing helpers for the Expense Lite demo."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


def normalize_date(value: str) -> str:
    """Normalize a date string for an expense record."""
    if not isinstance(value, str):
        raise ValueError("date must be a string")

    text = value.strip()
    for date_format in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            parsed = datetime.strptime(text, date_format)
            return parsed.date().isoformat()
        except ValueError:
            continue

    raise ValueError("date must use YYYY-MM-DD or YYYY/MM/DD format")


def load_expenses_json(path: str) -> list[dict]:
    """Load JSON expense records from a local file."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("expense JSON must contain a list of records")
    if not all(isinstance(item, dict) for item in data):
        raise ValueError("each expense record must be an object")
    return data
