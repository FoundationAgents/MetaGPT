#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : self-host open llm model with ollama which isn't openai-api-compatible

import json
from enum import Enum, auto
from typing import AsyncGenerator, Optional, Tuple

from metagpt.configs.llm_config import LLMConfig, LLMType
from metagpt.const import USE_CONFIG_TIMEOUT
from metagpt.logs import log_llm_stream, logger
from metagpt.provider.base_llm import BaseLLM
from metagpt.provider.general_api_requestor import GeneralAPIRequestor, OpenAIResponse
from metagpt.provider.llm_provider_registry import register_provider
from metagpt.utils.cost_manager import TokenCostManager


class OllamaMessageAPI(Enum):
    # default
    CHAT = auto()
    GENERATE = auto()
    EMBED = auto()
    EMBEDDINGS = auto()


class OllamaMessageBase:
    api_type = OllamaMessageAPI.CHAT

    def __init__(self, model: str, **additional_kwargs) -> None:
        self.model, self.additional_kwargs = model, additional_kwargs
        self._image_b64_rms = len("data:image/jpeg;base64,")

    @property
    def api_suffix(self) -> str:
        raise NotImplementedError

    def apply(self, messages: list[dict]) -> dict:
        raise NotImplementedError

    def decode(self, response: OpenAIResponse) -> dict:
        """Fix Ollama API response parsing, support multi-line JSON streaming responses"""
        try:
            # Get raw data
            data = response.data.decode("utf-8")
            
            # Remove possible BOM markers
            if data.startswith('\ufeff'):
                data = data[1:]
            
            # Process multi-line JSON (streaming responses)
            lines = data.strip().split('\n')
            json_objects = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Skip SSE format "data: " prefix
                if line.startswith('data: '):
                    line = line[6:]
                
                # Skip end markers
                if line == '[DONE]':
                    continue
                    
                try:
                    # Try to parse each line of JSON
                    json_obj = json.loads(line)
                    json_objects.append(json_obj)
                except json.JSONDecodeError:
                    # If single line parsing fails, it might be partial data, skip
                    continue
            
            # If there are multiple JSON objects, return the last one (usually the complete response)
            if json_objects:
                return json_objects[-1]
            else:
                # If no JSON was successfully parsed, try to parse the entire data
                return json.loads(data)
                
        except json.JSONDecodeError as e:
            # If all parsing fails, return error message
            try:
                data = response.data.decode("utf-8")
                logger.warning(f"Ollama API response parsing failed: {e}, Raw data: {data[:200]}...")
                return {"error": f"JSON parsing failed: {e}", "raw_data": data[:200]}
            except Exception as e2:
                logger.error(f"Ollama API response parsing completely failed: {e2}")
                return {"error": f"Response parsing failed: {e2}"}

    def get_choice(self, to_choice_dict: dict) -> str:
        # Prioritize handling exception responses
        if "error" in to_choice_dict:
            # Return error message and partial raw data
            raw = to_choice_dict.get("raw_data", "")
            return f"[Ollama Error] {to_choice_dict['error']} | Raw: {raw[:200]}"
        # Normal response
        if "message" in to_choice_dict:
            message = to_choice_dict["message"]
            if message.get("role") == "assistant":
                return message.get("content", "")
            else:
                return str(message)
        # Fallback to return all content
        return str(to_choice_dict)

    def _parse_input_msg(self, msg: dict) -> Tuple[Optional[str], Optional[str]]:
        if "type" in msg:
            tpe = msg["type"]
            if tpe == "text":
                return msg["text"], None
            elif tpe == "image_url":
                return None, msg["image_url"]["url"][self._image_b64_rms :]
            else:
                raise ValueError
        else:
            raise ValueError


class OllamaMessageMeta(type):
    registed_message = {}

    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)
        for base in bases:
            if issubclass(base, OllamaMessageBase):
                api_type = attrs["api_type"]
                assert api_type not in OllamaMessageMeta.registed_message, "api_type already exist"
                assert isinstance(api_type, OllamaMessageAPI), "api_type not support"
                OllamaMessageMeta.registed_message[api_type] = cls

    @classmethod
    def get_message(cls, input_type: OllamaMessageAPI) -> type[OllamaMessageBase]:
        return cls.registed_message[input_type]


