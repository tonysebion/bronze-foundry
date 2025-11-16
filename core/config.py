from __future__ import annotations

from datetime import date as _date
from pathlib import Path
from typing import Any, Dict, List
import copy
import logging

import yaml

from core.config_validation import validate_config_dict
from core.paths import build_bronze_relative_path

logger = logging.getLogger(__name__)


def _read_yaml(path: str) -> Dict[str, Any]:
    logger.info(f"Loading config from {path}")

    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    try:
        with open(path, "r", encoding="utf-8") as handle:
            cfg = yaml.safe_load(handle)
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in config file: {exc}")

    if not isinstance(cfg, dict):
        raise ValueError("Config must be a YAML dictionary/object")

    return cfg


def load_config(path: str) -> Dict[str, Any]:
    cfg = _read_yaml(path)
    if "sources" in cfg:
        raise ValueError("Config contains multiple sources; use load_configs() instead.")
    return validate_config_dict(cfg)


def load_configs(path: str) -> List[Dict[str, Any]]:
    raw = _read_yaml(path)
    if "sources" not in raw:
        return [validate_config_dict(raw)]

    sources = raw["sources"]
    if not isinstance(sources, list) or not sources:
        raise ValueError("'sources' must be a non-empty list")
    if "source" in raw:
        raise ValueError("Config cannot contain both 'source' and 'sources'")

    platform = raw.get("platform")
    base_silver = raw.get("silver")
    results: List[Dict[str, Any]] = []

    for idx, entry in enumerate(sources):
        if not isinstance(entry, dict):
            raise ValueError("Each item in 'sources' must be a dictionary")
        if "source" not in entry:
            raise ValueError("Each item in 'sources' must include a 'source' section")

        merged_cfg: Dict[str, Any] = {
            "platform": copy.deepcopy(platform),
            "source": copy.deepcopy(entry["source"]),
        }

        entry_silver = copy.deepcopy(base_silver) if base_silver else {}
        if "silver" in entry:
            entry_silver = entry_silver or {}
            entry_silver.update(copy.deepcopy(entry["silver"]))
        if entry_silver:
            merged_cfg["silver"] = entry_silver

        name = entry.get("name")
        if name:
            merged_cfg["source"]["config_name"] = name
        merged_cfg["source"]["_source_list_index"] = idx
        results.append(validate_config_dict(merged_cfg))

    return results


def build_relative_path(cfg: Dict[str, Any], run_date: _date) -> str:
    return build_bronze_relative_path(cfg, run_date)
