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
from openai.types.completion_usage import CompletionUsage

from metagpt.configs.llm_config import LLMType
from metagpt.provider.llm_provider_registry import create_llm_instance
from metagpt.provider.openai_api import OpenAILLM
from metagpt.utils.cost_manager import CostManager
from metagpt.utils.token_counter import TOKEN_COSTS
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

    def test_avian_models_in_token_costs(self):
        """Verify all Avian models have entries in TOKEN_COSTS for CostManager."""
        avian_models = [
            "deepseek/deepseek-v3.2",
            "moonshotai/kimi-k2.5",
            "z-ai/glm-5",
            "minimax/minimax-m2.5",
        ]
        for model in avian_models:
            assert model in TOKEN_COSTS, f"{model} missing from TOKEN_COSTS"
            assert "prompt" in TOKEN_COSTS[model]
            assert "completion" in TOKEN_COSTS[model]

    def test_avian_cost_manager_update(self):
        """Verify CostManager.update_cost tracks costs for Avian models."""
        cost_manager = CostManager()
        cost_manager.update_cost(
            prompt_tokens=1000,
            completion_tokens=500,
            model="deepseek/deepseek-v3.2",
        )
        assert cost_manager.total_prompt_tokens == 1000
        assert cost_manager.total_completion_tokens == 500
        assert cost_manager.total_cost > 0

    def test_avian_update_costs_via_base_llm(self):
        """Verify _update_costs delegates to CostManager properly."""
        llm = OpenAILLM(mock_llm_config_avian)
        llm.cost_manager = CostManager()
        usage = CompletionUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150)
        llm._update_costs(usage)
        costs = llm.get_costs()
        assert costs.total_prompt_tokens == 100
        assert costs.total_completion_tokens == 50
        assert costs.total_cost > 0


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
    llm.cost_manager = CostManager()

    resp = await llm.acompletion(messages)
    assert resp.choices[0].finish_reason == "stop"
    assert resp.choices[0].message.content == resp_cont

    await llm_general_chat_funcs_test(llm, prompt, messages, resp_cont)
