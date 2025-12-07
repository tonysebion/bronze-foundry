"""Compatibility shim exposing Bronze storage and writer dataclasses."""

from __future__ import annotations

from core.domain.services.processing import ChunkWriterConfig, StoragePlan

__all__ = [
    "ChunkWriterConfig",
    "StoragePlan",
]
