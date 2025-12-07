"""OpenMetadata integration package for Bronze Foundry (L1 Platform).

This package provides the OpenMetadata API client for catalog integration.
"""

from __future__ import annotations

from core.platform.om.client import (
    ColumnSchema,
    LineageEdge,
    OpenMetadataClient,
    TableSchema,
)

__all__ = ["ColumnSchema", "LineageEdge", "OpenMetadataClient", "TableSchema"]
