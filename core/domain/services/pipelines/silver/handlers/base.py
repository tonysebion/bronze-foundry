"""Base class for Silver pattern handlers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict

import pandas as pd

if TYPE_CHECKING:
    from core.infrastructure.config import DatasetConfig


class BasePatternHandler(ABC):
    """Base class for Silver pattern handlers.

    Each handler processes a specific entity kind (EVENT, STATE, DERIVED_EVENT, etc.)
    according to its pattern rules.

    Attributes:
        dataset: The dataset configuration containing Silver processing rules.
    """

    def __init__(self, dataset: "DatasetConfig") -> None:
        """Initialize the handler.

        Args:
            dataset: Dataset configuration with Silver settings.
        """
        self.dataset = dataset

    @abstractmethod
    def process(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """Process DataFrame according to pattern rules.

        Args:
            df: Input DataFrame with prepared data.

        Returns:
            Dict mapping output name to processed DataFrame.
            For example: {"events": df} or {"state_current": df, "state_history": df}
        """
        pass

    @abstractmethod
    def validate(self, df: pd.DataFrame) -> None:
        """Validate DataFrame has required columns for this pattern.

        Args:
            df: Input DataFrame to validate.

        Raises:
            ValueError: If required columns are missing.
        """
        pass

    @property
    def natural_keys(self) -> list[str]:
        """Get natural key columns from dataset config."""
        return self.dataset.silver.natural_keys

    @property
    def event_ts_column(self) -> str | None:
        """Get event timestamp column from dataset config."""
        return self.dataset.silver.event_ts_column

    @property
    def change_ts_column(self) -> str | None:
        """Get change timestamp column from dataset config."""
        return self.dataset.silver.change_ts_column
