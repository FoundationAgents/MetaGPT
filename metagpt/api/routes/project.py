#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/01/10
@Author  : MetaGPT-Pro Team
@File    : project.py
@Desc    : API routes for Sprint/Backlog System
"""
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import List
from metagpt.project.board_tracker import board_tracker
from metagpt.project.backlog_manager import BacklogManager
from metagpt.project.schemas import (
    TaskStatus,
    TaskMoveRequest,
    TaskMoveResponse,
    SprintResponse,
    BacklogResponse,
    BoardResponse,
    ProjectMetrics,
    Task,
    Story,
    Priority
)
from metagpt.logs import logger
from pydantic import BaseModel
from metagpt.project.state_manager import state_manager
from metagpt.project.schemas import (
    TaskStatus,
    TaskMoveRequest,
    TaskMoveResponse,
    SprintResponse,
    BacklogResponse,
    BoardResponse,
    ProjectMetrics,
    Task,
    Story,
    Priority,
    ProjectMetadata
)

class AddStoryRequest(BaseModel):
    title: str
    description: str = ""
    priority: Priority = Priority.MEDIUM

class AddTaskRequest(BaseModel):
    title: str
    description: str = ""
    priority: Priority = Priority.MEDIUM
    type: str = "task" # task, bug
    parent_story_id: str = None

router = APIRouter()

@router.get("/", response_model=List[ProjectMetadata])
async def list_projects():
    """List all persistent projects"""
    try:
        return await state_manager.list_projects()
    except Exception as e:
        logger.exception(f"Failed to list projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/backlog/story", response_model=Story)
async def add_story(project_id: str, req: AddStoryRequest):
    """Add a new story to the backlog"""
    try:
        manager = _get_backlog_manager(project_id)
        story = await manager.add_story(
            title=req.title,
            description=req.description,
            priority=req.priority
        )
        return story
    except Exception as e:
        logger.exception(f"Failed to add story: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/backlog/task", response_model=Task)
async def add_task(project_id: str, req: AddTaskRequest):
    """Add a new task or bug to the backlog and board"""
    try:
        manager = _get_backlog_manager(project_id)
        task = await manager.add_task(
            title=req.title,
            description=req.description,
            priority=req.priority,
            type=req.type,
            parent_story_id=req.parent_story_id
        )
        
        # Sync to board
        await board_tracker.add_task(project_id, task)
        
        return task
    except Exception as e:
        logger.exception(f"Failed to add task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Cache backlog managers per project
_backlog_managers: dict[str, BacklogManager] = {}


def _get_backlog_manager(project_id: str) -> BacklogManager:
    """Get or create BacklogManager for a project"""
    if project_id not in _backlog_managers:
        _backlog_managers[project_id] = BacklogManager(project_id)
    return _backlog_managers[project_id]


@router.get("/{project_id}/sprints")
async def get_sprints(project_id: str):
    """Get all sprints for a project"""
    try:
        manager = _get_backlog_manager(project_id)
        sprints = await manager.load_sprints()
        current = await manager.get_current_sprint()
        
        return {
            "sprints": [s.model_dump() for s in sprints],
            "current_sprint": current,
            "total_sprints": len(sprints)
        }
    except Exception as e:
        logger.exception(f"Failed to get sprints: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/sprint/{sprint_num}")
async def get_sprint(project_id: str, sprint_num: int):
    """Get a specific sprint with task details"""
    try:
        manager = _get_backlog_manager(project_id)
        sprints = await manager.load_sprints()
        
        sprint = next((s for s in sprints if s.number == sprint_num), None)
        if not sprint:
            raise HTTPException(status_code=404, detail=f"Sprint {sprint_num} not found")
        
        # Load backlog to get task details
        backlog = await manager.load()
        tasks = []
        if backlog:
            for task_id in sprint.tasks:
                if task_id in backlog.tasks:
                    tasks.append(backlog.tasks[task_id])
        
        return SprintResponse(
            sprint_num=sprint.number,
            name=sprint.name,
            tasks=tasks,
            progress=sprint.progress_percent,
            goals=sprint.goals
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get sprint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/backlog")
async def get_backlog(project_id: str):
    """Get the full project backlog"""
    try:
        manager = _get_backlog_manager(project_id)
        backlog = await manager.load()
        
        if not backlog:
            # Return empty backlog instead of 404
            return BacklogResponse(
                stories=[],
                total_points=0,
                priority_order=[]
            )
        
        return BacklogResponse(
            stories=list(backlog.stories.values()),
            total_points=backlog.total_points,
            priority_order=backlog.priority_order
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get backlog: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/board")
async def get_board(project_id: str):
    """Get the current Kanban board state"""
    try:
        board = board_tracker.get_board(project_id)
        tasks = board_tracker.get_tasks(project_id)
        
        if not board:
            # Try loading from disk
            board = await board_tracker.load_board(project_id)
            if not board:
                # Return empty board instead of 404
                return BoardResponse(
                    todo=[],
                    in_progress=[],
                    review=[],
                    testing=[],
                    done=[],
                    blocked=[]
                )
        
        def get_tasks_for_column(task_ids: List[str]) -> List[Task]:
            return [tasks[tid] for tid in task_ids if tid in tasks]
        
        return BoardResponse(
            todo=get_tasks_for_column(board.todo),
            in_progress=get_tasks_for_column(board.in_progress),
            review=get_tasks_for_column(board.review),
            testing=get_tasks_for_column(board.testing),
            done=get_tasks_for_column(board.done),
            blocked=get_tasks_for_column(board.blocked)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get board: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/task/move", response_model=TaskMoveResponse)
async def move_task(project_id: str, req: TaskMoveRequest):
    """Move a task to a new status"""
    try:
        success = await board_tracker.move_task(
            project_id=project_id,
            task_id=req.task_id,
            new_status=req.new_status
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Task or board not found")
        
        # Also update in backlog
        manager = _get_backlog_manager(project_id)
        await manager.update_task_status(req.task_id, req.new_status)
        
        return TaskMoveResponse(
            updated=True,
            task_id=req.task_id,
            new_status=req.new_status.value,
            message=f"Task moved to {req.new_status.value}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to move task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/metrics", response_model=ProjectMetrics)
async def get_metrics(project_id: str):
    """Get project progress metrics"""
    try:
        metrics = board_tracker.get_metrics(project_id)
        
        # Enrich with sprint info
        manager = _get_backlog_manager(project_id)
        sprints = await manager.load_sprints()
        current = await manager.get_current_sprint()
        
        metrics.current_sprint = current
        metrics.total_sprints = len(sprints)
        
        return metrics
    except Exception as e:
        logger.exception(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/{project_id}/board/stream")
async def board_websocket(websocket: WebSocket, project_id: str):
    """WebSocket for real-time board updates"""
    await websocket.accept()
    board_tracker.add_websocket(project_id, websocket)
    
    try:
        # Send initial state
        board = board_tracker.get_board(project_id)
        if board:
            await websocket.send_json({
                "type": "initial_state",
                "board": board.model_dump()
            })
        
        # Keep connection alive
        while True:
            data = await websocket.receive_text()
            # Handle any client commands if needed
    except WebSocketDisconnect:
        board_tracker.remove_websocket(project_id, websocket)
    except Exception:
        board_tracker.remove_websocket(project_id, websocket)
