#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/5 22:59
@Author  : alexanderwu
@File    : __init__.py
"""

from importlib import import_module

from metagpt.provider.openai_api import OpenAILLM
from metagpt.provider.azure_openai_api import AzureOpenAILLM
from metagpt.provider.human_provider import HumanProvider


def _safe_import(module_path: str, attr_name: str):
    try:
        module = import_module(module_path)
        return getattr(module, attr_name)
    except (ImportError, ModuleNotFoundError):
        return None


GeminiLLM = _safe_import("metagpt.provider.google_gemini_api", "GeminiLLM")
OllamaLLM = _safe_import("metagpt.provider.ollama_api", "OllamaLLM")
ZhiPuAILLM = _safe_import("metagpt.provider.zhipuai_api", "ZhiPuAILLM")
MetaGPTLLM = _safe_import("metagpt.provider.metagpt_api", "MetaGPTLLM")
SparkLLM = _safe_import("metagpt.provider.spark_api", "SparkLLM")
QianFanLLM = _safe_import("metagpt.provider.qianfan_api", "QianFanLLM")
DashScopeLLM = _safe_import("metagpt.provider.dashscope_api", "DashScopeLLM")
AnthropicLLM = _safe_import("metagpt.provider.anthropic_api", "AnthropicLLM")
BedrockLLM = _safe_import("metagpt.provider.bedrock_api", "BedrockLLM")
ArkLLM = _safe_import("metagpt.provider.ark_api", "ArkLLM")
OpenrouterReasoningLLM = _safe_import("metagpt.provider.openrouter_reasoning", "OpenrouterReasoningLLM")

__all__ = [
    "GeminiLLM",
    "OpenAILLM",
    "ZhiPuAILLM",
    "AzureOpenAILLM",
    "MetaGPTLLM",
    "OllamaLLM",
    "HumanProvider",
    "SparkLLM",
    "QianFanLLM",
    "DashScopeLLM",
    "AnthropicLLM",
    "BedrockLLM",
    "ArkLLM",
    "OpenrouterReasoningLLM",
]
