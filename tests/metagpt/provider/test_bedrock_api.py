import json

import pytest

from metagpt.provider.bedrock.utils import (
    NOT_SUPPORT_STREAM_MODELS,
    SUPPORT_STREAM_MODELS,
)
from metagpt.provider.bedrock_api import BedrockLLM
from tests.metagpt.provider.mock_llm_config import mock_llm_config_bedrock
from tests.metagpt.provider.req_resp_const import (
    BEDROCK_PROVIDER_REQUEST_BODY,
    BEDROCK_PROVIDER_RESPONSE_BODY,
)

# all available model from bedrock
models = SUPPORT_STREAM_MODELS | NOT_SUPPORT_STREAM_MODELS
messages = [{"role": "user", "content": "Hi!"}]
usage = {
    "prompt_tokens": 1000000,
    "completion_tokens": 1000000,
}


def get_provider_name(model: str) -> str:
    arr = model.split(".")
    if len(arr) == 2:
        provider, model_name = arr  # meta、mistral……
    elif len(arr) == 3:
        # some model_ids may contain country like us.xx.xxx
        _, provider, model_name = arr
    return provider


def deal_special_provider(provider: str, model: str, stream: bool = False) -> str:
    # for ai21
    if "j2-" in model:
        provider = f"{provider}-j2"
    elif "jamba-" in model:
        provider = f"{provider}-jamba"
    elif "command-r" in model:
        provider = f"{provider}-command-r"
    if stream and "ai21" in model:
        provider = f"{provider}-stream"
    return provider


async def mock_invoke_model(self: BedrockLLM, *args, **kwargs) -> dict:
    provider = get_provider_name(self.model)
    self._update_costs(usage, self.model)
    provider = deal_special_provider(provider, self.model)
    return BEDROCK_PROVIDER_RESPONSE_BODY[provider]


async def mock_invoke_model_stream(self: BedrockLLM, *args, **kwargs) -> dict:
    # use json object to mock EventStream
    def dict2bytes(x):
        return json.dumps(x).encode("utf-8")

    provider = get_provider_name(self.model)

    if provider == "amazon":
        response_body_bytes = dict2bytes({"outputText": "Hello World"})
    elif provider == "anthropic":
        response_body_bytes = dict2bytes(
            {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "Hello World"}}
        )
    elif provider == "cohere":
        response_body_bytes = dict2bytes({"is_finished": False, "text": "Hello World"})
    else:
        provider = deal_special_provider(provider, self.model, stream=True)
        response_body_bytes = dict2bytes(BEDROCK_PROVIDER_RESPONSE_BODY[provider])

    response_body_stream = {"body": [{"chunk": {"bytes": response_body_bytes}}]}
    self._update_costs(usage, self.model)
    return response_body_stream


def get_bedrock_request_body(model_id) -> dict:
    provider = get_provider_name(model_id)
    provider = deal_special_provider(provider, model_id)
    return BEDROCK_PROVIDER_REQUEST_BODY[provider]


def is_subset(subset, superset) -> bool:
    """Ensure all fields in request body are allowed.

    ```python
    subset = {"prompt": "hello","kwargs": {"temperature": 0.9,"p": 0.0}}
    superset = {"prompt": "hello", "kwargs": {"temperature": 0.0, "top-p": 0.0}}
    is_subset(subset, superset)
    ```

    """
    for key, value in subset.items():
        if key not in superset:
            return False
        if isinstance(value, dict):
            if not isinstance(superset[key], dict):
                return False
            if not is_subset(value, superset[key]):
                return False
    return True


@pytest.fixture(scope="class", params=models)
def bedrock_api(request) -> BedrockLLM:
    model_id = request.param
    mock_llm_config_bedrock.model = model_id
    api = BedrockLLM(mock_llm_config_bedrock)
    return api


class TestBedrockAPI:
    def _patch_invoke_model(self, mocker):
        mocker.patch("metagpt.provider.bedrock_api.BedrockLLM.invoke_model", mock_invoke_model)

    def _patch_invoke_model_stream(self, mocker):
        mocker.patch(
            "metagpt.provider.bedrock_api.BedrockLLM.invoke_model_with_response_stream",
            mock_invoke_model_stream,
        )

    def test_get_request_body(self, bedrock_api: BedrockLLM):
        """Ensure request body has correct format"""
        provider = bedrock_api.provider
        request_body = json.loads(provider.get_request_body(messages, bedrock_api._const_kwargs))
        assert is_subset(request_body, get_bedrock_request_body(bedrock_api.config.model))

    @pytest.mark.asyncio
    async def test_aask(self, bedrock_api: BedrockLLM, mocker):
        self._patch_invoke_model(mocker)
        self._patch_invoke_model_stream(mocker)
        assert await bedrock_api.aask(messages, stream=False) == "Hello World"
        assert await bedrock_api.aask(messages, stream=True) == "Hello World"
