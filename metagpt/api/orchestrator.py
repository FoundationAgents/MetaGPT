import asyncio
from typing import Optional
from metagpt.team import Team
from metagpt.config2 import config
from metagpt.logs import logger
from metagpt.api.schemas import CompanyStatus, RoleStatus, ProjectRequest
from metagpt.project.state_manager import state_manager
from metagpt.project.event_system import event_bus, Event, EventType

class GlobalOrchestrator:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GlobalOrchestrator, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.team: Optional[Team] = None
        self.running_task: Optional[asyncio.Task] = None
        self._status = "idle"
        self._initialized = True

    @property
    def status(self) -> str:
        if self.running_task and not self.running_task.done():
            return "running"
        return "idle"

    def hire(self, roles: list = None):
        """Initialize a new company team with SCRUM agents"""
        # CRITICAL: Use use_mgx=False to avoid MGXEnv which requires a "Mike" TeamLeader role
        # Standard Environment works with any roles without special requirements
        self.team = Team(use_mgx=False)
        self.team.hire(roles or [])
        
        # Hire our custom SCRUM agents if no roles provided
        if not self.team.env.get_roles():
            from metagpt.roles.scrum.product_owner import ProductOwner
            from metagpt.roles.scrum.scrum_master import ScrumMaster
            from metagpt.roles.scrum.architect import Architect
            from metagpt.roles.scrum.engineer import Engineer
            from metagpt.roles.scrum.qa_engineer import QAEngineer
            
            scrum_team = [
                ProductOwner(),  # Alice - manages backlog
                ScrumMaster(),   # Bob - facilitates ceremonies
                Architect(),     # (uses default name) - system design
                Engineer(),      # Alex - implements features
                QAEngineer(),    # Charlie - writes tests
            ]
            self.team.hire(scrum_team)
            logger.info(f"Hired SCRUM team: {[r.name for r in scrum_team]}")
        logger.info("New Team hired.")

    async def start_project(self, req: ProjectRequest):
        if self.status == "running":
            raise ValueError("Company is already running a project.")
        
        requirement_text = req.requirement
        
        # Determine project_id with proper precedence
        if req.project_name:
            project_id = req.project_name
        elif req.conversation_id:
            project_id = req.conversation_id.replace("conv_", "proj_")
        else:
            project_id = "default_project"
        
        try:
            # 1. Initialize Persistent Project State
            project_meta = await state_manager.create_project(
                name=project_id,
                description=f"Project derived from conversation {req.conversation_id}",
            )
            # Reassign project_id to ensure consistency (though usually same)
            project_id = project_meta.id
            
            # Check if using pre-approved requirements from conversation
            if req.conversation_id:
                from metagpt.conversation import conversation_manager
                approved_text = await conversation_manager.get_approved_requirement_text(req.conversation_id)
                if approved_text:
                    requirement_text = approved_text
                    logger.info(f"Using approved requirements from conversation {req.conversation_id}")
            
            # 2. Handle Project Name config updates
            if req.project_name:
                config.update_via_cli(
                    project_path=req.project_name, 
                    project_name=req.project_name, 
                    inc=True, 
                    reqa_file="", 
                    max_auto_summarize_code=0
                )
            
            # 3. Generate Task Breakdown & Sprint Plan
            # Pass persistence-aware project_id
            await self._initialize_project_management(project_id, requirement_text)
            
            if not self.team:
                self.hire()

            # 4. Hook Environment for Real-time structured events
            self._hook_environment(project_id)

            self.team.invest(req.investment)
            self.team.run_project(requirement_text)  # Use potentially enhanced requirement
        except Exception as e:
            logger.exception(f"Start Project failed: {e}")
            raise ValueError(f"Start Project failed at step: {e}")
        
        # Start background task
        self.running_task = asyncio.create_task(self._run_loop(req.n_round, project_id))
        logger.info(f"Project started: {project_id}")
    
    async def _initialize_project_management(self, project_id: str, requirements: str):
        """Initialize task breakdown, sprints, and Kanban board"""
        try:
            from metagpt.project.task_breakdown import TaskBreakdownGenerator
            from metagpt.project.sprint_planner import SprintPlanner
            from metagpt.project.backlog_manager import BacklogManager
            from metagpt.project.board_tracker import board_tracker
            
            # 1. Generate task breakdown
            generator = TaskBreakdownGenerator()
            breakdown = await generator.generate(requirements)
            
            # 2. Initialize backlog
            manager = BacklogManager(project_id)
            await manager.initialize(
                epics=breakdown["epics"],
                stories=breakdown["stories"],
                tasks=breakdown["tasks"]
            )
            
            # 3. Create sprints
            planner = SprintPlanner()
            sprints = planner.create_sprints(
                tasks=breakdown["tasks"],
                stories=breakdown["stories"]
            )
            await manager.save_sprints(sprints)
            
            # 4. Initialize board
            await board_tracker.initialize_board(project_id, breakdown["tasks"])
            
            logger.info(f"Project management initialized for {project_id}")
        except Exception as e:
            logger.warning(f"Failed to initialize project management: {e}")
            # Non-fatal - continue with standard workflow

    def _hook_environment(self, project_id: str):
        if hasattr(self.team.env, "_is_hooked") and self.team.env._is_hooked:
            return
            
        original_publish = self.team.env.publish_message
        
        def new_publish(*args, **kwargs):
            # args[0] is typically the message
            if args:
                message = args[0]
                if hasattr(message, 'content'):
                    # Emit structured event
                    asyncio.create_task(event_bus.publish(Event(
                        type=EventType.AGENT_ACTING,
                        project_id=project_id,
                        agent_id=message.role,
                        payload={
                            "role": message.role,
                            "content": message.content,
                            "cause_by": str(message.cause_by),
                            "sent_from": message.sent_from
                        }
                    )))
            return original_publish(*args, **kwargs)
        
        object.__setattr__(self.team.env, "publish_message", new_publish)
        self.team.env._is_hooked = True

    async def _run_loop(self, n_round: int, project_id: str):
        try:
            self._status = "running"
            await self.team.run(n_round=n_round, idea=None)
            
            # Broadcast completion
            await event_bus.publish(Event(
                type=EventType.PROJECT_COMPLETED,
                project_id=project_id
            ))
        except Exception as e:
            logger.exception(f"Error in project run loop: {e}")
            await event_bus.publish(Event(
                type=EventType.SYSTEM_ERROR,
                project_id=project_id,
                payload={"error": str(e)}
            ))
        finally:
            self._status = "idle"

    async def stop(self):
        if self.running_task and not self.running_task.done():
            self.running_task.cancel()
            try:
                await self.running_task
            except asyncio.CancelledError:
                pass
            logger.info("Project stopped manually.")

    def get_status(self) -> CompanyStatus:
        if not self.team:
             return CompanyStatus(status="not_hired", roles=[], is_idle=True)
        
        roles_status = []
        for role in self.team.env.roles.values():
            todo = role.rc.todo
            roles_status.append(RoleStatus(
                name=role.name,
                profile=role.profile,
                goal=role.goal,
                is_idle=role.is_idle,
                current_todo=str(todo) if todo else None
            ))
            
        return CompanyStatus(
            status=self.status,
            roles=roles_status,
            is_idle=self.team.env.is_idle
        )

    # Log Streaming Logic
    def _log_sink(self, message):
         # Broadcast raw log as System Info event
         # Note: logging sink is sync, need careful async handling
         # For simplicity, we might skip full Event wrapping for high-volume logs 
         # or fire-and-forget
         pass 

    def start_log_stream(self):
        # Deprecated: Loguru sink should likely be handled by EventSystem or global logger config
        pass

    def add_websocket(self, ws):
        # Backward compatibility wrapper
        event_bus.add_websocket(ws)

    def remove_websocket(self, ws):
        # Backward compatibility wrapper
        event_bus.remove_websocket(ws)

    async def get_plan(self):
        """Retrieve the current project plan/tasks from the generated file"""
        if not self.team:
            return None
        
        from metagpt.const import DEFAULT_WORKSPACE_ROOT
        import glob
        import os
        import json
        
        # Search for project_schedule.json
        search_path = DEFAULT_WORKSPACE_ROOT
        if config.project_name:
             search_path = search_path / config.project_name
        
        files = glob.glob(str(search_path / "**/project_schedule.json"), recursive=True)
        
        if files:
            latest_file = max(files, key=os.path.getmtime)
            try:
                with open(latest_file, 'r', encoding='utf-8') as f:
                     return json.load(f)
            except:
                return None
        return None

# Global Instance
orchestrator = GlobalOrchestrator()
