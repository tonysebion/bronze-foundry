"""Verify that DbExtractor uses RateLimiter before executing queries."""

from datetime import date
from unittest.mock import Mock


def test_db_extractor_uses_rate_limiter(monkeypatch):
    limiter = Mock()
    limiter.acquire = Mock()

    def fake_from_config(extractor_cfg, run_cfg, *, component=None, env_var=None):
        assert component == "db_extractor"
        assert env_var == "BRONZE_DB_RPS"
        return limiter

    monkeypatch.setattr(
        "core.adapters.extractors.db_extractor.RateLimiter.from_config",
        fake_from_config,
    )

    monkeypatch.setenv("CLAIMS_DB_CONN_STR", "driver=example")

    monkeypatch.setattr(
        "core.adapters.extractors.db_extractor.fetch_records_from_query",
        lambda *args, **kwargs: ([], None),
    )

    from core.adapters.extractors.db_extractor import DbExtractor

    extractor = DbExtractor()
    config = {
        "source": {
            "system": "claims",
            "table": "claims_header",
            "db": {"conn_str_env": "CLAIMS_DB_CONN_STR", "base_query": "SELECT 1"},
            "run": {},
        }
    }

    extractor.fetch_records(config, date(2025, 1, 1))

    limiter.acquire.assert_called_once()
