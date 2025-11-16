"""Unit tests for Bronze reference metadata handling."""

from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

import pytest

from core.io import write_batch_metadata
from scripts.generate_sample_data import HYBRID_DELTA_DAYS, HYBRID_REFERENCE_DATE

REPO_ROOT = Path(__file__).resolve().parents[1]
HYBRID_DIR = REPO_ROOT / "docs" / "examples" / "data" / "bronze_samples"


def _write_metadata_with_reference(
    tmp_path: Path, run_date: dt.date, reference_mode: dict[str, object]
) -> Path:
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


@pytest.fixture(scope="module", autouse=True)
def ensure_hybrid_samples() -> None:
    subprocess.run(
        [sys.executable, "scripts/generate_sample_data.py"],
        cwd=REPO_ROOT,
        check=True,
    )
    yield


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


def test_hybrid_samples_cover_delta_sequence() -> None:
    for combo in ("hybrid_cdc", "hybrid_incremental"):
        base = HYBRID_DIR / combo / "system=retail_demo" / "table=orders" / f"pattern={combo}"
        reference_meta_path = base / f"dt={HYBRID_REFERENCE_DATE.isoformat()}" / "reference" / "_metadata.json"
        assert reference_meta_path.exists()
        reference_meta = json.loads(reference_meta_path.read_text())
        assert reference_meta["reference_mode"]["reference_run_date"] == HYBRID_REFERENCE_DATE.isoformat()
        for offset in range(1, HYBRID_DELTA_DAYS + 1):
            delta_date = HYBRID_REFERENCE_DATE + dt.timedelta(days=offset)
            delta_meta_path = (
                base
                / f"dt={delta_date.isoformat()}"
                / "delta"
                / "point"
                / "_metadata.json"
            )
            assert delta_meta_path.exists()
            delta_meta = json.loads(delta_meta_path.read_text())
            assert delta_meta["reference_mode"]["reference_run_date"] == HYBRID_REFERENCE_DATE.isoformat()
            assert delta_meta["reference_mode"]["role"] == "delta"
            cumulative_meta_path = (
                base
                / f"dt={delta_date.isoformat()}"
                / "delta"
                / "cumulative"
                / "_metadata.json"
            )
            assert cumulative_meta_path.exists()
            cumulative_meta = json.loads(cumulative_meta_path.read_text())
            assert cumulative_meta["reference_mode"]["delta_mode"] == "cumulative"
