"""Pattern verification test data module.

This module provides infrastructure for generating multi-batch test data
to verify load pattern business logic (SNAPSHOT, INCREMENTAL_APPEND,
INCREMENTAL_MERGE, CURRENT_HISTORY).

Key components:
- PatternTestDataGenerator: Generates multi-batch time series data
- PatternAssertions: Configuration-driven assertion validation
"""

from tests.integration.pattern_data.generators import (
    PatternTestDataGenerator,
    PatternScenario,
)

__all__ = [
    "PatternTestDataGenerator",
    "PatternScenario",
]
