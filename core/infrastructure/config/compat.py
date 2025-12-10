"""Compatibility helpers for configuration loading."""

from __future__ import annotations

from typing import Any, Dict

from core.foundation.primitives.exceptions import (
    DeprecationSpec,
    emit_compat,
    emit_deprecation,
)

DEFAULT_CONFIG_VERSION = 1


def ensure_config_version(config: Dict[str, Any], *, default: int = DEFAULT_CONFIG_VERSION) -> int:
    """Ensure config_version is present, emitting compat warning if needed."""
    version = config.get("config_version")
    if version is None:
        emit_compat("Config missing config_version; defaulting to 1", code="CFG004")
        version = default
        config["config_version"] = version
    return version


__all__ = [
    "DeprecationSpec",
    "emit_compat",
    "emit_deprecation",
    "DEFAULT_CONFIG_VERSION",
    "ensure_config_version",
]
