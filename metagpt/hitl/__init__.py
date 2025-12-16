#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Human-in-the-Loop (HITL) module for MetaGPT.

This module provides infrastructure for human intervention at critical decision points
in the software development workflow, enabling human-AI collaboration.
"""

from metagpt.hitl.checkpoint import (
    CheckpointConfig,
    CheckpointResult,
    CheckpointStage,
    ReviewDecision,
)
from metagpt.hitl.review_gate import HumanReviewGate
from metagpt.hitl.interface import HumanInterface

__all__ = [
    "CheckpointConfig",
    "CheckpointResult",
    "CheckpointStage",
    "ReviewDecision",
    "HumanReviewGate",
    "HumanInterface",
]
