"""Unit tests for Bronze reference metadata handling."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest

from core.io import write_batch_metadata


def _write_metadata_with_reference(tmp_path: Path, run_date: dt.date, reference_mode: dict[str, object]) -> Path:
    path = tmp_path / f"system=retail_demo/table=orders/pattern=full/dt={run_date.isoformat()}"
    path.mkdir(parents=True, exist_ok=True)
    metadata = {
        "record_count": 100,
        "chunk_count": 2,
        "run_date": run_date.isoformat(),
        "reference_mode": reference_mode,
        "load_pattern": "full",
    }
    write_batch_metadata(path, record_count=100, chunk_count=2, extra_metadata=metadata)
    return path


def test_reference_then_cdc_delta(tmp_path: Path) -> None:
    ref_path = _write_metadata_with_reference(
        tmp_path,
        dt.date(2025, 11, 13),
        {"role": "reference", "cadence_days": 7, "delta_patterns": ["cdc"]},
    )
    delta_path = _write_metadata_with_reference(
        tmp_path,
        dt.date(2025, 11, 14),
        {"role": "delta", "delta_patterns": ["cdc"]},
    )
    ref_meta = json.loads((ref_path / "_metadata.json").read_text())
    delta_meta = json.loads((delta_path / "_metadata.json").read_text())
    assert ref_meta["reference_mode"]["role"] == "reference"
    assert delta_meta["reference_mode"]["role"] == "delta"
    assert delta_meta["reference_mode"]["delta_patterns"] == ["cdc"]


def test_reference_then_incremental_delta(tmp_path: Path) -> None:
    ref_path = _write_metadata_with_reference(
        tmp_path,
        dt.date(2025, 11, 13),
        {"role": "reference", "cadence_days": 7, "delta_patterns": ["incremental_merge"]},
    )
    delta_path = _write_metadata_with_reference(
        tmp_path,
        dt.date(2025, 11, 14),
        {"role": "delta", "delta_patterns": ["incremental_merge"]},
    )
    ref_meta = json.loads((ref_path / "_metadata.json").read_text())
    delta_meta = json.loads((delta_path / "_metadata.json").read_text())
    assert "incremental_merge" in ref_meta["reference_mode"]["delta_patterns"]
    assert delta_meta["reference_mode"]["role"] == "delta"
