#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Decision trace data models for observability and traceability.

This module defines the core data structures for tracing AI decision-making
processes throughout the MetaGPT workflow.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class TraceLevel(str, Enum):
    """Tracing verbosity levels."""

    MINIMAL = "minimal"  # Only key milestones (PRD complete, Design complete, etc.)
    STANDARD = "standard"  # Action-level tracing with inputs/outputs
    VERBOSE = "verbose"  # Full LLM prompts, responses, and internal reasoning


class DecisionType(str, Enum):
    """Types of decisions that can be traced."""

    THINK = "think"  # Role._think() decision-making
    ACT = "act"  # Role._act() execution
    LLM_CALL = "llm_call"  # LLM API call
    HITL = "hitl"  # Human-in-the-loop intervention
    STATE_CHANGE = "state"  # State transition
    ERROR = "error"  # Error occurred


class TraceSpan(BaseModel):
    """A single trace span representing one decision or action.
    
    Spans form a tree structure via parent_span_id, allowing reconstruction
    of the complete decision hierarchy.
    """

    span_id: str = Field(default_factory=lambda: uuid4().hex[:12], description="Unique span identifier")
    parent_span_id: Optional[str] = Field(default=None, description="Parent span ID for hierarchy")
    trace_id: str = Field(default="", description="Project-level trace ID linking all spans")

    # What happened
    decision_type: DecisionType = Field(description="Type of decision or action")
    name: str = Field(default="", description="Name of the action, e.g., 'WritePRD.run'")

    # Who made the decision
    role_name: str = Field(default="", description="Name of the role (e.g., 'Alice')")
    role_profile: str = Field(default="", description="Profile of the role (e.g., 'Product Manager')")

    # When it happened
    start_time: datetime = Field(default_factory=datetime.now, description="Span start timestamp")
    end_time: Optional[datetime] = Field(default=None, description="Span end timestamp")
    duration_ms: int = Field(default=0, description="Duration in milliseconds")

    # Context: inputs and outputs
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Input data summary")
    output_data: Dict[str, Any] = Field(default_factory=dict, description="Output data summary")

    # The "chain of thought" - most important for auditing
    reasoning: str = Field(default="", description="Natural language explanation of the decision")
    alternatives_considered: List[str] = Field(
        default_factory=list, description="Alternative options that were considered"
    )
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence in the decision (0-1)")

    # Metadata
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    # Error tracking
    error: Optional[str] = Field(default=None, description="Error message if span failed")
    error_traceback: Optional[str] = Field(default=None, description="Full error traceback")


class LLMCallTrace(TraceSpan):
    """Extended trace span specifically for LLM API calls.
    
    Captures detailed information about LLM interactions including
    prompts, responses, token usage, and costs.
    """

    decision_type: DecisionType = DecisionType.LLM_CALL

    # LLM-specific fields
    model: str = Field(default="", description="LLM model name")
    prompt: str = Field(default="", description="User prompt sent to LLM")
    system_prompt: str = Field(default="", description="System prompt/instructions")
    response: str = Field(default="", description="LLM response")
    tokens_input: int = Field(default=0, description="Input tokens consumed")
    tokens_output: int = Field(default=0, description="Output tokens generated")
    cost_usd: float = Field(default=0.0, description="Estimated cost in USD")
    temperature: float = Field(default=0.0, description="Temperature parameter used")


class ProjectTrace(BaseModel):
    """Complete trace for a project execution.
    
    Contains all spans from a single project run, along with summary
    statistics and metadata.
    """

    trace_id: str = Field(default_factory=lambda: uuid4().hex, description="Unique project trace ID")
    project_name: str = Field(default="", description="Name of the project")
    idea: str = Field(default="", description="Original user requirement/idea")

    start_time: datetime = Field(default_factory=datetime.now, description="Project start time")
    end_time: Optional[datetime] = Field(default=None, description="Project end time")

    spans: List[TraceSpan] = Field(default_factory=list, description="All trace spans in chronological order")

    # Summary statistics
    total_llm_calls: int = Field(default=0, description="Total number of LLM API calls")
    total_cost_usd: float = Field(default=0.0, description="Total cost in USD")
    roles_involved: List[str] = Field(default_factory=list, description="List of roles that participated")

    # Configuration used for this trace
    trace_level: TraceLevel = Field(default=TraceLevel.STANDARD, description="Trace verbosity level used")


class TraceConfig(BaseModel):
    """Configuration for observability and tracing."""

    enabled: bool = Field(default=False, description="Enable tracing globally")
    level: TraceLevel = Field(default=TraceLevel.STANDARD, description="Trace verbosity level")
    save_on_complete: bool = Field(default=True, description="Auto-save trace when project completes")
    output_dir: str = Field(default="traces", description="Directory for trace output files")
