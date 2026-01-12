#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Product Owner Role - Following MetaGPT patterns from build_customized_multi_agents.py
"""
import asyncio
from metagpt.actions import UserRequirement
from metagpt.actions.scrum.refine_story import RefineStory
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.project.event_system import event_bus, Event, EventType


class ProductOwner(Role):
    """
    Product Owner SCRUM Agent.
    
    Responsibilities:
    - Refines and prioritizes user stories
    - Defines acceptance criteria
    - Manages product backlog
    
    Following the MetaGPT multi-agent pattern from official examples.
    """
    
    name: str = "Alice"
    profile: str = "Product Owner"
    goal: str = "Define and prioritize product requirements as user stories"
    constraints: str = "Stories must have clear acceptance criteria and business value"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set actions this role can perform
        self.set_actions([RefineStory])
        # Watch for user requirements (initial trigger)
        self._watch([UserRequirement])
    
    async def _act(self) -> Message:
        """
        Execute the Product Owner's action.
        Following the pattern from build_customized_multi_agents.py
        """
        logger.info(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        
        todo = self.rc.todo
        project_id = getattr(self.context, 'project_id', 'default') if self.context else 'default'
        
        # Publish AGENT_ACTING event
        await event_bus.publish(Event(
            type=EventType.AGENT_ACTING,
            project_id=project_id,
            agent_id=self.name,
            payload={
                "name": self.name,
                "profile": self.profile,
                "role": self.profile,
                "action": todo.name,
                "status": "executing",
                "message": f"{self.name} is refining user stories..."
            }
        ))
        
        # Get the most recent memory as context
        msg = self.get_memories(k=1)[0]
        
        # Run the action with the context
        result = await todo.run(context=msg.content)
        
        # Save to workspace
        try:
            from metagpt.project.workspace import get_workspace
            workspace = get_workspace(project_id)
            workspace.save_prd(result, metadata={
                "agent": self.name,
                "action": todo.name,
                "source": "product_owner"
            })
            logger.info(f"PRD saved to workspace for project {project_id}")
        except Exception as e:
            logger.warning(f"Failed to save PRD to workspace: {e}")
        
        # Publish AGENT_COMPLETED event with result
        await event_bus.publish(Event(
            type=EventType.AGENT_COMPLETED,
            project_id=project_id,
            agent_id=self.name,
            payload={
                "name": self.name,
                "profile": self.profile,
                "role": self.profile,
                "action": todo.name,
                "status": "completed",
                "output": result[:500] + "..." if len(result) > 500 else result,
                "message": f"{self.name} completed story refinement"
            }
        ))
        
        # Publish ARTIFACT_CREATED event
        await event_bus.publish(Event(
            type=EventType.ARTIFACT_CREATED,
            project_id=project_id,
            agent_id=self.name,
            payload={
                "artifact_type": "user_stories",
                "file_path": "docs/PRD.md",
                "content": result,
                "created_by": self.name
            }
        ))
        
        # Create response message
        msg = Message(
            content=result,
            role=self.profile,
            cause_by=type(todo)
        )
        
        return msg
