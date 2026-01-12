#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/01/10
@Author  : MetaGPT-Pro Team
@File    : schemas.py
@Desc    : Pydantic schemas for Sprint/Backlog System
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import uuid


class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    TESTING = "testing"
    DONE = "done"
    BLOCKED = "blocked"


class ProjectStatus(str, Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ExecutionMode(str, Enum):
    AUTONOMOUS = "autonomous"
    HYBRID = "hybrid"
    INTERACTIVE = "interactive"


class ProjectMetadata(BaseModel):
    id: str
    name: str
    description: str = ""
    status: ProjectStatus = ProjectStatus.PLANNING
    mode: ExecutionMode = ExecutionMode.HYBRID
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    owner: Optional[str] = None
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class TaskType(str, Enum):
    EPIC = "epic"
    STORY = "story"
    TASK = "task"
    BUG = "bug"


class Priority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


STORY_POINTS = [1, 2, 3, 5, 8, 13, 21]


class Task(BaseModel):
    id: str = Field(default_factory=lambda: f"TASK-{uuid.uuid4().hex[:6].upper()}")
    title: str
    description: str = ""
    type: TaskType = TaskType.TASK
    story_points: int = 2
    status: TaskStatus = TaskStatus.TODO
    assigned_to: Optional[str] = None
    parent_story: Optional[str] = None
    depends_on: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class Story(BaseModel):
    id: str = Field(default_factory=lambda: f"STORY-{uuid.uuid4().hex[:6].upper()}")
    title: str
    description: str = ""
    priority: Priority = Priority.MEDIUM
    story_points: int = 5
    status: TaskStatus = TaskStatus.TODO
    tasks: List[str] = Field(default_factory=list)
    acceptance_criteria: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class Epic(BaseModel):
    id: str = Field(default_factory=lambda: f"EPIC-{uuid.uuid4().hex[:6].upper()}")
    title: str
    description: str = ""
    stories: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class Sprint(BaseModel):
    number: int
    name: str
    duration_days: int = 7
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    goals: List[str] = Field(default_factory=list)
    tasks: List[str] = Field(default_factory=list)
    total_points: int = 0
    completed_points: int = 0
    
    @property
    def progress_percent(self) -> int:
        if self.total_points == 0:
            return 0
        return int((self.completed_points / self.total_points) * 100)
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class Backlog(BaseModel):
    project_id: str
    epics: Dict[str, Epic] = Field(default_factory=dict)
    stories: Dict[str, Story] = Field(default_factory=dict)
    tasks: Dict[str, Task] = Field(default_factory=dict)
    priority_order: List[str] = Field(default_factory=list)
    
    @property
    def total_points(self) -> int:
        return sum(s.story_points for s in self.stories.values())
    
    @property
    def completed_points(self) -> int:
        return sum(s.story_points for s in self.stories.values() if s.status == TaskStatus.DONE)


class BoardState(BaseModel):
    project_id: str
    todo: List[str] = Field(default_factory=list)
    in_progress: List[str] = Field(default_factory=list)
    review: List[str] = Field(default_factory=list)
    testing: List[str] = Field(default_factory=list)
    done: List[str] = Field(default_factory=list)
    blocked: List[str] = Field(default_factory=list)
    
    def get_tasks_by_status(self, status: TaskStatus) -> List[str]:
        return getattr(self, status.value, [])
    
    def move_task(self, task_id: str, new_status: TaskStatus) -> bool:
        for status in TaskStatus:
            column = getattr(self, status.value, [])
            if task_id in column:
                column.remove(task_id)
                break
        target_column = getattr(self, new_status.value, [])
        if task_id not in target_column:
            target_column.append(task_id)
        return True


class ProjectMetrics(BaseModel):
    project_id: str
    current_sprint: int = 1
    total_sprints: int = 1
    progress_percent: int = 0
    velocity: float = 0.0
    points_completed: int = 0
    points_remaining: int = 0
    blocked_count: int = 0
    estimated_completion: Optional[str] = None
    # Task counts
    tasks_done: int = 0
    tasks_in_progress: int = 0
    tasks_remaining: int = 0


class TaskMoveRequest(BaseModel):
    task_id: str
    new_status: TaskStatus


class TaskMoveResponse(BaseModel):
    updated: bool
    task_id: str
    new_status: str
    message: str = ""


class SprintResponse(BaseModel):
    sprint_num: int
    name: str
    tasks: List[Task]
    progress: int
    goals: List[str]


class BacklogResponse(BaseModel):
    stories: List[Story]
    total_points: int
    priority_order: List[str]


class BoardResponse(BaseModel):
    todo: List[Task]
    in_progress: List[Task]
    review: List[Task]
    testing: List[Task]
    done: List[Task]
    blocked: List[Task]
