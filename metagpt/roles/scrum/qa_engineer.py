#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/01/12
@Author  : MetaGPT-Pro Team
@File    : qa_engineer.py
@Desc    : QA Engineer SCRUM Agent
"""
from metagpt.roles.scrum_role import SCRUMRole
from metagpt.actions.write_test import WriteTest
from metagpt.actions import UserRequirement
from metagpt.logs import logger

class QAEngineer(SCRUMRole):
    """
    QA Engineer Role.
    Responsible for quality assurance and testing.
    """
    
    name: str = "Charlie"
    profile: str = "QA Engineer"
    goal: str = "Ensure high code quality through comprehensive testing."
    constraints: str = "Test cases must cover all requirements."
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Primary actions
        self.set_actions([WriteTest])
        
        # Watch for assignments or code completion
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
            if "test" in last_msg.content.lower() or "verify" in last_msg.content.lower():
                 self.todo_action = "WriteTest"
                 return True
        
        return await super()._think()
