#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/2/27
@Author  : avianion
@File    : test_avian_api.py
@Desc    : Tests for Avian LLM provider (OpenAI-compatible)
"""

import pytest
from openai.types.chat import ChatCompletionChunk

from metagpt.configs.llm_config import LLMType
from metagpt.provider.llm_provider_registry import create_llm_instance
from metagpt.provider.openai_api import OpenAILLM
from tests.metagpt.provider.mock_llm_config import mock_llm_config_avian
from tests.metagpt.provider.req_resp_const import (
    get_openai_chat_completion,
    get_openai_chat_completion_chunk,
    llm_general_chat_funcs_test,
    messages,
    prompt,
    resp_cont_tmpl,
)

name = "Avian assistant"
resp_cont = resp_cont_tmpl.format(name=name)
default_resp = get_openai_chat_completion(name)
default_resp_chunk = get_openai_chat_completion_chunk(name, usage_as_dict=True)


class TestAvianProvider:
    def test_avian_llm_type_exists(self):
        """Verify that the AVIAN LLMType enum value exists."""
        assert LLMType.AVIAN.value == "avian"

    def test_avian_registered_as_openai_compatible(self):
        """Verify Avian is registered and creates an OpenAILLM instance."""
        llm = create_llm_instance(mock_llm_config_avian)
        assert isinstance(llm, OpenAILLM)

    def test_avian_client_kwargs(self):
        """Verify that Avian client kwargs are correctly configured."""
        instance = OpenAILLM(mock_llm_config_avian)
        kwargs = instance._make_client_kwargs()
        assert kwargs["api_key"] == "avian-mock-key"
        assert kwargs["base_url"] == "https://api.avian.io/v1"
        assert "http_client" not in kwargs

    def test_avian_model_set(self):
        """Verify the model name is correctly set on the instance."""
        instance = OpenAILLM(mock_llm_config_avian)
        assert instance.model == "deepseek/deepseek-v3.2"


async def mock_avian_acompletions_create(self, stream: bool = False, **kwargs) -> ChatCompletionChunk:
    if stream:

        class Iterator(object):
            async def __aiter__(self):
                yield default_resp_chunk

        return Iterator()
    else:
        return default_resp


@pytest.mark.asyncio
async def test_avian_acompletion(mocker):
    mocker.patch("openai.resources.chat.completions.AsyncCompletions.create", mock_avian_acompletions_create)

    llm = OpenAILLM(mock_llm_config_avian)

    resp = await llm.acompletion(messages)
    assert resp.choices[0].finish_reason == "stop"
    assert resp.choices[0].message.content == resp_cont

    await llm_general_chat_funcs_test(llm, prompt, messages, resp_cont)
