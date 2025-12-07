from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_runtime_loaders = None


def _get_runtime_loaders():
    global _runtime_loaders
    if _runtime_loaders is None:
        _runtime_loaders = import_module("core.runtime.config.loaders")
    return _runtime_loaders


def load_config(
    path: str, *, strict: bool = False, enable_env_substitution: bool = True
) -> Any:
    """Legacy compatibility shim for load_config."""

    return _get_runtime_loaders().load_config(
        path, strict=strict, enable_env_substitution=enable_env_substitution
    )


def load_configs(
    path: str, *, strict: bool = False, enable_env_substitution: bool = True
) -> List[Any]:
    """Legacy compatibility shim for load_configs."""

    return _get_runtime_loaders().load_configs(
        path, strict=strict, enable_env_substitution=enable_env_substitution
    )


def load_config_with_env(
    config_path: Path, env_config_path: Optional[Path] = None
) -> Tuple[Any, Optional[Any]]:
    """Legacy shim to load dataset + environment config."""

    return _get_runtime_loaders().load_config_with_env(
        config_path, env_config_path=env_config_path
    )


def ensure_root_config(cfg: Dict[str, Any]) -> Any:
    """Legacy shim to ensure typed RootConfig instances."""

    return _get_runtime_loaders().ensure_root_config(cfg)


__all__ = [
    "ensure_root_config",
    "load_config",
    "load_config_with_env",
    "load_configs",
]
