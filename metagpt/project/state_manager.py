#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/01/12
@Author  : MetaGPT-Pro Team
@File    : state_manager.py
@Desc    : Central coordination for project state and persistence
"""
import json
import uuid
import asyncio
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from metagpt.const import DEFAULT_WORKSPACE_ROOT
from metagpt.logs import logger
from metagpt.project.schemas import ProjectMetadata, ProjectStatus, ExecutionMode
from metagpt.project.backlog_manager import BacklogManager
from metagpt.project.board_tracker import board_tracker
from metagpt.project.event_system import event_bus, Event, EventType


class StateManager:
    """Singleton Manager for Global Project State"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StateManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._projects: Dict[str, ProjectMetadata] = {}
        self._root = DEFAULT_WORKSPACE_ROOT / "projects"
        self._root.mkdir(parents=True, exist_ok=True)
        self._initialized = True
        
    async def create_project(
        self, 
        name: str, 
        description: str = "", 
        mode: ExecutionMode = ExecutionMode.HYBRID
    ) -> ProjectMetadata:
        """Create a new project with initialized state"""
        
        # 1. Generate ID and Metadata
        project_id = f"proj_{uuid.uuid4().hex[:8]}"
        project = ProjectMetadata(
            id=project_id,
            name=name,
            description=description,
            mode=mode,
            status=ProjectStatus.PLANNING
        )
        
        # 2. Persist Metadata
        await self.save_project(project)
        self._projects[project_id] = project
        
        # 3. Initialize Sub-managers (Backlog, Board)
        # Note: We just ensure directories exist here. Logic for populating them is on-demand elsewhere or empty.
        # BacklogManager initializes its own folders on __init__
        BacklogManager(project_id) 
        
        # 4. Broadcast Event
        await event_bus.publish(Event(
            type=EventType.PROJECT_CREATED,
            project_id=project_id,
            payload=project.model_dump()
        ))
        
        logger.info(f"Created project {name} ({project_id})")
        return project

    async def get_project(self, project_id: str) -> Optional[ProjectMetadata]:
        """Get project metadata, loading from disk if needed"""
        if project_id in self._projects:
            return self._projects[project_id]
        
        # Try load from disk
        project = await self._load_project_from_disk(project_id)
        if project:
            self._projects[project_id] = project
            
        return project

    async def list_projects(self) -> List[ProjectMetadata]:
        """List all projects found in workspace"""
        projects = []
        
        # Scan directory
        if not self._root.exists():
            return []
            
        for project_dir in self._root.iterdir():
            if project_dir.is_dir():
                project_id = project_dir.name
                project = await self.get_project(project_id)
                if project:
                    projects.append(project)
                    
        # Sort by updated_at desc
        return sorted(projects, key=lambda p: p.updated_at, reverse=True)

    async def update_project(
        self, 
        project_id: str, 
        mode: Optional[ExecutionMode] = None,
        status: Optional[ProjectStatus] = None
    ) -> Optional[ProjectMetadata]:
        """Update project settings"""
        project = await self.get_project(project_id)
        if not project:
            return None
            
        updated = False
        if mode and mode != project.mode:
            project.mode = mode
            updated = True
            
        if status and status != project.status:
            project.status = status
            updated = True
            
        if updated:
            project.updated_at = datetime.now()
            await self.save_project(project)
            
            await event_bus.publish(Event(
                type=EventType.PROJECT_UPDATED,
                project_id=project_id,
                payload=project.model_dump()
            ))
            
        return project

    async def save_project(self, project: ProjectMetadata):
        """Persist project metadata"""
        project_dir = self._root / project.id
        project_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = project_dir / "project.json"
        
        # Use simple synchronous write for now, can be asyncified if needed
        data = project.model_dump()
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    async def _load_project_from_disk(self, project_id: str) -> Optional[ProjectMetadata]:
        """Load specific project json"""
        file_path = self._root / project_id / "project.json"
        if not file_path.exists():
            return None
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return ProjectMetadata(**data)
        except Exception as e:
            logger.error(f"Failed to load project {project_id}: {e}")
            return None

# Global instance
state_manager = StateManager()
