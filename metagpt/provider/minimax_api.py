#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provider for MiniMax.
MiniMax exposes an OpenAI-compatible Chat Completions API, so this provider
subclasses ``OpenAILLM`` and only customizes the request constraints that MiniMax
requires (temperature must be in (0.0, 1.0]).

Two regional endpoints are supported by setting ``base_url`` accordingly:
  - global (default): https://api.minimax.io/v1
  - China:           https://api.minimaxi.com/v1

config2.yaml example:
```yaml
llm:
  api_type: "minimax"
  model: "MiniMax-M3"  # or MiniMax-M2.7
  base_url: "https://api.minimax.io/v1"  # global endpoint; use https://api.minimaxi.com/v1 for China
  api_key: "YOUR_API_KEY"
  temperature: 0.5  # MiniMax requires temperature in (0.0, 1.0]
```
"""

from __future__ import annotations

from metagpt.configs.llm_config import LLMType
from metagpt.const import USE_CONFIG_TIMEOUT
from metagpt.provider.llm_provider_registry import register_provider
from metagpt.provider.openai_api import OpenAILLM

# MiniMax requires the sampling temperature to be strictly greater than 0 and at most 1.
MINIMAX_MIN_TEMPERATURE = 0.01
MINIMAX_MAX_TEMPERATURE = 1.0


@register_provider(LLMType.MINIMAX)
class MiniMaxLLM(OpenAILLM):
    """OpenAI-compatible provider for the MiniMax Chat Completions API.

    MiniMax accepts the standard OpenAI Chat Completions request shape. The only
    constraint that needs enforcing here is ``temperature``, which must be in the
    open-closed range (0.0, 1.0]; a non-positive temperature is rejected by the API,
    so it is bumped up to ``MINIMAX_MIN_TEMPERATURE``.
    """

    def _cons_kwargs(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT, **extra_kwargs) -> dict:
        kwargs = super()._cons_kwargs(messages, timeout=timeout, **extra_kwargs)
        # MiniMax rejects temperature <= 0; clamp to the valid range (0.0, 1.0].
        temperature = kwargs.get("temperature")
        if temperature is None or temperature <= 0:
            kwargs["temperature"] = MINIMAX_MIN_TEMPERATURE
        elif temperature > MINIMAX_MAX_TEMPERATURE:
            kwargs["temperature"] = MINIMAX_MAX_TEMPERATURE
        return kwargs
