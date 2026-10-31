"""Tests for the Desearch web search provider."""
import json
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from metagpt.tools.search_engine_desearch import DesearchWrapper


def test_credentials(monkeypatch):
    monkeypatch.delenv("DESEARCH_API_KEY", raising=False)
    with pytest.raises(ValueError, match="DESEARCH_API_KEY"):
        DesearchWrapper()
    monkeypatch.setenv("DESEARCH_API_KEY", "env-secret")
    assert DesearchWrapper(api_key="").api_key == "env-secret"
    wrapper = DesearchWrapper(api_key="explicit-secret")
    assert wrapper.api_key == "explicit-secret"
    assert "explicit-secret" not in repr(wrapper)
    assert "api_key" not in wrapper.model_dump()


@pytest.mark.asyncio
@pytest.mark.parametrize("as_string", [True, False])
@pytest.mark.parametrize("owned_session", [True, False])
async def test_search(monkeypatch, as_string, owned_session):
    response = MagicMock()
    response.json = AsyncMock(
        return_value={
            "data": [
                {
                    "title": "Example",
                    "link": "https://example.org",
                    "snippet": "Text",
                    "extra": "ignored",
                },
                {"title": "Second"},
            ]
        }
    )
    session = MagicMock(spec=aiohttp.ClientSession)
    session.get.return_value.__aenter__ = AsyncMock(return_value=response)
    factory = MagicMock()
    factory.return_value.__aenter__ = AsyncMock(return_value=session)
    monkeypatch.setattr(aiohttp, "ClientSession", factory)
    wrapper = DesearchWrapper(
        api_key="secret", proxy="http://proxy", **({} if owned_session else {"aiosession": session})
    )
    result = await wrapper.run("example", max_results=1, as_string=as_string)
    assert (json.loads(result) if as_string else result) == [
        {"title": "Example", "link": "https://example.org", "snippet": "Text"}
    ]
    response.raise_for_status.assert_called_once()
    args, kwargs = session.get.call_args
    assert args == ("https://api.desearch.ai/web",)
    assert kwargs["params"] == {"query": "example"}
    assert kwargs["headers"] == {"Authorization": "Bearer secret"}
    assert kwargs["proxy"] == "http://proxy"
    response.json.return_value = {"data": []}
    assert await wrapper.run("empty", as_string=False) == []
    response.raise_for_status.side_effect = aiohttp.ClientResponseError(MagicMock(), (), status=401)
    with pytest.raises(aiohttp.ClientResponseError):
        await wrapper.run("error")
    session.get.reset_mock()
    assert await wrapper.run("zero", max_results=0, as_string=False) == []
    session.get.assert_not_called()


@pytest.mark.asyncio
async def test_search_config_dispatch(monkeypatch):
    from metagpt.configs.search_config import SearchConfig
    from metagpt.tools.search_engine import SearchEngine

    monkeypatch.setenv("DESEARCH_API_KEY", "env-secret")
    run = AsyncMock(return_value=[{"title": "Example", "link": "https://example.org", "snippet": "Text"}])
    monkeypatch.setattr(DesearchWrapper, "run", run)
    engine = SearchEngine.from_search_config(SearchConfig(api_type="desearch"))
    assert await engine.run("example", max_results=2, as_string=False) == run.return_value
    run.assert_awaited_once_with("example", max_results=2, as_string=False)
