"""High-level schema evolution checking for Bronze extraction.

This module provides a facade for schema evolution checking that:
- Resolves configuration from source/run config hierarchy
- Converts schema snapshots to SchemaSpec format
- Performs compatibility checks and reports errors

Moved from core.orchestration.runner.job to maintain layer boundaries.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from core.domain.adapters.schema.evolution import (
    EvolutionConfig,
    SchemaEvolution,
    SchemaEvolutionMode,
)
from core.domain.adapters.schema.types import ColumnSpec, DataType, SchemaSpec

logger = logging.getLogger(__name__)

__all__ = ["SchemaEvolutionChecker"]


class SchemaEvolutionChecker:
    """High-level schema evolution checking for Bronze extractions.

    Encapsulates the logic for:
    - Resolving schema evolution config from various config locations
    - Converting schema snapshots (list of dicts) to SchemaSpec
    - Checking schema compatibility between runs
    """

    def __init__(self, cfg: Dict[str, Any]) -> None:
        """Initialize checker with pipeline configuration.

        Args:
            cfg: Full pipeline configuration dict
        """
        self.cfg = cfg
        self._source_cfg = cfg.get("source", {})
        self._evolution_config: Optional[EvolutionConfig] = None

    @property
    def evolution_config(self) -> EvolutionConfig:
        """Get or create evolution config (lazy initialization)."""
        if self._evolution_config is None:
            self._evolution_config = self._resolve_config()
        return self._evolution_config

    def _resolve_config(self) -> EvolutionConfig:
        """Resolve schema evolution config from configuration hierarchy.

        Looks for config in:
        1. source.run.schema_evolution
        2. schema_evolution (top-level)

        Returns:
            Resolved EvolutionConfig
        """
        schema_cfg = self._source_cfg.get("run", {}).get("schema_evolution")
        if not schema_cfg or not isinstance(schema_cfg, dict):
            schema_cfg = self.cfg.get("schema_evolution") or {}
        if not isinstance(schema_cfg, dict):
            schema_cfg = {}

        mode_str = schema_cfg.get("mode", "strict")
        try:
            mode = SchemaEvolutionMode(mode_str)
        except ValueError:
            logger.warning(
                "Unknown schema_evolution.mode '%s', defaulting to strict", mode_str
            )
            mode = SchemaEvolutionMode.STRICT

        protected_columns = schema_cfg.get("protected_columns", [])
        if not isinstance(protected_columns, list):
            protected_columns = []

        return EvolutionConfig(
            mode=mode,
            allow_type_relaxation=schema_cfg.get("allow_type_relaxation", False),
            allow_precision_increase=schema_cfg.get("allow_precision_increase", True),
            protected_columns=protected_columns,
        )

    def schema_spec_from_snapshot(
        self, snapshot: List[Dict[str, Any]]
    ) -> SchemaSpec:
        """Convert a schema snapshot (list of column dicts) to SchemaSpec.

        Args:
            snapshot: List of column definitions with name, dtype, nullable

        Returns:
            SchemaSpec instance
        """
        columns: List[ColumnSpec] = []
        for entry in snapshot:
            name = entry.get("name")
            if not name:
                continue
            dtype = entry.get("dtype", "any")
            columns.append(
                ColumnSpec(
                    name=name,
                    type=DataType.from_string(dtype),
                    nullable=entry.get("nullable", True),
                )
            )
        return SchemaSpec(columns=columns)

    def check_compatibility(
        self,
        previous_schema: Optional[List[Dict[str, Any]]],
        current_schema: Optional[List[Dict[str, Any]]],
    ) -> None:
        """Check schema compatibility between previous and current run.

        Args:
            previous_schema: Schema from previous run (from manifest)
            current_schema: Schema from current run

        Raises:
            RuntimeError: If schemas are incompatible per evolution rules
        """
        if not previous_schema or not current_schema:
            return

        evolution = SchemaEvolution(self.evolution_config)
        previous_spec = self.schema_spec_from_snapshot(previous_schema)
        current_spec = self.schema_spec_from_snapshot(current_schema)
        result = evolution.check_evolution(previous_spec, current_spec)

        if not result.compatible:
            logger.error(
                "Schema drift blocked by evolution rules: %s", result.to_dict()
            )
            raise RuntimeError(
                "Schema drift detected and blocked by configured evolution rules. "
                f"Details: {result.to_dict()}"
            )

    def get_config_for_metadata(self) -> Dict[str, Any]:
        """Get config dict including schema evolution block for metadata.

        Returns:
            Config dict with schema_evolution section included
        """
        metadata_cfg: Dict[str, Any] = dict(self.cfg)
        run_schema = self._source_cfg.get("run", {}).get("schema_evolution")
        if run_schema:
            metadata_cfg["schema_evolution"] = run_schema
        return metadata_cfg
