#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Scrum Master Role - Following MetaGPT patterns from build_customized_multi_agents.py
"""
from metagpt.actions.scrum.write_tests import WriteTests
from metagpt.actions.scrum.facilitate_scrum import FacilitateScrum
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.project.event_system import event_bus, Event, EventType


class ScrumMaster(Role):
    """
    Scrum Master SCRUM Agent.
    
    Responsibilities:
    - Facilitates SCRUM ceremonies
    - Removes blockers
    - Coaches the team
    
    Following the MetaGPT multi-agent pattern from official examples.
    """
    
    name: str = "Bob"
    profile: str = "Scrum Master"
    goal: str = "Facilitate effective team collaboration and SCRUM practices"
    constraints: str = "Must ensure team follows SCRUM principles"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set actions this role can perform
        self.set_actions([FacilitateScrum])
        # Watch for QA Engineer's output (tests complete = sprint done)
        self._watch([WriteTests])
    
    async def _act(self) -> Message:
        """
        Execute the Scrum Master's action.
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
                "message": f"{self.name} is facilitating SCRUM..."
            }
        ))
        
        # Get the most recent memory as context (from QA Engineer)
        msg = self.get_memories(k=1)[0]
        
        # Run the action with the context
        result = await todo.run(context=msg.content)
        
        # Save to workspace - save sprint review
        try:
            from metagpt.project.workspace import get_workspace
            workspace = get_workspace(project_id)
            
            # Save sprint review artifact
            workspace.save_artifact("review", result, artifact_type="sprint")
            
            logger.info(f"Sprint review saved to workspace for project {project_id}")
        except Exception as e:
            logger.warning(f"Failed to save sprint review to workspace: {e}")
        
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
                "message": f"{self.name} completed SCRUM facilitation"
            }
        ))
        
        # Publish SPRINT_COMPLETED event
        await event_bus.publish(Event(
            type=EventType.SPRINT_COMPLETED,
            project_id=project_id,
            agent_id=self.name,
            payload={
                "name": self.name,
                "profile": self.profile,
                "sprint_status": "completed",
                "summary": result[:500] if len(result) > 500 else result,
                "message": "🎉 Sprint completed!"
            }
        ))
        
        # Publish PROJECT_COMPLETED event (for now, single sprint = project done)
        await event_bus.publish(Event(
            type=EventType.PROJECT_COMPLETED,
            project_id=project_id,
            agent_id=self.name,
            payload={
                "name": self.name,
                "profile": self.profile,
                "status": "completed",
                "message": "🎉 Project completed!"
            }
        ))
        
        # Create response message
        msg = Message(
            content=result,
            role=self.profile,
            cause_by=type(todo)
        )
        
        return msg
