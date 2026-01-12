#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/01/12
@Author  : MetaGPT-Pro Team
@File    : sprint_planning.py
@Desc    : Sprint Planning ceremony action - selects stories and creates sprint backlog
"""
from typing import Dict, List, Optional
from datetime import datetime

from pydantic import Field

from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.project.schemas import Sprint, Story, Task, Priority, TaskStatus
from metagpt.project.sprint_planner import SprintPlanner
from metagpt.project.backlog_manager import BacklogManager
from metagpt.schema import Message
from metagpt.tools.tool_registry import register_tool


SPRINT_PLANNING_PROMPT = """
You are conducting Sprint Planning for Sprint {sprint_number}.

## Product Backlog (Prioritized)
{backlog_summary}

## Team Velocity
- Historical velocity: {velocity} story points per sprint
- Sprint duration: {sprint_duration} days

## Your Task
1. Select stories from the Product Backlog that fit within the velocity
2. Break down stories into specific tasks if needed
3. Create clear sprint goals

Respond with a JSON object containing:
{{
    "sprint_goals": ["goal1", "goal2", "goal3"],
    "selected_stories": ["STORY-XXX", "STORY-YYY"],
    "notes": "Any additional planning notes"
}}
"""


@register_tool(include_functions=["run"])
class SprintPlanningAction(Action):
    """Conducts Sprint Planning ceremony to create Sprint Backlog"""
    
    name: str = "SprintPlanning"
    desc: str = "Conduct Sprint Planning to select stories and create sprint backlog"
    
    velocity: int = Field(default=20, description="Team velocity in story points")
    sprint_duration: int = Field(default=7, description="Sprint duration in days")
    
    async def run(
        self,
        project_id: str,
        sprint_number: int = 1,
        backlog_manager: Optional[BacklogManager] = None,
        **kwargs
    ) -> Message:
        """
        Conduct Sprint Planning ceremony.
        
        Args:
            project_id: The project identifier
            sprint_number: The sprint number to plan
            backlog_manager: Optional backlog manager instance
            
        Returns:
            Message containing sprint planning results
        """
        logger.info(f"Starting Sprint Planning for Sprint {sprint_number}")
        
        # Load or create backlog manager
        if not backlog_manager:
            backlog_manager = BacklogManager(project_id)
            await backlog_manager.load()
        
        backlog = backlog_manager.get_backlog()
        if not backlog:
            return Message(
                content="No backlog found. Please create product backlog first.",
                role="ScrumMaster"
            )
        
        # Get prioritized stories summary
        backlog_summary = self._format_backlog_summary(backlog)
        
        # Use LLM to help with sprint planning decisions
        prompt = SPRINT_PLANNING_PROMPT.format(
            sprint_number=sprint_number,
            backlog_summary=backlog_summary,
            velocity=self.velocity,
            sprint_duration=self.sprint_duration
        )
        
        planning_response = await self._aask(prompt)
        
        # Create sprint using SprintPlanner
        sprint_planner = SprintPlanner(
            sprint_duration=self.sprint_duration,
            velocity=self.velocity
        )
        
        # Filter to only TODO tasks
        available_tasks = {
            tid: task for tid, task in backlog.tasks.items()
            if task.status == TaskStatus.TODO
        }
        
        sprints = sprint_planner.create_sprints(
            tasks=available_tasks,
            stories=backlog.stories,
            start_date=datetime.now()
        )
        
        # Save sprints
        await backlog_manager.save_sprints(sprints)
        
        # Generate summary
        if sprints:
            current_sprint = sprints[0] if sprint_number <= len(sprints) else sprints[-1]
            summary = self._generate_planning_summary(current_sprint, backlog)
        else:
            summary = "No tasks available for sprint planning."
        
        logger.info(f"Sprint Planning completed: {len(sprints)} sprints created")
        
        return Message(
            content=f"## Sprint Planning Complete\n\n{summary}\n\n### LLM Planning Notes:\n{planning_response}",
            role="ScrumMaster",
            cause_by=self
        )
    
    def _format_backlog_summary(self, backlog) -> str:
        """Format backlog for LLM prompt"""
        lines = []
        for story_id in backlog.priority_order[:10]:  # Top 10 stories
            if story_id in backlog.stories:
                story = backlog.stories[story_id]
                task_count = len(story.tasks)
                lines.append(
                    f"- [{story.priority.value.upper()}] {story.id}: {story.title} "
                    f"({story.story_points} pts, {task_count} tasks)"
                )
        return "\n".join(lines) if lines else "No stories in backlog"
    
    def _generate_planning_summary(self, sprint: Sprint, backlog) -> str:
        """Generate human-readable planning summary"""
        task_details = []
        for task_id in sprint.tasks[:5]:  # First 5 tasks
            if task_id in backlog.tasks:
                task = backlog.tasks[task_id]
                task_details.append(f"  - {task.title} ({task.story_points} pts)")
        
        return f"""**Sprint {sprint.number}: {sprint.name}**
- Duration: {sprint.duration_days} days
- Start: {sprint.start_date.strftime('%Y-%m-%d') if sprint.start_date else 'TBD'}
- End: {sprint.end_date.strftime('%Y-%m-%d') if sprint.end_date else 'TBD'}
- Total Points: {sprint.total_points}
- Tasks: {len(sprint.tasks)}

**Sprint Goals:**
{chr(10).join(f'- {g}' for g in sprint.goals)}

**Selected Tasks:**
{chr(10).join(task_details)}
"""
