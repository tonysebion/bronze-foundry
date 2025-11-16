from __future__ import annotations

import pytest

import asyncio

from core.extractors.api_extractor import ApiExtractor
from core.extractors.async_http import HTTPX_AVAILABLE


@pytest.mark.skipif(not HTTPX_AVAILABLE, reason="httpx not installed")
def test_api_extractor_async_pagination(monkeypatch):
    extractor = ApiExtractor()
    api_cfg = {
        "base_url": "https://api.example.com",
        "endpoint": "/users",
        "pagination": {"type": "none"},
    }
    run_cfg = {"timeout_seconds": 5}

    class DummyClient:
        async def get(self, endpoint, **kwargs):
            return {"items": [{"id": 42}]}

    class DummyLimiter:
        @staticmethod
        def from_config(*args, **kwargs):
            return None

    class DummySpan:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr("core.extractors.api_extractor.AsyncApiClient", lambda *args, **kwargs: DummyClient())
    monkeypatch.setattr("core.extractors.api_extractor.RateLimiter.from_config", DummyLimiter.from_config)
    monkeypatch.setattr("core.extractors.api_extractor.trace_span", lambda name: DummySpan())

    async def _run():
        return await extractor._paginate_async(
            api_cfg["base_url"],
            api_cfg["endpoint"],
            headers={},
            api_cfg=api_cfg,
            run_cfg=run_cfg,
        )

    results = asyncio.run(_run())
    assert results == [{"id": 42}]
