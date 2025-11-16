"""Core runner that wires config, extractor, IO, and storage together."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from pathlib import Path
from datetime import date, datetime

from core.extractors.base import BaseExtractor
from core.extractors.api_extractor import ApiExtractor
from core.extractors.db_extractor import DbExtractor
from core.extractors.file_extractor import FileExtractor
from core.io import chunk_records
from core.storage import get_storage_backend
from core.patterns import LoadPattern
from core.catalog import report_schema_snapshot, report_quality_snapshot, report_run_metadata
from core.runner.chunks import ChunkProcessor
from core.bronze.base import emit_bronze_metadata, infer_schema
from core.bronze.plan import (
    build_chunk_writer_config,
    compute_output_formats,
    resolve_load_pattern,
)

logger = logging.getLogger(__name__)


def build_extractor(cfg: Dict[str, Any]) -> BaseExtractor:
    src = cfg["source"]
    src_type = src.get("type", "api")

    if src_type == "api":
        return ApiExtractor()
    if src_type == "db":
        return DbExtractor()
    if src_type == "custom":
        custom_cfg = src.get("custom_extractor", {})
        module_name = custom_cfg["module"]
        class_name = custom_cfg["class_name"]

        import importlib

        module = importlib.import_module(module_name)
        cls = getattr(module, class_name)
        return cls()
    if src_type == "file":
        return FileExtractor()

    raise ValueError(f"Unknown source.type: {src_type}")


class ExtractJob:
    def __init__(self, cfg: Dict[str, Any], run_date: date, local_output_base: Path, relative_path: str) -> None:
        self.cfg = cfg
        self.run_date = run_date
        self.relative_path = relative_path
        self._out_dir = local_output_base / relative_path
        self.created_files: List[Path] = []
        self.load_pattern: Optional[LoadPattern] = None
        self.output_formats: Dict[str, bool] = {}
        self.storage_plan: Optional[StoragePlan] = None
        self.schema_snapshot: List[Dict[str, str]] = []

    @property
    def source_cfg(self) -> Dict[str, Any]:
        return self.cfg["source"]

    def run(self) -> int:
        try:
            return self._run()
        except Exception:
            self._cleanup_on_failure()
            raise

    def _run(self) -> int:
        extractor = build_extractor(self.cfg)
        logger.info(
            f"Starting extract for {self.source_cfg['system']}.{self.source_cfg['table']} on {self.run_date}"
        )
        records, new_cursor = extractor.fetch_records(self.cfg, self.run_date)
        logger.info(f"Retrieved {len(records)} records from extractor")
        if not records:
            logger.warning("No records returned from extractor")
            return 0

        self.schema_snapshot = infer_schema(records)

        chunk_count, chunk_files = self._process_chunks(records)
        self.created_files.extend(chunk_files)
        self._emit_metadata(record_count=len(records), chunk_count=chunk_count, cursor=new_cursor)

        logger.info("Finished Bronze extract run successfully")
        return 0

    def _process_chunks(self, records: List[Dict[str, Any]]) -> tuple[int, List[Path]]:
        run_cfg = self.source_cfg["run"]
        self.load_pattern = resolve_load_pattern(run_cfg)
        logger.info(f"Load pattern: {self.load_pattern.value} ({self.load_pattern.describe()})")

        max_rows_per_file = int(run_cfg.get("max_rows_per_file", 0))
        max_file_size_mb = run_cfg.get("max_file_size_mb")
        chunks = chunk_records(records, max_rows_per_file, max_file_size_mb)

        platform_cfg = self.cfg["platform"]
        bronze_output = platform_cfg["bronze"]["output_defaults"]
        self.output_formats = compute_output_formats(run_cfg, bronze_output)
        parquet_compression = run_cfg.get(
            "parquet_compression", bronze_output.get("default_parquet_compression", "snappy")
        )

        storage_enabled = run_cfg.get("storage_enabled", run_cfg.get("s3_enabled", False))
        storage_backend = get_storage_backend(platform_cfg) if storage_enabled else None
        if storage_backend:
            logger.info(f"Initialized {storage_backend.get_backend_type()} storage backend")

        self._out_dir.mkdir(parents=True, exist_ok=True)

        writer_config, self.storage_plan = build_chunk_writer_config(
            bronze_output,
            run_cfg,
            self._out_dir,
            self.relative_path,
            self.load_pattern,
            storage_backend,
            self.output_formats,
        )

        parallel_workers = int(run_cfg.get("parallel_workers", 1))
        processor = ChunkProcessor(writer_config, parallel_workers)
        chunk_files = processor.process(chunks)
        return len(chunks), chunk_files

    def _emit_metadata(self, record_count: int, chunk_count: int, cursor: Optional[str]) -> None:
        reference_mode = self.source_cfg["run"].get("reference_mode")
        metadata_path = emit_bronze_metadata(
            self._out_dir,
            self.run_date,
            self.source_cfg["system"],
            self.source_cfg["table"],
            self.relative_path,
            self.output_formats,
            self.load_pattern,
            reference_mode,
            self.schema_snapshot,
            chunk_count,
            record_count,
            cursor,
            self.created_files,
        )
        self.created_files.append(metadata_path)

        stats = {
            "record_count": record_count,
            "chunk_count": chunk_count,
            "artifact_count": len(self.created_files),
        }
        dataset_id = f"bronze:{self.source_cfg['system']}.{self.source_cfg['table']}"
        report_schema_snapshot(dataset_id, self.schema_snapshot)
        report_quality_snapshot(dataset_id, stats)
        report_run_metadata(
            dataset_id,
            {
                "run_date": self.run_date.isoformat(),
                "load_pattern": self.load_pattern.value if self.load_pattern else LoadPattern.FULL.value,
                "chunk_count": chunk_count,
                "record_count": record_count,
                "relative_path": self.relative_path,
                "status": "success",
            },
        )

    def _cleanup_on_failure(self) -> None:
        run_cfg = self.source_cfg.get("run", {})
        cleanup_on_failure = run_cfg.get("cleanup_on_failure", True)
        if not (cleanup_on_failure and self.created_files):
            return

        logger.info(f"Cleaning up {len(self.created_files)} files due to failure")
        for file_path in self.created_files:
            try:
                if file_path.exists():
                    file_path.unlink()
                    logger.debug(f"Deleted {file_path}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup {file_path}: {cleanup_error}")


def run_extract(
    cfg: Dict[str, Any],
    run_date: date,
    local_output_base: Path,
    relative_path: str,
) -> int:
    job = ExtractJob(cfg, run_date, local_output_base, relative_path)
    try:
        return job.run()
    except Exception as exc:
        logger.error(f"Extract failed: {exc}", exc_info=True)
        raise
