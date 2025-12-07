"""Backward compatibility shim for storage policy helpers."""

from core.io.storage.policy import (
    StorageMetadata,
    VALID_BOUNDARIES,
    VALID_CLOUD_PROVIDERS,
    VALID_PROVIDER_TYPES,
    enforce_storage_scope,
    validate_storage_metadata,
)

__all__ = [
    "StorageMetadata",
    "VALID_BOUNDARIES",
    "VALID_CLOUD_PROVIDERS",
    "VALID_PROVIDER_TYPES",
    "enforce_storage_scope",
    "validate_storage_metadata",
]
