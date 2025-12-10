"""Chunk coordination helper for Bronze writes."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.domain.services.processing.chunk_config import (
    build_chunk_writer_config,
    compute_output_formats,
)
from core.foundation.primitives.patterns import LoadPattern
from core.infrastructure.io.storage import get_storage_backend
from core.infrastructure.io.storage.plan import StoragePlan
from core.infrastructure.runtime.chunking import ChunkProcessor, ChunkWriter, chunk_records

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ChunkWriteResult:
    chunk_count: int
    chunk_files: List[Path]
    storage_plan: Optional[StoragePlan]
    output_formats: Dict[str, bool]


class ChunkCoordinator:
    """Central chunking helper moved into infrastructure."""

    def __init__(self) -> None:
        self._logger = logger

    def write_chunks(
        self,
        *,
        records: List[Dict[str, Any]],
        run_cfg: Dict[str, Any],
        platform_cfg: Dict[str, Any],
        load_pattern: LoadPattern,
        bronze_path: Path,
        relative_path: str,
    ) -> ChunkWriteResult:
        bronze_output = platform_cfg["bronze"]["output_defaults"]
        parallel_workers = int(run_cfg.get("parallel_workers", 1))
        max_rows_per_file = int(run_cfg.get("max_rows_per_file", 0))
        max_file_size_mb = run_cfg.get("max_file_size_mb")

        chunks = chunk_records(records, max_rows_per_file, max_file_size_mb)
        output_formats = compute_output_formats(run_cfg, bronze_output)

        storage_enabled = run_cfg.get("storage_enabled", run_cfg.get("s3_enabled", False))
        storage_backend = get_storage_backend(platform_cfg) if storage_enabled else None
        if storage_backend:
            logger.info(
                "Initialized %s storage backend",
                storage_backend.get_backend_type(),
            )

        writer_config, storage_plan = build_chunk_writer_config(
            bronze_output,
            run_cfg,
            bronze_path,
            relative_path,
            load_pattern,
            storage_backend,
            output_formats,
        )

        writer = ChunkWriter(writer_config)
        processor = ChunkProcessor(writer, parallel_workers)
        chunk_files = processor.process(chunks)

        return ChunkWriteResult(
            chunk_count=len(chunk_files),
            chunk_files=chunk_files,
            storage_plan=storage_plan,
            output_formats=output_formats,
        )
