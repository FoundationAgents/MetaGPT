#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/01/12
@Author  : MetaGPT-Pro Team
@File    : product_owner.py
@Desc    : Product Owner SCRUM Agent
"""
from typing import Type

from metagpt.roles.scrum_role import SCRUMRole
from metagpt.actions.refine_backlog import RefineBacklog
from metagpt.actions.write_prd import WritePRD
from metagpt.actions import UserRequirement
from metagpt.logs import logger

class ProductOwner(SCRUMRole):
    """
    Product Owner Role.
    Responsible for defining stories, prioritizing backlog, and maintaining product vision.
    """
    
    name: str = "Alice"
    profile: str = "Product Owner"
    goal: str = "Maximize product value by managing and prioritizing the product backlog."
    constraints: str = "Ensure stories are convenient, valuable, and verifiable."
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Primary actions
        self.set_actions([RefineBacklog])
        
        # Watch for User Requirements
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
        If new UserRequirement observed -> RefineBacklog
        """
        # Default behavior from Role might be enough if we set_actions correctly.
        # But we might want custom logic to decide between RefineBacklog vs WritePRD.
        
        # For now, simplistic React:
        # For now, simplistic React:
        if self.rc.news:
            last_msg = self.rc.news[-1]
            if last_msg.cause_by == UserRequirement:
                # Find RefineBacklog action
                for i, action in enumerate(self.actions):
                    if isinstance(action, RefineBacklog):
                        self.rc.todo = action
                        self.rc.state = i
                        return True
                
        return await super()._think()
