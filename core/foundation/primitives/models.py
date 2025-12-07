"""Core model types for bronze-foundry.

This module contains foundational model enums that are used across layers.
These are pure data structures with minimal dependencies.
"""

from __future__ import annotations

from enum import Enum

from core.foundation.primitives.base import RichEnumMixin
from core.foundation.primitives.patterns import LoadPattern


class SilverModel(RichEnumMixin, str, Enum):
    """Silver transformation model types.

    Defines how Bronze data is transformed into Silver:
    - SCD_TYPE_1: Keep only latest version of each business key
    - SCD_TYPE_2: Track current + historical rows (slowly changing dimension)
    - INCREMENTAL_MERGE: Emit incremental changes for merge targets
    - FULL_MERGE_DEDUPE: Emit deduplicated snapshot for full merges
    - PERIODIC_SNAPSHOT: Emit exact Bronze snapshot for periodic refreshes
    """

    SCD_TYPE_1 = "scd_type_1"
    SCD_TYPE_2 = "scd_type_2"
    INCREMENTAL_MERGE = "incremental_merge"
    FULL_MERGE_DEDUPE = "full_merge_dedupe"
    PERIODIC_SNAPSHOT = "periodic_snapshot"

    @classmethod
    def default_for_load_pattern(cls, pattern: LoadPattern) -> "SilverModel":
        """Return the default SilverModel for a given LoadPattern."""
        mapping = {
            LoadPattern.SNAPSHOT: cls.PERIODIC_SNAPSHOT,
            LoadPattern.INCREMENTAL_APPEND: cls.INCREMENTAL_MERGE,
            LoadPattern.INCREMENTAL_MERGE: cls.INCREMENTAL_MERGE,
            LoadPattern.CURRENT_HISTORY: cls.SCD_TYPE_2,
        }
        return mapping.get(pattern, cls.PERIODIC_SNAPSHOT)

    @property
    def requires_dedupe(self) -> bool:
        """Check if this model requires deduplication logic."""
        return self in {self.SCD_TYPE_1, self.SCD_TYPE_2, self.FULL_MERGE_DEDUPE}

    @property
    def emits_history(self) -> bool:
        """Check if this model emits history records."""
        return self == self.SCD_TYPE_2


# RichEnumMixin class variables must be set AFTER class definition due to Enum metaclass
# No _default - SilverModel requires explicit value (None raises ValueError)
SilverModel._aliases = {
    "scd_type_1": "scd_type_1",
    "scd1": "scd_type_1",
    "scd type 1": "scd_type_1",
    "scd_type_2": "scd_type_2",
    "scd2": "scd_type_2",
    "scd type 2": "scd_type_2",
    "incremental_merge": "incremental_merge",
    "incremental": "incremental_merge",
    "full_merge_dedupe": "full_merge_dedupe",
    "full_merge": "full_merge_dedupe",
    "full merge": "full_merge_dedupe",
    "periodic_snapshot": "periodic_snapshot",
    "periodic": "periodic_snapshot",
}
SilverModel._descriptions = {
    "scd_type_1": "Keep only the latest version of each business key (SCD Type 1)",
    "scd_type_2": "Track current + historical rows for each business key (SCD Type 2)",
    "incremental_merge": "Emit incremental changes for merge targets (CDC/timestamp)",
    "full_merge_dedupe": "Emit a deduplicated snapshot suitable for full merges",
    "periodic_snapshot": "Emit the exact Bronze snapshot for periodic refreshes",
}

# Backward compatibility alias
SILVER_MODEL_ALIASES = SilverModel._aliases
