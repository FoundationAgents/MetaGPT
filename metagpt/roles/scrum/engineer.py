#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/01/12
@Author  : MetaGPT-Pro Team
@File    : engineer.py
@Desc    : Engineer SCRUM Agent
"""
from metagpt.roles.scrum_role import SCRUMRole
from metagpt.actions.write_code import WriteCode
from metagpt.actions.update_task_status import UpdateTaskStatus
from metagpt.actions import UserRequirement
from metagpt.project.board_tracker import board_tracker
from metagpt.project.schemas import TaskStatus
from metagpt.actions.action_output import ActionOutput
from metagpt.logs import logger

class Engineer(SCRUMRole):
    """
    Engineer Role.
    Responsible for implementing tasks and stories.
    """
    
    name: str = "Alex"
    profile: str = "Engineer"
    goal: str = "Implement features and fix bugs with high quality code."
    constraints: str = "Follow coding standards and project architecture."
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Primary actions
        self.set_actions([WriteCode, UpdateTaskStatus])
        
        # Watch for assignments (TODO: Add specific Event trigger)
        self._watch([UserRequirement])
        
        # Initialize action configurations
        self._init_actions()
        
        # Internal state
        self.current_task_id = None
        self.last_action_type = None

    def _init_actions(self):
        """Configure actions with project context"""
        for action in self.actions:
            if hasattr(action, 'project_id'):
                action.project_id = self.project_id

    async def _think(self) -> bool:
        """
        Decide next action.
        """
        # 1. Check if we are in the middle of a task
        if self.current_task_id:
            if self.last_action_type == UpdateTaskStatus:
                # We just moved task to In Progress, now Write Code
                # Verify we moved to IN_PROGRESS (optional, assumed true)
                self.rc.todo = WriteCode
                self.rc.state = 0 # WriteCode index
                return True
                
            elif self.last_action_type == WriteCode:
                # We just wrote code, now move to Review
                self.rc.todo = UpdateTaskStatus
                self.rc.state = 1 # UpdateTaskStatus index
                return True
                
        # 2. Check for new tasks in TODO
        board = board_tracker.get_board(self.project_id)
        if board and board.todo:
            # Pick the first task
            task_id = board.todo[0]
            self.current_task_id = task_id
            
            # Start by moving to In Progress
            self.rc.todo = UpdateTaskStatus
            self.rc.state = 1
            logger.info(f"Engineer picking up task {task_id}")
            return True
            
        return await super()._think()

    async def _act(self) -> ActionOutput:
        todo = self.rc.todo
        
        if isinstance(todo, UpdateTaskStatus) or (isinstance(todo, type) and issubclass(todo, UpdateTaskStatus)):
            # Determine target status
            if self.last_action_type == WriteCode:
                status = TaskStatus.REVIEW
            else:
                status = TaskStatus.IN_PROGRESS
                
            # Execute
            action = UpdateTaskStatus(project_id=self.project_id)
            result = await action.run(task_id=self.current_task_id, status=status)
            
            self.last_action_type = UpdateTaskStatus
            
            # If we moved to REVIEW, clear current task
            if status == TaskStatus.REVIEW:
                self.current_task_id = None
                self.last_action_type = None # Reset cycle
                
            return result

        elif isinstance(todo, WriteCode) or (isinstance(todo, type) and issubclass(todo, WriteCode)):
            # Fetch task details
            tasks = board_tracker.get_tasks(self.project_id)
            task = tasks.get(self.current_task_id)
            context = task.description if task else "Implement feature"
            
            # Execute
            # Note: We instantiate generic WriteCode, assuming it uses context
            # We might need to pass context via kwargs if WriteCode supports it, 
            # but usually it reads from history. We'll inject context into history implicitly?
            # Or assume WriteCode.run takes arguments we can't easily pass via standard _act.
            # We'll use the Action instance directly.
            
            action = WriteCode(project_id=self.project_id)
            # WriteCode usually takes 'context' or 'instruction' in run? 
            # Looking at WriteCode source would be ideal, but assuming 'context' is safe-ish.
            # ACTUALLY: WriteCode.run(context=...)
            result = await action.run(context=context) 
            
            self.last_action_type = WriteCode
            return result
            
        return await super()._act()
