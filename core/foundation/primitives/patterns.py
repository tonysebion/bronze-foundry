"""Shared load-pattern utilities for Bronze/Silver workflows.

Load Patterns per Spec Section 4:
- SNAPSHOT: Complete snapshot each run (replaces all data)
- INCREMENTAL_APPEND: Append new/changed records (insert-only)
- INCREMENTAL_MERGE: Merge/upsert with existing data

Legacy pattern names (deprecated):
- full -> SNAPSHOT
- cdc -> INCREMENTAL_APPEND
- current_history -> kept for backward compatibility during transition
"""

from __future__ import annotations

from enum import Enum

from core.foundation.primitives.base import RichEnumMixin


class LoadPattern(RichEnumMixin, str, Enum):
    """Supported extraction patterns per spec Section 4."""

    # New spec-compliant names
    SNAPSHOT = "snapshot"
    INCREMENTAL_APPEND = "incremental_append"
    INCREMENTAL_MERGE = "incremental_merge"

    # Legacy compatibility (will be removed in future)
    CURRENT_HISTORY = "current_history"

    @property
    def chunk_prefix(self) -> str:
        """Prefix used for chunk file names."""
        value_str = str(self.value)
        return value_str.replace("_", "-")

    @property
    def folder_name(self) -> str:
        """Return folder name fragment for this pattern."""
        value_str = str(self.value)
        return f"pattern={value_str}"

    @property
    def is_incremental(self) -> bool:
        """Check if this pattern requires incremental/watermark logic."""
        return self in (self.INCREMENTAL_APPEND, self.INCREMENTAL_MERGE)

    @property
    def requires_merge(self) -> bool:
        """Check if this pattern requires merge/upsert logic."""
        return self == self.INCREMENTAL_MERGE


# RichEnumMixin class variables must be set AFTER class definition due to Enum metaclass
# These enable the base class normalize()/describe() methods to work correctly
LoadPattern._default = "SNAPSHOT"
LoadPattern._aliases = {
    "full": "snapshot",
    "cdc": "incremental_append",
}
LoadPattern._descriptions = {
    "snapshot": "Complete snapshot each run (replaces all data)",
    "incremental_append": "Append new/changed records (insert-only CDC)",
    "incremental_merge": "Merge/upsert with existing data",
    "current_history": "Maintains split current + history tables (SCD Type 2)",
}
