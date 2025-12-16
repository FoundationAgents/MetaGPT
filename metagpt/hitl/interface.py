#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Terminal-based human interface for HITL.

Provides a command-line interface for humans to review AI-generated artifacts
and provide feedback at checkpoints.
"""

import asyncio
from typing import Optional

from metagpt.hitl.checkpoint import CheckpointResult, CheckpointStage, ReviewDecision
from metagpt.logs import logger


class HumanInterface:
    """Singleton interface for human interaction via terminal."""

    _instance: Optional["HumanInterface"] = None

    @classmethod
    def get_instance(cls) -> "HumanInterface":
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def request_review(
        self, stage: CheckpointStage, content: str, context: str = ""
    ) -> CheckpointResult:
        """
        Display content and collect human review via terminal.

        Args:
            stage: The checkpoint stage
            content: The artifact content to review
            context: Additional context for the reviewer

        Returns:
            CheckpointResult with human's decision and feedback
        """
        # Display header
        print("\n" + "=" * 80)
        print(f"🔍 HUMAN REVIEW REQUIRED - Stage: {stage.value.upper()}")
        print("=" * 80)

        if context:
            print(f"\n📋 Context:\n{context}\n")

        # Display content (truncated if too long)
        print("📄 Content to Review:")
        print("-" * 80)
        display_content = content[:2000] + "\n... (truncated)" if len(content) > 2000 else content
        print(display_content)
        print("-" * 80)

        # Collect decision
        print("\n🎯 Your Decision:")
        print("  [A] Approve - Continue with this output")
        print("  [M] Modify  - Approve with feedback for refinement")
        print("  [R] Reject  - Stop and revise from scratch")
        print("  [S] Skip    - Skip this checkpoint")

        while True:
            try:
                choice = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: input("\nEnter choice (A/M/R/S): ").strip().upper()
                )

                if choice == "A":
                    return CheckpointResult(stage=stage, decision=ReviewDecision.APPROVE)
                elif choice == "M":
                    feedback = await self._get_multiline_input(
                        "Enter your feedback/modification instructions:"
                    )
                    return CheckpointResult(stage=stage, decision=ReviewDecision.MODIFY, feedback=feedback)
                elif choice == "R":
                    reason = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: input("Reason for rejection: ").strip()
                    )
                    return CheckpointResult(stage=stage, decision=ReviewDecision.REJECT, feedback=reason)
                elif choice == "S":
                    return CheckpointResult(stage=stage, decision=ReviewDecision.SKIP)
                else:
                    print("❌ Invalid choice. Please enter A, M, R, or S.")
            except KeyboardInterrupt:
                print("\n⚠️  Review interrupted. Treating as REJECT.")
                return CheckpointResult(
                    stage=stage, decision=ReviewDecision.REJECT, feedback="User interrupted"
                )

    async def _get_multiline_input(self, prompt: str) -> str:
        """
        Collect multiline input from user.

        Args:
            prompt: Prompt to display to user

        Returns:
            Multiline input as a single string
        """
        print(f"\n{prompt}")
        print("(Enter your feedback, then type 'END' on a new line to finish)")

        lines = []
        while True:
            line = await asyncio.get_event_loop().run_in_executor(None, input)
            if line.strip().upper() == "END":
                break
            lines.append(line)
        return "\n".join(lines)
