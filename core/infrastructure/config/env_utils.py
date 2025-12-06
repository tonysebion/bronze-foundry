"""Reusable helpers for configuration resolution."""

from __future__ import annotations

import logging
import os
import re
from typing import Any, Dict, Iterable

logger = logging.getLogger(__name__)


def resolve_env_vars(value: Any) -> Any:
    """Recursively resolve ${VAR_NAME} placeholders in config values."""
    if isinstance(value, str):
        pattern = re.compile(r"\$\{([^}]+)\}")

        def replacer(match: re.Match) -> str:
            var_name = match.group(1)
            env_value = os.environ.get(var_name)
            if env_value is None:
                logger.warning(
                    f"Environment variable {var_name} not found, keeping placeholder"
                )
                return match.group(0)
            return env_value

        return pattern.sub(replacer, value)
    if isinstance(value, dict):
        return {k: resolve_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [resolve_env_vars(item) for item in value]
    return value


def resolve_env_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve env vars for all values in a dictionary."""
    return {k: resolve_env_vars(v) for k, v in data.items()}
