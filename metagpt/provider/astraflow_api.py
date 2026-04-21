#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Astraflow LLM provider (by UCloud / 优刻得).

Astraflow is an OpenAI-compatible AI model aggregation platform supporting 200+ models.

Endpoints:
  Global : https://api-us-ca.umodelverse.ai/v1   (env var: ASTRAFLOW_API_KEY)
  China  : https://api.modelverse.cn/v1          (env var: ASTRAFLOW_CN_API_KEY)

Sign-up / docs: https://astraflow.ucloud.cn/

config2.yaml example (global endpoint):
```yaml
llm:
  api_type: "astraflow"
  api_key: "YOUR_ASTRAFLOW_API_KEY"
  model: "deepseek-ai/DeepSeek-V3"
```

config2.yaml example (China endpoint):
```yaml
llm:
  api_type: "astraflow_cn"
  api_key: "YOUR_ASTRAFLOW_CN_API_KEY"
  model: "deepseek-ai/DeepSeek-V3"
```
"""

from metagpt.configs.llm_config import LLMConfig, LLMType
from metagpt.provider.llm_provider_registry import register_provider
from metagpt.provider.openai_api import OpenAILLM

ASTRAFLOW_GLOBAL_BASE_URL = "https://api-us-ca.umodelverse.ai/v1"
ASTRAFLOW_CN_BASE_URL = "https://api.modelverse.cn/v1"


@register_provider(LLMType.ASTRAFLOW)
class AstraflowLLM(OpenAILLM):
    """LLM provider for Astraflow global endpoint (https://api-us-ca.umodelverse.ai/v1).

    Astraflow is an OpenAI-compatible platform by UCloud that aggregates 200+ AI models.
    Use this class when your API key targets the international / global region.
    """

    def _init_client(self):
        """Override base URL to point at the Astraflow global endpoint unless the
        user has explicitly set a custom base_url in their config."""
        if not self.config.base_url or self.config.base_url == "https://api.openai.com/v1":
            self.config.base_url = ASTRAFLOW_GLOBAL_BASE_URL
        super()._init_client()


@register_provider(LLMType.ASTRAFLOW_CN)
class AstraflowCNLLM(OpenAILLM):
    """LLM provider for Astraflow China endpoint (https://api.modelverse.cn/v1).

    Astraflow is an OpenAI-compatible platform by UCloud that aggregates 200+ AI models.
    Use this class when your API key targets the China / mainland region.
    """

    def _init_client(self):
        """Override base URL to point at the Astraflow China endpoint unless the
        user has explicitly set a custom base_url in their config."""
        if not self.config.base_url or self.config.base_url == "https://api.openai.com/v1":
            self.config.base_url = ASTRAFLOW_CN_BASE_URL
        super()._init_client()
