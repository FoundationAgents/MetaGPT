#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/01/10
@Author  : MetaGPT-Pro Team
@File    : backlog_manager.py
@Desc    : Manages project backlog, priorities, and persistence
"""
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from metagpt.logs import logger
from metagpt.const import DEFAULT_WORKSPACE_ROOT
from metagpt.project.schemas import (
    Epic, Story, Task, Backlog, Sprint, TaskStatus, Priority
)


class BacklogManager:
    """Manages the project backlog with persistence"""
    
    def __init__(self, project_id: str, storage_root: Path = None):
        self.project_id = project_id
        self.storage_root = storage_root or DEFAULT_WORKSPACE_ROOT / "projects" / project_id
        self.storage_root.mkdir(parents=True, exist_ok=True)
        
        self._backlog: Optional[Backlog] = None
        self._sprints: List[Sprint] = []
    
    @property
    def backlog_file(self) -> Path:
        return self.storage_root / "backlog.json"
    
    @property
    def sprints_dir(self) -> Path:
        sprints_path = self.storage_root / "sprints"
        sprints_path.mkdir(parents=True, exist_ok=True)
        return sprints_path
    
    async def initialize(
        self,
        epics: Dict[str, Epic],
        stories: Dict[str, Story],
        tasks: Dict[str, Task]
    ) -> Backlog:
        """Initialize backlog with breakdown data"""
        self._backlog = Backlog(
            project_id=self.project_id,
            epics=epics,
            stories=stories,
            tasks=tasks,
            priority_order=self._calculate_priority_order(stories)
        )
        
        await self.save()
        return self._backlog
    
    def _calculate_priority_order(self, stories: Dict[str, Story]) -> List[str]:
        """Sort stories by priority"""
        priority_map = {
            Priority.CRITICAL: 0,
            Priority.HIGH: 1,
            Priority.MEDIUM: 2,
            Priority.LOW: 3
        }
        
        sorted_stories = sorted(
            stories.values(),
            key=lambda s: (priority_map.get(s.priority, 2), -s.story_points)
        )
        return [s.id for s in sorted_stories]
    
    async def save(self) -> None:
        """Persist backlog to disk"""
        if not self._backlog:
            return
        
        data = {
            "project_id": self._backlog.project_id,
            "epics": {k: v.model_dump() for k, v in self._backlog.epics.items()},
            "stories": {k: v.model_dump() for k, v in self._backlog.stories.items()},
            "tasks": {k: v.model_dump() for k, v in self._backlog.tasks.items()},
            "priority_order": self._backlog.priority_order
        }
        
        with open(self.backlog_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.debug(f"Backlog saved to {self.backlog_file}")
    
    async def load(self) -> Optional[Backlog]:
        """Load backlog from disk"""
        if not self.backlog_file.exists():
            return None
        
        try:
            with open(self.backlog_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._backlog = Backlog(
                project_id=data["project_id"],
                epics={k: Epic(**v) for k, v in data.get("epics", {}).items()},
                stories={k: Story(**v) for k, v in data.get("stories", {}).items()},
                tasks={k: Task(**v) for k, v in data.get("tasks", {}).items()},
                priority_order=data.get("priority_order", [])
            )
            return self._backlog
        except Exception as e:
            logger.exception(f"Failed to load backlog: {e}")
            return None
    
    async def save_sprints(self, sprints: List[Sprint]) -> None:
        """Persist sprints to disk"""
        self._sprints = sprints
        
        for sprint in sprints:
            sprint_file = self.sprints_dir / f"sprint_{sprint.number}.json"
            with open(sprint_file, 'w', encoding='utf-8') as f:
                json.dump(sprint.model_dump(), f, indent=2, default=str)
        
        # Save current sprint number
        current_file = self.sprints_dir / "current.txt"
        with open(current_file, 'w') as f:
            f.write("1")
        
        logger.debug(f"Saved {len(sprints)} sprints")
    
    async def load_sprints(self) -> List[Sprint]:
        """Load sprints from disk"""
        sprints = []
        
        for sprint_file in sorted(self.sprints_dir.glob("sprint_*.json")):
            try:
                with open(sprint_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                sprints.append(Sprint(**data))
            except Exception as e:
                logger.warning(f"Failed to load {sprint_file}: {e}")
        
        self._sprints = sprints
        return sprints
    
    async def get_current_sprint(self) -> int:
        """Get current sprint number"""
        current_file = self.sprints_dir / "current.txt"
        if current_file.exists():
            return int(current_file.read_text().strip())
        return 1
    
    async def set_current_sprint(self, sprint_num: int) -> None:
        """Set current sprint number"""
        current_file = self.sprints_dir / "current.txt"
        current_file.write_text(str(sprint_num))
    
    def get_backlog(self) -> Optional[Backlog]:
        """Get cached backlog"""
        return self._backlog
    
    def get_sprints(self) -> List[Sprint]:
        """Get cached sprints"""
        return self._sprints
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID"""
        if self._backlog and task_id in self._backlog.tasks:
            return self._backlog.tasks[task_id]
        return None
    
    async def update_task_status(self, task_id: str, status: TaskStatus) -> bool:
        """Update a task's status"""
        if not self._backlog or task_id not in self._backlog.tasks:
            return False
        
        task = self._backlog.tasks[task_id]
        task.status = status
        task.updated_at = datetime.now()
        
        if status == TaskStatus.DONE:
            task.completed_at = datetime.now()
        
        # Update parent story if all tasks done
        if task.parent_story and task.parent_story in self._backlog.stories:
            story = self._backlog.stories[task.parent_story]
            all_done = all(
                self._backlog.tasks[tid].status == TaskStatus.DONE
                for tid in story.tasks
                if tid in self._backlog.tasks
            )
            if all_done:
                story.status = TaskStatus.DONE
        
        await self.save()
        return True
    
        self._backlog.priority_order.remove(story_id)
        self._backlog.priority_order.insert(new_index, story_id)
        return True

    async def add_story(self, title: str, description: str, priority: Priority) -> Story:
        """Add a new user story to the backlog"""
        if not self._backlog:
            # Initialize empty backlog if needed
            self._backlog = Backlog(project_id=self.project_id)
        
        story = Story(
            title=title,
            description=description,
            priority=priority,
            status=TaskStatus.TODO
        )
        
        self._backlog.stories[story.id] = story
        self._backlog.priority_order.append(story.id)
        
        await self.save()
        return story

    async def add_task(self, title: str, description: str, priority: Priority, type: str = "task", parent_story_id: Optional[str] = None) -> Task:
        """Add a new task or bug to the backlog"""
        if not self._backlog:
            self._backlog = Backlog(project_id=self.project_id)
            
        task = Task(
            title=title,
            description=description,
            type=type, # task, bug
            status=TaskStatus.TODO,
            parent_story=parent_story_id
        )
        
        self._backlog.tasks[task.id] = task
        
        # Link to story if parent provided
        if parent_story_id and parent_story_id in self._backlog.stories:
            self._backlog.stories[parent_story_id].tasks.append(task.id)
            
        await self.save()
        
        # Also add to Board? Yes, if it's actionable.
        # We need to import board_tracker strictly or assume caller handles it.
        # But to be safe, let's keep BacklogManager focused on storage 
        # and let the Controller (project.py) handle Board sync to avoid circular imports?
        # Actually board_tracker is a singleton imported in project.py.
        # So we leave board sync to project.py.
        
        return task
