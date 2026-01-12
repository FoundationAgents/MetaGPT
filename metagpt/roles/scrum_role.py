#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/01/12
@Author  : MetaGPT-Pro Team
@File    : scrum_role.py
@Desc    : Base Role class for SCRUM Agents with Event System Integration
"""
import asyncio
from typing import Optional, Dict, Any, List

from metagpt.roles.role import Role
from metagpt.schema import Message
from metagpt.logs import logger
from metagpt.project.event_system import event_bus, Event, EventType
from metagpt.project.state_manager import state_manager


class SCRUMRole(Role):
    """
    Base class for all SCRUM agents.
    Adds automatic event broadcasting, project context awareness,
    and enhanced inter-agent communication.
    """
    
    project_id: str = "default_project"
    sprint_id: Optional[str] = None
    current_task_id: Optional[str] = None
    _messages_received: List[Dict] = []
    _messages_sent: List[Dict] = []
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._messages_received = []
        self._messages_sent = []
        # Ensure project_id is set if passed in kwargs, else default
        if "project_id" in kwargs:
            self.project_id = kwargs["project_id"]
            
    async def run(self, with_message=None):
        """Override run to broadcast start/stop events"""
        await self._broadcast_event(
            EventType.AGENT_STARTED,
            payload={"action": "Starting agent execution"}
        )
        
        try:
            rsp = await super().run(with_message)
            await self._broadcast_event(
                EventType.AGENT_COMPLETED,
                payload={"action": "Agent execution completed", "result_preview": str(rsp)[:200] if rsp else None}
            )
            return rsp
        except Exception as e:
            await self._broadcast_event(EventType.AGENT_ERROR, payload={"error": str(e)})
            raise e

    async def _think(self) -> bool:
        """Override think to broadcast status"""
        await self._broadcast_event(
            EventType.AGENT_THINKING,
            payload={"action": "Analyzing situation and deciding next action"}
        )
        result = await super()._think()
        
        # Fix: Role._think might return True even if state is -1 (todo is None)
        # Return False if todo is None to stop the loop in Role._react
        if self.rc.todo is None:
            await self._broadcast_event(
                EventType.AGENT_WAITING,
                payload={"action": "No pending tasks - waiting for work"}
            )
            return False
            
        # Broadcast what we decided to do
        await self._broadcast_event(
            EventType.AGENT_THINKING,
            payload={
                "action": f"Decided next action: {self.rc.todo.__class__.__name__}",
                "next_action": str(self.rc.todo)
            }
        )
        return result

    async def _act(self) -> Message:
        """Override act to broadcast status and track task progress"""
        action_name = self.rc.todo.__class__.__name__ if self.rc.todo else "Unknown"
        
        await self._broadcast_event(
            EventType.AGENT_ACTING,
            payload={
                "action": f"Executing: {action_name}",
                "todo": str(self.rc.todo),
                "task_id": self.current_task_id
            }
        )
        
        result = await super()._act()
        
        # Broadcast completion of action
        await self._broadcast_event(
            EventType.AGENT_ACTING, 
            payload={
                "action": f"Completed: {action_name}",
                "result_preview": str(result.content)[:200] if result and hasattr(result, 'content') else None
            }
        )
        
        return result
    
    async def _observe(self) -> int:
        """Override observe to track messages received"""
        count = await super()._observe()
        
        if count > 0 and self.rc.news:
            # Log received messages
            for msg in self.rc.news:
                msg_info = {
                    "from": msg.sent_from if hasattr(msg, 'sent_from') else msg.role,
                    "content_preview": str(msg.content)[:100] if msg.content else None,
                    "cause_by": str(msg.cause_by)
                }
                self._messages_received.append(msg_info)
                
                await self._broadcast_event(
                    EventType.AGENT_ACTING,
                    payload={
                        "action": f"Received message from {msg_info['from']}",
                        "message_from": msg_info['from'],
                        "message_preview": msg_info['content_preview']
                    }
                )
        
        return count

    async def _broadcast_event(self, event_type: EventType, payload: Dict[str, Any] = None):
        """Helper to broadcast agent events with rich context"""
        if not payload:
            payload = {}
        
        # Add comprehensive agent context
        payload.update({
            "name": self.name,
            "profile": self.profile,
            "goal": self.goal,
            "sprint_id": self.sprint_id,
            "current_task": self.current_task_id,
            "is_idle": self.is_idle,
            "state": self.rc.state,
            "todo": str(self.rc.todo) if self.rc.todo else None,
        })
        
        # Format for frontend consumption
        event = Event(
            type=event_type,
            project_id=self.project_id,
            agent_id=self.profile,
            task_id=self.current_task_id,
            sprint_id=self.sprint_id,
            payload=payload
        )
        
        try:
            await event_bus.publish(event)
        except Exception as e:
            logger.warning(f"Failed to broadcast event: {e}")

    async def send_message_to_agent(self, target_agent: str, message_content: str, request_type: str = "info"):
        """
        Send a message to another agent (inter-agent communication).
        
        Args:
            target_agent: Name or profile of the target agent
            message_content: The message to send
            request_type: Type of request (info, help, handoff, etc.)
        """
        msg_info = {
            "to": target_agent,
            "content": message_content,
            "type": request_type
        }
        self._messages_sent.append(msg_info)
        
        # Broadcast the communication
        await self._broadcast_event(
            EventType.AGENT_ACTING,
            payload={
                "action": f"Sending {request_type} message to {target_agent}",
                "message_to": target_agent,
                "message_type": request_type,
                "message_preview": message_content[:100]
            }
        )
        
        # Create and publish message through environment
        if self.rc.env:
            msg = Message(
                content=message_content,
                role=self.profile,
                cause_by=f"inter_agent_{request_type}",
                sent_from=self.name,
                send_to=target_agent
            )
            self.rc.env.publish_message(msg)
            
    async def request_help(self, from_agent: str, topic: str):
        """Request help from another agent"""
        await self.send_message_to_agent(
            from_agent, 
            f"Need assistance with: {topic}",
            request_type="help"
        )
        
    async def handoff_task(self, to_agent: str, task_id: str, context: str):
        """Hand off a task to another agent"""
        await self._broadcast_event(
            EventType.TASK_ASSIGNED,
            payload={
                "action": f"Handing off task {task_id} to {to_agent}",
                "task_id": task_id,
                "assigned_to": to_agent,
                "context": context[:200]
            }
        )
        
        await self.send_message_to_agent(
            to_agent,
            f"Task handoff: {task_id}\nContext: {context}",
            request_type="handoff"
        )

    async def complete_task(self, task_id: str, result: str = None):
        """Mark a task as complete and broadcast the event"""
        self.current_task_id = None
        
        await self._broadcast_event(
            EventType.TASK_COMPLETED,
            payload={
                "action": f"Task {task_id} completed",
                "task_id": task_id,
                "result_preview": result[:200] if result else None,
                "completed_by": self.name
            }
        )
        
        logger.info(f"{self.profile} ({self.name}) completed task {task_id}")

    async def start_task(self, task_id: str, task_title: str = None):
        """Start working on a task and broadcast the event"""
        self.current_task_id = task_id
        
        await self._broadcast_event(
            EventType.TASK_STARTED,
            payload={
                "action": f"Starting task: {task_title or task_id}",
                "task_id": task_id,
                "task_title": task_title,
                "assigned_to": self.name
            }
        )
        
        logger.info(f"{self.profile} ({self.name}) started task {task_id}")

    async def report_blocker(self, task_id: str, blocker_description: str):
        """Report a blocker on a task"""
        await self._broadcast_event(
            EventType.TASK_BLOCKED,
            payload={
                "action": f"Task {task_id} is blocked",
                "task_id": task_id,
                "blocker": blocker_description,
                "reported_by": self.name
            }
        )
        
        # Also notify Scrum Master
        await self.send_message_to_agent(
            "Scrum Master",
            f"Blocker on task {task_id}: {blocker_description}",
            request_type="blocker"
        )

    def get_activity_summary(self) -> Dict[str, Any]:
        """Get a summary of this agent's activity for reporting"""
        return {
            "name": self.name,
            "profile": self.profile,
            "project_id": self.project_id,
            "current_task": self.current_task_id,
            "sprint": self.sprint_id,
            "is_idle": self.is_idle,
            "messages_received": len(self._messages_received),
            "messages_sent": len(self._messages_sent),
            "recent_messages_received": self._messages_received[-5:],
            "recent_messages_sent": self._messages_sent[-5:]
        }

    async def persist_state(self):
        """Manually trigger state persistence"""
        # TODO: Implement granular state saving to project directory
        pass
