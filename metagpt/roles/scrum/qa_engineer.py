#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
QA Engineer Role - Following MetaGPT patterns from build_customized_multi_agents.py
"""
import re
from metagpt.actions.scrum.write_feature import WriteFeature
from metagpt.actions.scrum.write_tests import WriteTests
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.project.event_system import event_bus, Event, EventType


class QAEngineer(Role):
    """
    QA Engineer SCRUM Agent.
    
    Responsibilities:
    - Writes tests for features
    - Ensures quality standards
    - Reviews code for issues
    
    Following the MetaGPT multi-agent pattern from official examples.
    """
    
    name: str = "Charlie"
    profile: str = "QA Engineer"
    goal: str = "Ensure software quality through comprehensive testing"
    constraints: str = "Tests must be thorough and cover edge cases"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set actions this role can perform
        self.set_actions([WriteTests])
        # Watch for Engineer's output (implementation)
        self._watch([WriteFeature])
    
    async def _act(self) -> Message:
        """
        Execute the QA Engineer's action.
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
                "message": f"{self.name} is writing tests..."
            }
        ))
        
        # Get the most recent memory as context (from Engineer)
        msg = self.get_memories(k=1)[0]
        
        # Run the action with the context
        result = await todo.run(context=msg.content)
        
        # Save to workspace - extract and save test files
        try:
            from metagpt.project.workspace import get_workspace
            workspace = get_workspace(project_id)
            
            # Try to extract test code blocks and save them
            saved_files = self._save_test_files(workspace, result)
            
            # Also save the full test suite as a markdown file
            workspace.save_artifact("test_suite", result, artifact_type="tests")
            
            logger.info(f"Tests saved to workspace for project {project_id}: {saved_files}")
        except Exception as e:
            logger.warning(f"Failed to save tests to workspace: {e}")
        
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
                "message": f"{self.name} completed test writing"
            }
        ))
        
        # Publish ARTIFACT_CREATED event
        await event_bus.publish(Event(
            type=EventType.ARTIFACT_CREATED,
            project_id=project_id,
            agent_id=self.name,
            payload={
                "artifact_type": "tests",
                "file_path": "tests/",
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
    
    def _save_test_files(self, workspace, content: str) -> list:
        """Extract test code blocks from content and save them as files."""
        saved_files = []
        
        # Pattern to match code blocks with filenames
        code_pattern = r'```(\w+)?\s*(?:#\s*)?(\S+\.(?:py|js|ts))?\n(.*?)```'
        matches = re.findall(code_pattern, content, re.DOTALL)
        
        for i, (lang, filename, code) in enumerate(matches):
            if not filename:
                # Generate test filename
                ext_map = {'python': 'py', 'javascript': 'js', 'typescript': 'ts'}
                ext = ext_map.get(lang, lang) if lang else 'py'
                filename = f"test_{i}.{ext}"
            
            # Ensure it's a test file
            if not filename.startswith('test_'):
                filename = f"test_{filename}"
            
            try:
                workspace.save_test_file(filename, code.strip())
                saved_files.append(filename)
            except Exception as e:
                logger.warning(f"Failed to save {filename}: {e}")
        
        return saved_files
