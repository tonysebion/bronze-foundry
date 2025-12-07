"""Shared mixins for extractor functionality.

These mixins provide common patterns used across multiple extractor implementations
to reduce code duplication and ensure consistent behavior.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, Optional, TypeVar

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from core.platform.resilience import RateLimiter


logger = logging.getLogger(__name__)

T = TypeVar("T")


class RateLimitMixin:
    """Mixin providing rate limiter creation from configuration."""

    def create_rate_limiter(
        self,
        source_cfg: Dict[str, Any],
        run_cfg: Dict[str, Any],
        component: str,
        env_var: Optional[str] = None,
    ) -> Optional[RateLimiter]:
        """Create a rate limiter from source and run configuration.

        Args:
            source_cfg: Source-specific configuration (e.g., db_cfg, api_cfg)
            run_cfg: Run configuration from source.run
            component: Component name for logging
            env_var: Optional environment variable override for rate limit

        Returns:
            Configured RateLimiter, or None if rate limiting is disabled
        """
        return RateLimiter.from_config(
            source_cfg,
            run_cfg,
            component=component,
            env_var=env_var,
        )


def create_retry_decorator(
    max_attempts: int = 3,
    multiplier: float = 1.0,
    min_wait: int = 2,
    max_wait: int = 10,
    retry_exceptions: tuple = (Exception,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Create a configured retry decorator.

    This factory function creates a tenacity retry decorator with consistent
    settings used across extractors.

    Args:
        max_attempts: Maximum number of retry attempts
        multiplier: Exponential backoff multiplier
        min_wait: Minimum wait time in seconds
        max_wait: Maximum wait time in seconds
        retry_exceptions: Tuple of exception types to retry on

    Returns:
        Configured retry decorator

    Example:
        @create_retry_decorator(max_attempts=5, retry_exceptions=(ConnectionError,))
        def my_function():
            ...
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=multiplier, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(retry_exceptions),
        reraise=True,
    )


# Default retry decorator matching existing extractor behavior
default_retry = create_retry_decorator(
    max_attempts=3,
    multiplier=1.0,
    min_wait=2,
    max_wait=10,
    retry_exceptions=(Exception,),
)
