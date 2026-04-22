#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Astraflow LLM provider (by UCloud / 优刻得).
Astraflow is an OpenAI-compatible AI model aggregation platform supporting 200+ models.

Global endpoint : https://api-us-ca.umodelverse.ai/v1  (env var: ASTRAFLOW_API_KEY)
China  endpoint : https://api.modelverse.cn/v1         (env var: ASTRAFLOW_CN_API_KEY)
Sign up         : https://astraflow.ucloud.cn/

config2.yaml example (global):
```yaml
llm:
  api_type: "astraflow"
  api_key: "YOUR_ASTRAFLOW_API_KEY"
  model: "YOUR_MODEL_NAME"
```

config2.yaml example (China):
```yaml
llm:
  api_type: "astraflow_cn"
  api_key: "YOUR_ASTRAFLOW_CN_API_KEY"
  model: "YOUR_MODEL_NAME"
```
"""
from metagpt.configs.llm_config import LLMConfig, LLMType
from metagpt.provider.llm_provider_registry import register_provider
from metagpt.provider.openai_api import OpenAILLM

# Base URLs for both regional endpoints
_ASTRAFLOW_BASE_URL = "https://api-us-ca.umodelverse.ai/v1"
_ASTRAFLOW_CN_BASE_URL = "https://api.modelverse.cn/v1"

_BASE_URL_MAP = {
    LLMType.ASTRAFLOW: _ASTRAFLOW_BASE_URL,
    LLMType.ASTRAFLOW_CN: _ASTRAFLOW_CN_BASE_URL,
}


@register_provider([LLMType.ASTRAFLOW, LLMType.ASTRAFLOW_CN])
class AstraflowLLM(OpenAILLM):
    """LLM provider for Astraflow (UCloud / 优刻得).

    Astraflow is fully OpenAI-compatible, so this class is a lightweight
    subclass of OpenAILLM that selects the correct regional base URL
    when the caller has not set one explicitly.

    See https://astraflow.ucloud.cn/ for API key registration.
    """

    def __init__(self, config: LLMConfig):
        # If the user has not customised base_url, inject the correct
        # regional default before the parent class initialises the client.
        if not config.base_url or config.base_url == "https://api.openai.com/v1":
            config.base_url = _BASE_URL_MAP.get(config.api_type, _ASTRAFLOW_BASE_URL)
        super().__init__(config)
