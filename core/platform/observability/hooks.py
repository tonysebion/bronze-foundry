"""Resilience instrumentation hooks for observability consumers."""

from __future__ import annotations

import logging
from typing import Callable, List, Optional

logger = logging.getLogger(__name__)

ResilienceStateHook = Callable[[str, Optional[str], str], None]

_hooks: List[ResilienceStateHook] = []


def emit_resilience_state(
    component_name: str, breaker_key: Optional[str], state: str
) -> None:
    """Invoke registered resilience hooks (best-effort)."""
    for hook in list(_hooks):
        try:
            hook(component_name, breaker_key, state)
        except Exception as exc:  # pragma: no cover - best effort
            logger.debug(
                "Observability resilience hook failed (%s:%s -> %s): %s",
                component_name,
                breaker_key,
                state,
                exc,
            )


def register_resilience_state_hook(hook: ResilienceStateHook) -> Callable[[], None]:
    """Register a callback to receive resilience state changes."""

    _hooks.append(hook)

    def _unregister() -> None:
        try:
            _hooks.remove(hook)
        except ValueError:
            pass

    return _unregister


def list_resilience_hooks() -> List[ResilienceStateHook]:
    """Return a snapshot of registered resilience hooks."""

    return list(_hooks)


__all__ = [
    "ResilienceStateHook",
    "emit_resilience_state",
    "register_resilience_state_hook",
    "list_resilience_hooks",
]
