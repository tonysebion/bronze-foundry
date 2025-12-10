"""Legacy entrypoint for path/partition helpers re-exporting the partition builder."""

from __future__ import annotations

from datetime import datetime as _datetime

from core.infrastructure.runtime.paths.partition_builder import (
    BronzePartition,
    SilverPartition,
    build_bronze_partition,
    build_bronze_relative_path,
    build_silver_partition,
    build_silver_partition_path,
)

datetime = _datetime

__all__ = [
    "BronzePartition",
    "SilverPartition",
    "build_bronze_partition",
    "build_silver_partition",
    "build_bronze_relative_path",
    "build_silver_partition_path",
]
