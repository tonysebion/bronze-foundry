from __future__ import annotations

import copy
import logging
from typing import Any, Dict

from .typed_models import SilverConfig, DataClassification
from pydantic import ValidationError
from core.deprecation import emit_compat, emit_deprecation, DeprecationSpec
from core.patterns import LoadPattern
from core.storage.policy import validate_storage_metadata

logger = logging.getLogger(__name__)

# Valid values for new spec fields
VALID_DATA_CLASSIFICATIONS = [e.value for e in DataClassification]
VALID_ENVIRONMENTS = ["dev", "staging", "prod", "test", "local"]
VALID_LAYERS = ["bronze", "silver"]
VALID_SCHEMA_EVOLUTION_MODES = ["strict", "allow_new_nullable", "ignore_unknown"]


def _normalize_silver_config(
    raw_silver: Dict[str, Any] | None,
    source: Dict[str, Any],
    load_pattern: LoadPattern,
) -> Dict[str, Any]:
    try:
        model = SilverConfig.from_raw(raw_silver, source, load_pattern)
    except ValidationError as exc:
        error_fields = {err.get("loc", (None,))[0] for err in exc.errors()}
        if "require_checksum" in error_fields:
            raise ValueError("silver.require_checksum must be a boolean") from exc
        raise
    return model.to_dict()


def _validate_spec_fields(cfg: Dict[str, Any]) -> None:
    """Validate new spec fields per Section 2.

    Validates:
    - pipeline_id: Optional string
    - layer: "bronze" or "silver"
    - domain: Optional string
    - environment: "dev", "staging", "prod", "test", "local"
    - data_classification: "public", "internal", "confidential", "restricted"
    - owners: dict with semantic_owner and technical_owner
    - schema_evolution: dict with mode and allow_type_relaxation
    """
    # Validate layer
    layer = cfg.get("layer", "bronze")
    if layer not in VALID_LAYERS:
        raise ValueError(f"layer must be one of {VALID_LAYERS}, got '{layer}'")

    # Validate environment
    environment = cfg.get("environment", "dev")
    if environment not in VALID_ENVIRONMENTS:
        raise ValueError(
            f"environment must be one of {VALID_ENVIRONMENTS}, got '{environment}'"
        )

    # Validate data_classification
    classification = cfg.get("data_classification", "internal")
    if isinstance(classification, str):
        classification = classification.lower()
    if classification not in VALID_DATA_CLASSIFICATIONS:
        raise ValueError(
            f"data_classification must be one of {VALID_DATA_CLASSIFICATIONS}, got '{classification}'"
        )

    # Validate owners
    owners = cfg.get("owners")
    if owners is not None:
        if not isinstance(owners, dict):
            raise ValueError("owners must be a dictionary")
        for key in ("semantic_owner", "technical_owner"):
            if key in owners and owners[key] is not None:
                if not isinstance(owners[key], str):
                    raise ValueError(f"owners.{key} must be a string")

    # Validate schema_evolution
    schema_evolution = cfg.get("schema_evolution")
    if schema_evolution is not None:
        if not isinstance(schema_evolution, dict):
            raise ValueError("schema_evolution must be a dictionary")
        mode = schema_evolution.get("mode", "strict")
        if mode not in VALID_SCHEMA_EVOLUTION_MODES:
            raise ValueError(
                f"schema_evolution.mode must be one of {VALID_SCHEMA_EVOLUTION_MODES}, got '{mode}'"
            )
        allow_relaxation = schema_evolution.get("allow_type_relaxation", False)
        if not isinstance(allow_relaxation, bool):
            raise ValueError("schema_evolution.allow_type_relaxation must be a boolean")

    # Validate pipeline_id if provided
    pipeline_id = cfg.get("pipeline_id")
    if pipeline_id is not None and not isinstance(pipeline_id, str):
        raise ValueError("pipeline_id must be a string")

    # Validate domain if provided
    domain = cfg.get("domain")
    if domain is not None and not isinstance(domain, str):
        raise ValueError("domain must be a string")


