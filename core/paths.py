from __future__ import annotations

from pathlib import Path
from datetime import date, datetime

from core.patterns import LoadPattern
from core.partitioning import build_bronze_partition


def build_bronze_relative_path(cfg: dict, run_date: date) -> str:
    platform_cfg = cfg["platform"]
    source_cfg = cfg["source"]

    bronze = platform_cfg["bronze"]
    partitioning = bronze.get("partitioning", {})
    use_dt = partitioning.get("use_dt_partition", True)

    partition_strategy = partitioning.get("partition_strategy", "date")

    # Try to get path structure from config; fallback to defaults
    path_structure = cfg.get("path_structure", {})
    bronze_keys = path_structure.get("bronze", {}) if isinstance(path_structure, dict) else {}
    
    system_key = bronze_keys.get("system_key", "system")
    entity_key = bronze_keys.get("entity_key", "table")
    pattern_key = bronze_keys.get("pattern_key", "pattern")
    date_key = bronze_keys.get("date_key", "dt")

    system = source_cfg["system"]
    table = source_cfg["table"]

    base_path = f"{system_key}={system}/{entity_key}={table}/"

    run_cfg = source_cfg.get("run", {})
    load_pattern = run_cfg.get("load_pattern", LoadPattern.FULL.value)
    bronze_options = bronze.get("options", {})
    run_cfg = cfg["source"].get("run", {})
    pattern_folder = (
        bronze_options.get("pattern_folder")
        or run_cfg.get("pattern_folder")
        or load_pattern
    )
    if pattern_folder:
        base_path += f"{pattern_key}={pattern_folder}/"

    if not use_dt:
        return base_path

    if partition_strategy == "date":
        partition = build_bronze_partition(cfg, run_date)
        return partition.relative_path().as_posix() + "/"
    elif partition_strategy == "hourly":
        current_hour = datetime.now().strftime("%H")
        return f"{base_path}{date_key}={run_date.isoformat()}/hour={current_hour}/"
    elif partition_strategy == "timestamp":
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        return f"{base_path}{date_key}={run_date.isoformat()}/batch={timestamp}/"
    elif partition_strategy == "batch_id":
        from datetime import datetime as dt
        import uuid

        batch_id = (
            run_cfg.get("batch_id")
            or f"{dt.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        )
        return f"{base_path}{date_key}={run_date.isoformat()}/batch_id={batch_id}/"
    else:
        return f"{base_path}{date_key}={run_date.isoformat()}/"


def build_silver_partition_path(
    silver_base: Path,
    domain: str,
    entity: str,
    version: int,
    load_partition_name: str,
    include_pattern_folder: bool,
    load_pattern: LoadPattern,
    run_date: date,
    path_structure: dict | None = None,
    pattern_folder: str | None = None,
) -> Path:
    # Extract path structure keys for silver layer
    if path_structure and isinstance(path_structure, dict):
        silver_keys = path_structure.get("silver", {})
    else:
        silver_keys = {}

    domain_key = silver_keys.get("domain_key", "domain")
    entity_key = silver_keys.get("entity_key", "entity")
    version_key = silver_keys.get("version_key", "v")
    pattern_key = silver_keys.get("pattern_key", "pattern")
    load_date_key = silver_keys.get("load_date_key", "load_date")

    # Build path: domain/entity/v{version}/[pattern/]load_date
    path = silver_base / f"{domain_key}={domain}" / f"{entity_key}={entity}" / f"{version_key}{version}"
    if include_pattern_folder:
        # Use pattern_folder if provided, otherwise fall back to load_pattern enum value
        pattern_value = pattern_folder if pattern_folder else load_pattern.value
        path = path / f"{pattern_key}={pattern_value}"
    path = path / f"{load_date_key}={run_date.isoformat()}"
    return path
