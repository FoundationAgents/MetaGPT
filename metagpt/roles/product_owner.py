#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/01/12
@Author  : MetaGPT-Pro Team
@File    : product_owner.py
@Desc    : ProductOwner AI role - manages product backlog and maximizes value
"""
from typing import List, Optional, Dict

from pydantic import Field

from metagpt.actions import Action, UserRequirement
from metagpt.logs import logger
from metagpt.project.schemas import Story, Priority, TaskStatus
from metagpt.project.backlog_manager import BacklogManager
from metagpt.roles.di.role_zero import RoleZero
from metagpt.schema import Message
from metagpt.tools.tool_registry import register_tool


PRODUCT_OWNER_INSTRUCTION = """
You are a Product Owner responsible for maximizing the value delivered by the team.

## Your Responsibilities
1. **Manage Product Backlog** - Prioritize stories based on business value
2. **Define Acceptance Criteria** - Clear criteria for when stories are done
3. **Approve Increments** - Validate completed work meets expectations
4. **Stakeholder Communication** - Represent stakeholder needs to the team

## Available Tools
- BacklogPrioritize: Reorder backlog based on value
- DefineAcceptanceCriteria: Create acceptance criteria for stories
- ApproveIncrement: Validate completed work
- RefineBacklog: Add details and estimates to backlog items

## Guidelines
- Focus on business value, not technical implementation
- Keep backlog prioritized and refined
- Be available to answer team questions
- Accept or reject increments based on acceptance criteria
"""


PRIORITIZE_PROMPT = """
You are prioritizing the product backlog for maximum business value.

## Current Backlog
{backlog_items}

## Prioritization Criteria
1. Business value and ROI
2. Dependencies (foundational items first)
3. Risk reduction
4. Customer impact

Respond with a JSON array of story IDs in priority order (highest first):
["STORY-XXX", "STORY-YYY", ...]

Also provide a brief rationale for the top 3 priorities.
"""


ACCEPTANCE_CRITERIA_PROMPT = """
Create acceptance criteria for the following user story:

## Story
**Title:** {title}
**Description:** {description}

Create 3-5 clear, testable acceptance criteria in the format:
- Given [context], when [action], then [expected result]

