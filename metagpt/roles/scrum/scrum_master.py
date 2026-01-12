#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/01/12
@Author  : MetaGPT-Pro Team
@File    : scrum_master.py
@Desc    : Scrum Master SCRUM Agent
"""
from typing import Type

from metagpt.roles.scrum_role import SCRUMRole
from metagpt.actions.conduct_standup import ConductStandup
from metagpt.actions import UserRequirement
from metagpt.logs import logger

class ScrumMaster(SCRUMRole):
    """
    Scrum Master Role.
    Responsible for removing blockers and facilitating SCRUM ceremonies.
    """
    
    name: str = "Bob"
    profile: str = "Scrum Master"
    goal: str = "Facilitate the SCRUM process, remove blockers, and ensure team efficiency."
    constraints: str = "Adhere to SCRUM guidelines."
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Primary actions
        self.set_actions([ConductStandup])
        
        # Watch for User Requirements (e.g. "Start Standup")
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
            content = last_msg.content.lower()
            if "standup" in content or "status" in content:
                 # Find ConductStandup action
                 for i, action in enumerate(self.actions):
                     if isinstance(action, ConductStandup):
                         self.rc.todo = action
                         self.rc.state = i
                         return True
        
        return await super()._think()
