import asyncio
from pathlib import Path
from metagpt.project.state_manager import state_manager
from metagpt.project.backlog_manager import BacklogManager
from metagpt.project.board_tracker import board_tracker
from metagpt.project.schemas import TaskStatus
from metagpt.roles.scrum.product_owner import ProductOwner
from metagpt.roles.scrum.scrum_master import ScrumMaster
from metagpt.roles.scrum.engineer import Engineer
from metagpt.schema import Message
from metagpt.actions import UserRequirement

async def test_scrum_workflow():
    project_name = "integration_test_project"
    
    import traceback
    try:
        # 1. Project Creation
        print(f"\n[Test] Creating project: {project_name}")
        project = await state_manager.create_project(project_name, "Test Description")
        assert project is not None
        assert project.id.startswith("proj_")
        project_id = project.id
        
        # 2. Product Owner Refines Backlog
        print(f"[Test] PO Refining Backlog for {project_id}")
        po = ProductOwner(project_id=project_id)
        
        # Simulate User Requirement
        req = Message(content="Build a login system with Google Auth.", cause_by=UserRequirement)
        po.put_message(req)
        
        # Run PO
        await po.run()
        
        # Verify Backlog
        backlog_mgr = BacklogManager(project_id)
        await backlog_mgr.load()
        backlog = backlog_mgr.get_backlog()
        assert len(backlog.epics) > 0
        assert len(backlog.stories) > 0
        assert len(backlog.tasks) > 0
        print(f"[Verified] Backlog has {len(backlog.tasks)} tasks.")
        
        # 3. Scrum Master Conducts Standup
        print(f"[Test] SM Conducting Standup")
        sm = ScrumMaster(project_id=project_id)
        sm.put_message(Message(content="Time for standup", cause_by=UserRequirement))
        
        await sm.run()
        # (Verification is checking logs/output, simpler here)
        
        # 4. Engineer Pick/Update Task
        print(f"[Test] Engineer Updating Task")
        # Get a task ID
        task_id = list(backlog.tasks.keys())[0]
        
        eng = Engineer(project_id=project_id)
        # Force action: Engineer actions are usually triggered by messages or todo check
        # We simulate the action run directly
        update_action = list(eng.actions)[0] # Assuming UpdateTaskStatus is first or we instantiate it
        # Actually Engineer has UpdateTaskStatus. We can instantiate it.
        from metagpt.actions.update_task_status import UpdateTaskStatus
        action = UpdateTaskStatus(project_id=project_id)
        await action.run(task_id=task_id, status=TaskStatus.IN_PROGRESS)
        
        # Verify Board
        board_state = board_tracker.get_board(project_id)
        assert task_id in board_state.in_progress
        print(f"[Verified] Task {task_id} moved to IN_PROGRESS.")
        
        print(f"[Success] All test steps completed.")

    except Exception as e:
        print(f"[Error] Test failed: {e}")
        traceback.print_exc()
        raise e

if __name__ == "__main__":
    asyncio.run(test_scrum_workflow())
