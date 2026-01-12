#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/01/12
@Author  : MetaGPT-Pro Team
@File    : scrum_master.py
@Desc    : ScrumMaster AI role - facilitates SCRUM ceremonies and removes blockers
"""
from typing import List, Optional

from pydantic import Field

from metagpt.actions import UserRequirement
from metagpt.actions.scrum import (
    SprintPlanningAction,
    DailyStandupAction,
    SprintReviewAction,
    RetrospectiveAction,
)
from metagpt.logs import logger
from metagpt.project.backlog_manager import BacklogManager
from metagpt.project.board_tracker import board_tracker
from metagpt.roles.di.role_zero import RoleZero
from metagpt.schema import Message
from metagpt.tools.tool_registry import register_tool


SCRUM_MASTER_INSTRUCTION = """
You are a Scrum Master responsible for facilitating SCRUM ceremonies and helping the team work effectively.

## Your Responsibilities
1. **Facilitate Ceremonies** - Sprint Planning, Daily Standup, Sprint Review, Retrospective
2. **Remove Blockers** - Identify and help resolve impediments
3. **Track Progress** - Monitor sprint velocity and burndown
4. **Coach Team** - Help team follow SCRUM practices

## Available Tools
- SprintPlanning: Conduct sprint planning to create sprint backlog
- DailyStandup: Run daily standup to track progress
- SprintReview: Review completed increment at sprint end
- Retrospective: Facilitate retrospective for continuous improvement

## Guidelines
- Always prioritize unblocking the team
- Keep ceremonies focused and time-boxed
- Provide actionable insights from metrics
- Support but don't micromanage the development team
"""


@register_tool(include_functions=["run_standup", "run_sprint_planning", "run_sprint_review", "run_retrospective"])
class ScrumMaster(RoleZero):
    """
    ScrumMaster AI Role - Facilitates SCRUM ceremonies and removes blockers.
    
    The ScrumMaster is responsible for:
    - Facilitating all SCRUM ceremonies
    - Monitoring sprint progress and velocity
    - Identifying and helping resolve blockers
    - Coaching the team on SCRUM practices
    """
    
    name: str = "Sam"
    profile: str = "Scrum Master"
    goal: str = "Facilitate SCRUM ceremonies, remove blockers, and help the team deliver value"
    constraints: str = "Focus on process facilitation, not task assignment"
    instruction: str = SCRUM_MASTER_INSTRUCTION
    
    # Tools available to ScrumMaster
    tools: list[str] = [
        "SprintPlanning",
        "DailyStandup",
        "SprintReview",
        "Retrospective",
        "RoleZero",
    ]
    
    # Configuration
    sprint_duration: int = Field(default=7, description="Sprint duration in days")
    velocity: int = Field(default=20, description="Team velocity in story points")
    current_project_id: Optional[str] = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([
            SprintPlanningAction,
            DailyStandupAction,
            SprintReviewAction,
            RetrospectiveAction,
        ])
        self._watch([UserRequirement])
    
    def _update_tool_execution(self):
        """Register SCRUM ceremony tools"""
        self.tool_execution_map.update({
            "SprintPlanning.run": self.run_sprint_planning,
            "SprintPlanning": self.run_sprint_planning,
            "DailyStandup.run": self.run_standup,
            "DailyStandup": self.run_standup,
            "SprintReview.run": self.run_sprint_review,
            "SprintReview": self.run_sprint_review,
            "Retrospective.run": self.run_retrospective,
            "Retrospective": self.run_retrospective,
        })
    
    async def run_sprint_planning(
        self,
        project_id: str = None,
        sprint_number: int = 1,
        **kwargs
    ) -> str:
        """
        Conduct Sprint Planning ceremony.
        
        Args:
            project_id: The project to plan for
            sprint_number: The sprint number to plan
            
        Returns:
            Sprint planning summary
        """
        project_id = project_id or self.current_project_id
        if not project_id:
            return "Error: No project_id specified"
        
        logger.info(f"ScrumMaster initiating Sprint Planning for {project_id}")
        
        action = SprintPlanningAction(
            velocity=self.velocity,
            sprint_duration=self.sprint_duration
        )
        action.set_context(self.context)
        action.set_llm(self.llm)
        
        result = await action.run(
            project_id=project_id,
            sprint_number=sprint_number
        )
        
        return result.content
    
    async def run_standup(
        self,
        project_id: str = None,
        **kwargs
    ) -> str:
        """
        Conduct Daily Standup ceremony.
        
        Args:
            project_id: The project to run standup for
            
        Returns:
            Standup report
        """
        project_id = project_id or self.current_project_id
        if not project_id:
            return "Error: No project_id specified"
        
        logger.info(f"ScrumMaster facilitating Daily Standup for {project_id}")
        
        action = DailyStandupAction()
        action.set_context(self.context)
        action.set_llm(self.llm)
        
        result = await action.run(project_id=project_id)
        
        return result.content
    
    async def run_sprint_review(
        self,
        project_id: str = None,
        sprint_number: int = 1,
        **kwargs
    ) -> str:
        """
        Conduct Sprint Review ceremony.
        
        Args:
            project_id: The project to review
            sprint_number: The sprint number to review
            
        Returns:
            Sprint review report
        """
        project_id = project_id or self.current_project_id
        if not project_id:
            return "Error: No project_id specified"
        
        logger.info(f"ScrumMaster conducting Sprint Review for {project_id}")
        
        action = SprintReviewAction()
        action.set_context(self.context)
        action.set_llm(self.llm)
        
        result = await action.run(
            project_id=project_id,
            sprint_number=sprint_number
        )
        
        return result.content
    
    async def run_retrospective(
        self,
        project_id: str = None,
        sprint_number: int = 1,
        **kwargs
    ) -> str:
        """
        Conduct Sprint Retrospective ceremony.
        
        Args:
            project_id: The project to retrospect
            sprint_number: The sprint number to analyze
            
        Returns:
            Retrospective report
        """
        project_id = project_id or self.current_project_id
        if not project_id:
            return "Error: No project_id specified"
        
        logger.info(f"ScrumMaster facilitating Retrospective for {project_id}")
        
        action = RetrospectiveAction()
        action.set_context(self.context)
        action.set_llm(self.llm)
        
        result = await action.run(
            project_id=project_id,
            sprint_number=sprint_number
        )
        
        return result.content
    
    def set_project(self, project_id: str):
        """Set the current project context"""
        self.current_project_id = project_id
        logger.info(f"ScrumMaster assigned to project: {project_id}")
