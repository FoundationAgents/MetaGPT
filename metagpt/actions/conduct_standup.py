#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/01/12
@Author  : MetaGPT-Pro Team
@File    : conduct_standup.py
@Desc    : Action to conduct daily standup
"""
from metagpt.actions.action import Action
from metagpt.actions.action_output import ActionOutput
from metagpt.logs import logger
from metagpt.project.board_tracker import board_tracker
from pydantic import BaseModel

class OutputParams(BaseModel):
    content: str

class ConductStandup(Action):
    """
    Conduct Daily Standup.
    1. Check Board Status.
    2. Identify Blockers.
    3. Generate Report.
    """
    
    name: str = "ConductStandup"
    project_id: str = "default_project"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if "project_id" in kwargs:
            self.project_id = kwargs["project_id"]

    async def run(self, *args, **kwargs) -> ActionOutput:
        logger.info(f"Conducting Standup for project {self.project_id}")
        
        # 1. Get Board State
        state = board_tracker.get_board(self.project_id)
        
        # 2. Analyze
        blocked_tasks = state.blocked
        in_progress = state.in_progress
        
        report = []
        report.append(f"## Daily Standup Report ({self.project_id})")
        report.append(f"- **Blocked Tasks**: {len(blocked_tasks)}")
        report.append(f"- **In Progress**: {len(in_progress)}")
        
        if blocked_tasks:
            report.append("\n### Blockers:")
            for task_id in blocked_tasks:
                report.append(f"- {task_id}")
                
        summary = "\n".join(report)
        return ActionOutput(content=summary, instruct_content=OutputParams(content=summary))
