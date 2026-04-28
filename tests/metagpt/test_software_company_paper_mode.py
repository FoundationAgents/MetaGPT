#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path

from metagpt.software_company import (
    _compose_idea_with_literature_context,
    _compose_paper_collaboration_idea,
    _render_literature_context,
    _resolve_intent_with_fallback,
    _save_literature_context_to_fixed_file,
)


def test_compose_idea_with_empty_context():
    idea = "Build a simple app"
    assert _compose_idea_with_literature_context(idea, None) == idea
    assert _compose_idea_with_literature_context(idea, "") == idea


def test_compose_idea_with_literature_context():
    idea = "Build a simple app"
    context = "- Topic: RL\n- Summary: ...\n- Key Papers:"
    merged = _compose_idea_with_literature_context(idea, context)
    assert "Build a simple app" in merged
    assert "Literature Review Context" in merged
    assert context in merged


def test_compose_paper_collaboration_idea():
    idea = _compose_paper_collaboration_idea(
        topic="reinforcement learning",
        literature_context="- Topic: reinforcement learning",
    )
    assert "Research topic: reinforcement learning." in idea
    assert "ProductManager should define research objectives" in idea
    assert "DataAnalyst should summarize trends" in idea
    assert "Literature Review Context" in idea


def test_render_literature_context_no_papers():
    payload = {"topic": "agents", "summary": "S", "papers": []}
    rendered = _render_literature_context(payload)
    assert "- Topic: agents" in rendered
    assert "- Summary:" in rendered
    assert "No papers extracted." in rendered


def test_render_literature_context_with_papers():
    payload = {
        "topic": "agents",
        "summary": "S",
        "papers": [
            {
                "title": "Paper A",
                "year": "2024",
                "venue": "arXiv",
                "url": "https://arxiv.org/abs/1234.5678",
                "abstract": "A short abstract",
            }
        ],
    }
    rendered = _render_literature_context(payload)
    assert "Paper A (2024, arXiv)" in rendered
    assert "URL: https://arxiv.org/abs/1234.5678" in rendered
    assert "Abstract: A short abstract" in rendered


def test_save_literature_context_to_fixed_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    out = _save_literature_context_to_fixed_file("content")
    assert out == tmp_path / "workspace" / "paper_search_result.md"
    assert out.exists()
    assert out.read_text(encoding="utf-8") == "content"


def test_save_literature_context_skips_empty(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    out = _save_literature_context_to_fixed_file("")
    assert out is None
    assert not (tmp_path / "workspace" / "paper_search_result.md").exists()


def test_save_path_is_relative_to_cwd(tmp_path, monkeypatch):
    nested = tmp_path / "nested"
    nested.mkdir(parents=True, exist_ok=True)
    monkeypatch.chdir(nested)
    out = _save_literature_context_to_fixed_file("abc")
    assert out == Path.cwd() / "workspace" / "paper_search_result.md"


def test_resolve_intent_prefers_agent_high_confidence_paper():
    idea = "Build a web dashboard"
    agent_result = {
        "collaboration_mode": "paper",
        "topic": "software architecture",
        "confidence": 0.92,
    }
    is_paper, topic = _resolve_intent_with_fallback(idea=idea, agent_result=agent_result)
    assert is_paper is True
    assert topic == "software architecture"


def test_resolve_intent_prefers_agent_high_confidence_software():
    idea = "please find papers about reinforcement learning"
    agent_result = {
        "collaboration_mode": "software",
        "topic": "ignore this",
        "confidence": 0.91,
    }
    is_paper, topic = _resolve_intent_with_fallback(idea=idea, agent_result=agent_result)
    assert is_paper is False
    assert topic == idea


def test_resolve_intent_falls_back_when_agent_low_confidence():
    idea = "please find papers about reinforcement learning"
    agent_result = {
        "collaboration_mode": "software",
        "topic": "ignore this",
        "confidence": 0.20,
    }
    is_paper, topic = _resolve_intent_with_fallback(idea=idea, agent_result=agent_result)
    assert is_paper is True
    assert topic == "reinforcement learning"
