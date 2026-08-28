#!/usr/bin/env python
# -*- coding: utf-8 -*-

from metagpt.configs.llm_config import LLMType
from metagpt.provider.dashscope_api import DashScopeLLM
from metagpt.provider.llm_provider_registry import LLM_REGISTRY


def test_qwen_provider_registry():
    """Verify that QWEN and QWENCLOUD LLMTypes resolve to DashScopeLLM provider."""
    assert LLM_REGISTRY.get_provider(LLMType.DASHSCOPE) is DashScopeLLM
    assert LLM_REGISTRY.get_provider(LLMType.QWEN) is DashScopeLLM
    assert LLM_REGISTRY.get_provider(LLMType.QWENCLOUD) is DashScopeLLM
