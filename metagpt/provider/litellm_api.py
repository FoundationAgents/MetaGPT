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

from typing import Optional

import litellm
from litellm import CustomStreamWrapper, ModelResponse
from litellm.exceptions import APIConnectionError
from tenacity import after_log, retry, retry_if_exception_type, stop_after_attempt, wait_random_exponential

from metagpt.configs.llm_config import LLMConfig, LLMType
from metagpt.const import USE_CONFIG_TIMEOUT
from metagpt.logs import log_llm_stream, logger
from metagpt.provider.base_llm import BaseLLM
from metagpt.provider.llm_provider_registry import register_provider
from metagpt.utils.common import log_and_reraise
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

    def _update_costs(self, usage, model: str = None, local_calc_usage: bool = True):
        # LiteLLM returns an OpenAI-shaped pydantic usage object; convert to dict for BaseLLM._update_costs.
        if usage is not None and hasattr(usage, "model_dump"):
            usage = usage.model_dump()
        super()._update_costs(usage, model, local_calc_usage)
