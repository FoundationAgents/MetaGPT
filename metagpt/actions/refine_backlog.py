#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/01/12
@Author  : MetaGPT-Pro Team
@File    : refine_backlog.py
@Desc    : Action to refine requirements into structured backlog items
"""
from typing import Optional

from metagpt.actions.action import Action
from metagpt.actions.action_output import ActionOutput
from metagpt.project.task_breakdown import TaskBreakdownGenerator
from metagpt.project.backlog_manager import BacklogManager
from metagpt.project.sprint_planner import SprintPlanner
from metagpt.project.board_tracker import board_tracker
from metagpt.logs import logger


from pydantic import BaseModel

class OutputParams(BaseModel):
    content: str

class RefineBacklog(Action):
    """Refine requirements into Backlog Items (Epics, Stories, Tasks)"""
    
    name: str = "RefineBacklog"
    project_id: str = "default_project"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if "project_id" in kwargs:
            self.project_id = kwargs["project_id"]

    async def run(self, requirements: str, **kwargs) -> ActionOutput:
        logger.info(f"Refining backlog for project {self.project_id}")
        
        # 1. Generate Breakdown
        generator = TaskBreakdownGenerator()
        breakdown = await generator.generate(requirements)
        
        # 2. Save to BacklogManager
        # Note: BacklogManager expects project_id
        manager = BacklogManager(self.project_id)
        
        # Check if already initialized, if so, we might be merging (TODO)
        # For now, we initialize/overwrite
        await manager.initialize(
            epics=breakdown["epics"],
            stories=breakdown["stories"],
            tasks=breakdown["tasks"]
        )
        
        # 3. Create Sprints (Initial Plan)
        planner = SprintPlanner()
        sprints = planner.create_sprints(
            tasks=breakdown["tasks"],
            stories=breakdown["stories"]
        )
        await manager.save_sprints(sprints)
        
        # 4. Initialize Board
        await board_tracker.initialize_board(self.project_id, breakdown["tasks"])
        
        summary = f"Backlog refined: {len(breakdown['epics'])} Epics, {len(breakdown['stories'])} Stories, {len(breakdown['tasks'])} Tasks created."
        return ActionOutput(content=summary, instruct_content=OutputParams(content=summary))
