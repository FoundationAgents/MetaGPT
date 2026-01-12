#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/01/12
@Author  : MetaGPT-Pro Team
@File    : scrum.py
@Desc    : API routes for SCRUM ceremonies (Sprint Planning, Standup, Review, Retrospective)
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

from metagpt.project.backlog_manager import BacklogManager
from metagpt.project.board_tracker import board_tracker
from metagpt.logs import logger

router = APIRouter()

# Cache for backlog managers
_backlog_managers: dict[str, BacklogManager] = {}


def _get_backlog_manager(project_id: str) -> BacklogManager:
    """Get or create BacklogManager for a project"""
    if project_id not in _backlog_managers:
        _backlog_managers[project_id] = BacklogManager(project_id)
    return _backlog_managers[project_id]


# Request/Response Models
class SprintPlanningRequest(BaseModel):
    sprint_number: int = 1
    velocity: int = 20
    sprint_duration: int = 7


class CeremonyResponse(BaseModel):
    success: bool
    ceremony: str
    project_id: str
    timestamp: str
    report: str


class StandupStatusRequest(BaseModel):
    team_status: Optional[Dict[str, str]] = None


class ApproveIncrementRequest(BaseModel):
    story_id: str


# SCRUM Ceremony Endpoints

@router.post("/{project_id}/ceremony/sprint-planning", response_model=CeremonyResponse)
async def run_sprint_planning(project_id: str, req: SprintPlanningRequest, background_tasks: BackgroundTasks):
    """
    Run Sprint Planning ceremony.
    Creates sprint backlog from prioritized product backlog.
    """
    try:
        from metagpt.actions.scrum.sprint_planning import SprintPlanningAction
        
        action = SprintPlanningAction(
            velocity=req.velocity,
            sprint_duration=req.sprint_duration
        )
        
        manager = _get_backlog_manager(project_id)
        
        result = await action.run(
            project_id=project_id,
            sprint_number=req.sprint_number,
            backlog_manager=manager
        )
        
        return CeremonyResponse(
            success=True,
            ceremony="Sprint Planning",
            project_id=project_id,
            timestamp=datetime.now().isoformat(),
            report=result.content
        )
    except Exception as e:
        logger.exception(f"Sprint Planning failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/ceremony/daily-standup", response_model=CeremonyResponse)
async def run_daily_standup(project_id: str, req: Optional[StandupStatusRequest] = None):
    """
    Run Daily Standup ceremony.
    Collects status, identifies blockers, generates report.
    """
    try:
        from metagpt.actions.scrum.daily_standup import DailyStandupAction
        
        action = DailyStandupAction()
        
        team_status = req.team_status if req else None
        
        result = await action.run(
            project_id=project_id,
            team_status=team_status
        )
        
        return CeremonyResponse(
            success=True,
            ceremony="Daily Standup",
            project_id=project_id,
            timestamp=datetime.now().isoformat(),
            report=result.content
        )
    except Exception as e:
        logger.exception(f"Daily Standup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/ceremony/sprint-review", response_model=CeremonyResponse)
async def run_sprint_review(project_id: str, sprint_number: int = 1):
    """
    Run Sprint Review ceremony.
    Reviews completed increment and validates against acceptance criteria.
    """
    try:
        from metagpt.actions.scrum.sprint_review import SprintReviewAction
        
        action = SprintReviewAction()
        manager = _get_backlog_manager(project_id)
        
        result = await action.run(
            project_id=project_id,
            sprint_number=sprint_number,
            backlog_manager=manager
        )
        
        return CeremonyResponse(
            success=True,
            ceremony="Sprint Review",
            project_id=project_id,
            timestamp=datetime.now().isoformat(),
            report=result.content
        )
    except Exception as e:
        logger.exception(f"Sprint Review failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/ceremony/retrospective", response_model=CeremonyResponse)
async def run_retrospective(project_id: str, sprint_number: int = 1):
    """
    Run Sprint Retrospective ceremony.
    Analyzes sprint, identifies improvements, creates action items.
    """
    try:
        from metagpt.actions.scrum.retrospective import RetrospectiveAction
        
        action = RetrospectiveAction()
        manager = _get_backlog_manager(project_id)
        
        result = await action.run(
            project_id=project_id,
            sprint_number=sprint_number,
            backlog_manager=manager
        )
        
        return CeremonyResponse(
            success=True,
            ceremony="Retrospective",
            project_id=project_id,
            timestamp=datetime.now().isoformat(),
            report=result.content
        )
    except Exception as e:
        logger.exception(f"Retrospective failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/backlog/prioritize")
async def prioritize_backlog(project_id: str):
    """
    Have Product Owner AI prioritize the backlog.
    """
    try:
        from metagpt.roles.product_owner import BacklogPrioritizeAction
        
        action = BacklogPrioritizeAction()
        
        result = await action.run(project_id=project_id)
        
        return {
            "success": True,
            "project_id": project_id,
            "result": result.content
        }
    except Exception as e:
        logger.exception(f"Prioritization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/story/{story_id}/approve")
async def approve_increment(project_id: str, story_id: str):
    """
    Have Product Owner AI approve or reject a story increment.
    """
    try:
        from metagpt.roles.product_owner import ApproveIncrementAction
        
        action = ApproveIncrementAction()
        
        result = await action.run(project_id=project_id, story_id=story_id)
        
        return {
            "success": True,
            "project_id": project_id,
            "story_id": story_id,
            "result": result.content
        }
    except Exception as e:
        logger.exception(f"Approval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/ceremony/history")
async def get_ceremony_history(project_id: str):
    """
    Get history of ceremonies run for this project.
    """
    # TODO: Implement ceremony history storage
    return {
        "project_id": project_id,
        "ceremonies": [],
        "message": "Ceremony history not yet implemented"
    }