Respond with a JSON array of acceptance criteria strings.
"""


class BacklogPrioritizeAction(Action):
    """Action to prioritize product backlog"""
    
    name: str = "BacklogPrioritize"
    desc: str = "Prioritize product backlog based on business value"
    
    async def run(self, project_id: str, **kwargs) -> Message:
        backlog_manager = BacklogManager(project_id)
        await backlog_manager.load()
        
        backlog = backlog_manager.get_backlog()
        if not backlog or not backlog.stories:
            return Message(content="No stories in backlog to prioritize", role="ProductOwner")
        
        # Format stories for LLM
        items = []
        for story_id, story in backlog.stories.items():
            items.append(f"- {story.id}: {story.title} ({story.story_points} pts, {story.priority.value})")
        
        prompt = PRIORITIZE_PROMPT.format(backlog_items="\n".join(items))
        response = await self._aask(prompt)
        
        return Message(
            content=f"## Backlog Prioritization\n\n{response}",
            role="ProductOwner",
            cause_by=self
        )


class DefineAcceptanceCriteriaAction(Action):
    """Action to define acceptance criteria for stories"""
    
    name: str = "DefineAcceptanceCriteria"
    desc: str = "Define acceptance criteria for user stories"
    
    async def run(self, project_id: str, story_id: str, **kwargs) -> Message:
        backlog_manager = BacklogManager(project_id)
        await backlog_manager.load()
        
        backlog = backlog_manager.get_backlog()
        if not backlog or story_id not in backlog.stories:
            return Message(content=f"Story {story_id} not found", role="ProductOwner")
        
        story = backlog.stories[story_id]
        
        prompt = ACCEPTANCE_CRITERIA_PROMPT.format(
            title=story.title,
            description=story.description
        )
        
        response = await self._aask(prompt)
        
        return Message(
            content=f"## Acceptance Criteria for {story_id}\n\n{response}",
            role="ProductOwner",
            cause_by=self
        )


class ApproveIncrementAction(Action):
    """Action to approve/reject completed increment"""
    
    name: str = "ApproveIncrement"
    desc: str = "Approve or reject completed increment based on acceptance criteria"
    
    async def run(self, project_id: str, story_id: str, **kwargs) -> Message:
        backlog_manager = BacklogManager(project_id)
        await backlog_manager.load()
        
        backlog = backlog_manager.get_backlog()
        if not backlog or story_id not in backlog.stories:
            return Message(content=f"Story {story_id} not found", role="ProductOwner")
        
        story = backlog.stories[story_id]
        
        # Check if all tasks are done
        all_done = all(
            backlog.tasks[tid].status == TaskStatus.DONE
            for tid in story.tasks
            if tid in backlog.tasks
        )
        
        if all_done:
            story.status = TaskStatus.DONE
            await backlog_manager.save()
            return Message(
                content=f"✅ **APPROVED**: Story {story_id} '{story.title}' meets acceptance criteria.",
                role="ProductOwner",
                cause_by=self
            )
        else:
            incomplete = [
                tid for tid in story.tasks
                if tid in backlog.tasks and backlog.tasks[tid].status != TaskStatus.DONE
            ]
            return Message(
                content=f"❌ **NOT APPROVED**: Story {story_id} has {len(incomplete)} incomplete tasks.",
                role="ProductOwner",
                cause_by=self
            )


@register_tool(include_functions=["prioritize_backlog", "define_acceptance_criteria", "approve_increment"])
class ProductOwner(RoleZero):
    """
    ProductOwner AI Role - Manages product backlog and maximizes value.
    
    The ProductOwner is responsible for:
    - Managing and prioritizing the Product Backlog
    - Defining acceptance criteria for stories
    - Approving completed increments
    - Representing stakeholder needs
    """
    
    name: str = "Paula"
    profile: str = "Product Owner"
    goal: str = "Maximize product value through effective backlog management"
    constraints: str = "Focus on business value, not technical implementation"
    instruction: str = PRODUCT_OWNER_INSTRUCTION
    
    # Tools available to ProductOwner
    tools: list[str] = [
        "BacklogPrioritize",
        "DefineAcceptanceCriteria",
        "ApproveIncrement",
        "RoleZero",
    ]
    
    current_project_id: Optional[str] = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([
            BacklogPrioritizeAction,
            DefineAcceptanceCriteriaAction,
            ApproveIncrementAction,
        ])
        self._watch([UserRequirement])
    
    def _update_tool_execution(self):
        """Register Product Owner tools"""
        self.tool_execution_map.update({
            "BacklogPrioritize.run": self.prioritize_backlog,
            "BacklogPrioritize": self.prioritize_backlog,
            "DefineAcceptanceCriteria.run": self.define_acceptance_criteria,
            "DefineAcceptanceCriteria": self.define_acceptance_criteria,
            "ApproveIncrement.run": self.approve_increment,
            "ApproveIncrement": self.approve_increment,
        })
    
    async def prioritize_backlog(
        self,
        project_id: str = None,
        **kwargs
    ) -> str:
        """
        Prioritize the product backlog based on business value.
        
        Args:
            project_id: The project to prioritize
            
        Returns:
            Prioritization result
        """
        project_id = project_id or self.current_project_id
        if not project_id:
            return "Error: No project_id specified"
        
        logger.info(f"ProductOwner prioritizing backlog for {project_id}")
        
        action = BacklogPrioritizeAction()
        action.set_context(self.context)
        action.set_llm(self.llm)
        
        result = await action.run(project_id=project_id)
        return result.content
    
    async def define_acceptance_criteria(
        self,
        project_id: str = None,
        story_id: str = "",
        **kwargs
    ) -> str:
        """
        Define acceptance criteria for a user story.
        
        Args:
            project_id: The project containing the story
            story_id: The story to define criteria for
            
        Returns:
            Acceptance criteria
        """
        project_id = project_id or self.current_project_id
        if not project_id:
            return "Error: No project_id specified"
        if not story_id:
            return "Error: No story_id specified"
        
        logger.info(f"ProductOwner defining acceptance criteria for {story_id}")
        
        action = DefineAcceptanceCriteriaAction()
        action.set_context(self.context)
        action.set_llm(self.llm)
        
        result = await action.run(project_id=project_id, story_id=story_id)
        return result.content
    
    async def approve_increment(
        self,
        project_id: str = None,
        story_id: str = "",
        **kwargs
    ) -> str:
        """
        Approve or reject a completed increment.
        
        Args:
            project_id: The project containing the story
            story_id: The story to approve/reject
            
        Returns:
            Approval result
        """
        project_id = project_id or self.current_project_id
        if not project_id:
            return "Error: No project_id specified"
        if not story_id:
            return "Error: No story_id specified"
        
        logger.info(f"ProductOwner evaluating {story_id} for approval")
        
        action = ApproveIncrementAction()
        action.set_context(self.context)
        action.set_llm(self.llm)
        
        result = await action.run(project_id=project_id, story_id=story_id)
        return result.content
    
    def set_project(self, project_id: str):
        """Set the current project context"""
        self.current_project_id = project_id
        logger.info(f"ProductOwner assigned to project: {project_id}")
