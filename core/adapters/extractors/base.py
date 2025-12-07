"""Backward compatibility shim for extractor base utilities."""

from core.io.extractors.base import (
    BaseExtractor,
    EXTRACTOR_REGISTRY,
    ExtractionResult,
    get_extractor_class,
    list_extractor_types,
    register_extractor,
)

__all__ = [
    "BaseExtractor",
    "EXTRACTOR_REGISTRY",
    "ExtractionResult",
    "get_extractor_class",
    "list_extractor_types",
    "register_extractor",
]
