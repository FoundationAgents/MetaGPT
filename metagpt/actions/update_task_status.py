#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/01/12
@Author  : MetaGPT-Pro Team
@File    : update_task_status.py
@Desc    : Action to update task status on the board
"""
from metagpt.actions.action import Action
from metagpt.actions.action_output import ActionOutput
from metagpt.logs import logger
from metagpt.project.board_tracker import board_tracker
from metagpt.project.schemas import TaskStatus


from pydantic import BaseModel

class OutputParams(BaseModel):
    content: str
    instruct_content: str

class UpdateTaskStatus(Action):
    """
    Update Task Status.
    Moves task on the Kanban board.
    """
    
    name: str = "UpdateTaskStatus"
    project_id: str = "default_project"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if "project_id" in kwargs:
            self.project_id = kwargs["project_id"]

    async def run(self, task_id: str, status: TaskStatus, **kwargs) -> ActionOutput:
        logger.info(f"Updating task {task_id} to {status} in {self.project_id}")
        
        success = await board_tracker.move_task(
            project_id=self.project_id,
            task_id=task_id,
            new_status=status
        )
        
        if success:
            content = f"Moved {task_id} to {status}"
            return ActionOutput(content=content, instruct_content=OutputParams(content=content, instruct_content=content))
        else:
            content = f"Failed to move {task_id}"
            return ActionOutput(content=content, instruct_content=OutputParams(content=content, instruct_content=f"Failed"))
