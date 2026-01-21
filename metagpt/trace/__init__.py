#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Observability and Traceability module for MetaGPT.

This module provides infrastructure for tracing AI decision-making processes,
enabling human auditing of the complete "chain of thought" throughout the
software development workflow.

Key components:
- TraceCollector: Central service for collecting trace spans
- TraceSpan/LLMCallTrace: Data models for individual decisions
- ProjectTrace: Complete trace for a project execution
- TraceReporter: Generate human-readable Markdown reports
- Decorators: Automatic tracing via @trace_action, @trace_think, @trace_act
"""

from metagpt.trace.collector import CURRENT_TRACE, TraceCollector
from metagpt.trace.decorators import trace_act, trace_action, trace_think
from metagpt.trace.models import (
    DecisionType,
    LLMCallTrace,
    ProjectTrace,
    TraceConfig,
    TraceLevel,
    TraceSpan,
)
from metagpt.trace.reporter import TraceReporter

__all__ = [
    # Models
    "TraceLevel",
    "DecisionType",
    "TraceSpan",
    "LLMCallTrace",
    "ProjectTrace",
    "TraceConfig",
    # Collector
    "TraceCollector",
    "CURRENT_TRACE",
    # Decorators
    "trace_action",
    "trace_think",
    "trace_act",
    # Reporter
    "TraceReporter",
]
