#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/7/8
@File    : search_engine_tavily.py
@Desc    : Tavily (https://tavily.com) search engine wrapper. Tavily is a web
           search API purpose-built for LLM agents, returning LLM-optimized
           content. Mirrors the aiohttp-based SerpAPI/Serper wrappers so it
           works under the existing `search_engine_mocker` test harness and
           adds no new runtime dependency (aiohttp is already required).
           API reference: https://docs.tavily.com/documentation/api-reference/endpoint/search
"""
import json
from typing import Any, Optional

import aiohttp
from pydantic import BaseModel, ConfigDict, model_validator


class TavilyAPIWrapper(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    api_key: str
    url: str = "https://api.tavily.com/search"
    # Latency/relevance tradeoff: "basic", "advanced", "fast", "ultra-fast".
    search_depth: str = "basic"
    # Search category: "general", "news", "finance".
    topic: str = "general"
    aiosession: Optional[aiohttp.ClientSession] = None
    proxy: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def validate_tavily(cls, values: dict) -> dict:
        if "api_key" not in values:
            raise ValueError(
                "To use the Tavily search engine, make sure you provide the `api_key` when constructing an "
                "object. You can obtain an API key from https://app.tavily.com/."
            )
        return values

    async def run(self, query: str, max_results: int = 8, as_string: bool = True, **kwargs: Any) -> str:
        """Run query through Tavily and parse the result asynchronously."""
        return self._process_response(await self.results(query, max_results), as_string=as_string)

    async def results(self, query: str, max_results: int = 8) -> dict:
        """Use aiohttp to run the query through Tavily and return the raw results asynchronously."""
        payload = self.get_payload(query, max_results)
        headers = self.get_headers()

        if not self.aiosession:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.url, json=payload, headers=headers, proxy=self.proxy) as response:
                    response.raise_for_status()
                    res = await response.json()
        else:
            async with self.aiosession.post(self.url, json=payload, headers=headers, proxy=self.proxy) as response:
                response.raise_for_status()
                res = await response.json()

        return res

    def get_payload(self, query: str, max_results: int) -> dict:
        return {
            "query": query,
            "search_depth": self.search_depth,
            "topic": self.topic,
            "max_results": max_results,
        }

    def get_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    @staticmethod
    def _process_response(res: dict, as_string: bool = True) -> str:
        """Process the response from Tavily into MetaGPT's `{link, snippet, title}` shape."""
        if "results" not in res:
            raise ValueError(f"Got error from Tavily: {res}")

        results = [
            {"link": item.get("url"), "snippet": item.get("content"), "title": item.get("title")}
            for item in res["results"]
        ]
        return json.dumps(results, ensure_ascii=False) if as_string else results


if __name__ == "__main__":
    import fire

    fire.Fire(TavilyAPIWrapper().run)
