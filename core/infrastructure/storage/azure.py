"""Backward compatibility shim for the Azure storage backend."""

from core.io.storage.azure import AzureStorage, AzureStorageBackend

__all__ = ["AzureStorage", "AzureStorageBackend"]
