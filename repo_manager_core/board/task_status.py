"""Shared status constants for the BoardFlow handoff protocol."""

from __future__ import annotations

VALID_STATUSES = {"TODO", "IN_PROGRESS", "BLOCKED", "READY_FOR_REVIEW", "DONE"}
ENTRY_POINT_NAMES = {"main", "run", "app"}
