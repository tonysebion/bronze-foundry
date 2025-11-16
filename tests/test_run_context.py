from datetime import date
from pathlib import Path

from core.context import (
    build_run_context,
    dump_run_context,
    load_run_context,
    run_context_from_dict,
    run_context_to_dict,
)
from core.patterns import LoadPattern


def _sample_config(tmp_path: Path) -> dict:
    return {
        "platform": {
            "bronze": {
                "output_defaults": {},
            }
        },
        "source": {
            "system": "retail_demo",
            "table": "orders",
            "run": {
                "local_output_dir": str(tmp_path),
                "load_pattern": "full",
            },
        },
    }


def test_run_context_round_trip(tmp_path: Path) -> None:
    cfg = _sample_config(tmp_path)
    ctx = build_run_context(cfg, date(2025, 11, 14))

    payload = run_context_to_dict(ctx)
    restored = run_context_from_dict(payload)

    assert restored.dataset_id == ctx.dataset_id
    assert restored.run_date == ctx.run_date
    assert restored.relative_path == ctx.relative_path
    assert restored.load_pattern == LoadPattern.FULL


def test_run_context_file_round_trip(tmp_path: Path) -> None:
    cfg = _sample_config(tmp_path)
    ctx = build_run_context(cfg, date(2025, 11, 15))

    path = tmp_path / "context.json"
    dump_run_context(ctx, path)
    loaded = load_run_context(path)

    assert loaded.dataset_id == ctx.dataset_id
    assert loaded.run_date == ctx.run_date
    assert loaded.bronze_path == ctx.bronze_path
