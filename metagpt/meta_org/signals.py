#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Signal models for Meta-Org Agent.

This module defines the data structures for capturing organizational health signals
that indicate when the agent team structure needs adjustment.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SignalType(str, Enum):
    """Types of organizational health signals."""

    # Outcome Signals - Results of execution
    FAILURE = "failure"  # Task or action failed
    RETRY = "retry"  # Retry occurred
    ROLLBACK = "rollback"  # Rollback occurred
    REVIEW_BLOCK = "review_block"  # Review blocked progress
    VALUE_UNCLEAR = "value_unclear"  # User value not clear

    # Process Signals - How work is being done
    LOOP_DETECTED = "loop"  # Repeated back-and-forth
    SLOW_DECISION = "slow"  # Decision took too long
    CONFLICT = "conflict"  # Disagreement between agents
    REWORK = "rework"  # Frequent rework on same item

    # Cognitive Signals - Quality of thinking
    UNCERTAINTY = "uncertainty"  # High uncertainty in output
    ASSUMPTION_GAP = "assumption"  # Unverified assumptions
    BLIND_SPOT = "blind_spot"  # Issue no agent is watching
    LOW_CONFIDENCE = "low_confidence"  # Agent expressed low confidence


class SignalSeverity(str, Enum):
    """Severity levels for signals."""

    LOW = "low"  # Minor issue, informational
    MEDIUM = "medium"  # Notable issue, should investigate
    HIGH = "high"  # Serious issue, needs attention
    CRITICAL = "critical"  # Critical issue, immediate action


class OrgSignal(BaseModel):
    """A single organizational health signal.
    
    Signals are collected throughout project execution and analyzed
    to detect patterns that indicate organizational structure issues.
    """

    signal_id: str = Field(default_factory=lambda: datetime.now().isoformat())
    signal_type: SignalType = Field(description="Type of signal")
    severity: SignalSeverity = Field(default=SignalSeverity.MEDIUM, description="Severity level")

    # Source information
    source_role: str = Field(default="", description="Role that generated the signal")
    source_action: str = Field(default="", description="Action that generated the signal")
    project_id: str = Field(default="", description="Project identifier")

    # Signal details
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional signal data")
    message: str = Field(default="", description="Human-readable description")

    # Metadata
    timestamp: datetime = Field(default_factory=datetime.now)
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")


class OrgPattern(BaseModel):
    """A detected pattern from multiple signals.
    
    Patterns are identified by analyzing collections of signals
    and represent systemic organizational issues.
    """

    pattern_type: str = Field(description="Type of pattern (blind_spot, overload, conflict, etc.)")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in pattern detection")

    # Supporting evidence
    supporting_signals: List[str] = Field(
        default_factory=list, description="Signal IDs that support this pattern"
    )
    affected_roles: List[str] = Field(default_factory=list, description="Roles involved in pattern")

    # Pattern details
    description: str = Field(description="Human-readable pattern description")
    recommendation: str = Field(default="", description="Recommended action")

    # Metadata
    detected_at: datetime = Field(default_factory=datetime.now)
    severity: SignalSeverity = Field(default=SignalSeverity.MEDIUM)


class OrgMetrics(BaseModel):
    """Aggregated metrics for organizational health."""

    # Outcome metrics
    total_failures: int = 0
    total_retries: int = 0
    total_review_blocks: int = 0
    success_rate: float = 0.0

    # Process metrics
    avg_decision_time_ms: float = 0.0
    loop_count: int = 0
    conflict_count: int = 0
    rework_rate: float = 0.0

    # Cognitive metrics
    uncertainty_rate: float = 0.0  # % of outputs with uncertainty
    assumption_gaps: int = 0
    blind_spot_count: int = 0

    # Per-role metrics
    role_metrics: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    # Time window
    window_start: Optional[datetime] = None
    window_end: Optional[datetime] = None
