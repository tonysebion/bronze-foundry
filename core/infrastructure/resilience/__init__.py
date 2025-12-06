"""Resilience patterns for bronze-foundry.

This package contains failure handling and recovery patterns:
- retry: RetryPolicy, CircuitBreaker, RateLimiter, execute_with_retry
- late_data: Late data detection and handling (allow, reject, quarantine)
- constants: Default values for resilience patterns
"""

from .constants import (
    DEFAULT_MAX_ATTEMPTS,
    DEFAULT_BASE_DELAY,
    DEFAULT_MAX_DELAY,
    DEFAULT_BACKOFF_MULTIPLIER,
    DEFAULT_JITTER,
    DEFAULT_FAILURE_THRESHOLD,
    DEFAULT_COOLDOWN_SECONDS,
    DEFAULT_HALF_OPEN_MAX_CALLS,
    DEFAULT_LATE_DATA_THRESHOLD_DAYS,
    DEFAULT_QUARANTINE_PATH,
    DEFAULT_CHUNK_SIZE_BYTES,
    DEFAULT_STORAGE_TIMEOUT_SECONDS,
)
from .retry import (
    RetryPolicy,
    CircuitBreaker,
    CircuitState,
    RateLimiter,
    execute_with_retry,
    execute_with_retry_async,
    wrap_storage_error,
    wrap_extraction_error,
    wrap_requests_exception,
    wrap_boto3_exception,
    wrap_azure_exception,
)
from .late_data import (
    LateDataMode,
    LateDataConfig,
    LateDataResult,
    LateDataHandler,
    BackfillWindow,
    build_late_data_handler,
    parse_backfill_window,
)

__all__ = [
    # Constants
    "DEFAULT_MAX_ATTEMPTS",
    "DEFAULT_BASE_DELAY",
    "DEFAULT_MAX_DELAY",
    "DEFAULT_BACKOFF_MULTIPLIER",
    "DEFAULT_JITTER",
    "DEFAULT_FAILURE_THRESHOLD",
    "DEFAULT_COOLDOWN_SECONDS",
    "DEFAULT_HALF_OPEN_MAX_CALLS",
    "DEFAULT_LATE_DATA_THRESHOLD_DAYS",
    "DEFAULT_QUARANTINE_PATH",
    "DEFAULT_CHUNK_SIZE_BYTES",
    "DEFAULT_STORAGE_TIMEOUT_SECONDS",
    # Retry and circuit breaker
    "RetryPolicy",
    "CircuitBreaker",
    "CircuitState",
    "execute_with_retry",
    "execute_with_retry_async",
    # Rate limiting
    "RateLimiter",
    # Error wrapping
    "wrap_storage_error",
    "wrap_extraction_error",
    "wrap_requests_exception",
    "wrap_boto3_exception",
    "wrap_azure_exception",
    # Late data
    "LateDataMode",
    "LateDataConfig",
    "LateDataResult",
    "LateDataHandler",
    "BackfillWindow",
    "build_late_data_handler",
    "parse_backfill_window",
]
