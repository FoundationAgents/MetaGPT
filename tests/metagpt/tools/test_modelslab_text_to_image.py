#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/3/1
@File    : test_modelslab_text_to_image.py
"""
import pytest

from metagpt.tools.modelslab_text_to_image import (
    ModelsLabText2Image,
    oas3_modelslab_text_to_image,
)


@pytest.mark.asyncio
async def test_text_2_image_success(mocker):
    """Test successful image generation (immediate success response)."""
    mock_post = mocker.patch("aiohttp.ClientSession.post")
    mock_get = mocker.patch("aiohttp.ClientSession.get")

    # Mock API response: immediate success
    mock_api_response = mocker.AsyncMock()
    mock_api_response.status = 200
    mock_api_response.json.return_value = {
        "status": "success",
        "output": ["https://modelslab.com/output/test.png"],
    }
    mock_post.return_value.__aenter__.return_value = mock_api_response

    # Mock image download
    mock_img_response = mocker.AsyncMock()
    mock_img_response.status = 200
    mock_img_response.read.return_value = b"fake_image_bytes"
    mock_get.return_value.__aenter__.return_value = mock_img_response

    client = ModelsLabText2Image(api_key="test_key", model_id="flux")
    result = await client.text_2_image("A futuristic city at night")

    assert result == b"fake_image_bytes"
    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args
    assert "modelslab.com/api/v6/images/text2img" in str(call_kwargs)


@pytest.mark.asyncio
async def test_text_2_image_processing(mocker):
    """Test async polling when API returns status: processing."""
    call_count = 0

    async def mock_json():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First call: processing
            return {"status": "processing", "id": "req_123", "eta": 10}
        else:
            # Second call: success
            return {"status": "success", "output": ["https://modelslab.com/output/test.png"]}

    mock_post = mocker.patch("aiohttp.ClientSession.post")
    mock_get = mocker.patch("aiohttp.ClientSession.get")
    mocker.patch("asyncio.sleep", return_value=None)

    mock_response = mocker.AsyncMock()
    mock_response.status = 200
    mock_response.json.side_effect = mock_json
    mock_post.return_value.__aenter__.return_value = mock_response

    mock_img_response = mocker.AsyncMock()
    mock_img_response.status = 200
    mock_img_response.read.return_value = b"polled_image_bytes"
    mock_get.return_value.__aenter__.return_value = mock_img_response

    client = ModelsLabText2Image(api_key="test_key")
    result = await client.text_2_image("A sunset over mountains")

    assert result == b"polled_image_bytes"
    assert call_count >= 2  # initial call + at least one poll


@pytest.mark.asyncio
async def test_text_2_image_error(mocker):
    """Test error response from API returns empty bytes."""
    mock_post = mocker.patch("aiohttp.ClientSession.post")

    mock_response = mocker.AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {
        "status": "error",
        "message": "Invalid API key",
    }
    mock_post.return_value.__aenter__.return_value = mock_response

    client = ModelsLabText2Image(api_key="bad_key")
    result = await client.text_2_image("Test prompt")

    assert result == b""


@pytest.mark.asyncio
async def test_oas3_modelslab_text_to_image_no_key(mocker):
    """Test that missing API key returns empty bytes."""
    mocker.patch.dict("os.environ", {}, clear=True)
    result = await oas3_modelslab_text_to_image("Test", api_key="")
    assert result == b""


@pytest.mark.asyncio
async def test_oas3_modelslab_text_to_image_env_key(mocker):
    """Test that MODELSLAB_API_KEY env var is used when api_key not provided."""
    mocker.patch.dict("os.environ", {"MODELSLAB_API_KEY": "env_key_123"})
    mock_post = mocker.patch("aiohttp.ClientSession.post")
    mock_get = mocker.patch("aiohttp.ClientSession.get")

    mock_response = mocker.AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {
        "status": "success",
        "output": ["https://modelslab.com/output/test.png"],
    }
    mock_post.return_value.__aenter__.return_value = mock_response

    mock_img = mocker.AsyncMock()
    mock_img.status = 200
    mock_img.read.return_value = b"env_key_image"
    mock_get.return_value.__aenter__.return_value = mock_img

    result = await oas3_modelslab_text_to_image("Test prompt")
    assert result == b"env_key_image"

    # Verify the API key from env was used
    call_json = mock_post.call_args.kwargs.get("json", {})
    assert call_json.get("key") == "env_key_123"


@pytest.mark.asyncio
async def test_size_parsing(mocker):
    """Test that size_type is correctly parsed into width/height."""
    mock_post = mocker.patch("aiohttp.ClientSession.post")
    mock_get = mocker.patch("aiohttp.ClientSession.get")

    mock_response = mocker.AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {
        "status": "success",
        "output": ["https://modelslab.com/output/test.png"],
    }
    mock_post.return_value.__aenter__.return_value = mock_response

    mock_img = mocker.AsyncMock()
    mock_img.status = 200
    mock_img.read.return_value = b"size_test"
    mock_get.return_value.__aenter__.return_value = mock_img

    client = ModelsLabText2Image(api_key="test_key")
    await client.text_2_image("Test", size_type="1344x768")

    call_json = mock_post.call_args.kwargs.get("json", {})
    assert call_json["width"] == 1344
    assert call_json["height"] == 768
