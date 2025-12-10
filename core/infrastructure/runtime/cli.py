"""Shared CLI helpers for configuration, logging, and webhooks."""

from __future__ import annotations

import argparse
import logging
from datetime import date
from typing import List, Optional

from core.foundation.primitives.logging import setup_logging
from core.infrastructure.runtime.options import RunOptions


def parse_config_paths(config_value: Optional[str]) -> List[str]:
    """Normalize a comma-separated --config argument into individual paths."""
    if not config_value:
        return []
    return [token.strip() for token in config_value.split(",") if token.strip()]


def parse_run_date(date_value: Optional[str]) -> Optional[date]:
    """Convert an ISO date string into a date object."""
    if not date_value:
        return None
    return date.fromisoformat(date_value)


def configure_logging_from_args(
    args: argparse.Namespace,
    *,
    log_format_attr: str = "log_format",
    verbose_attr: str = "verbose",
    quiet_attr: str = "quiet",
    use_colors: bool = True,
) -> None:
    """Configure logging based on shared CLI flags."""
    verbose = bool(getattr(args, verbose_attr, False))
    quiet = bool(getattr(args, quiet_attr, False))
    log_format = getattr(args, log_format_attr, None)
    level = logging.DEBUG if verbose else logging.ERROR if quiet else logging.INFO
    setup_logging(level=level, format_type=log_format, use_colors=use_colors)


def select_webhooks(
    args: argparse.Namespace,
    run_options: Optional[RunOptions],
    *,
    success: bool,
    success_attr: str = "on_success_webhook",
    failure_attr: str = "on_failure_webhook",
) -> List[str]:
    """Pick the appropriate success/failure webhook list."""
    if run_options:
        return (
            run_options.on_success_webhooks
            if success
            else run_options.on_failure_webhooks
        )
    attr = success_attr if success else failure_attr
    raw = getattr(args, attr, None)
    return list(raw) if isinstance(raw, list) else raw or []


__all__ = [
    "configure_logging_from_args",
    "parse_config_paths",
    "parse_run_date",
    "select_webhooks",
]
