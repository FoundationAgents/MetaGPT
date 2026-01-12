from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from metagpt.api.orchestrator import orchestrator
from metagpt.api.schemas import ProjectRequest, CompanyStatus
from metagpt.roles.scrum_role import SCRUMRole

router = APIRouter()


class AgentActivity(BaseModel):
    name: str
    profile: str
    project_id: Optional[str] = None
    current_task: Optional[str] = None
    sprint: Optional[str] = None
    is_idle: bool = True
    messages_received: int = 0
    messages_sent: int = 0
    recent_messages: List[Dict] = []
    status: str = "idle"
    current_action: Optional[str] = None


class TeamActivity(BaseModel):
    status: str
    is_running: bool
    agents: List[AgentActivity]
    total_messages: int = 0


@router.post("/hire")
async def hire_team():
    """Initialize or Reset the Virtual Company Team"""
    orchestrator.hire()
    return {"message": "Team has been hired and is ready for work."}

@router.post("/run")
async def run_project(req: ProjectRequest):
    """Submit a new project/requirement to the company"""
    try:
        await orchestrator.start_project(req)
        return {"message": "Project started successfully.", "project": req.project_name}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/stop")
async def stop_project():
    """Stop the current project execution"""
    await orchestrator.stop()
    return {"message": "Project execution stopped."}

@router.get("/status", response_model=CompanyStatus)
async def get_status():
    """Get the current detailed status of the company"""
    return orchestrator.get_status()

@router.get("/activity", response_model=TeamActivity)
async def get_team_activity():
    """Get detailed activity information for all agents"""
    if not orchestrator.team:
        return TeamActivity(
            status="not_hired",
            is_running=False,
            agents=[],
            total_messages=0
        )
    
    agents = []
    total_messages = 0
    
    for role in orchestrator.team.env.roles.values():
        # Get activity summary if role is a SCRUMRole
        activity_data = {
            "name": role.name,
            "profile": role.profile,
            "is_idle": role.is_idle,
            "status": "idle" if role.is_idle else "working",
            "current_action": str(role.rc.todo) if role.rc.todo else None,
        }
        
        if isinstance(role, SCRUMRole):
            summary = role.get_activity_summary()
            activity_data.update({
                "project_id": summary.get("project_id"),
                "current_task": summary.get("current_task"),
                "sprint": summary.get("sprint"),
                "messages_received": summary.get("messages_received", 0),
                "messages_sent": summary.get("messages_sent", 0),
                "recent_messages": summary.get("recent_messages_received", []) + 
                                   summary.get("recent_messages_sent", []),
            })
            total_messages += summary.get("messages_received", 0) + summary.get("messages_sent", 0)
        
        agents.append(AgentActivity(**activity_data))
    
    return TeamActivity(
        status=orchestrator.status,
        is_running=orchestrator.status == "running",
        agents=agents,
        total_messages=total_messages
    )

@router.get("/agents")
async def list_agents():
    """List all hired agents with their roles and capabilities"""
    if not orchestrator.team:
        return {"agents": [], "message": "No team hired yet. Call /company/hire first."}
    
    agents = []
    for role in orchestrator.team.env.roles.values():
        agent_info = {
            "name": role.name,
            "profile": role.profile,
            "goal": role.goal,
            "is_idle": role.is_idle,
            "actions": [a.__class__.__name__ for a in role.actions] if hasattr(role, 'actions') else [],
            "watching": [str(w) for w in role.rc.watch] if hasattr(role.rc, 'watch') and role.rc.watch else []
        }
        
        # Add SCRUM-specific info
        if isinstance(role, SCRUMRole):
            agent_info.update({
                "project_id": role.project_id,
                "sprint_id": role.sprint_id,
                "current_task_id": role.current_task_id
            })
        
        agents.append(agent_info)
    
    return {
        "agents": agents,
        "total": len(agents),
        "company_status": orchestrator.status
    }

@router.get("/history")
async def get_history():
    """Get the global message history of the company"""
    if not orchestrator.team:
        return []
    # return list of messages
    return [m.model_dump() for m in orchestrator.team.env.history.get()]

@router.get("/plan")
async def get_plan():
    """Get the current project plan (WBS/Tasks)"""
    plan = await orchestrator.get_plan()
    if not plan:
        return {"message": "Plan not available yet or no project running."}
    return plan
