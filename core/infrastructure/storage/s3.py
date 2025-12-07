"""Backward compatibility shim for the S3 storage backend."""

from core.io.storage.s3 import S3Storage, S3StorageBackend

__all__ = ["S3Storage", "S3StorageBackend"]
