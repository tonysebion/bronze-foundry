"""Backward compatibility shim for storage path helpers."""

from core.io.storage.path_utils import build_partition_path, sanitize_partition_value

__all__ = ["build_partition_path", "sanitize_partition_value"]
