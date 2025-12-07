"""Cross-cutting infrastructure concerns for bronze-foundry.

DEPRECATED: Use these canonical packages instead:
    - core.config for configuration
    - core.resilience for retry/circuit breaker
    - core.storage for storage backends

Import from canonical packages directly:
    from core.config import load_config, RootConfig
    from core.resilience import RetryPolicy, CircuitBreaker
    from core.storage import get_storage_backend
"""

# Backward compatibility - redirect to canonical packages
from core import config
from core import resilience
from core import storage

__all__ = [
    "config",
    "resilience",
    "storage",
]
