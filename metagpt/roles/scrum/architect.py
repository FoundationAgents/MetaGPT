#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/01/12
@Author  : MetaGPT-Pro Team
@File    : architect.py
@Desc    : Architect SCRUM Agent
"""
from metagpt.roles.scrum_role import SCRUMRole
from metagpt.actions.design_api import WriteDesign
from metagpt.actions import UserRequirement
from metagpt.logs import logger

class Architect(SCRUMRole):
    """
    Architect Role.
    Responsible for system design and API specifications.
    """
    
    name: str = "David"
    profile: str = "Architect"
    goal: str = "Design a robust, scalable, and efficient system architecture."
    constraints: str = "Ensure design meets requirements and uses best practices."
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Primary actions
        self.set_actions([WriteDesign])
        
        # Watch for requirements or assignments
        self._watch([UserRequirement])
        
        # Initialize action configurations
        self._init_actions()

    def _init_actions(self):
        """Configure actions with project context"""
        for action in self.actions:
            if hasattr(action, 'project_id'):
                action.project_id = self.project_id

    async def _think(self) -> bool:
        """
        Decide next action.
        """
        if self.rc.news:
            last_msg = self.rc.news[-1]
            if "design" in last_msg.content.lower():
                 self.todo_action = "WriteDesign"
                 return True
        
        return await super()._think()
