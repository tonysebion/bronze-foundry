"""Centralized path & partition abstractions for Bronze and Silver layers."""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from datetime import date
from typing import Dict, Any


@dataclass(frozen=True)
class BronzePartition:
    system: str
    table: str
    pattern: str
    run_date: date
    system_key: str = "system"
    entity_key: str = "table"
    pattern_key: str = "pattern"
    date_key: str = "dt"

    def relative_path(self) -> Path:
        return (
            Path(f"{self.system_key}={self.system}")
            / f"{self.entity_key}={self.table}"
            / f"{self.pattern_key}={self.pattern}"
            / f"{self.date_key}={self.run_date.isoformat()}"
        )


@dataclass(frozen=True)
class SilverPartition:
    domain: str
    entity: str
    version: int
    load_partition_name: str
    run_date: date
    include_pattern_folder: bool
    pattern: str | None = None
    domain_key: str = "domain"
    entity_key: str = "entity"
    version_key: str = "v"
    pattern_key: str = "pattern"
    load_date_key: str = "load_date"

    def base_path(self) -> Path:
        parts = [
            f"{self.domain_key}={self.domain}",
            f"{self.entity_key}={self.entity}",
            f"{self.version_key}{self.version}",
        ]
        if self.include_pattern_folder and self.pattern:
            parts.append(f"{self.pattern_key}={self.pattern}")
        parts.append(f"{self.load_date_key}={self.run_date.isoformat()}")
        return Path("/").joinpath(*parts)  # normalized assembly


def build_bronze_partition(cfg: Dict[str, Any], run_date: date) -> BronzePartition:
    source = cfg["source"]
    platform = cfg["platform"]
    bronze_options = platform.get("bronze", {}).get("options", {})
    pattern_folder = bronze_options.get("pattern_folder")
    run_cfg = source.get("run", {})
    pattern = pattern_folder or run_cfg.get("pattern_folder") or run_cfg.get("load_pattern", "full")
    
    # Get path structure keys
    path_structure = cfg.get("path_structure", {})
    bronze_keys = path_structure.get("bronze", {}) if isinstance(path_structure, dict) else {}
    
    system_key = bronze_keys.get("system_key", "system")
    entity_key = bronze_keys.get("entity_key", "table")
    pattern_key = bronze_keys.get("pattern_key", "pattern")
    date_key = bronze_keys.get("date_key", "dt")
    
    return BronzePartition(
        system=source["system"],
        table=source["table"],
        pattern=pattern,
        run_date=run_date,
        system_key=system_key,
        entity_key=entity_key,
        pattern_key=pattern_key,
        date_key=date_key,
    )


def build_silver_partition(cfg: Dict[str, Any], run_date: date) -> SilverPartition:
    silver = cfg.get("silver", {})
    source = cfg["source"]
    pattern = source.get("run", {}).get("load_pattern", "full")
    
    # Get path structure keys
    path_structure = cfg.get("path_structure", {})
    silver_keys = path_structure.get("silver", {}) if isinstance(path_structure, dict) else {}
    
    domain_key = silver_keys.get("domain_key", "domain")
    entity_key = silver_keys.get("entity_key", "entity")
    version_key = silver_keys.get("version_key", "v")
    pattern_key = silver_keys.get("pattern_key", "pattern")
    load_date_key = silver_keys.get("load_date_key", "load_date")
    
    return SilverPartition(
        domain=silver.get("domain", "default"),
        entity=silver.get("entity", "dataset"),
        version=silver.get("version", 1),
        load_partition_name=silver.get("load_partition_name", "load_date"),
        run_date=run_date,
        include_pattern_folder=silver.get("include_pattern_folder", False),
        pattern=pattern,
        domain_key=domain_key,
        entity_key=entity_key,
        version_key=version_key,
        pattern_key=pattern_key,
        load_date_key=load_date_key,
    )
