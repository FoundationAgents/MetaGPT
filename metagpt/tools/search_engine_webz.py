#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/10/31 20:00
@Author  : TINGyu123644
@File    : search_engine_webz.py
"""
import json
from typing import Any, Dict, Optional, Union

import aiohttp
from pydantic import BaseModel, ConfigDict, model_validator


class WebzAPIWrapper(BaseModel):
    """Wrapper for the Webz.io News Search API (https://docs.webz.io/docs/webz/news-search-api)."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    api_key: str
    url: str = "http://api.webz.io/api/news/context"
    aiosession: Optional[aiohttp.ClientSession] = None
    proxy: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def validate_webz(cls, values: dict) -> dict:
        if "api_key" not in values:
            raise ValueError(
                "To use the Webz.io News Search engine, make sure you provide the `api_key` when constructing an "
                "object. You can obtain an API key from https://webz.io/."
            )

        return values

    async def run(self, query: str, max_results: int = 8, as_string: bool = True, **kwargs: Any) -> str:
        """Run a query through the Webz.io News Search API and parse the result async."""
        return self._process_response(await self.results(query, max_results), as_string=as_string)

    async def results(self, query: str, max_results: int = 8) -> dict:
        """Use aiohttp to run the query through the Webz.io News Search API and return the results async."""
        payload = json.dumps({"query": query, "k": max_results}, sort_keys=True)
        headers = self.get_headers()

        if not self.aiosession:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.url, data=payload, headers=headers, proxy=self.proxy) as response:
                    response.raise_for_status()
                    res = await response.json()
        else:
            async with self.aiosession.post(self.url, data=payload, headers=headers, proxy=self.proxy) as response:
                response.raise_for_status()
                res = await response.json()

        return res

    def get_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    @staticmethod
    def _process_response(res: dict, as_string: bool = False) -> Union[str, list[dict[str, str]]]:
        """Map Webz.io results to MetaGPT's standard search-result fields.

        Maps article titles, URLs, publication dates, source domains and the most relevant
        text excerpts (falling back to the article summary when no matching chunk is returned).
        """
        details = []
        for item in res.get("results", []):
            article = item.get("article") or {}
            chunk = item.get("chunk") or {}
            metadata = item.get("metadata") or {}
            detail = {
                "title": article.get("title"),
                "snippet": chunk.get("text") or article.get("summary"),
                "url": article.get("url"),
                "published_at": article.get("published_at"),
                "domain": metadata.get("domain"),
            }
            details.append({k: v for k, v in detail.items() if v is not None})

        return json.dumps(details) if as_string else details


if __name__ == "__main__":
    import fire

    fire.Fire(WebzAPIWrapper().run)
