#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations
import requests
import json
import warnings
from typing import Optional

import aiohttp
from pydantic import BaseModel, ConfigDict, model_validator


class BoChaAPIWrapper(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    api_key: str
    bocha_url: str = "https://api.bocha.cn/v1/web-search"
    aiosession: Optional[aiohttp.ClientSession] = None
    proxy: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def validate_api_key(cls, values: dict) -> dict:
        if "api_key" in values:
            values.setdefault("api_key", values["api_key"])
            warnings.warn("`api_key` is deprecated, use `api_key` instead", DeprecationWarning, stacklevel=2)
        return values

    async def run(
        self,
        query: str,
        max_results: int = 8,
        as_string: bool = True,
    ) -> str | list[dict]:
        """Return the results of a BoCha search using the official bocha API.

        Args:
            query: The search query.
            max_results: The number of results to return.
            as_string: A boolean flag to determine the return type of the results. If True, the function will
                return a formatted string with the search results. If False, it will return a list of dictionaries
                containing detailed information about each search result.

        Returns:
            The results of the search.
        """
        params = {
            "query": query,
            "freshness": "noLimit",
            "summary": True,
            "count": max_results,
            "include": "",
            "exclude": ""
        }
        result = await self.results(params)
        search_results = result["webPages"]["value"]
        focus = ["snippet", "link", "title"]
        for item_dict in search_results:
            item_dict["link"] = item_dict["url"]
            item_dict["title"] = item_dict["name"]
        details = [{i: j for i, j in item_dict.items() if i in focus} for item_dict in search_results]
        if as_string:
            return safe_results(details)
        return details

    async def results(self, params: dict) -> dict:
        # 构建请求头
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        # 发送API请求
        response = requests.post(self.bocha_url, headers=headers, json=params)

        return response.json()["data"]

def safe_results(results: str | list) -> str:
    """Return the results of a bocha search in a safe format.

    Args:
        results: The search results.

    Returns:
        The results of the search.
    """
    if isinstance(results, list):
        safe_message = json.dumps([result for result in results])
    else:
        safe_message = results.encode("utf-8", "ignore").decode("utf-8")
    return safe_message


if __name__ == "__main__":
    import fire

    fire.Fire(BoChaAPIWrapper().run)