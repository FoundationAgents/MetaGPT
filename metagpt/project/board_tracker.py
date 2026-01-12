#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/01/10
@Author  : MetaGPT-Pro Team
@File    : board_tracker.py
@Desc    : Kanban board state management with real-time event streaming
"""
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime
from fastapi import WebSocket
from metagpt.logs import logger
from metagpt.const import DEFAULT_WORKSPACE_ROOT
from metagpt.project.schemas import (
    BoardState, Task, TaskStatus, ProjectMetrics
)
from metagpt.project.event_system import event_bus, Event, EventType


class BoardTracker:
    """Singleton tracker for Kanban board state with WebSocket streaming"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BoardTracker, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._boards: Dict[str, BoardState] = {}
        self._tasks: Dict[str, Dict[str, Task]] = {}  # project_id -> {task_id: Task}
        self._websockets: Dict[str, Set[WebSocket]] = {}  # project_id -> websockets
        self._history: Dict[str, List[dict]] = {}
        self._initialized = True
    
    def _get_storage_dir(self, project_id: str) -> Path:
        path = DEFAULT_WORKSPACE_ROOT / "projects" / project_id
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    async def initialize_board(self, project_id: str, tasks: Dict[str, Task]) -> BoardState:
        """Initialize board for a project"""
        board = BoardState(project_id=project_id)
        
        # Add all tasks to 'todo' column initially
        for task_id, task in tasks.items():
            if task.status == TaskStatus.TODO:
                board.todo.append(task_id)
            else:
                column = getattr(board, task.status.value, board.todo)
                column.append(task_id)
        
        self._boards[project_id] = board
        self._tasks[project_id] = tasks
        self._history[project_id] = []
        
        await self._save_board(project_id)
        logger.info(f"Initialized board for project {project_id} with {len(tasks)} tasks")
        return board
    
    async def add_task(self, project_id: str, task: Task) -> bool:
        """Add a new task to the board"""
        if project_id not in self._boards:
            # If board doesn't exist, we might need to initialize it?
            # Or just fail? For now, assume board exists or we initialize empty.
            await self.initialize_board(project_id, {task.id: task})
            return True
        
        board = self._boards[project_id]
        if project_id not in self._tasks:
            self._tasks[project_id] = {}
            
        self._tasks[project_id][task.id] = task
        
        # Add to column based on status
        column = getattr(board, task.status.value, board.todo)
        if task.id not in column:
            column.append(task.id)
            
        await self._save_board(project_id)
        
        # Notify
        await self._broadcast(project_id, {
            "type": "task_created",
            "task_id": task.id,
            "task_title": task.title,
            "status": task.status.value,
            "timestamp": datetime.now().isoformat()
        })
        
        # Also publish to global event bus
        event = Event(
            type=EventType.TASK_CREATED,
            project_id=project_id,
            task_id=task.id,
            payload={"task": task.model_dump()},
            metadata={"title": task.title}
        )
        await event_bus.publish(event)
        
        return True
    
    async def move_task(
        self,
        project_id: str,
        task_id: str,
        new_status: TaskStatus,
        notify: bool = True
    ) -> bool:
        """Move a task to a new status column"""
        if project_id not in self._boards:
            logger.warning(f"Board not found for project {project_id}")
            return False
        
        board = self._boards[project_id]
        tasks = self._tasks.get(project_id, {})
        
        if task_id not in tasks:
            logger.warning(f"Task {task_id} not found")
            return False
        
        task = tasks[task_id]
        old_status = task.status
        
        # Check dependencies for blocked status
        if new_status != TaskStatus.BLOCKED:
            for dep_id in task.depends_on:
                if dep_id in tasks and tasks[dep_id].status != TaskStatus.DONE:
                    logger.info(f"Task {task_id} blocked by dependency {dep_id}")
                    new_status = TaskStatus.BLOCKED
                    break
        
        # Move on board
        board.move_task(task_id, new_status)
        
        # Update task
        task.status = new_status
        task.updated_at = datetime.now()
        if new_status == TaskStatus.DONE:
            task.completed_at = datetime.now()
        
        # Record history
        self._history[project_id].append({
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "old_status": old_status.value,
            "new_status": new_status.value
        })
        
        # Save and notify
        await self._save_board(project_id)
        
        if notify:
            msg_payload = {
                "type": "task_moved",
                "task_id": task_id,
                "task_title": task.title,
                "old_status": old_status.value,
                "new_status": new_status.value,
                "timestamp": datetime.now().isoformat()
            }
            
            # Broadcast to board-specific websockets
            await self._broadcast(project_id, msg_payload)
            
            # Also publish to global event bus for activity stream
            event = Event(
                type=EventType.TASK_MOVED,
                project_id=project_id,
                task_id=task_id,
                payload=msg_payload,
                metadata={"title": task.title, "from": old_status.value, "to": new_status.value}
            )
            await event_bus.publish(event)
        
        # Check if this unblocks other tasks
        await self._check_unblock_dependents(project_id, task_id, new_status)
        
        return True
    
    async def _check_unblock_dependents(self, project_id: str, completed_task_id: str, status: TaskStatus):
        """Check and unblock tasks that depended on the completed task"""
        if status != TaskStatus.DONE:
            return
        
        tasks = self._tasks.get(project_id, {})
        
        for task_id, task in tasks.items():
            if task.status == TaskStatus.BLOCKED and completed_task_id in task.depends_on:
                # Check if all dependencies are now done
                all_deps_done = all(
                    tasks[dep_id].status == TaskStatus.DONE
                    for dep_id in task.depends_on
                    if dep_id in tasks
                )
                
                if all_deps_done:
                    await self.move_task(project_id, task_id, TaskStatus.TODO)
                    logger.info(f"Task {task_id} unblocked")
    
    async def _save_board(self, project_id: str) -> None:
        """Persist board state to disk"""
        storage_dir = self._get_storage_dir(project_id)
        
        # Save board state
        board_file = storage_dir / "board_state.json"
        if project_id in self._boards:
            with open(board_file, 'w', encoding='utf-8') as f:
                json.dump(self._boards[project_id].model_dump(), f, indent=2)
        
        # Save history
        history_file = storage_dir / "task_history.json"
        if project_id in self._history:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self._history[project_id], f, indent=2)
    
    async def load_board(self, project_id: str) -> Optional[BoardState]:
        """Load board state from disk"""
        storage_dir = self._get_storage_dir(project_id)
        board_file = storage_dir / "board_state.json"
        
        if not board_file.exists():
            return None
        
        try:
            with open(board_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            board = BoardState(**data)
            self._boards[project_id] = board
            return board
        except Exception as e:
            logger.exception(f"Failed to load board: {e}")
            return None
    
    def get_board(self, project_id: str) -> Optional[BoardState]:
        """Get board state for a project"""
        return self._boards.get(project_id)
    
    def get_tasks(self, project_id: str) -> Dict[str, Task]:
        """Get all tasks for a project"""
        return self._tasks.get(project_id, {})
    
    def get_metrics(self, project_id: str) -> ProjectMetrics:
        """Calculate project metrics"""
        tasks = self._tasks.get(project_id, {})
        board = self._boards.get(project_id)
        
        if not tasks or not board:
            return ProjectMetrics(project_id=project_id)
        
        total_points = sum(t.story_points for t in tasks.values())
        done_points = sum(
            t.story_points for t in tasks.values()
            if t.status == TaskStatus.DONE
        )
        blocked_count = len(board.blocked)
        
        progress = int((done_points / total_points * 100)) if total_points > 0 else 0
        
        return ProjectMetrics(
            project_id=project_id,
            current_sprint=1,
            total_sprints=1,
            progress_percent=progress,
            velocity=done_points,
            points_completed=done_points,
            points_remaining=total_points - done_points,
            blocked_count=blocked_count
        )
    
    # WebSocket management
    def add_websocket(self, project_id: str, ws: WebSocket):
        """Register a WebSocket for a project"""
        if project_id not in self._websockets:
            self._websockets[project_id] = set()
        self._websockets[project_id].add(ws)
    
    def remove_websocket(self, project_id: str, ws: WebSocket):
        """Unregister a WebSocket"""
        if project_id in self._websockets:
            self._websockets[project_id].discard(ws)
    
    async def _broadcast(self, project_id: str, message: dict):
        """Broadcast message to all WebSockets for a project"""
        if project_id not in self._websockets:
            return
        
        msg_str = json.dumps(message)
        for ws in list(self._websockets[project_id]):
            try:
                await ws.send_text(msg_str)
            except Exception:
                self._websockets[project_id].discard(ws)


# Global instance
board_tracker = BoardTracker()
