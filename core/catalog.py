"""
Placeholder catalog integration hooks.

Future implementations can call external services (e.g., OpenMetadata) from here.
"""

from __future__ import annotations

import logging
from typing import Mapping, Any

logger = logging.getLogger(__name__)


def notify_catalog(event_name: str, payload: Mapping[str, Any]) -> None:
    """
    Lightweight hook for emitting catalog events.

    Currently this only logs at INFO level so operators can verify the payload.
    Downstream integrations can replace this function with actual API calls.
    """
    logger.info("Catalog event '%s': %s", event_name, payload)
