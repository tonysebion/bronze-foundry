from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytest

from core.extractors.db_extractor import DbExtractor


class DummyConnection:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


class DummyCursor:
    def __init__(self, rows: List[Tuple[Any, ...]], columns: List[str]) -> None:
        self.rows = rows
        self.columns = columns
        self.description = [(col,) for col in columns]
        self.connection = DummyConnection()
        self.offset = 0

    def fetchmany(self, size: int) -> List[Tuple[Any, ...]]:
        chunk = self.rows[self.offset : self.offset + size]
        self.offset += len(chunk)
        return chunk


def _build_cfg() -> Dict[str, Any]:
    return {
        "source": {
            "system": "sales",
            "table": "orders",
            "db": {
                "driver": "pyodbc",
                "conn_str_env": "DB_CONN",
                "base_query": "SELECT id, value FROM orders",
                "incremental": {"enabled": True, "cursor_column": "id"},
                "fetch_batch_size": 1,
            },
            "run": {"load_pattern": "full"},
        }
    }


def test_db_extractor_incremental_query(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    cfg = _build_cfg()
    state_file = tmp_path / "state.json"
    state_file.write_text(json.dumps({"cursor": "100", "last_run": "2025-01-01"}))

    extractor = DbExtractor()
    monkeypatch.setattr(
        DbExtractor,
        "_get_state_file_path",
        lambda self, cfg: state_file,
    )

    rows = [(101, "alpha"), (105, "beta")]

    call_info: Dict[str, Any] = {}

    def fake_execute(self, driver: str, conn_str: str, query: str, params: Optional[Tuple] = None):
        call_info["query"] = query
        call_info["params"] = params
        return DummyCursor(rows, ["id", "value"])

    monkeypatch.setattr(DbExtractor, "_execute_query", fake_execute)
    monkeypatch.setenv("DB_CONN", "driver={driver};server=prod")

    records, cursor = extractor.fetch_records(cfg, date(2025, 11, 14))

    assert len(records) == 2
    assert cursor == "105"
    assert "WHERE id > ?" in call_info["query"]
    assert call_info["params"] == ("100",)
    saved = json.loads(state_file.read_text(encoding="utf-8"))
    assert saved["cursor"] == "105"
    assert saved["last_run"] == "2025-11-14"
