"""Backward compatibility shim for storage lock helpers."""

from core.io.storage.locks import LockAcquireError, file_lock

__all__ = ["LockAcquireError", "file_lock"]
