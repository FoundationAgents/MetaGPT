#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DesignSystem Action - Architect designs system architecture.
Following MetaGPT Action pattern from examples.
"""
from metagpt.actions import Action


class DesignSystem(Action):
    """Action for Architect to design system architecture."""
    
    PROMPT_TEMPLATE: str = """
You are a Software Architect. Based on the following user stories and requirements, design a system architecture.

Requirements/Stories:
{context}

Provide a comprehensive design including:

1. **System Overview**
   - High-level architecture description
   - Key components and their responsibilities

2. **Technical Stack**
   - Frontend technologies
   - Backend technologies  
   - Database recommendations
   - Infrastructure considerations

3. **Component Design**
   - Main modules/services
   - Interfaces between components
   - Data flow

4. **API Design**
   - Key endpoints
   - Request/Response formats
   - Authentication approach

5. **Data Model**
   - Core entities
   - Relationships
   - Key attributes

Return a well-structured technical design document.
"""
    
    name: str = "DesignSystem"
    
    async def run(self, context: str) -> str:
        """
        Design system architecture based on requirements.
        
        Args:
            context: User stories and requirements
            
        Returns:
            System design document
        """
        prompt = self.PROMPT_TEMPLATE.format(context=context)
        rsp = await self._aask(prompt)
        return rsp
