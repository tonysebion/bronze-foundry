from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import List

from core.context import RunContext
from core.parallel import _safe_run_extract, run_parallel_extracts
from core.patterns import LoadPattern


def _build_context(name: str) -> RunContext:
    base_dir = Path(".")
    return RunContext(
        cfg={},
        run_date=date.today(),
        relative_path="",
        local_output_dir=base_dir,
        bronze_path=base_dir,
        source_system="system",
        source_table="table",
        dataset_id=name,
        config_name=name,
        load_pattern=LoadPattern.FULL,
    )


def test_safe_run_extract_success(monkeypatch):
    monkeypatch.setattr("core.parallel.run_extract", lambda context: 0)
    context = _build_context("success")
    status, error = _safe_run_extract(context)
    assert status == 0
    assert error is None


def test_safe_run_extract_failure(monkeypatch):
    def raise_error(context):
        raise RuntimeError("boom")

    monkeypatch.setattr("core.parallel.run_extract", raise_error)
    context = _build_context("fail")
    status, error = _safe_run_extract(context)
    assert status == -1
    assert isinstance(error, RuntimeError)


def test_run_parallel_extracts_reports_statuses(monkeypatch):
    contexts: List[RunContext] = [
        _build_context("success"),
        _build_context("partial"),
    ]

    def fake_safe(context):
        if context.config_name == "success":
            return 0, None
        return -1, RuntimeError("failed")

    monkeypatch.setattr("core.parallel._safe_run_extract", fake_safe)
    results = run_parallel_extracts(contexts, max_workers=2)

    assert len(results) == len(contexts)
    assert any(status == -1 for _, status, _ in results)
    assert any(status == 0 for _, status, _ in results)
