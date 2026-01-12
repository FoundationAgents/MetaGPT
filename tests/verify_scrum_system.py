#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Standalone test script for SCRUM components - no pytest required
"""
import sys
import asyncio
from datetime import datetime

# Add project to path
sys.path.insert(0, '.')

def test_schemas():
    """Test SCRUM schemas"""
    print("Testing SCRUM Schemas...")
    
    from metagpt.project.schemas import (
        Task, Story, Sprint, Epic, Backlog, TaskStatus, Priority, BoardState
    )
    
    # Test Task
    task = Task(title="Test Task", story_points=5)
    assert task.title == "Test Task"
    assert task.story_points == 5
    assert task.status == TaskStatus.TODO
    print("  ✓ Task creation")
    
    # Test Story
    story = Story(title="Test Story", priority=Priority.HIGH, story_points=8)
    assert story.priority == Priority.HIGH
    print("  ✓ Story creation")
    
    # Test Sprint
    sprint = Sprint(number=1, name="Sprint 1", total_points=20, completed_points=10)
    assert sprint.progress_percent == 50
    print("  ✓ Sprint creation and progress calculation")
    
    # Test BoardState
    board = BoardState(project_id="test", todo=["T-1", "T-2"])
    board.move_task("T-1", TaskStatus.IN_PROGRESS)
    assert "T-1" not in board.todo
    assert "T-1" in board.in_progress
    print("  ✓ BoardState task movement")
    
    # Test Backlog
    s1 = Story(id="S1", title="S1", story_points=5, status=TaskStatus.DONE)
    s2 = Story(id="S2", title="S2", story_points=8, status=TaskStatus.TODO)
    backlog = Backlog(project_id="test", stories={"S1": s1, "S2": s2})
    assert backlog.total_points == 13
    assert backlog.completed_points == 5
    print("  ✓ Backlog total/completed points")
    
    print("✅ All schema tests passed!\n")


def test_sprint_planner():
    """Test SprintPlanner"""
    print("Testing SprintPlanner...")
    
    from metagpt.project.sprint_planner import SprintPlanner
    from metagpt.project.schemas import Task
    
    tasks = {
        "T1": Task(id="T1", title="Task 1", story_points=5),
        "T2": Task(id="T2", title="Task 2", story_points=8),
        "T3": Task(id="T3", title="Task 3", story_points=3),
    }
    
    planner = SprintPlanner(velocity=10)
    sprints = planner.create_sprints(tasks, {})
    
    assert len(sprints) >= 1
    assert sprints[0].number == 1
    print(f"  ✓ Created {len(sprints)} sprints from 3 tasks")
    
    print("✅ SprintPlanner tests passed!\n")


async def test_backlog_manager():
    """Test BacklogManager"""
    print("Testing BacklogManager...")
    
    import tempfile
    from pathlib import Path
    from metagpt.project.backlog_manager import BacklogManager
    from metagpt.project.schemas import Epic, Story, Task, TaskStatus
    
    with tempfile.TemporaryDirectory() as tmp:
        manager = BacklogManager("test_project", storage_root=Path(tmp) / "test_project")
        
        # Initialize
        epics = {"E1": Epic(id="E1", title="Core")}
        stories = {"S1": Story(id="S1", title="Login")}
        tasks = {"T1": Task(id="T1", title="Form")}
        
        backlog = await manager.initialize(epics, stories, tasks)
        assert backlog.project_id == "test_project"
        print("  ✓ Backlog initialization")
        
        # Update task status
        result = await manager.update_task_status("T1", TaskStatus.IN_PROGRESS)
        assert result is True
        assert manager.get_task("T1").status == TaskStatus.IN_PROGRESS
        print("  ✓ Task status update")
        
        # Reload
        manager2 = BacklogManager("test_project", storage_root=Path(tmp) / "test_project")
        loaded = await manager2.load()
        assert loaded is not None
        assert "S1" in loaded.stories
        print("  ✓ Backlog persistence")
    
    print("✅ BacklogManager tests passed!\n")


def test_ceremony_actions():
    """Test ceremony action helper methods"""
    print("Testing Ceremony Actions...")
    
    from metagpt.project.schemas import Task, Story, Sprint, Backlog, BoardState, TaskStatus, Priority
    from metagpt.actions.scrum.sprint_planning import SprintPlanningAction
    from metagpt.actions.scrum.daily_standup import DailyStandupAction
    from metagpt.actions.scrum.sprint_review import SprintReviewAction
    from metagpt.actions.scrum.retrospective import RetrospectiveAction
    
    # Test SprintPlanningAction
    action = SprintPlanningAction()
    story = Story(id="S1", title="Login", priority=Priority.HIGH, story_points=8)
    backlog = Backlog(project_id="test", stories={"S1": story}, priority_order=["S1"])
    summary = action._format_backlog_summary(backlog)
    assert "S1" in summary
    assert "Login" in summary
    print("  ✓ SprintPlanningAction._format_backlog_summary")
    
    # Test DailyStandupAction
    action = DailyStandupAction()
    board = BoardState(project_id="test", blocked=["T1"])
    tasks = {"T1": Task(id="T1", title="Blocked Task", depends_on=["T2"])}
    details = action._get_blocked_details(board, tasks)
    assert "Blocked Task" in details
    print("  ✓ DailyStandupAction._get_blocked_details")
    
    # Test SprintReviewAction
    action = SprintReviewAction()
    tasks_list = [
        Task(id="T1", title="Done Task", status=TaskStatus.DONE, story_points=5),
        Task(id="T2", title="Pending Task", status=TaskStatus.TODO, story_points=3),
    ]
    formatted = action._format_task_list(tasks_list)
    assert "✅" in formatted
    assert "⏳" in formatted
    print("  ✓ SprintReviewAction._format_task_list")
    
    # Test RetrospectiveAction
    action = RetrospectiveAction()
    sprints = [
        Sprint(number=1, name="S1", completed_points=15),
        Sprint(number=2, name="S2", completed_points=20),
    ]
    analysis = action._analyze_velocity(sprints, 2)
    assert "Average" in analysis
    print("  ✓ RetrospectiveAction._analyze_velocity")
    
    print("✅ All ceremony action tests passed!\n")


def test_imports():
    """Test that all SCRUM modules can be imported"""
    print("Testing SCRUM module imports...")
    
    from metagpt.roles import ScrumMaster, ProductOwner
    print("  ✓ ScrumMaster import")
    print("  ✓ ProductOwner import")
    
    from metagpt.actions.scrum import (
        SprintPlanningAction,
        DailyStandupAction, 
        SprintReviewAction,
        RetrospectiveAction
    )
    print("  ✓ SprintPlanningAction import")
    print("  ✓ DailyStandupAction import")
    print("  ✓ SprintReviewAction import")
    print("  ✓ RetrospectiveAction import")
    
    from metagpt.scrum_team import ScrumTeam
    print("  ✓ ScrumTeam import")
    
    print("✅ All imports successful!\n")


def main():
    print("=" * 60)
    print("SCRUM System Verification Tests")
    print("=" * 60)
    print()
    
    try:
        test_schemas()
        test_sprint_planner()
        asyncio.run(test_backlog_manager())
        test_ceremony_actions()
        test_imports()
        
        print("=" * 60)
        print("🎉 ALL TESTS PASSED! SCRUM System is fully functional.")
        print("=" * 60)
        return 0
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
