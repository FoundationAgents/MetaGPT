#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test module for the Firecrawl tool."""

import os
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import aiohttp

from metagpt.tools.libs.firecrawl import Firecrawl

API_KEY = "YOUR-FIRECRAWL-API-KEY"
API_URL = "https://api.firecrawl.dev"

EXPECTED_HEADERS = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {API_KEY}',
}

@pytest.fixture
def firecrawl():
    """Create a Firecrawl instance for testing."""
    return Firecrawl(api_key=API_KEY, api_url=API_URL)

def test_initialization():
    tool = Firecrawl(api_key=API_KEY, api_url=API_URL)
    assert tool.api_key == API_KEY
    assert tool.api_url == API_URL

def test_initialization_with_env_vars():
    os.environ["FIRECRAWL_API_KEY"] = API_KEY
    os.environ["FIRECRAWL_API_URL"] = API_URL
    tool = Firecrawl()
    assert tool.api_key == API_KEY
    assert tool.api_url == API_URL
    del os.environ["FIRECRAWL_API_KEY"]
    del os.environ["FIRECRAWL_API_URL"]

def test_initialization_without_api_key():
    with pytest.raises(ValueError, match="No API key provided"):
        Firecrawl()

def mock_aiohttp_session(method: str, mock_response_data: dict, status: int = 200):
    mock_response = AsyncMock()
    mock_response.status = status
    mock_response.json = AsyncMock(return_value=mock_response_data)

    mock_cm_response = MagicMock()
    mock_cm_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_cm_response.__aexit__ = AsyncMock(return_value=None)

    mock_method = MagicMock(return_value=mock_cm_response)

    mock_session = MagicMock()
    setattr(mock_session, method, mock_method)

    mock_session_cm = MagicMock()
    mock_session_cm.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_cm.__aexit__ = AsyncMock(return_value=None)

    return mock_session_cm

@pytest.mark.asyncio
async def test_map_url(firecrawl):
    with patch("aiohttp.ClientSession", return_value=mock_aiohttp_session("post", {"success": True, "links": ["http://example.com/page1"]})):
        result = await firecrawl.map_url("http://example.com")
        assert result == {"success": True, "links": ["http://example.com/page1"]}

@pytest.mark.asyncio
async def test_scrape_url(firecrawl):
    with patch("aiohttp.ClientSession", return_value=mock_aiohttp_session("post", {"success": True, "data": {"title": "Example"}})):
        result = await firecrawl.scrape_url("http://example.com")
        assert result == {"success": True, "data": {"title": "Example"}}

@pytest.mark.asyncio
async def test_search(firecrawl):
    with patch("aiohttp.ClientSession", return_value=mock_aiohttp_session("post", {"success": True, "results": [{"title": "Test Result"}]})):
        result = await firecrawl.search("test query")
        assert result == {"success": True, "results": [{"title": "Test Result"}]}

@pytest.mark.asyncio
async def test_crawl_url(firecrawl):
    with patch("aiohttp.ClientSession", return_value=mock_aiohttp_session("post", {"success": True, "id": "test_job_id"})):
        result = await firecrawl.crawl_url("http://example.com")
        assert result == {"success": True, "id": "test_job_id"}

@pytest.mark.asyncio
async def test_get_crawl_status(firecrawl):
    with patch("aiohttp.ClientSession", return_value=mock_aiohttp_session("get", {"success": True, "status": "completed"})):
        result = await firecrawl.get_crawl_status("test_job_id")
        assert result == {"success": True, "status": "completed"}

@pytest.mark.asyncio
async def test_extract(firecrawl):
    with patch("aiohttp.ClientSession", return_value=mock_aiohttp_session("post", {"success": True, "data": {"extracted": "content"}})):
        result = await firecrawl.extract(["http://example.com"])
        assert result == {"success": True, "data": {"extracted": "content"}}

@pytest.mark.asyncio
async def test_get_extract_status(firecrawl):
    with patch("aiohttp.ClientSession", return_value=mock_aiohttp_session("get", {"success": True, "status": "completed"})):
        result = await firecrawl.get_extract_status("test_job_id")
        assert result == {"success": True, "status": "completed"}

@pytest.mark.asyncio
async def test_error_handling(firecrawl):
    mock_response = AsyncMock()
    mock_response.status = 400
    mock_response.json = AsyncMock(return_value={"error": "Test error", "details": "Test error details"})
    mock_response.request_info = MagicMock()
    mock_response.history = []

    mock_context = MagicMock()
    mock_context.__aenter__ = AsyncMock(return_value=mock_response)
    mock_context.__aexit__ = AsyncMock(return_value=None)

    def mock_post(*args, **kwargs):
        return mock_context

    mock_session = MagicMock()
    mock_session.post = mock_post

    mock_session_cm = MagicMock()
    mock_session_cm.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_cm.__aexit__ = AsyncMock(return_value=None)

    with patch("aiohttp.ClientSession", return_value=mock_session_cm):
        with pytest.raises(aiohttp.ClientResponseError):
            await firecrawl.map_url("http://example.com")

@pytest.mark.asyncio
async def test_params_integration(firecrawl):
    with patch("aiohttp.ClientSession", return_value=mock_aiohttp_session("post", {"success": True})):
        params = {"param1": "value1", "param2": "value2"}
        result = await firecrawl.map_url("http://example.com", params=params)
        assert result == {"success": True}
