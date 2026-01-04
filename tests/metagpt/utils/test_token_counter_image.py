#!/usr/bin/env python
# -*- coding: utf-8 -*-


from metagpt.utils.token_counter import count_image_tokens, count_message_tokens


def test_count_image_tokens_low():
    token_cost = count_image_tokens("http://example.com/image.png", detail="low")
    assert token_cost == 85


def test_count_image_tokens_auto_default():
    # Should default to high detail estimate (765)
    token_cost = count_image_tokens("http://example.com/image.png", detail="auto")
    assert token_cost == 765


def test_count_message_tokens_with_image_low():
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What is in this image?"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "http://example.com/image.png",
                        "detail": "low",
                    },
                },
            ],
        }
    ]
    # Text tokens: "What is in this image?" -> 5 tokens (approx)
    # Image tokens: 85
    # Message overhead: 3
    # Total should be roughly 93
    tokens = count_message_tokens(messages, model="gpt-4-vision-preview")
    assert tokens > 90 and tokens < 95


def test_count_message_tokens_with_image_auto():
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Analyze this."},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "http://example.com/image.png"
                        # detail defaults to auto
                    },
                },
            ],
        }
    ]
    # Text tokens: "Analyze this." -> ~3
    # Image tokens: 765 (default estimate)
    # Message overhead: 3
    # Total ~ 771
    tokens = count_message_tokens(messages, model="gpt-4-vision-preview")
    assert tokens > 760 and tokens < 780
