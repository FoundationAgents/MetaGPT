#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests for observability and traceability functionality.
"""

import json
from pathlib import Path

import pytest

from metagpt.trace import (
    DecisionType,
    LLMCallTrace,
    ProjectTrace,
    TraceCollector,
    TraceConfig,
    TraceLevel,
    TraceReporter,
    TraceSpan,
)


def test_trace_config_defaults():
    """Test that TraceConfig has correct default values."""
    config = TraceConfig()
    assert config.enabled is False
    assert config.level == TraceLevel.STANDARD
    assert config.save_on_complete is True
    assert config.output_dir == "traces"


def test_trace_config_custom():
    """Test custom TraceConfig."""
    config = TraceConfig(enabled=True, level=TraceLevel.VERBOSE, save_on_complete=False, output_dir="custom_traces")
    assert config.enabled is True
    assert config.level == TraceLevel.VERBOSE
    assert config.save_on_complete is False
    assert config.output_dir == "custom_traces"


def test_trace_span_creation():
    """Test TraceSpan creation."""
    span = TraceSpan(
        name="test_action",
        decision_type=DecisionType.ACT,
        role_name="TestRole",
        role_profile="Test Profile",
        reasoning="Test reasoning",
    )
    assert span.name == "test_action"
    assert span.decision_type == DecisionType.ACT
    assert span.role_name == "TestRole"
    assert span.reasoning == "Test reasoning"
    assert span.span_id  # Should be auto-generated


def test_llm_call_trace():
    """Test LLMCallTrace creation."""
    trace = LLMCallTrace(
        name="LLM:gpt-4",
        model="gpt-4",
        prompt="Test prompt",
        response="Test response",
        tokens_input=100,
        tokens_output=50,
        cost_usd=0.01,
    )
    assert trace.decision_type == DecisionType.LLM_CALL
    assert trace.model == "gpt-4"
    assert trace.tokens_input == 100
    assert trace.tokens_output == 50
    assert trace.cost_usd == 0.01


def test_collector_singleton():
    """Test that TraceCollector is a singleton."""
    TraceCollector.reset()
    c1 = TraceCollector.get_instance()
    c2 = TraceCollector.get_instance()
    assert c1 is c2


def test_project_lifecycle():
    """Test complete project trace lifecycle."""
    TraceCollector.reset()
    collector = TraceCollector.get_instance(TraceLevel.STANDARD)

    # Start project
    collector.start_project("test_project", "Test idea")
    assert collector.project_trace is not None
    assert collector.project_trace.project_name == "test_project"
    assert collector.project_trace.idea == "Test idea"

    # Add a span
    span = collector.start_span("test.action", DecisionType.ACT, role_name="TestRole")
    collector.end_span(span, reasoning="Completed test action", confidence=0.95)

    # Verify span was added
    assert len(collector.project_trace.spans) == 1
    assert collector.project_trace.spans[0].name == "test.action"
    assert collector.project_trace.spans[0].confidence == 0.95

    # End project
    collector.end_project()
    assert collector.project_trace.end_time is not None


def test_nested_spans():
    """Test nested span hierarchy."""
    TraceCollector.reset()
    collector = TraceCollector.get_instance()
    collector.start_project("nested_test", "Test nested spans")

    # Parent span
    parent = collector.start_span("parent", DecisionType.THINK)

    # Child span
    child = collector.start_span("child", DecisionType.ACT)
    assert child.parent_span_id == parent.span_id

    collector.end_span(child)
    collector.end_span(parent)

    assert len(collector.project_trace.spans) == 2


def test_llm_call_tracking():
    """Test LLM call tracking."""
    TraceCollector.reset()
    collector = TraceCollector.get_instance(TraceLevel.VERBOSE)
    collector.start_project("llm_test", "Test LLM tracking")

    collector.trace_llm_call(
        model="gpt-4",
        prompt="Test prompt",
        system_prompt="System instructions",
        response="Test response",
        tokens_input=100,
        tokens_output=50,
        cost_usd=0.015,
        role_name="TestRole",
    )

    assert collector.project_trace.total_llm_calls == 1
    assert collector.project_trace.total_cost_usd == 0.015

    llm_calls = collector.get_llm_calls()
    assert len(llm_calls) == 1
    assert llm_calls[0].model == "gpt-4"


def test_trace_filtering():
    """Test filtering spans by role and type."""
    TraceCollector.reset()
    collector = TraceCollector.get_instance()
    collector.start_project("filter_test", "Test filtering")

    # Add spans of different types and roles
    span1 = collector.start_span("think1", DecisionType.THINK, role_name="Role1")
    collector.end_span(span1)

    span2 = collector.start_span("act1", DecisionType.ACT, role_name="Role1")
    collector.end_span(span2)

    span3 = collector.start_span("think2", DecisionType.THINK, role_name="Role2")
    collector.end_span(span3)

    # Filter by role
    role1_spans = collector.get_spans_by_role("Role1")
    assert len(role1_spans) == 2

    # Filter by type
    think_spans = collector.get_spans_by_type(DecisionType.THINK)
    assert len(think_spans) == 2


def test_trace_persistence(tmp_path):
    """Test saving and loading traces."""
    TraceCollector.reset()
    collector = TraceCollector.get_instance()
    collector.start_project("persist_test", "Test persistence")

    span = collector.start_span("test", DecisionType.ACT)
    collector.end_span(span, reasoning="Test span")
    collector.end_project()

    # Save trace
    trace_file = tmp_path / "test_trace.json"
    saved_path = collector.save(trace_file)
    assert saved_path.exists()

    # Load trace
    loaded_trace = TraceCollector.load(trace_file)
    assert loaded_trace.project_name == "persist_test"
    assert len(loaded_trace.spans) == 1


def test_trace_reporter_markdown():
    """Test markdown report generation."""
    trace = ProjectTrace(
        project_name="test_report",
        idea="Test markdown generation",
        spans=[
            TraceSpan(
                name="test_action",
                decision_type=DecisionType.ACT,
                role_name="TestRole",
                role_profile="Test Profile",
                reasoning="Did something important",
                alternatives_considered=["Option A", "Option B"],
                confidence=0.85,
            )
        ],
    )

    md = TraceReporter.to_markdown(trace)

    # Verify markdown structure
    assert "# Trace Report: test_report" in md
    assert "## Overview" in md
    assert "## Decision Timeline" in md
    assert "test_action" in md
    assert "Did something important" in md
    assert "Option A" in md
    assert "85%" in md  # Confidence


def test_trace_reporter_save(tmp_path):
    """Test saving markdown report."""
    trace = ProjectTrace(project_name="save_test", idea="Test save", spans=[])

    report_file = tmp_path / "test_report.md"
    saved_path = TraceReporter.save_report(trace, report_file)

    assert saved_path.exists()
    content = saved_path.read_text()
    assert "# Trace Report: save_test" in content


def test_trace_levels():
    """Test different trace levels."""
    # MINIMAL - should skip LLM details
    TraceCollector.reset()
    collector_min = TraceCollector.get_instance(TraceLevel.MINIMAL)
    collector_min.start_project("minimal", "Test")
    collector_min.trace_llm_call(
        model="gpt-4",
        prompt="test",
        system_prompt="test",
        response="test",
        tokens_input=10,
        tokens_output=5,
        cost_usd=0.01,
    )
    assert len(collector_min.project_trace.spans) == 0  # LLM calls skipped in MINIMAL

    # STANDARD - should truncate prompts
    TraceCollector.reset()
    collector_std = TraceCollector.get_instance(TraceLevel.STANDARD)
    collector_std.start_project("standard", "Test")
    long_prompt = "x" * 200
    collector_std.trace_llm_call(
        model="gpt-4",
        prompt=long_prompt,
        system_prompt="test",
        response="test",
        tokens_input=10,
        tokens_output=5,
        cost_usd=0.01,
    )
    llm_trace = collector_std.get_llm_calls()[0]
    assert "[200 chars]" in llm_trace.prompt  # Truncated

    # VERBOSE - should keep full prompts
    TraceCollector.reset()
    collector_verb = TraceCollector.get_instance(TraceLevel.VERBOSE)
    collector_verb.start_project("verbose", "Test")
    collector_verb.trace_llm_call(
        model="gpt-4",
        prompt=long_prompt,
        system_prompt="test",
        response="test",
        tokens_input=10,
        tokens_output=5,
        cost_usd=0.01,
    )
    llm_trace_verb = collector_verb.get_llm_calls()[0]
    assert llm_trace_verb.prompt == long_prompt  # Full prompt
