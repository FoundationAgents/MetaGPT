"""Async web search through the Desearch API."""
from __future__ import annotations

import json
import os
from typing import Optional

import aiohttp
from pydantic import BaseModel, ConfigDict, Field, model_validator


class DesearchWrapper(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    api_key: str = Field(default="", repr=False, exclude=True)
    aiosession: Optional[aiohttp.ClientSession] = None
    proxy: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def validate_api_key(cls, values: dict) -> dict:
        values = dict(values)
        values["api_key"] = values.get("api_key") or os.getenv("DESEARCH_API_KEY", "")
        if not values["api_key"]:
            raise ValueError("Set DESEARCH_API_KEY or provide api_key to use Desearch.")
        return values

    async def run(self, query: str, max_results: int = 8, as_string: bool = True) -> str | list[dict]:
        """Search the web and limit the returned results locally."""
        if max_results <= 0:
            return "[]" if as_string else []
        if self.aiosession is None:
            async with aiohttp.ClientSession() as session:
                result = await self._results(session, query)
        else:
            result = await self._results(self.aiosession, query)
        details = [
            {key: item.get(key, "") for key in ("title", "link", "snippet")} for item in result["data"][:max_results]
        ]
        return json.dumps(details, ensure_ascii=False) if as_string else details

    async def _results(self, session: aiohttp.ClientSession, query: str) -> dict:
        async with session.get(
            "https://api.desearch.ai/web",
            params={"query": query},
            headers={"Authorization": f"Bearer {self.api_key}"},
            proxy=self.proxy,
            timeout=aiohttp.ClientTimeout(total=60),
        ) as response:
            response.raise_for_status()
            return await response.json()
