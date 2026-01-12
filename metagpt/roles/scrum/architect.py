#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Architect Role - Following MetaGPT patterns from build_customized_multi_agents.py
"""
from metagpt.actions.scrum.refine_story import RefineStory
from metagpt.actions.scrum.design_system import DesignSystem
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.project.event_system import event_bus, Event, EventType


class Architect(Role):
    """
    Architect SCRUM Agent.
    
    Responsibilities:
    - Designs system architecture
    - Makes technical decisions
    - Creates high-level design documents
    
    Following the MetaGPT multi-agent pattern from official examples.
    """
    
    name: str = "David"
    profile: str = "Architect"
    goal: str = "Design robust and scalable system architecture"
    constraints: str = "Design must be implementable and maintainable"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set actions this role can perform
        self.set_actions([DesignSystem])
        # Watch for Product Owner's output (user stories)
        self._watch([RefineStory])
    
    async def _act(self) -> Message:
        """
        Execute the Architect's action.
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
                "message": f"{self.name} is designing system architecture..."
            }
        ))
        
        # Get the most recent memory as context (from Product Owner)
        msg = self.get_memories(k=1)[0]
        
        # Run the action with the context
        result = await todo.run(context=msg.content)
        
        # Save to workspace
        try:
            from metagpt.project.workspace import get_workspace
            workspace = get_workspace(project_id)
            workspace.save_system_design(result, metadata={
                "agent": self.name,
                "action": todo.name,
                "source": "architect"
            })
            logger.info(f"System Design saved to workspace for project {project_id}")
        except Exception as e:
            logger.warning(f"Failed to save System Design to workspace: {e}")
        
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
                "message": f"{self.name} completed system design"
            }
        ))
        
        # Publish ARTIFACT_CREATED event
        await event_bus.publish(Event(
            type=EventType.ARTIFACT_CREATED,
            project_id=project_id,
            agent_id=self.name,
            payload={
                "artifact_type": "system_design",
                "file_path": "docs/SYSTEM_DESIGN.md",
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
