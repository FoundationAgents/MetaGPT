#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests for Human-in-the-Loop (HITL) functionality.
"""

import pytest

from metagpt.hitl import (
    CheckpointConfig,
    CheckpointResult,
    CheckpointStage,
    HumanReviewGate,
    ReviewDecision,
)


def test_checkpoint_config_defaults():
    """Test that CheckpointConfig has correct default values."""
    config = CheckpointConfig()
    assert config.enabled is False
    assert CheckpointStage.PRD in config.stages
    assert CheckpointStage.SYSTEM_DESIGN in config.stages
    assert config.timeout_seconds == 0
    assert config.auto_approve_on_timeout is False


def test_checkpoint_config_custom():
    """Test custom CheckpointConfig."""
    config = CheckpointConfig(
        enabled=True,
        stages=[CheckpointStage.CODE],
        timeout_seconds=300,
        auto_approve_on_timeout=True,
    )
    assert config.enabled is True
    assert config.stages == [CheckpointStage.CODE]
    assert config.timeout_seconds == 300
    assert config.auto_approve_on_timeout is True


def test_checkpoint_result_creation():
    """Test CheckpointResult creation."""
    result = CheckpointResult(
        stage=CheckpointStage.PRD,
        decision=ReviewDecision.APPROVE,
        feedback="Looks good!",
    )
    assert result.stage == CheckpointStage.PRD
    assert result.decision == ReviewDecision.APPROVE
    assert result.feedback == "Looks good!"
    assert result.modified_content is None


def test_review_decision_enum():
    """Test ReviewDecision enum values."""
    assert ReviewDecision.APPROVE.value == "approve"
    assert ReviewDecision.MODIFY.value == "modify"
    assert ReviewDecision.REJECT.value == "reject"
    assert ReviewDecision.SKIP.value == "skip"


def test_checkpoint_stage_enum():
    """Test CheckpointStage enum values."""
    assert CheckpointStage.PRD.value == "prd"
    assert CheckpointStage.SYSTEM_DESIGN.value == "system_design"
    assert CheckpointStage.CODE.value == "code"
    assert CheckpointStage.TEST.value == "test"
    assert CheckpointStage.CUSTOM.value == "custom"


@pytest.mark.asyncio
async def test_review_gate_with_mock_interface(monkeypatch):
    """Test HumanReviewGate with mocked interface."""
    from metagpt.hitl.interface import HumanInterface

    # Mock the request_review method to auto-approve
    async def mock_request_review(self, stage, content, context=""):
        return CheckpointResult(stage=stage, decision=ReviewDecision.APPROVE)

    monkeypatch.setattr(HumanInterface, "request_review", mock_request_review)

    gate = HumanReviewGate(stage=CheckpointStage.PRD)
    result = await gate.run("Test PRD Content", context="Test Context")

    assert result.decision == ReviewDecision.APPROVE
    assert result.stage == CheckpointStage.PRD


@pytest.mark.asyncio
async def test_review_gate_with_modification(monkeypatch):
    """Test HumanReviewGate with modification decision."""
    from metagpt.hitl.interface import HumanInterface

    # Mock the request_review method to return modify decision
    async def mock_request_review(self, stage, content, context=""):
        return CheckpointResult(
            stage=stage,
            decision=ReviewDecision.MODIFY,
            feedback="Please add more details about error handling",
        )

    monkeypatch.setattr(HumanInterface, "request_review", mock_request_review)

    gate = HumanReviewGate(stage=CheckpointStage.SYSTEM_DESIGN)
    result = await gate.run("Test Design Content")

    assert result.decision == ReviewDecision.MODIFY
    assert result.stage == CheckpointStage.SYSTEM_DESIGN
    assert "error handling" in result.feedback


@pytest.mark.asyncio
async def test_review_gate_with_rejection(monkeypatch):
    """Test HumanReviewGate with rejection decision."""
    from metagpt.hitl.interface import HumanInterface

    # Mock the request_review method to return reject decision
    async def mock_request_review(self, stage, content, context=""):
        return CheckpointResult(
            stage=stage,
            decision=ReviewDecision.REJECT,
            feedback="This doesn't meet requirements",
        )

    monkeypatch.setattr(HumanInterface, "request_review", mock_request_review)

    gate = HumanReviewGate(stage=CheckpointStage.CODE)
    result = await gate.run("Test Code Content")

    assert result.decision == ReviewDecision.REJECT
    assert "doesn't meet requirements" in result.feedback