def validate_config_dict(cfg: Dict[str, Any]) -> Dict[str, Any]:
    cfg = copy.deepcopy(cfg)

    # Validate top-level sections
    if "platform" not in cfg:
        raise ValueError("Config must contain a 'platform' section")
    if "source" not in cfg:
        raise ValueError("Config must contain a 'source' section")

    # Validate new spec fields (Section 2)
    _validate_spec_fields(cfg)

    platform = cfg["platform"]
    if not isinstance(platform, dict):
        raise ValueError("'platform' must be a dictionary")

    if "bronze" not in platform:
        raise ValueError("Missing platform.bronze section in config")
    bronze = platform["bronze"]
    if not isinstance(bronze, dict):
        raise ValueError("'platform.bronze' must be a dictionary")

    storage_backend = bronze.get("storage_backend", "s3")
    valid_backends = ["s3", "azure", "local"]
    if storage_backend not in valid_backends:
        raise ValueError(
            f"platform.bronze.storage_backend must be one of {valid_backends}"
        )

    if storage_backend == "s3":
        if "s3_connection" not in platform:
            raise ValueError(
                "Missing platform.s3_connection section (required for S3 backend)"
            )
        for key in ("s3_bucket", "s3_prefix"):
            if key not in bronze:
                raise ValueError(
                    f"Missing required key 'platform.bronze.{key}' in config"
                )
    elif storage_backend == "azure":
        if "azure_connection" not in platform:
            raise ValueError(
                "Missing platform.azure_connection section (required for Azure backend)"
            )
        if "azure_container" not in bronze:
            raise ValueError("Azure backend requires platform.bronze.azure_container")
    elif storage_backend == "local":
        if "local_path" not in bronze:
            legacy_output_dir = bronze.get("output_dir")
            if legacy_output_dir:
                bronze["local_path"] = legacy_output_dir
                emit_compat(
                    "Using platform.bronze.output_dir as local_path; add explicit local_path to silence warning",
                    code="CFG001",
                )
                emit_deprecation(
                    DeprecationSpec(
                        code="CFG001",
                        message="Implicit local_path fallback will be removed; define platform.bronze.local_path",
                        since="1.1.0",
                        remove_in="1.3.0",
                    )
                )
            else:
                raise ValueError("Local backend requires platform.bronze.local_path")

    logger.debug("Validated storage backend: %s", storage_backend)
    validate_storage_metadata(cfg["platform"])

    source = cfg["source"]
    if not isinstance(source, dict):
        raise ValueError("'source' must be a dictionary")

    for key in ("system", "table", "run"):
        if key not in source:
            raise ValueError(f"Missing required key 'source.{key}' in config")

    source_type = source.get("type", "api")
    valid_source_types = ["api", "db", "custom", "file"]
    if source_type not in valid_source_types:
        raise ValueError(
            f"Invalid source.type: '{source_type}'. Must be one of {valid_source_types}"
        )

    if source_type == "api" and "api" not in source:
        raise ValueError("source.type='api' requires 'source.api' section")
    if source_type == "db" and "db" not in source:
        raise ValueError("source.type='db' requires 'source.db' section")
    if source_type == "custom" and "custom_extractor" not in source:
        raise ValueError(
            "source.type='custom' requires 'source.custom_extractor' section"
        )
    if source_type == "file" and "file" not in source:
        raise ValueError("source.type='file' requires 'source.file' section")

    if source_type == "custom":
        custom = source["custom_extractor"]
        if "module" not in custom or "class_name" not in custom:
            raise ValueError(
                "source.custom_extractor requires 'module' and 'class_name'"
            )

    if source_type == "file":
        file_cfg = source["file"]
        if not isinstance(file_cfg, dict):
            raise ValueError("source.file must be a dictionary of options")
        if "path" not in file_cfg:
            raise ValueError(
                "source.file requires 'path' to point to the local dataset"
            )
        file_format = file_cfg.get("format")
        valid_formats = ["csv", "tsv", "json", "jsonl", "parquet"]
        if file_format and file_format.lower() not in valid_formats:
            raise ValueError(
                f"source.file.format must be one of {valid_formats} (got '{file_format}')"
            )
        if "delimiter" in file_cfg and not isinstance(file_cfg["delimiter"], str):
            raise ValueError("source.file.delimiter must be a string when provided")
        if "limit_rows" in file_cfg:
            limit_rows = file_cfg["limit_rows"]
            if not isinstance(limit_rows, int) or limit_rows <= 0:
                raise ValueError("source.file.limit_rows must be a positive integer")

    if source_type == "db":
        db = source["db"]
        if "conn_str_env" not in db:
            raise ValueError(
                "source.db requires 'conn_str_env' to specify connection string env var"
            )
        if "base_query" not in db:
            raise ValueError("source.db requires 'base_query' for SQL query")

    if source_type == "api":
        api = source["api"]
        if "base_url" not in api and "url" in api:
            api["base_url"] = api["url"]
            emit_compat("source.api.url key is deprecated; use base_url", code="CFG002")
            emit_deprecation(
                DeprecationSpec(
                    code="CFG002",
                    message="Legacy 'url' field will be removed; rename to base_url",
                    since="1.1.0",
                    remove_in="1.3.0",
                )
            )
        if "endpoint" not in api:
            api["endpoint"] = "/"
            emit_compat("Defaulting missing endpoint to '/'", code="CFG003")
            emit_deprecation(
                DeprecationSpec(
                    code="CFG003",
                    message="Implicit endpoint default will be removed; specify source.api.endpoint explicitly",
                    since="1.1.0",
                    remove_in="1.3.0",
                )
            )
        if "base_url" not in api:
            raise ValueError("source.api requires 'base_url'")
        if "endpoint" not in api:
            raise ValueError("source.api requires 'endpoint'")

    run_cfg = source.get("run", {})
    pattern_value = run_cfg.get("load_pattern", LoadPattern.SNAPSHOT.value)
    pattern = LoadPattern.normalize(pattern_value)
    run_cfg["load_pattern"] = pattern.value

    if "max_file_size_mb" in run_cfg:
        max_size = run_cfg["max_file_size_mb"]
        if not isinstance(max_size, (int, float)) or max_size <= 0:
            raise ValueError("source.run.max_file_size_mb must be a positive number")

    if "parallel_workers" in run_cfg:
        workers = run_cfg["parallel_workers"]
        if not isinstance(workers, int) or workers < 1:
            raise ValueError(
                "source.run.parallel_workers must be a positive integer (1 or greater)"
            )
        if workers > 32:
            logger.warning(
                f"source.run.parallel_workers={workers} is very high and may cause resource issues"
            )

    reference_mode = run_cfg.get("reference_mode")
    if reference_mode is not None:
        if not isinstance(reference_mode, dict):
            raise ValueError("source.run.reference_mode must be a dictionary")
        enabled = reference_mode.get("enabled", True)
        if not isinstance(enabled, bool):
            raise ValueError("source.run.reference_mode.enabled must be a boolean")
        role = reference_mode.get("role", "reference")
        if role not in {"reference", "delta", "auto"}:
            raise ValueError(
                "source.run.reference_mode.role must be one of 'reference', 'delta', or 'auto'"
            )
        cadence = reference_mode.get("cadence_days")
        if cadence is not None:
            if not isinstance(cadence, int) or cadence <= 0:
                raise ValueError(
                    "source.run.reference_mode.cadence_days must be a positive integer"
                )
        delta_patterns = reference_mode.get("delta_patterns", [])
        if delta_patterns and not all(isinstance(p, str) for p in delta_patterns):
            raise ValueError(
                "source.run.reference_mode.delta_patterns must be a list of strings"
            )
        run_cfg["reference_mode"] = {
            "enabled": enabled,
            "role": role,
            "cadence_days": cadence,
            "delta_patterns": delta_patterns,
        }

    partition_strategy = (
        platform.get("bronze", {})
        .get("partitioning", {})
        .get("partition_strategy", "date")
    )
    valid_strategies = ["date", "hourly", "timestamp", "batch_id"]
    if partition_strategy not in valid_strategies:
        raise ValueError(
            f"platform.bronze.partitioning.partition_strategy must be one of {valid_strategies}"
        )

    normalized_silver = _normalize_silver_config(cfg.get("silver"), source, pattern)
    run_cfg["silver"] = normalized_silver
    cfg["silver"] = normalized_silver

    source.setdefault("config_name", f"{source['system']}.{source['table']}")
    logger.info(
        "Successfully validated config for %s.%s", source["system"], source["table"]
    )
    return cfg
