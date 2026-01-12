#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/01/12
@Author  : MetaGPT-Pro Team
@File    : scrum_team.py
@Desc    : ScrumTeam orchestrator - manages full SCRUM sprint cycle
"""
from typing import List, Optional
from datetime import datetime

from pydantic import Field

from metagpt.team import Team
from metagpt.roles.scrum_master import ScrumMaster
from metagpt.roles.product_owner import ProductOwner
from metagpt.roles.architect import Architect
from metagpt.roles.engineer import Engineer
from metagpt.project.backlog_manager import BacklogManager
from metagpt.project.sprint_planner import SprintPlanner
from metagpt.project.board_tracker import board_tracker
from metagpt.project.task_breakdown import TaskBreakdown
from metagpt.logs import logger
from metagpt.schema import Message


class ScrumTeam(Team):
    """
    ScrumTeam orchestrates multi-agent collaboration using SCRUM methodology.
    
    Extends the base Team class to add SCRUM-specific functionality:
    - Sprint cycle management
    - Ceremony orchestration
    - Velocity tracking
    - Backlog management integration
    
    Example usage:
        ```python
        team = ScrumTeam()
        team.hire_scrum_team()
        team.invest(5.0)
        team.run_project("Build a calculator app")
        await team.run_sprint()
        ```
    """
    
    # SCRUM Configuration
    sprint_duration: int = Field(default=7, description="Sprint duration in days")
    velocity: int = Field(default=20, description="Team velocity in story points per sprint")
    current_sprint: int = Field(default=0, description="Current sprint number")
    project_id: Optional[str] = None
    
    # Team members
    scrum_master: Optional[ScrumMaster] = None
    product_owner: Optional[ProductOwner] = None
    
    def hire_scrum_team(
        self,
        include_architect: bool = True,
        include_engineer: bool = True,
        additional_roles: List = None
    ):
        """
        Hire the standard SCRUM team with core roles.
        
        Args:
            include_architect: Include Architect role
            include_engineer: Include Engineer role
            additional_roles: Additional role instances to add
        """
        # Create SCRUM-specific roles
        self.scrum_master = ScrumMaster(
            sprint_duration=self.sprint_duration,
            velocity=self.velocity
        )
        self.product_owner = ProductOwner()
        
        # Build team roster
        team_roles = [
            self.product_owner,
            self.scrum_master,
        ]
        
        if include_architect:
            team_roles.append(Architect())
        
        if include_engineer:
            team_roles.append(Engineer())
        
        if additional_roles:
            team_roles.extend(additional_roles)
        
        # Hire all roles
        self.hire(team_roles)
        
        logger.info(f"ScrumTeam assembled with {len(team_roles)} members")
    
    def run_project(self, requirement: str, project_id: str = None):
        """
        Initialize a new project with the given requirement.
        
        Args:
            requirement: The project requirement/idea
            project_id: Optional project identifier (auto-generated if not provided)
        """
        # Generate project ID if not provided
        if not project_id:
            project_id = f"scrum_project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.project_id = project_id
        
        # Set project context for SCRUM roles
        if self.scrum_master:
            self.scrum_master.set_project(project_id)
        if self.product_owner:
            self.product_owner.set_project(project_id)
        
        # Store the requirement for team processing
        self._idea = requirement
        
        logger.info(f"Project '{project_id}' initialized with requirement: {requirement[:100]}...")
    
    async def run_sprint(self, n_round: int = 3) -> dict:
        """
        Execute a complete sprint cycle.
        
        This includes:
        1. Sprint Planning (if first sprint or new planning needed)
        2. Development work (via team.run)
        3. Sprint Review
        4. Sprint Retrospective
        
        Args:
            n_round: Number of rounds for development work
            
        Returns:
            Dict containing sprint results
        """
        if not self.project_id:
            raise ValueError("No project set. Call run_project() first.")
        
        self.current_sprint += 1
        sprint_num = self.current_sprint
        
        logger.info(f"Starting Sprint {sprint_num}")
        
        results = {
            "sprint_number": sprint_num,
            "project_id": self.project_id,
            "phases": {}
        }
        
        # Phase 1: Sprint Planning
        logger.info("Phase 1: Sprint Planning")
        if self.scrum_master:
            planning_result = await self.scrum_master.run_sprint_planning(
                project_id=self.project_id,
                sprint_number=sprint_num
            )
            results["phases"]["planning"] = planning_result
        
        # Phase 2: Development (via standard Team.run)
        logger.info("Phase 2: Development Work")
        dev_result = await self.run(
            n_round=n_round,
            idea=self._idea if sprint_num == 1 else f"Continue Sprint {sprint_num} work",
            send_to="",
            auto_archive=False
        )
        results["phases"]["development"] = str(dev_result)
        
        # Phase 3: Daily Standup (simulated at end of sprint for this implementation)
        logger.info("Phase 3: Daily Standup")
        if self.scrum_master:
            standup_result = await self.scrum_master.run_standup(
                project_id=self.project_id
            )
            results["phases"]["standup"] = standup_result
        
        # Phase 4: Sprint Review
        logger.info("Phase 4: Sprint Review")
        if self.scrum_master:
            review_result = await self.scrum_master.run_sprint_review(
                project_id=self.project_id,
                sprint_number=sprint_num
            )
            results["phases"]["review"] = review_result
        
        # Phase 5: Sprint Retrospective
        logger.info("Phase 5: Sprint Retrospective")
        if self.scrum_master:
            retro_result = await self.scrum_master.run_retrospective(
                project_id=self.project_id,
                sprint_number=sprint_num
            )
            results["phases"]["retrospective"] = retro_result
        
        logger.info(f"Sprint {sprint_num} completed")
        
        return results
    
    async def run_daily_standup(self) -> str:
        """
        Run a daily standup outside of sprint context.
        
        Returns:
            Standup report
        """
        if not self.project_id:
            return "No project set"
        
        if self.scrum_master:
            return await self.scrum_master.run_standup(project_id=self.project_id)
        
        return "No ScrumMaster available"
    
    async def prioritize_backlog(self) -> str:
        """
        Have the Product Owner prioritize the backlog.
        
        Returns:
            Prioritization result
        """
        if not self.project_id:
            return "No project set"
        
        if self.product_owner:
            return await self.product_owner.prioritize_backlog(project_id=self.project_id)
        
        return "No ProductOwner available"
    
    def get_sprint_status(self) -> dict:
        """
        Get current sprint status.
        
        Returns:
            Dict with sprint status information
        """
        if not self.project_id:
            return {"error": "No project set"}
        
        metrics = board_tracker.get_metrics(self.project_id)
        
        return {
            "project_id": self.project_id,
            "current_sprint": self.current_sprint,
            "progress_percent": metrics.progress_percent,
            "points_completed": metrics.points_completed,
            "points_remaining": metrics.points_remaining,
            "blocked_count": metrics.blocked_count
        }