class OllamaMessageChat(OllamaMessageBase, metaclass=OllamaMessageMeta):
    api_type = OllamaMessageAPI.CHAT

    @property
    def api_suffix(self) -> str:
        return "/api/chat"

    def apply(self, messages: list[dict]) -> dict:
        content = messages[0]["content"]
        prompts = []
        images = []
        if isinstance(content, list):
            for msg in content:
                prompt, image = self._parse_input_msg(msg)
                if prompt:
                    prompts.append(prompt)
                if image:
                    images.append(image)
        else:
            prompts.append(content)
        messes = []
        for prompt in prompts:
            if len(images) > 0:
                messes.append({"role": "user", "content": prompt, "images": images})
            else:
                messes.append({"role": "user", "content": prompt})
        sends = {"model": self.model, "messages": messes}
        sends.update(self.additional_kwargs)
        return sends

    def get_choice(self, to_choice_dict: dict) -> str:
        message = to_choice_dict["message"]
        if message["role"] == "assistant":
            return message["content"]
        else:
            raise ValueError


class OllamaMessageGenerate(OllamaMessageChat, metaclass=OllamaMessageMeta):
    api_type = OllamaMessageAPI.GENERATE

    @property
    def api_suffix(self) -> str:
        return "/api/generate"

    def apply(self, messages: list[dict]) -> dict:
        content = messages[0]["content"]
        prompts = []
        images = []
        if isinstance(content, list):
            for msg in content:
                prompt, image = self._parse_input_msg(msg)
                if prompt:
                    prompts.append(prompt)
                if image:
                    images.append(image)
        else:
            prompts.append(content)
        if len(images) > 0:
            sends = {"model": self.model, "prompt": "\n".join(prompts), "images": images}
        else:
            sends = {"model": self.model, "prompt": "\n".join(prompts)}
        sends.update(self.additional_kwargs)
        return sends

    def get_choice(self, to_choice_dict: dict) -> str:
        return to_choice_dict["response"]


class OllamaMessageEmbeddings(OllamaMessageBase, metaclass=OllamaMessageMeta):
    api_type = OllamaMessageAPI.EMBEDDINGS

    @property
    def api_suffix(self) -> str:
        return "/api/embeddings"

    def apply(self, messages: list[dict]) -> dict:
        content = messages[0]["content"]
        prompts = []  # NOTE: not support image to embedding
        if isinstance(content, list):
            for msg in content:
                prompt, _ = self._parse_input_msg(msg)
                if prompt:
                    prompts.append(prompt)
        else:
            prompts.append(content)
        sends = {"model": self.model, "prompt": "\n".join(prompts)}
        sends.update(self.additional_kwargs)
        return sends


class OllamaMessageEmbed(OllamaMessageEmbeddings, metaclass=OllamaMessageMeta):
    api_type = OllamaMessageAPI.EMBED

    @property
    def api_suffix(self) -> str:
        return "/api/embed"

    def apply(self, messages: list[dict]) -> dict:
        content = messages[0]["content"]
        prompts = []  # NOTE: not support image to embedding
        if isinstance(content, list):
            for msg in content:
                prompt, _ = self._parse_input_msg(msg)
                if prompt:
                    prompts.append(prompt)
        else:
            prompts.append(content)
        sends = {"model": self.model, "input": prompts}
        sends.update(self.additional_kwargs)
        return sends


