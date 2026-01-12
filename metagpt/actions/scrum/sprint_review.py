#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/01/12
@Author  : MetaGPT-Pro Team
@File    : sprint_review.py
@Desc    : Sprint Review ceremony action - reviews completed increment and validates acceptance criteria
"""
from typing import Dict, List, Optional
from datetime import datetime

from pydantic import Field

from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.project.schemas import Task, Story, TaskStatus, Sprint
from metagpt.project.backlog_manager import BacklogManager
from metagpt.project.board_tracker import board_tracker
from metagpt.schema import Message
from metagpt.tools.tool_registry import register_tool


SPRINT_REVIEW_PROMPT = """
You are conducting a Sprint Review for Sprint {sprint_number}.

## Sprint Summary
{sprint_summary}

## Completed Work
{completed_work}

## Incomplete Work
{incomplete_work}

## Acceptance Criteria Status
{acceptance_status}

Based on this sprint review:
1. Evaluate what was successfully delivered
2. Identify what was not completed and why
3. Provide recommendations for the Product Backlog
4. Suggest any adjustments for future sprints

Format as a Sprint Review report.
"""


@register_tool(include_functions=["run"])
class SprintReviewAction(Action):
    """Conducts Sprint Review ceremony to review completed increment"""
    
    name: str = "SprintReview"
    desc: str = "Conduct Sprint Review to evaluate completed increment against acceptance criteria"
    
    async def run(
        self,
        project_id: str,
        sprint_number: int = 1,
        backlog_manager: Optional[BacklogManager] = None,
        **kwargs
    ) -> Message:
        """
        Conduct Sprint Review ceremony.
        
        Args:
            project_id: The project identifier
            sprint_number: The sprint number to review
            backlog_manager: Optional backlog manager instance
            
        Returns:
            Message containing sprint review results
        """
        logger.info(f"Starting Sprint Review for Sprint {sprint_number}")
        
        # Load backlog manager
        if not backlog_manager:
            backlog_manager = BacklogManager(project_id)
            await backlog_manager.load()
        
        backlog = backlog_manager.get_backlog()
        sprints = await backlog_manager.load_sprints()
        
        if not sprints:
            return Message(
                content="No sprints found. Run Sprint Planning first.",
                role="ScrumMaster"
            )
        
        # Get the sprint to review
        sprint = None
        for s in sprints:
            if s.number == sprint_number:
                sprint = s
                break
        
        if not sprint:
            sprint = sprints[-1]  # Review latest sprint
        
        # Categorize tasks
        completed_tasks = []
        incomplete_tasks = []
        
        for task_id in sprint.tasks:
            if task_id in backlog.tasks:
                task = backlog.tasks[task_id]
                if task.status == TaskStatus.DONE:
                    completed_tasks.append(task)
                else:
                    incomplete_tasks.append(task)
        
        # Calculate sprint metrics
        completed_points = sum(t.story_points for t in completed_tasks)
        total_points = sprint.total_points
        completion_rate = (completed_points / total_points * 100) if total_points > 0 else 0
        
        # Format completed work
        completed_work = self._format_task_list(completed_tasks) or "No tasks completed"
        
        # Format incomplete work
        incomplete_work = self._format_task_list(incomplete_tasks) or "All tasks completed!"
        
        # Check acceptance criteria
        acceptance_status = self._check_acceptance_criteria(completed_tasks, backlog)
        
        # Sprint summary
        sprint_summary = f"""
- Sprint: {sprint.number} - {sprint.name}
- Duration: {sprint.duration_days} days
- Completed: {len(completed_tasks)} / {len(sprint.tasks)} tasks
- Points: {completed_points} / {total_points} ({completion_rate:.1f}%)
- Goals: {', '.join(sprint.goals[:3])}
"""
        
        # Generate review using LLM
        prompt = SPRINT_REVIEW_PROMPT.format(
            sprint_number=sprint_number,
            sprint_summary=sprint_summary,
            completed_work=completed_work,
            incomplete_work=incomplete_work,
            acceptance_status=acceptance_status
        )
        
        review_analysis = await self._aask(prompt)
        
        # Create full review report
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        full_report = f"""# Sprint {sprint_number} Review Report
**Date:** {timestamp}
**Project:** {project_id}

## Sprint Summary
{sprint_summary}

## Completion Metrics
| Metric | Value |
|--------|-------|
| Tasks Completed | {len(completed_tasks)} / {len(sprint.tasks)} |
| Points Delivered | {completed_points} / {total_points} |
| Completion Rate | {completion_rate:.1f}% |

## Completed Work
{completed_work}

## Incomplete Work
{incomplete_work}

## Acceptance Criteria
{acceptance_status}

## Analysis & Recommendations
{review_analysis}

---
*Report generated by ScrumMaster AI*
"""
        
        logger.info(f"Sprint Review completed for Sprint {sprint_number}")
        
        return Message(
            content=full_report,
            role="ScrumMaster",
            cause_by=self
        )
    
    def _format_task_list(self, tasks: List[Task]) -> str:
        """Format list of tasks for display"""
        if not tasks:
            return ""
        
        lines = []
        for task in tasks:
            status_emoji = "✅" if task.status == TaskStatus.DONE else "⏳"
            lines.append(f"- {status_emoji} {task.title} ({task.story_points} pts)")
        
        return "\n".join(lines)
    
    def _check_acceptance_criteria(self, completed_tasks: List[Task], backlog) -> str:
        """Check acceptance criteria for completed stories"""
        story_status = {}
        
        for task in completed_tasks:
            if task.parent_story and task.parent_story in backlog.stories:
                story = backlog.stories[task.parent_story]
                if story.id not in story_status:
                    story_status[story.id] = {
                        "title": story.title,
                        "criteria": story.acceptance_criteria,
                        "completed_tasks": 0,
                        "total_tasks": len(story.tasks)
                    }
                story_status[story.id]["completed_tasks"] += 1
        
        if not story_status:
            return "No stories to evaluate"
        
        lines = []
        for story_id, status in story_status.items():
            completion = (status["completed_tasks"] / status["total_tasks"] * 100) if status["total_tasks"] > 0 else 0
            lines.append(f"**{story_id}: {status['title']}**")
            lines.append(f"  - Task Progress: {status['completed_tasks']}/{status['total_tasks']} ({completion:.0f}%)")
            if status["criteria"]:
                lines.append("  - Acceptance Criteria:")
                for ac in status["criteria"]:
                    lines.append(f"    - [ ] {ac}")
            lines.append("")
        
        return "\n".join(lines)
