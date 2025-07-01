#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Firecrawl Tool for MetaGPT.

This module provides a tool for interacting with the Firecrawl API, enabling web scraping,
crawling, searching, and information extraction capabilities.

Author: Ademílson Tonato <ftonato@sideguide.dev | ademilsonft@outlook.com>
"""

import os
from typing import Any, Dict, List, Optional, Union

import aiohttp
from metagpt.tools.tool_registry import register_tool


@register_tool(tags=["web", "scraping", "search"], include_functions=["map_url", "scrape_url", "search", "crawl_url", "extract"])
class Firecrawl:
    """A tool for web scraping, crawling, searching and information extraction using Firecrawl API.
    
    This tool provides methods to interact with the Firecrawl API for various web data collection
    and processing tasks. It supports URL mapping, scraping, searching, crawling, and information
    extraction.

    Attributes:
        api_key (str): The API key for authenticating with Firecrawl API.
        api_url (str): The base URL for the Firecrawl API.
    """

    def __init__(self, api_key: Optional[str] = None, api_url: Optional[str] = None):
        """Initialize the Firecrawl tool.

        Args:
            api_key (Optional[str]): API key for Firecrawl. Defaults to environment variable.
            api_url (Optional[str]): Base URL for Firecrawl API. Defaults to production URL.
        """
        self.api_key = api_key or os.getenv('FIRECRAWL_API_KEY')
        if not self.api_key:
            raise ValueError('No API key provided')
        self.api_url = api_url or os.getenv('FIRECRAWL_API_URL', 'https://api.firecrawl.dev')
        self.request_timeout = aiohttp.ClientTimeout(total=60)

    def _prepare_headers(self) -> Dict[str, str]:
        """Prepare headers for API requests.

        Returns:
            Dict[str, str]: Headers including content type and authorization.
        """
        return {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
        }

    def _prepare_request_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare request data with integration parameter.

        Args:
            data (Dict[str, Any]): The original request data.

        Returns:
            Dict[str, Any]: Request data with integration parameter added.
        """
        data['integration'] = 'metagpt'
        return data

    async def _handle_error(self, response: aiohttp.ClientResponse, action: str) -> None:
        """Handle API errors.

        Args:
            response (aiohttp.ClientResponse): The response from the API.
            action (str): Description of the action being performed.

        Raises:
            aiohttp.ClientResponseError: If the API request fails.
        """
        try:
            error_data = await response.json()
            error_message = error_data.get('error', 'No error message provided.')
            error_details = error_data.get('details', 'No additional error details provided.')
        except:
            raise aiohttp.ClientResponseError(
                response.request_info,
                response.history,
                status=response.status,
                message=f'Failed to parse Firecrawl error response as JSON. Status code: {response.status}'
            )

        message = f"Error during {action}: Status code {response.status}. {error_message} - {error_details}"
        raise aiohttp.ClientResponseError(
            response.request_info,
            response.history,
            status=response.status,
            message=message
        )

    async def map_url(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Map a URL to discover all available links.

        Args:
            url (str): The URL to map.
            params (Optional[Dict[str, Any]]): Additional parameters for the mapping operation.

        Returns:
            Dict[str, Any]: A dictionary containing the mapped URLs and related information.

        Raises:
            aiohttp.ClientResponseError: If the API request fails.
        """
        headers = self._prepare_headers()
        json_data = {'url': url}
        if params:
            json_data.update(params)
        json_data = self._prepare_request_data(json_data)

        async with aiohttp.ClientSession(timeout=self.request_timeout) as session:
            async with session.post(
                f'{self.api_url}/v1/map',
                headers=headers,
                json=json_data
            ) as response:
                if response.status == 200:
                    try:
                        return await response.json()
                    except:
                        raise Exception('Failed to parse Firecrawl response as JSON.')
                else:
                    await self._handle_error(response, 'map URL')

    async def scrape_url(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Scrape content from a specific URL.

        Args:
            url (str): The URL to scrape.
            params (Optional[Dict[str, Any]]): Additional parameters for the scraping operation.

        Returns:
            Dict[str, Any]: A dictionary containing the scraped content and metadata.

        Raises:
            aiohttp.ClientResponseError: If the API request fails.
        """
        headers = self._prepare_headers()
        json_data = {'url': url}
        if params:
            json_data.update(params)
        json_data = self._prepare_request_data(json_data)

        async with aiohttp.ClientSession(timeout=self.request_timeout) as session:
            async with session.post(
                f'{self.api_url}/v1/scrape',
                headers=headers,
                json=json_data
            ) as response:
                if response.status == 200:
                    try:
                        return await response.json()
                    except:
                        raise Exception('Failed to parse Firecrawl response as JSON.')
                else:
                    await self._handle_error(response, 'scrape URL')

    async def search(self, query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Perform a web search using Firecrawl.

        Args:
            query (str): The search query.
            params (Optional[Dict[str, Any]]): Additional parameters for the search operation.

        Returns:
            Dict[str, Any]: A dictionary containing search results and metadata.

        Raises:
            aiohttp.ClientResponseError: If the API request fails.
        """
        headers = self._prepare_headers()
        json_data = {'query': query}
        if params:
            json_data.update(params)
        json_data = self._prepare_request_data(json_data)

        async with aiohttp.ClientSession(timeout=self.request_timeout) as session:
            async with session.post(
                f'{self.api_url}/v1/search',
                headers=headers,
                json=json_data
            ) as response:
                if response.status == 200:
                    try:
                        return await response.json()
                    except:
                        raise Exception('Failed to parse Firecrawl response as JSON.')
                else:
                    await self._handle_error(response, 'search')

    async def crawl_url(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Start a crawl job for a given URL.

        Args:
            url (str): The URL to crawl.
            params (Optional[Dict[str, Any]]): Additional parameters for the crawl operation.

        Returns:
            Dict[str, Any]: A dictionary containing the crawl results and metadata.

        Raises:
            aiohttp.ClientResponseError: If the API request fails.
        """
        headers = self._prepare_headers()
        json_data = {'url': url}
        if params:
            json_data.update(params)
        json_data = self._prepare_request_data(json_data)

        async with aiohttp.ClientSession(timeout=self.request_timeout) as session:
            async with session.post(
                f'{self.api_url}/v1/crawl',
                headers=headers,
                json=json_data
            ) as response:
                if response.status == 200:
                    try:
                        return await response.json()
                    except:
                        raise Exception('Failed to parse Firecrawl response as JSON.')
                else:
                    await self._handle_error(response, 'start crawl job')

    async def get_crawl_status(self, job_id: str) -> Dict[str, Any]:
        """Get the status of a crawl job.

        Args:
            job_id (str): The ID of the crawl job.

        Returns:
            Dict[str, Any]: A dictionary containing the crawl job status and results.

        Raises:
            aiohttp.ClientResponseError: If the API request fails.
        """
        headers = self._prepare_headers()

        async with aiohttp.ClientSession(timeout=self.request_timeout) as session:
            async with session.get(
                f'{self.api_url}/v1/crawl/{job_id}',
                headers=headers
            ) as response:
                if response.status == 200:
                    try:
                        return await response.json()
                    except:
                        raise Exception('Failed to parse Firecrawl response as JSON.')
                else:
                    await self._handle_error(response, 'check crawl status')

    async def extract(self, urls: List[str], params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Extract structured information from URLs.

        Args:
            urls (List[str]): List of URLs to extract information from.
            params (Optional[Dict[str, Any]]): Additional parameters for the extraction operation.

        Returns:
            Dict[str, Any]: A dictionary containing the extracted information and metadata.

        Raises:
            aiohttp.ClientResponseError: If the API request fails.
        """
        headers = self._prepare_headers()
        json_data = {'urls': urls}
        if params:
            json_data.update(params)
        json_data = self._prepare_request_data(json_data)

        async with aiohttp.ClientSession(timeout=self.request_timeout) as session:
            async with session.post(
                f'{self.api_url}/v1/extract',
                headers=headers,
                json=json_data
            ) as response:
                if response.status == 200:
                    try:
                        return await response.json()
                    except:
                        raise Exception('Failed to parse Firecrawl response as JSON.')
                else:
                    await self._handle_error(response, 'extract')

    async def get_extract_status(self, job_id: str) -> Dict[str, Any]:
        """Get the status of an extract job.

        Args:
            job_id (str): The ID of the extract job.

        Returns:
            Dict[str, Any]: A dictionary containing the extract job status and results.

        Raises:
            aiohttp.ClientResponseError: If the API request fails.
        """
        headers = self._prepare_headers()

        async with aiohttp.ClientSession(timeout=self.request_timeout) as session:
            async with session.get(
                f'{self.api_url}/v1/extract/{job_id}',
                headers=headers
            ) as response:
                if response.status == 200:
                    try:
                        return await response.json()
                    except:
                        raise Exception('Failed to parse Firecrawl response as JSON.')
                else:
                    await self._handle_error(response, 'check extract status') 