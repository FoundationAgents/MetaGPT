#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RefineStory Action - Product Owner refines user stories.
Following MetaGPT Action pattern from examples.
"""
import re
from metagpt.actions import Action


class RefineStory(Action):
    """Action for Product Owner to refine and elaborate user stories."""
    
    PROMPT_TEMPLATE: str = """
You are a Product Owner. Based on the following requirement or context, create well-defined user stories.

Context:
{context}

For each user story, provide:
1. User Story: As a [role], I want [feature], so that [benefit]
2. Acceptance Criteria: Clear, testable criteria
3. Priority: High/Medium/Low
4. Story Points: 1-13 (Fibonacci)

Return your response in a clear, structured format.
"""
    
    name: str = "RefineStory"
    
    async def run(self, context: str) -> str:
        """
        Refine requirements into user stories.
        
        Args:
            context: The requirement or task description
            
        Returns:
            Refined user stories with acceptance criteria
        """
        prompt = self.PROMPT_TEMPLATE.format(context=context)
        rsp = await self._aask(prompt)
        return rsp
