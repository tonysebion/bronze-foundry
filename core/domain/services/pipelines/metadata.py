"""Shared metadata helpers used by Bronze and Silver pipelines."""

from __future__ import annotations

from typing import Any, Dict, List, Sequence


def _maybe_add(payload: Dict[str, Any], key: str, value: Any) -> None:
    if value is not None:
        payload[key] = value


def build_batch_metadata_extra(
    *,
    load_pattern: str,
    bronze_path: str,
    domain: str,
    entity: str,
    primary_keys: Sequence[str] | None = None,
    order_column: str | None = None,
    version: int | None = None,
    load_partition_name: str | None = None,
    include_pattern_folder: bool | None = None,
    partition_columns: Sequence[str] | None = None,
    write_parquet: bool | None = None,
    write_csv: bool | None = None,
    parquet_compression: str | None = None,
    normalization: Dict[str, Any] | None = None,
    schema: Dict[str, Any] | None = None,
    error_handling: Dict[str, Any] | None = None,
    require_checksum: bool | None = None,
    silver_model: str | None = None,
    artifacts: Dict[str, List[str]] | None = None,
    extra: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Build shared metadata payload used by both pipelines."""
    payload: Dict[str, Any] = {
        "load_pattern": load_pattern,
        "bronze_path": bronze_path,
        "domain": domain,
        "entity": entity,
    }

    if primary_keys:
        payload["primary_keys"] = list(primary_keys)
    _maybe_add(payload, "order_column", order_column)
    _maybe_add(payload, "version", version)
    _maybe_add(payload, "load_partition_name", load_partition_name)
    _maybe_add(payload, "include_pattern_folder", include_pattern_folder)
    if partition_columns:
        payload["partition_columns"] = list(partition_columns)
    _maybe_add(payload, "write_parquet", write_parquet)
    _maybe_add(payload, "write_csv", write_csv)
    _maybe_add(payload, "parquet_compression", parquet_compression)
    _maybe_add(payload, "normalization", normalization)
    _maybe_add(payload, "schema", schema)
    _maybe_add(payload, "error_handling", error_handling)
    _maybe_add(payload, "artifacts", artifacts)
    _maybe_add(payload, "require_checksum", require_checksum)
    _maybe_add(payload, "silver_model", silver_model)

    if extra:
        payload.update(extra)

    return payload


def build_checksum_metadata_extra(
    *,
    load_pattern: str,
    bronze_path: str,
    schema_snapshot: Sequence[Dict[str, str]],
    stats: Dict[str, Any],
    runtime_seconds: float | None = None,
) -> Dict[str, Any]:
    """Build extra metadata applied to checksum manifests."""
    payload: Dict[str, Any] = {
        "load_pattern": load_pattern,
        "bronze_path": bronze_path,
        "schema": list(schema_snapshot),
        "stats": stats,
    }
    _maybe_add(payload, "runtime_seconds", runtime_seconds)
    return payload
