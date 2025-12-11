"\"\"\"Helpers for reading Bronze partitions from cloud storage.\"\"\""

from __future__ import annotations

from pathlib import Path
from typing import Any, Tuple

from core.infrastructure.config import DatasetConfig, EnvironmentConfig
from core.infrastructure.io.storage.uri import StorageURI
from core.infrastructure.io.storage.fsspec import create_filesystem


def _normalize_bronze_key(prefix: str | None, bronze_path: Path) -> str:
    bronze_key = str(bronze_path).replace("\\\\", "/")
    if prefix:
        prefix_value = str(prefix).rstrip("/")
        bronze_key = f"{prefix_value}/{bronze_key}"
    return bronze_key


def build_bronze_storage_uri(
    dataset: DatasetConfig, bronze_path: Path, env_config: EnvironmentConfig
) -> StorageURI:
    """Build an S3 StorageURI for a Bronze partition."""
    bucket_ref = dataset.bronze.output_bucket or "bronze_data"
    if not env_config.s3:
        raise ValueError("S3 configuration is required to resolve Bronze partitions.")
    bucket = env_config.s3.get_bucket(bucket_ref)
    bronze_key = _normalize_bronze_key(dataset.bronze.output_prefix, bronze_path)
    return StorageURI(
        backend="s3",
        bucket=bucket,
        key=bronze_key,
        original=f"s3://{bucket}/{bronze_key}",
    )


def prepare_bronze_s3_filesystem(
    dataset: DatasetConfig, bronze_path: Path, env_config: EnvironmentConfig
) -> Tuple[StorageURI, Any]:
    """Prepare the StorageURI and filesystem for Bronze S3 partitions."""
    uri = build_bronze_storage_uri(dataset, bronze_path, env_config)
    fs = create_filesystem(uri, env_config)
    return uri, fs
