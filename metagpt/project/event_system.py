#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/01/12
@Author  : MetaGPT-Pro Team
@File    : event_system.py
@Desc    : Centralized event system for SCRUM Agents
"""
import asyncio
import json
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from fastapi import WebSocket
from pydantic import BaseModel, Field

from metagpt.const import DEFAULT_WORKSPACE_ROOT
from metagpt.logs import logger


class EventType(str, Enum):
    # Project Events
    PROJECT_CREATED = "project_created"
    PROJECT_UPDATED = "project_updated"
    PROJECT_COMPLETED = "project_completed"
    
    # Sprint Events
    SPRINT_PLANNED = "sprint_planned"
    SPRINT_STARTED = "sprint_started"
    SPRINT_COMPLETED = "sprint_completed"
    
    # Task Events
    TASK_CREATED = "task_created"
    TASK_ASSIGNED = "task_assigned"
    TASK_STARTED = "task_started"
    TASK_UPDATED = "task_updated"
    TASK_COMPLETED = "task_completed"
    TASK_VERIFIED = "task_verified"
    TASK_BLOCKED = "task_blocked"
    TASK_MOVED = "task_moved"
    
    # Agent Events
    AGENT_STARTED = "agent_started"
    AGENT_THINKING = "agent_thinking"
    AGENT_ACTING = "agent_acting"
    AGENT_WAITING = "agent_waiting"
    AGENT_COMPLETED = "agent_completed"
    AGENT_ERROR = "agent_error"
    
    # Human Events
    HUMAN_APPROVAL_REQUESTED = "human_approval_requested"
    HUMAN_APPROVAL_RECEIVED = "human_approval_received"
    HUMAN_INPUT_RECEIVED = "human_input_received"
    HUMAN_INTERVENTION = "human_intervention"
    
    # Artifact Events
    ARTIFACT_CREATED = "artifact_created"
    ARTIFACT_UPDATED = "artifact_updated"
    
    # System Events
    SYSTEM_ERROR = "system_error"
    SYSTEM_INFO = "system_info"


class Event(BaseModel):
    id: str = Field(default_factory=lambda: f"EVT-{uuid.uuid4().hex[:8]}")
    type: EventType
    timestamp: datetime = Field(default_factory=datetime.now)
    project_id: str
    sprint_id: Optional[str] = None
    task_id: Optional[str] = None
    agent_id: Optional[str] = None
    user_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class EventBus:
    """Singleton EventBus for broadcasting and persisting events"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventBus, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._websockets: Dict[str, Set[WebSocket]] = {}  # project_id -> websockets
        self._global_websockets: Set[WebSocket] = set()
        self._persistence_enabled = True
        self._log_root = DEFAULT_WORKSPACE_ROOT / "logs" / "events"
        self._log_root.mkdir(parents=True, exist_ok=True)
        self._initialized = True
        
    def add_websocket(self, ws: WebSocket, project_id: Optional[str] = None):
        """Register a WebSocket"""
        if project_id:
            if project_id not in self._websockets:
                self._websockets[project_id] = set()
            self._websockets[project_id].add(ws)
        else:
            self._global_websockets.add(ws)
            
    def remove_websocket(self, ws: WebSocket, project_id: Optional[str] = None):
        """Unregister a WebSocket"""
        if project_id and project_id in self._websockets:
            self._websockets[project_id].discard(ws)
        if ws in self._global_websockets:
            self._global_websockets.discard(ws)

    async def publish(self, event: Event):
        """Publish an event to all subscribers and persist only if persistence is enabled."""
        
        # 1. Persist (non-blocking if possible, but asyncio.to_thread is good for file IO)
        if self._persistence_enabled:
            await self._persist_event(event)

        # 2. Broadcast
        message = event.model_dump_json()
        
        # Project-specific subscribers
        if event.project_id in self._websockets:
            project_sockets = list(self._websockets[event.project_id])
            for ws in project_sockets:
                try:
                    await ws.send_text(message)
                except Exception:
                    self._websockets[event.project_id].discard(ws)
                    
        # Global subscribers
        global_sockets = list(self._global_websockets)
        for ws in global_sockets:
            try:
                await ws.send_text(message)
            except Exception:
                self._global_websockets.discard(ws)
                
        logger.debug(f"Event published: {event.type} [{event.id}]")

    async def _persist_event(self, event: Event):
        """Append event to detailed log file locally."""
        try:
            date_str = event.timestamp.strftime("%Y-%m-%d")
            log_file = self._log_root / f"{date_str}.jsonl"
            
            # Simple append mode
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(event.model_dump_json() + "\n")
                
        except Exception as e:
            logger.error(f"Failed to persist event {event.id}: {e}")

# Global instance
event_bus = EventBus()
