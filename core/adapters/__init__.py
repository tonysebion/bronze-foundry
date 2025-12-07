"""Backward compatibility shim for core.adapters."""
from core.domain.adapters import *
from core.domain.adapters import extractors, quality, schema, polybase

__all__ = ["extractors", "quality", "schema", "polybase"]
