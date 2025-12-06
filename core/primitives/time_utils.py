"""Shared time helpers for primitives."""

from __future__ import annotations

from datetime import datetime, timezone


def utc_isoformat() -> str:
    """Return the current UTC timestamp as an ISO string with 'Z' suffix."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
