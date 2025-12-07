"""Core infrastructure I/O layer.

Provides storage backends, HTTP clients, and extractor base classes.

Subpackages:
    extractors/ - Base extractor classes and registry
    http/       - HTTP clients and authentication
    storage/    - Storage backends (S3, Azure, local)
"""

from core.infrastructure.io.extractors import (
    BaseExtractor,
    ExtractionResult,
    get_extractor_class,
    register_extractor,
)
from core.infrastructure.io.storage import (
    BaseCloudStorage,
    get_storage_backend,
    StorageBackend,
)
from core.infrastructure.io.http import (
    AsyncApiClient,
    is_async_enabled,
)

__all__ = [
    # Extractors
    "BaseExtractor",
    "ExtractionResult",
    "get_extractor_class",
    "register_extractor",
    # Storage
    "BaseCloudStorage",
    "get_storage_backend",
    "StorageBackend",
    # HTTP
    "AsyncApiClient",
    "is_async_enabled",
]
