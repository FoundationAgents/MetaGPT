#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Human-in-the-Loop Checkpoint definitions.

Defines the data models and configuration for checkpoints where human review
can be requested during the software development workflow.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class CheckpointStage(str, Enum):
    """Stages in the development workflow where human review can be triggered."""

    PRD = "prd"
    SYSTEM_DESIGN = "system_design"
    CODE = "code"
    TEST = "test"
    CUSTOM = "custom"


class ReviewDecision(str, Enum):
    """Human's decision at a checkpoint."""

    APPROVE = "approve"  # Approve and continue with current output
    MODIFY = "modify"  # Approve with feedback for refinement
    REJECT = "reject"  # Reject and stop or revise from scratch
    SKIP = "skip"  # Skip this checkpoint without review


class CheckpointResult(BaseModel):
    """Result of a human review at a checkpoint."""

    stage: CheckpointStage = Field(description="The stage at which review occurred")
    decision: ReviewDecision = Field(description="Human's review decision")
    feedback: str = Field(default="", description="Human's feedback or modification instructions")
    modified_content: Optional[str] = Field(
        default=None, description="Directly modified content by human (optional)"
    )


class CheckpointConfig(BaseModel):
    """Configuration for Human-in-the-Loop checkpoints."""

    enabled: bool = Field(default=False, description="Enable HITL globally")
    stages: list[CheckpointStage] = Field(
        default=[CheckpointStage.PRD, CheckpointStage.SYSTEM_DESIGN],
        description="Stages requiring human review",
    )
    timeout_seconds: int = Field(default=0, description="Timeout for human input in seconds, 0 means infinite")
    auto_approve_on_timeout: bool = Field(
        default=False, description="Automatically approve if timeout is reached"
    )
