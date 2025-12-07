"""Legacy runtime shim exposing the new core.runtime package."""
from core.runtime import chunking, context, file_io, metadata, options, paths

__all__ = [
    chunking,
    context,
    file_io,
    metadata,
    options,
    paths,
]
