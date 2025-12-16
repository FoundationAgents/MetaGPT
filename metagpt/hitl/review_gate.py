#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HumanReviewGate - An Action that pauses workflow for human review.

This action serves as a checkpoint in the workflow where human intervention
is requested to review, approve, modify, or reject AI-generated artifacts.
"""

from metagpt.actions import Action
from metagpt.hitl.checkpoint import CheckpointResult, CheckpointStage
from metagpt.hitl.interface import HumanInterface
from metagpt.logs import logger


class HumanReviewGate(Action):
    """
    An action that pauses the workflow and requests human review.

    This gate can be inserted at any point in the workflow to enable
    human oversight and intervention.
    """

    name: str = "HumanReviewGate"
    stage: CheckpointStage = CheckpointStage.CUSTOM

    async def run(self, content_to_review: str, context: str = "") -> CheckpointResult:
        """
        Display content to human and wait for review decision.

        Args:
            content_to_review: The artifact (PRD, Design Doc, Code) to review
            context: Additional context for the reviewer

        Returns:
            CheckpointResult with human's decision and feedback

        Raises:
            ValueError: If human rejects the content
        """
        interface = HumanInterface.get_instance()

        logger.info(f"[HITL] Requesting human review at stage: {self.stage.value}")

        result = await interface.request_review(stage=self.stage, content=content_to_review, context=context)

        logger.info(f"[HITL] Human decision: {result.decision.value}")
        if result.feedback:
            logger.info(f"[HITL] Human feedback: {result.feedback[:200]}...")

        return result
