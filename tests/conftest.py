"""Shared test fixtures and configuration."""
from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"
REPO_ROOT = Path(__file__).resolve().parents[1]
