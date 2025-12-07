"""Backward compatibility shim to the new core.io.storage package."""

from core.io.storage import (
    AzureStorage,
    BaseCloudStorage,
    HealthCheckResult,
    LocalStorage,
    S3Storage,
    StorageBackend,
    get_backend_factory,
    get_storage_backend,
    list_backends,
    register_backend,
    register_storage_backend,
    resolve_backend_type,
)

__all__ = [
    "AzureStorage",
    "BaseCloudStorage",
    "HealthCheckResult",
    "LocalStorage",
    "S3Storage",
    "StorageBackend",
    "get_backend_factory",
    "get_storage_backend",
    "list_backends",
    "register_backend",
    "register_storage_backend",
    "resolve_backend_type",
]
