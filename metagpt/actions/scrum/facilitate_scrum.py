#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FacilitateScrum Action - Scrum Master facilitates ceremonies.
Following MetaGPT Action pattern from examples.
"""
from metagpt.actions import Action


class FacilitateScrum(Action):
    """Action for Scrum Master to facilitate SCRUM ceremonies."""
    
    PROMPT_TEMPLATE: str = """
You are a Scrum Master facilitating a {ceremony_type}. 

Context:
{context}

Based on the current project state and team activity, provide:

1. **Summary**: Brief overview of current status
2. **Discussion Points**: Key items to address
3. **Action Items**: Specific tasks or decisions needed
4. **Blockers**: Any impediments identified
5. **Next Steps**: Clear path forward

Format your response as a structured ceremony report.
"""
    
    name: str = "FacilitateScrum"
    
    async def run(self, context: str, ceremony_type: str = "Daily Standup") -> str:
        """
        Facilitate a SCRUM ceremony.
        
        Args:
            context: Current project and team state
            ceremony_type: Type of ceremony (Daily Standup, Sprint Planning, etc.)
            
        Returns:
            Ceremony facilitation output
        """
        prompt = self.PROMPT_TEMPLATE.format(
            context=context,
            ceremony_type=ceremony_type
        )
        rsp = await self._aask(prompt)
        return rsp
