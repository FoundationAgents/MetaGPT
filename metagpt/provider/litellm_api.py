#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/04/21
@Author  : aarish
@File    : litellm_api.py
@Desc    : LiteLLM provider — unified access to 100+ LLM providers via the LiteLLM AI gateway.
           https://docs.litellm.ai/docs/providers
"""
from __future__ import annotations

import json
import re
from typing import Optional

import litellm
from litellm import CustomStreamWrapper, ModelResponse
from litellm.exceptions import APIConnectionError
from tenacity import after_log, retry, retry_if_exception_type, stop_after_attempt, wait_random_exponential

from metagpt.configs.llm_config import LLMConfig, LLMType
from metagpt.const import USE_CONFIG_TIMEOUT
from metagpt.logs import log_llm_stream, logger
from metagpt.provider.base_llm import BaseLLM
from metagpt.provider.constant import GENERAL_FUNCTION_SCHEMA
from metagpt.provider.llm_provider_registry import register_provider
from metagpt.utils.common import CodeParser, log_and_reraise
from metagpt.utils.cost_manager import CostManager


@register_provider(LLMType.LITELLM)
class LiteLLM(BaseLLM):
    """LiteLLM AI gateway provider.

    Routes chat completions through litellm.acompletion(), which supports 100+ providers
    (OpenAI, Anthropic, Bedrock, Vertex, Ollama, OpenRouter, Groq, DeepSeek, etc.).

    Set `api_type: litellm` and a litellm-style model name (e.g. `anthropic/claude-3-5-sonnet-20241022`)
    in config2.yaml. See https://docs.litellm.ai/docs/providers for the full list.
    """

    def __init__(self, config: LLMConfig):
        self.config = config
        self.model = config.model
        self.pricing_plan = config.pricing_plan or self.model
        self.cost_manager: Optional[CostManager] = None

    def _cons_kwargs(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT, **extra_kwargs) -> dict:
        kwargs = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.config.max_token,
            "temperature": self.config.temperature,
            "timeout": self.get_timeout(timeout),
        }
        # Only forward api_key/api_base when the user has explicitly set them; otherwise
        # LiteLLM will pick up provider-specific env vars (OPENAI_API_KEY, ANTHROPIC_API_KEY, ...).
        if self.config.api_key and self.config.api_key != "sk-":
            kwargs["api_key"] = self.config.api_key
        if self.config.base_url and self.config.base_url != "https://api.openai.com/v1":
            kwargs["api_base"] = self.config.base_url
        if self.config.proxy:
            kwargs["proxy"] = self.config.proxy
        if self.config.reasoning:
            kwargs["thinking"] = {"type": "enabled", "budget_tokens": self.config.reasoning_max_token}
        if extra_kwargs:
            kwargs.update(extra_kwargs)
        return kwargs

    async def _achat_completion(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT) -> ModelResponse:
        rsp: ModelResponse = await litellm.acompletion(**self._cons_kwargs(messages, timeout=timeout))
        self._update_costs(rsp.usage)
        return rsp

    async def acompletion(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT) -> ModelResponse:
        return await self._achat_completion(messages, timeout=timeout)

    async def _achat_completion_stream(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT) -> str:
        stream: CustomStreamWrapper = await litellm.acompletion(
            **self._cons_kwargs(messages, timeout=timeout), stream=True
        )
        collected_messages = []
        usage = None
        async for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            content = getattr(delta, "content", None) or ""
            if content:
                log_llm_stream(content)
                collected_messages.append(content)
            if hasattr(chunk, "usage") and chunk.usage:
                usage = chunk.usage

        log_llm_stream("\n")
        full_reply_content = "".join(collected_messages)
        if usage is not None:
            self._update_costs(usage)
        return full_reply_content

    @retry(
        wait=wait_random_exponential(min=1, max=60),
        stop=stop_after_attempt(6),
        after=after_log(logger, logger.level("WARNING").name),
        retry=retry_if_exception_type(APIConnectionError),
        retry_error_callback=log_and_reraise,
    )
    async def acompletion_text(self, messages: list[dict], stream: bool = False, timeout=USE_CONFIG_TIMEOUT) -> str:
        """Async completion returning plain text. Supports stream-print."""
        if stream:
            return await self._achat_completion_stream(messages, timeout=timeout)
        rsp = await self._achat_completion(messages, timeout=timeout)
        return self.get_choice_text(rsp)

    def get_choice_text(self, rsp: ModelResponse) -> str:
        return rsp.choices[0].message.content if rsp.choices else ""

    async def _achat_completion_function(
        self, messages: list[dict], timeout: int = USE_CONFIG_TIMEOUT, **chat_configs
    ) -> ModelResponse:
        messages = self.format_msg(messages)
        kwargs = self._cons_kwargs(messages=messages, timeout=self.get_timeout(timeout), **chat_configs)
        rsp: ModelResponse = await litellm.acompletion(**kwargs)
        self._update_costs(rsp.usage)
        return rsp

    async def aask_code(self, messages: list[dict], timeout: int = USE_CONFIG_TIMEOUT, **kwargs) -> dict:
        """Use function-calling to ask for code. Mirrors OpenAILLM.aask_code.

        LiteLLM passes ``tools=[...]`` through to every provider that supports native
        function calling (OpenAI, Anthropic, Gemini, Bedrock, Groq, DeepSeek, ...) and
        returns the response in OpenAI-shape ``tool_calls`` format regardless of
        backend, so the OpenAI parsing logic transfers directly.

        Examples:
            >>> llm = LiteLLM(cfg)
            >>> msg = [{'role': 'user', 'content': "Write a python hello world code."}]
            >>> rsp = await llm.aask_code(msg)
            # -> {'language': 'python', 'code': "print('Hello, World!')"}
        """
        if "tools" not in kwargs:
            kwargs["tools"] = [{"type": "function", "function": GENERAL_FUNCTION_SCHEMA}]
        rsp = await self._achat_completion_function(messages, **kwargs)
        return self.get_choice_function_arguments(rsp)

    def _parse_arguments(self, arguments: str) -> dict:
        """Parse ``arguments`` JSON from a function-call response.

        Fallback when the JSON is malformed: regex out ``language`` and ``code`` keys.
        Mirrors OpenAILLM._parse_arguments for identical behaviour across providers.
        """
        if "language" not in arguments and "code" not in arguments:
            logger.warning(f"Not found `code`, `language`, We assume it is pure code:\n {arguments}\n. ")
            return {"language": "python", "code": arguments}

        language_pattern = re.compile(r'[\"\']?language[\"\']?\s*:\s*["\']([^"\']+?)["\']', re.DOTALL)
        language_match = language_pattern.search(arguments)
        language_value = language_match.group(1) if language_match else "python"

        code_pattern = r'(["\'`]{3}|["\'`])([\s\S]*?)\1'
        try:
            code_value = re.findall(code_pattern, arguments)[-1][-1]
        except Exception as e:
            logger.error(f"{e}, when re.findall({code_pattern}, {arguments})")
            code_value = None

        if code_value is None:
            raise ValueError(f"Parse code error for {arguments}")
        return {"language": language_value, "code": code_value}

    def get_choice_function_arguments(self, rsp: ModelResponse) -> dict:
        """Parse the first tool_call's function arguments.

        LiteLLM's ``ModelResponse`` mirrors OpenAI's ``ChatCompletion`` shape, so the
        same attribute access path works across providers.
        """
        message = rsp.choices[0].message
        if (
            message.tool_calls is not None
            and message.tool_calls[0].function is not None
            and message.tool_calls[0].function.arguments is not None
        ):
            try:
                return json.loads(message.tool_calls[0].function.arguments, strict=False)
            except json.decoder.JSONDecodeError as e:
                error_msg = (
                    f"Got JSONDecodeError for \n{'--' * 40} \n{message.tool_calls[0].function.arguments}, {str(e)}"
                )
                logger.error(error_msg)
                return self._parse_arguments(message.tool_calls[0].function.arguments)
        elif message.tool_calls is None and message.content is not None:
            # Some providers return the code block in content instead of tool_calls.
            code_formats = "```"
            if message.content.startswith(code_formats) and message.content.endswith(code_formats):
                code = CodeParser.parse_code(text=message.content)
                return {"language": "python", "code": code}
            return {"language": "markdown", "code": self.get_choice_text(rsp)}
        else:
            logger.error(f"Failed to parse \n {rsp}\n")
            raise Exception(f"Failed to parse \n {rsp}\n")

    def _update_costs(self, usage, model: str = None, local_calc_usage: bool = True):
        # LiteLLM returns an OpenAI-shaped pydantic usage object; convert to dict for BaseLLM._update_costs.
        if usage is not None and hasattr(usage, "model_dump"):
            usage = usage.model_dump()
        super()._update_costs(usage, model, local_calc_usage)
