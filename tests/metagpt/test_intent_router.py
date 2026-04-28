#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest

from metagpt.intent_router import (
    extract_paper_research_topic,
    looks_like_paper_research_topic,
    should_trigger_literature_review,
)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("find papers about reinforcement learning", True),
        ("please search essay on software engineering", True),
        ("我想检索关于多智能体系统的论文", True),
        ("Summarize this sprint plan", False),
        ("build me a todo app", False),
    ],
)
def test_looks_like_paper_research_topic(text, expected):
    assert looks_like_paper_research_topic(text) is expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Please do a survey on retrieval augmented generation", True),
        ("Need benchmark comparison for image segmentation", True),
        ("我想做文献综述", True),
        ("Create API specs for payment service", False),
        ("Add redis cache and unit tests", False),
    ],
)
def test_should_trigger_literature_review(text, expected):
    assert should_trigger_literature_review(text) is expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            "I want to search for essay whose topic is machine learning",
            "machine learning",
        ),
        (
            "Please find papers about software engining",
            "software engineering",
        ),
        (
            "Search papers on Reinforcment Learning please",
            "reinforcement learning",
        ),
        (
            "Can you retrieve papers regarding graph neural networks",
            "graph neural networks",
        ),
        (
            "请帮我找关于大模型推理优化的论文",
            "大模型推理优化的",
        ),
    ],
)
def test_extract_paper_research_topic_patterns(text, expected):
    assert extract_paper_research_topic(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("", ""),
        ("  ", ""),
        ("Create a 2048 game", "create a 2048 game"),
    ],
)
def test_extract_topic_edge_inputs(text, expected):
    assert extract_paper_research_topic(text) == expected


def test_extract_topic_fallback_strips_intent_tokens():
    text = "paper paper literature about federated learning paper"
    topic = extract_paper_research_topic(text)
    assert "paper" not in topic
    assert "literature" not in topic
    assert "federated learning" in topic


def test_extract_topic_handles_quotes_and_whitespace():
    text = "Please find papers about   '   Agentic Workflow   '   "
    assert extract_paper_research_topic(text) == "agentic workflow"
