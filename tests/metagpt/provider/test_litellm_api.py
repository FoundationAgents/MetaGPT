#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of LiteLLM provider

import pytest

from metagpt.provider.litellm_api import LiteLLM
from tests.metagpt.provider.mock_llm_config import mock_llm_config_litellm
from tests.metagpt.provider.req_resp_const import (
    get_openai_chat_completion,
    get_openai_chat_completion_chunk,
    llm_general_chat_funcs_test,
    messages,
    prompt,
    resp_cont_tmpl,
)

name = "LiteLLM-Claude"
resp_cont = resp_cont_tmpl.format(name=name)
default_resp = get_openai_chat_completion(name)
default_resp_chunk = get_openai_chat_completion_chunk(name, usage_as_dict=True)


async def mock_litellm_acompletion(**kwargs):
    """LiteLLM's module-level async completion — returns an OpenAI-shaped ModelResponse
    (or an async iterator of chunks when stream=True)."""
    if kwargs.get("stream"):

        class Iterator:
            async def __aiter__(self):
                yield default_resp_chunk

        return Iterator()
    return default_resp


@pytest.mark.asyncio
async def test_litellm_acompletion(mocker):
    mocker.patch("litellm.acompletion", mock_litellm_acompletion)

    llm = LiteLLM(mock_llm_config_litellm)

    resp = await llm.acompletion(messages)
    assert resp.choices[0].message.content == resp_cont

    await llm_general_chat_funcs_test(llm, prompt, messages, resp_cont)


def test_cons_kwargs_maps_config():
    llm = LiteLLM(mock_llm_config_litellm)
    kwargs = llm._cons_kwargs(messages)
    assert kwargs["model"] == "anthropic/claude-3-5-sonnet-20241022"
    assert kwargs["api_key"] == "sk-test"
    assert kwargs["messages"] == messages
    # Default base_url (openai) is NOT forwarded — LiteLLM routes by model prefix.
    assert "api_base" not in kwargs


def test_cons_kwargs_forwards_custom_base_url():
    from metagpt.configs.llm_config import LLMConfig

    cfg = LLMConfig(
        api_type="litellm",
        api_key="sk-test",
        base_url="https://my-proxy.example.com/v1",
        model="openrouter/meta-llama/llama-3-70b-instruct",
    )
    llm = LiteLLM(cfg)
    kwargs = llm._cons_kwargs(messages)
    assert kwargs["api_base"] == "https://my-proxy.example.com/v1"
