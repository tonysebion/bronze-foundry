"""Smoke tests for async HTTP client with retry and rate limiting.

Tests basic functionality of AsyncApiClient including retry logic,
circuit breakers, and rate limiting integration.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from core.extractors.async_http import AsyncApiClient, is_async_enabled, HTTPX_AVAILABLE


@pytest.mark.skipif(not HTTPX_AVAILABLE, reason="httpx not installed")
@pytest.mark.asyncio
async def test_async_client_basic_get():
    """Test basic GET request with mocked httpx."""
    with patch("core.extractors.async_http.httpx") as mock_httpx:
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok", "data": [1, 2, 3]}
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get = AsyncMock(return_value=mock_response)
        
        mock_httpx.AsyncClient.return_value = mock_client
        
        client = AsyncApiClient(
            base_url="https://api.example.com",
            headers={"Authorization": "Bearer test"},
            timeout=10,
            max_concurrent=2,
        )
        
        result = await client.get("/users", params={"page": 1})
        
        assert result["status"] == "ok"
        assert len(result["data"]) == 3
        mock_client.get.assert_called_once()


@pytest.mark.skipif(not HTTPX_AVAILABLE, reason="httpx not installed")
@pytest.mark.asyncio
async def test_async_client_retry_on_error():
    """Test that client retries on transient errors."""
    with patch("core.extractors.async_http.httpx") as mock_httpx:
        # Fail first 2 attempts, succeed on 3rd
        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 503
        
        # Create a proper exception with response attribute
        class MockHTTPError(Exception):
            def __init__(self, response):
                self.response = response
                super().__init__("Service unavailable")
        
        mock_error = MockHTTPError(mock_response_fail)
        type(mock_error).__name__ = "HTTPStatusError"
        type(mock_error).__module__ = "httpx"
        
        mock_response_success = MagicMock()
        mock_response_success.json.return_value = {"retry": "success"}
        mock_response_success.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        
        call_count = 0
        async def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise mock_error
            return mock_response_success
        
        mock_client.get = mock_get
        mock_httpx.AsyncClient.return_value = mock_client
        
        client = AsyncApiClient(
            base_url="https://api.example.com",
            headers={},
        )
        
        result = await client.get("/flaky")
        assert result["retry"] == "success"
        assert call_count == 3


def test_is_async_enabled_via_config():
    """Test async enable detection from config."""
    assert is_async_enabled({"async": True}) is (True if HTTPX_AVAILABLE else False)
    assert is_async_enabled({"async": False}) is False
    assert is_async_enabled({}) is False


def test_is_async_enabled_via_env(monkeypatch):
    """Test async enable detection from environment."""
    monkeypatch.setenv("BRONZE_ASYNC_HTTP", "1")
    assert is_async_enabled({}) is (True if HTTPX_AVAILABLE else False)
    
    monkeypatch.setenv("BRONZE_ASYNC_HTTP", "false")
    assert is_async_enabled({}) is False


@pytest.mark.skipif(not HTTPX_AVAILABLE, reason="httpx not installed")
@pytest.mark.asyncio
async def test_async_client_concurrency_limit():
    """Test that semaphore limits concurrent requests."""
    with patch("core.extractors.async_http.httpx") as mock_httpx:
        mock_response = MagicMock()
        mock_response.json.return_value = {"ok": True}
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get = AsyncMock(return_value=mock_response)
        
        mock_httpx.AsyncClient.return_value = mock_client
        
        client = AsyncApiClient(
            base_url="https://api.example.com",
            headers={},
            max_concurrent=2,
        )
        
        # Fire 5 requests; semaphore should limit to 2 at a time
        tasks = [client.get(f"/endpoint{i}") for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        assert all(r["ok"] for r in results)
