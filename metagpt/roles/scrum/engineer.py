#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Engineer Role - Following MetaGPT patterns from build_customized_multi_agents.py
"""
import re
from metagpt.actions.scrum.design_system import DesignSystem
from metagpt.actions.scrum.write_feature import WriteFeature
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.project.event_system import event_bus, Event, EventType


class Engineer(Role):
    """
    Engineer SCRUM Agent.
    
    Responsibilities:
    - Implements features based on design
    - Writes production code
    - Follows coding standards
    
    Following the MetaGPT multi-agent pattern from official examples.
    """
    
    name: str = "Alex"
    profile: str = "Engineer"
    goal: str = "Implement high-quality, maintainable code"
    constraints: str = "Code must follow best practices and be well-documented"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set actions this role can perform
        self.set_actions([WriteFeature])
        # Watch for Architect's output (system design)
        self._watch([DesignSystem])
    
    async def _act(self) -> Message:
        """
        Execute the Engineer's action.
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
                "message": f"{self.name} is implementing features..."
            }
        ))
        
        # Get the most recent memory as context (from Architect)
        msg = self.get_memories(k=1)[0]
        
        # Run the action with the context
        result = await todo.run(context=msg.content)
        
        # Save to workspace - extract and save code files
        try:
            from metagpt.project.workspace import get_workspace
            workspace = get_workspace(project_id)
            
            # Try to extract code blocks and save them as files
            saved_files = self._save_code_files(workspace, result)
            
            # Also save the full implementation as a markdown file
            workspace.save_artifact("implementation", result, artifact_type="code")
            
            logger.info(f"Implementation saved to workspace for project {project_id}: {saved_files}")
        except Exception as e:
            logger.warning(f"Failed to save implementation to workspace: {e}")
        
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
                "message": f"{self.name} completed feature implementation"
            }
        ))
        
        # Publish ARTIFACT_CREATED event
        await event_bus.publish(Event(
            type=EventType.ARTIFACT_CREATED,
            project_id=project_id,
            agent_id=self.name,
            payload={
                "artifact_type": "source_code",
                "file_path": "src/",
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
    
    def _save_code_files(self, workspace, content: str) -> list:
        """Extract code blocks from content and save them as files."""
        saved_files = []
        
        # Pattern to match code blocks with filenames
        # Matches: ```python filename.py or # filename.py at start of block
        code_pattern = r'```(\w+)?\s*(?:#\s*)?(\S+\.(?:py|js|ts|html|css|json|yaml|yml|md))?\n(.*?)```'
        matches = re.findall(code_pattern, content, re.DOTALL)
        
        for i, (lang, filename, code) in enumerate(matches):
            if not filename:
                # Generate filename from language
                ext_map = {'python': 'py', 'javascript': 'js', 'typescript': 'ts'}
                ext = ext_map.get(lang, lang) if lang else 'txt'
                filename = f"code_{i}.{ext}"
            
            try:
                workspace.save_source_file(filename, code.strip())
                saved_files.append(filename)
            except Exception as e:
                logger.warning(f"Failed to save {filename}: {e}")
        
        return saved_files
