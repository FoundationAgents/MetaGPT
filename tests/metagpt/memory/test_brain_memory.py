#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/8/27
@Author  : mashenquan
@File    : test_brain_memory.py
"""

import json

import pytest

from metagpt.config2 import Config
from metagpt.llm import LLM
from metagpt.memory.brain_memory import BrainMemory
from metagpt.schema import Message


@pytest.mark.asyncio
async def test_memory():
    memory = BrainMemory()
    memory.add_talk(Message(content="talk"))
    assert memory.history[0].role == "user"
    memory.add_answer(Message(content="answer"))
    assert memory.history[1].role == "assistant"
    redis_key = BrainMemory.to_redis_key("none", "user_id", "chat_id")
    await memory.dumps(redis_key=redis_key)
    assert memory.exists("talk")
    assert 1 == memory.to_int("1", 0)
    memory.last_talk = "AAA"
    assert memory.pop_last_talk() == "AAA"
    assert memory.last_talk is None
    assert memory.is_history_available
    assert memory.history_text

    memory = await BrainMemory.loads(redis_key=redis_key)
    assert memory


@pytest.mark.parametrize(
    ("input", "tag", "val"),
    [("[TALK]:Hello", "TALK", "Hello"), ("Hello", None, "Hello"), ("[TALK]Hello", None, "[TALK]Hello")],
)
def test_extract_info(input, tag, val):
    t, v = BrainMemory.extract_info(input)
    assert tag == t
    assert val == v


@pytest.mark.asyncio
@pytest.mark.parametrize("llm", [LLM()])
async def test_memory_llm(llm):
    memory = BrainMemory()
    for i in range(500):
        memory.add_talk(Message(content="Lily is a girl.\n"))

    res = await memory.is_related("apple", "moon", llm)
    assert not res

    res = await memory.rewrite(sentence="apple Lily eating", context="", llm=llm)
    assert "Lily" in res

    res = await memory.summarize(llm=llm)
    assert res

    res = await memory.get_title(llm=llm)
    assert res
    assert "Lily" in res
    assert memory.history or memory.historical_summary


def test_default_config_is_applied():
    # The field default must go through the validator, otherwise `config` stays
    # None and every method touching it raises AttributeError.
    memory = BrainMemory()
    assert isinstance(memory.config, Config)


@pytest.mark.asyncio
async def test_dumps_with_default_config():
    memory = BrainMemory()
    memory.add_talk(Message(content="talk"))
    # Used to raise AttributeError: 'NoneType' object has no attribute 'redis'
    await memory.dumps(redis_key=BrainMemory.to_redis_key("none", "user_id", "chat_id"))
    assert not memory.is_dirty


def test_config_is_not_serialized():
    # `config` holds llm.api_key, and model_dump_json() is what gets written to redis.
    memory = BrainMemory()
    dumped = memory.model_dump_json()
    assert "config" not in json.loads(dumped)
    assert "api_key" not in dumped


@pytest.mark.asyncio
async def test_metagpt_summarize_uses_config_redis_key():
    memory = BrainMemory()
    memory.add_talk(Message(content="Lily is a girl."))
    # Used to raise AttributeError: 'NoneType' object has no attribute 'key'
    res = await memory._metagpt_summarize(max_words=200)
    assert json.loads(res) == [{"content": "Lily is a girl.", "role": "user"}]


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
