"""Shared mixins for extractor functionality.

These mixins provide common patterns used across multiple extractor implementations
to reduce code duplication and ensure consistent behavior.

Note: For retry/resilience functionality, use ResilientExtractorMixin from
core.domain.adapters.extractors.resilience instead of decorator-based retries.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from core.platform.resilience import RateLimiter

logger = logging.getLogger(__name__)

__all__ = ["RateLimitMixin"]


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
