#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of LiteLLM provider

import json
from types import SimpleNamespace

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


def _fake_tool_call_response(arguments: dict) -> SimpleNamespace:
    """LiteLLM's ModelResponse mirrors OpenAI's ChatCompletion, so we can build a
    duck-typed stand-in for tool_call responses using SimpleNamespace."""
    function = SimpleNamespace(name="execute", arguments=json.dumps(arguments))
    tool_call = SimpleNamespace(type="function", function=function, id="call_1")
    message = SimpleNamespace(role="assistant", content=None, tool_calls=[tool_call])
    choice = SimpleNamespace(message=message, finish_reason="tool_calls", index=0)
    return SimpleNamespace(choices=[choice], usage=None)


@pytest.mark.asyncio
async def test_aask_code_forwards_tools_and_parses_arguments(mocker):
    """LiteLLM's aask_code must (1) inject the default ``tools=[...]`` schema,
    (2) forward it to ``litellm.acompletion``, (3) parse the returned tool_call
    arguments into a dict. This is the path used by Engineer / QAEngineer /
    DataAnalyst roles when LLM is configured with ``api_type: litellm``."""

    captured = {}

    async def _capturing_acompletion(**kwargs):
        captured.update(kwargs)
        return _fake_tool_call_response({"language": "python", "code": "print('hi')"})

    mocker.patch("litellm.acompletion", _capturing_acompletion)

    llm = LiteLLM(mock_llm_config_litellm)
    result = await llm.aask_code([{"role": "user", "content": "Write a hello world"}])

    # Default function schema was injected
    assert "tools" in captured, "aask_code should inject a default tools schema"
    assert captured["tools"][0]["type"] == "function"
    assert captured["tools"][0]["function"]["name"] == "execute"

    # Parsed arguments dict is returned
    assert result == {"language": "python", "code": "print('hi')"}


@pytest.mark.asyncio
async def test_aask_code_respects_user_supplied_tools(mocker):
    """When the caller passes their own ``tools=[...]``, the default schema must
    not overwrite it."""

    captured = {}

    async def _capturing_acompletion(**kwargs):
        captured.update(kwargs)
        return _fake_tool_call_response({"lang": "go", "code": "fmt.Println(1)"})

    mocker.patch("litellm.acompletion", _capturing_acompletion)

    custom_tools = [{"type": "function", "function": {"name": "go_tool", "parameters": {}}}]
    llm = LiteLLM(mock_llm_config_litellm)
    await llm.aask_code([{"role": "user", "content": "print 1 in Go"}], tools=custom_tools)

    assert captured["tools"] == custom_tools
