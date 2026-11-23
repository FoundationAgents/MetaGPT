#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/24 17:54
@Author  : alexanderwu
@File    : test_token_counter.py
"""
import pytest

from metagpt.utils.token_counter import count_message_tokens, count_output_tokens


def test_count_message_tokens():
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
    ]
    assert count_message_tokens(messages) == 15


def test_count_message_tokens_with_name():
    messages = [
        {"role": "user", "content": "Hello", "name": "John"},
        {"role": "assistant", "content": "Hi there!"},
    ]
    assert count_message_tokens(messages) == 17


def test_count_message_tokens_empty_input():
    """Empty input should return 3 tokens"""
    assert count_message_tokens([]) == 3


def test_count_message_tokens_invalid_model():
    """Invalid model should raise a KeyError"""
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
    ]
    with pytest.raises(NotImplementedError):
        count_message_tokens(messages, model="invalid_model")


def test_count_message_tokens_gpt_4():
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
    ]
    assert count_message_tokens(messages, model="gpt-4-0314") == 15


def test_count_string_tokens():
    """Test that the string tokens are counted correctly."""

    string = "Hello, world!"
    assert count_output_tokens(string, model="gpt-3.5-turbo-0301") == 4


def test_count_string_tokens_empty_input():
    """Test that the string tokens are counted correctly."""

    assert count_output_tokens("", model="gpt-3.5-turbo-0301") == 0


def test_count_string_tokens_gpt_4():
    """Test that the string tokens are counted correctly."""

    string = "Hello, world!"
    assert count_output_tokens(string, model="gpt-4-0314") == 4


if __name__ == "__main__":
    pytest.main([__file__, "-s"])


def test_count_message_tokens_tool_call_message_without_text():
    """An assistant message carrying only tool_calls (content None) adds no text tokens and must not raise."""
    with_tool_calls = [
        {"role": "user", "content": "Hello"},
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {"id": "1", "type": "function", "function": {"name": "f", "arguments": "{}"}}
            ],
        },
    ]
    empty_assistant = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": ""},
    ]

    assert count_message_tokens(with_tool_calls) == count_message_tokens(empty_assistant)


def test_count_message_tokens_counts_every_text_part():
    """Multimodal content is counted over all of its text parts, not only the last one."""
    one_part = [{"role": "user", "content": [{"type": "text", "text": "abcdefghij"}]}]
    two_parts = [
        {"role": "user", "content": [{"type": "text", "text": "abcde"}, {"type": "text", "text": "fghij"}]}
    ]

    assert count_message_tokens(two_parts) == count_message_tokens(one_part)