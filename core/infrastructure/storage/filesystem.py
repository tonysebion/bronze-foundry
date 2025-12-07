"""Backward compatibility shim for storage filesystem utilities."""

from core.io.storage import filesystem as filesystem_impl

create_filesystem = filesystem_impl.create_filesystem
get_fs_for_path = filesystem_impl.get_fs_for_path
fsspec = filesystem_impl.fsspec

__all__ = ["create_filesystem", "get_fs_for_path", "fsspec"]
