"""Backward compatibility shim for storage filesystem utilities."""

from core.io.storage.filesystem import create_filesystem, get_fs_for_path

__all__ = ["create_filesystem", "get_fs_for_path"]
