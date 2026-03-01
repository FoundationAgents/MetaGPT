#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/3/1
@File    : modelslab_text_to_image.py
@Desc    : ModelsLab Text-to-Image OAS3 api, which provides text-to-image functionality.
           ModelsLab supports Flux, SDXL, Stable Diffusion 3.5, and 100+ community models.
           API docs: https://docs.modelslab.com
"""
import asyncio
import os

import aiohttp

from metagpt.logs import logger

_MODELSLAB_TEXT2IMG_URL = "https://modelslab.com/api/v6/images/text2img"
_MODELSLAB_FETCH_URL = "https://modelslab.com/api/v6/images/fetch/{request_id}"
_POLL_INTERVAL = 5  # seconds
_POLL_TIMEOUT = 300  # seconds


class ModelsLabText2Image:
    def __init__(self, api_key: str, model_id: str = "flux"):
        """Initialize ModelsLab text-to-image client.

        :param api_key: ModelsLab API key (see https://modelslab.com/account/api-key)
        :param model_id: Model to use. Recommended: 'flux' (default), 'fluxpro',
                         'sdxl', 'sd3.5', 'realistic-vision-v6'.
        """
        self.api_key = api_key
        self.model_id = model_id

    async def text_2_image(self, text: str, size_type: str = "1024x1024") -> bytes:
        """Generate an image from text using ModelsLab API.

        ModelsLab uses key-in-body authentication and an asynchronous pattern:
        the API may return ``status: processing`` with a request_id, requiring
        polling of the fetch endpoint until ``status: success``.

        :param text: The text prompt used for image generation.
        :param size_type: Image dimensions as 'WxH'. Supported: '512x512',
                          '1024x1024', '1344x768', '768x1344'.
        :return: Raw image bytes (PNG).
        """
        dims = size_type.split("x")
        width = int(dims[0]) if len(dims) == 2 else 1024
        height = int(dims[1]) if len(dims) == 2 else 1024

        payload = {
            "key": self.api_key,
            "model_id": self.model_id,
            "prompt": text,
            "negative_prompt": "blurry, low quality, watermark, distorted",
            "width": width,
            "height": height,
            "samples": 1,
            "num_inference_steps": 30,
            "safety_checker": "no",
            "enhance_prompt": "yes",
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    _MODELSLAB_TEXT2IMG_URL,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
            except Exception as e:
                logger.error(f"ModelsLab API request failed: {e}")
                return b""

        if data.get("status") == "error":
            logger.error(f"ModelsLab error: {data.get('message', 'Unknown error')}")
            return b""

        if data.get("status") == "processing":
            request_id = str(data.get("id", ""))
            if not request_id:
                logger.error("ModelsLab returned processing status without request ID")
                return b""
            data = await self._poll_until_ready(request_id)
            if not data:
                return b""

        output = data.get("output", [])
        if not output:
            logger.error("ModelsLab returned no image output")
            return b""

        return await self._download_image(output[0])

    async def _poll_until_ready(self, request_id: str) -> dict:
        """Poll ModelsLab fetch endpoint until image is ready or timeout."""
        fetch_url = _MODELSLAB_FETCH_URL.format(request_id=request_id)
        fetch_payload = {"key": self.api_key}
        deadline = asyncio.get_event_loop().time() + _POLL_TIMEOUT

        async with aiohttp.ClientSession() as session:
            while asyncio.get_event_loop().time() < deadline:
                await asyncio.sleep(_POLL_INTERVAL)
                try:
                    async with session.post(
                        fetch_url,
                        json=fetch_payload,
                        headers={"Content-Type": "application/json"},
                    ) as response:
                        response.raise_for_status()
                        data = await response.json()
                except Exception as e:
                    logger.warning(f"ModelsLab poll error: {e}")
                    continue

                if data.get("status") == "error":
                    logger.error(f"ModelsLab generation failed: {data.get('message')}")
                    return {}
                if data.get("status") == "success":
                    return data

        logger.error(f"ModelsLab timed out after {_POLL_TIMEOUT}s (id={request_id})")
        return {}

    async def _download_image(self, url: str) -> bytes:
        """Download image from URL and return raw bytes."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    response.raise_for_status()
                    return await response.read()
            except Exception as e:
                logger.error(f"Failed to download image from {url}: {e}")
                return b""


async def oas3_modelslab_text_to_image(
    text: str,
    size_type: str = "1024x1024",
    model_id: str = "flux",
    api_key: str = "",
) -> bytes:
    """Text to image using ModelsLab API.

    Supports Flux, SDXL, Stable Diffusion 3.5, and 100+ community models.

    :param text: The text used for image conversion.
    :param size_type: Image size. Options: '512x512', '1024x1024',
                      '1344x768', '768x1344'. Default: '1024x1024'.
    :param model_id: ModelsLab model ID. Default: 'flux'. See
                     https://docs.modelslab.com for available models.
    :param api_key: ModelsLab API key (or set MODELSLAB_API_KEY env var).
    :return: Raw image bytes (PNG), or empty bytes on failure.
    """
    if not text:
        return b""
    if not api_key:
        api_key = os.environ.get("MODELSLAB_API_KEY", "")
    if not api_key:
        logger.error("ModelsLab API key not provided. Set MODELSLAB_API_KEY env var.")
        return b""
    return await ModelsLabText2Image(api_key=api_key, model_id=model_id).text_2_image(
        text, size_type=size_type
    )