@register_provider(LLMType.OLLAMA)
class OllamaLLM(BaseLLM):
    """
    Refs to `https://github.com/jmorganca/ollama/blob/main/docs/api.md#generate-a-chat-completion`
    """

    def __init__(self, config: LLMConfig):
        self.client = GeneralAPIRequestor(base_url=config.base_url, key=config.api_key)
        self.config = config
        self.model = config.model
        self.http_method = "post"
        self.use_system_prompt = False
        self.cost_manager = TokenCostManager()
        self.__init_ollama(config)

    @property
    def _llama_api_inuse(self) -> OllamaMessageAPI:
        return OllamaMessageAPI.CHAT

    @property
    def _llama_api_kwargs(self) -> dict:
        return {"options": {"temperature": 0.3}, "stream": self.config.stream}

    def __init_ollama(self, config: LLMConfig):
        assert config.base_url, "ollama base url is required!"
        assert config.model, "ollama model is required!"
        self.model = config.model
        self.pricing_plan = self.model
        ollama_message = OllamaMessageMeta.get_message(self._llama_api_inuse)
        self.ollama_message = ollama_message(model=self.model, **self._llama_api_kwargs)

    def get_usage(self, resp: dict) -> dict:
        return {"prompt_tokens": resp.get("prompt_eval_count", 0), "completion_tokens": resp.get("eval_count", 0)}

    async def _achat_completion(self, messages: list[dict], timeout: int = USE_CONFIG_TIMEOUT) -> dict:
        resp, _, _ = await self.client.arequest(
            method=self.http_method,
            url=self.ollama_message.api_suffix,
            params=self.ollama_message.apply(messages=messages),
            request_timeout=self.get_timeout(timeout),
        )
        if isinstance(resp, AsyncGenerator):
            return await self._processing_openai_response_async_generator(resp)
        elif isinstance(resp, OpenAIResponse):
            return self._processing_openai_response(resp)
        else:
            raise ValueError

    def get_choice_text(self, rsp):
        return self.ollama_message.get_choice(rsp)

    async def acompletion(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT) -> dict:
        return await self._achat_completion(messages, timeout=self.get_timeout(timeout))

    async def _achat_completion_stream(self, messages: list[dict], timeout: int = USE_CONFIG_TIMEOUT) -> str:
        resp, _, _ = await self.client.arequest(
            method=self.http_method,
            url=self.ollama_message.api_suffix,
            params=self.ollama_message.apply(messages=messages),
            request_timeout=self.get_timeout(timeout),
            stream=True,
        )
        if isinstance(resp, AsyncGenerator):
            return await self._processing_openai_response_async_generator(resp)
        elif isinstance(resp, OpenAIResponse):
            # For non-streaming responses, extract text content
            resp_dict = self._processing_openai_response(resp)
            return self.ollama_message.get_choice(resp_dict)
        else:
            raise ValueError

    def _processing_openai_response(self, openai_resp: OpenAIResponse) -> dict:
        resp = self.ollama_message.decode(openai_resp)
        usage = self.get_usage(resp)
        self._update_costs(usage)
        return resp

    async def _processing_openai_response_async_generator(self, ag_openai_resp: AsyncGenerator[OpenAIResponse, None]):
        collected_content = []
        usage = {}
        async for raw_chunk in ag_openai_resp:
            chunk = self.ollama_message.decode(raw_chunk)

            if not chunk.get("done", False):
                content = self.ollama_message.get_choice(chunk)
                collected_content.append(content)
                log_llm_stream(content)
            else:
                # stream finished
                usage = self.get_usage(chunk)
        log_llm_stream("\n")

        self._update_costs(usage)
        full_content = "".join(collected_content)
        return full_content


@register_provider(LLMType.OLLAMA_GENERATE)
class OllamaGenerate(OllamaLLM):
    @property
    def _llama_api_inuse(self) -> OllamaMessageAPI:
        return OllamaMessageAPI.GENERATE

    @property
    def _llama_api_kwargs(self) -> dict:
        return {"options": {"temperature": 0.3}, "stream": self.config.stream}


@register_provider(LLMType.OLLAMA_EMBEDDINGS)
class OllamaEmbeddings(OllamaLLM):
    @property
    def _llama_api_inuse(self) -> OllamaMessageAPI:
        return OllamaMessageAPI.EMBEDDINGS

    @property
    def _llama_api_kwargs(self) -> dict:
        return {"options": {"temperature": 0.3}}

    @property
    def _llama_embedding_key(self) -> str:
        return "embedding"

    async def _achat_completion(self, messages: list[dict], timeout: int = USE_CONFIG_TIMEOUT) -> dict:
        resp, _, _ = await self.client.arequest(
            method=self.http_method,
            url=self.ollama_message.api_suffix,
            params=self.ollama_message.apply(messages=messages),
            request_timeout=self.get_timeout(timeout),
        )
        if isinstance(resp, OpenAIResponse):
            decoded_resp = self.ollama_message.decode(resp)
            return decoded_resp.get(self._llama_embedding_key, {})
        else:
            raise ValueError("Expected OpenAIResponse")

    async def _achat_completion_stream(self, messages: list[dict], timeout: int = USE_CONFIG_TIMEOUT) -> str:
        return await self._achat_completion(messages, timeout=self.get_timeout(timeout))

    def get_choice_text(self, rsp) -> str:
        if isinstance(rsp, dict):
            return str(rsp)
        return str(rsp)


@register_provider(LLMType.OLLAMA_EMBED)
class OllamaEmbed(OllamaEmbeddings):
    @property
    def _llama_api_inuse(self) -> OllamaMessageAPI:
        return OllamaMessageAPI.EMBED

    @property
    def _llama_embedding_key(self) -> str:
        return "embeddings"
