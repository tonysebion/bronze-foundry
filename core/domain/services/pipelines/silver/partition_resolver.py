"""Partition column resolution for Silver outputs.

This module extracts the complex partition column resolution logic from SilverProcessor
into a dedicated class with clear, focused methods for each strategy.
"""

from __future__ import annotations

import logging
from typing import Dict, List, TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from core.infrastructure.config import DatasetConfig

logger = logging.getLogger(__name__)

__all__ = ["PartitionColumnResolver"]


class PartitionColumnResolver:
    """Resolves partition columns for Silver output based on dataset configuration.

    Supports three strategies:
    1. V1 unified temporal configuration (record_time_partition)
    2. Legacy explicit partition_by configuration
    3. Default derivation based on entity kind
    """

    def __init__(self, dataset: "DatasetConfig") -> None:
        """Initialize resolver with dataset configuration.

        Args:
            dataset: Dataset configuration containing silver partition settings
        """
        self.dataset = dataset
        self.silver = dataset.silver

    def resolve(self, frames: Dict[str, pd.DataFrame]) -> List[str]:
        """Resolve partition columns and add them to frames if needed.

        Args:
            frames: Dictionary of output DataFrames to potentially modify

        Returns:
            List of partition column names

        Raises:
            ValueError: If partition configuration is invalid or source columns missing
        """
        # Strategy 1: V1 unified temporal configuration
        if self.silver.record_time_partition:
            return self._resolve_v1_temporal(frames)

        # Strategy 2: Legacy explicit partition_by
        if self.silver.partition_by:
            return self._resolve_legacy_partition_by(frames)

        # Strategy 3: Default based on entity kind
        return self._resolve_default(frames)

    def _resolve_v1_temporal(self, frames: Dict[str, pd.DataFrame]) -> List[str]:
        """Resolve V1 unified temporal partition configuration.

        Args:
            frames: Output DataFrames to modify

        Returns:
            List containing the partition key

        Raises:
            ValueError: If record_time_column is missing or not in frames
        """
        partition_key = self.silver.record_time_partition
        source_column = self.silver.record_time_column

        if not partition_key:
            raise ValueError(
                "record_time_partition is not configured"
            )

        if not source_column:
            raise ValueError(
                "record_time_partition specified but record_time_column is missing"
            )

        for frame in frames.values():
            if source_column not in frame.columns:
                raise ValueError(
                    f"record_time_column '{source_column}' not found in Silver output"
                )
            frame[partition_key] = pd.to_datetime(
                frame[source_column], errors="coerce"
            ).dt.date.astype(str)

        return [partition_key]

    def _resolve_legacy_partition_by(self, frames: Dict[str, pd.DataFrame]) -> List[str]:
        """Resolve legacy explicit partition_by configuration.

        Args:
            frames: Output DataFrames to modify

        Returns:
            List of partition column names

        Raises:
            ValueError: If partition columns cannot be derived
        """
        partition_by = self.silver.partition_by

        for frame in frames.values():
            for column in partition_by:
                if column in frame.columns:
                    continue

                if column.endswith("_dt"):
                    self._derive_date_column(frame, column)
                else:
                    raise ValueError(
                        f"Partition column '{column}' missing from Silver output"
                    )

        return partition_by

    def _derive_date_column(self, frame: pd.DataFrame, column: str) -> None:
        """Derive a date partition column from timestamp columns.

        Args:
            frame: DataFrame to modify
            column: Target date column name (should end with _dt)

        Raises:
            ValueError: If no source timestamp column is available
        """
        source = self._find_timestamp_source(frame)
        if not source:
            raise ValueError(f"Unable to derive partition column '{column}'")

        frame[column] = pd.to_datetime(
            frame[source], errors="coerce"
        ).dt.date.astype(str)

    def _find_timestamp_source(self, frame: pd.DataFrame) -> str | None:
        """Find the best timestamp source column in a frame.

        Args:
            frame: DataFrame to search

        Returns:
            Column name if found, None otherwise
        """
        # Prefer event_ts_column, fall back to change_ts_column
        if self.silver.event_ts_column and self.silver.event_ts_column in frame.columns:
            return self.silver.event_ts_column
        if self.silver.change_ts_column and self.silver.change_ts_column in frame.columns:
            return self.silver.change_ts_column
        return None

    def _resolve_default(self, frames: Dict[str, pd.DataFrame]) -> List[str]:
        """Resolve default partition based on entity kind.

        Args:
            frames: Output DataFrames to modify

        Returns:
            List containing the default partition column name
        """
        if self.silver.entity_kind.is_event_like:
            return self._resolve_default_event(frames)
        return self._resolve_default_state(frames)

    def _resolve_default_event(self, frames: Dict[str, pd.DataFrame]) -> List[str]:
        """Resolve default partition for event-like entities.

        Args:
            frames: Output DataFrames to modify

        Returns:
            List containing the event date partition column
        """
        column = (self.silver.event_ts_column or "event_ts") + "_dt"

        for frame in frames.values():
            source = self._find_timestamp_source(frame)
            if source:
                frame[column] = pd.to_datetime(
                    frame[source], errors="coerce"
                ).dt.date.astype(str)

        return [column]

    def _resolve_default_state(self, frames: Dict[str, pd.DataFrame]) -> List[str]:
        """Resolve default partition for state-like entities.

        Args:
            frames: Output DataFrames to modify

        Returns:
            List containing the effective_from_dt column
        """
        column = "effective_from_dt"

        for frame in frames.values():
            if "effective_from" in frame.columns:
                frame[column] = pd.to_datetime(
                    frame["effective_from"], errors="coerce"
                ).dt.date.astype(str)
            elif self.silver.change_ts_column and self.silver.change_ts_column in frame.columns:
                frame[column] = pd.to_datetime(
                    frame[self.silver.change_ts_column], errors="coerce"
                ).dt.date.astype(str)

        return [column]
