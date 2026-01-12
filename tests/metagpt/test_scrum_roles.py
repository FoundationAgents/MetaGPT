#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for SCRUM roles (ScrumMaster, ProductOwner)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

# Test SCRUM Schemas
from metagpt.project.schemas import (
    Task, Story, Sprint, Epic, Backlog, TaskStatus, Priority, BoardState
)


class TestScrumSchemas:
    """Test SCRUM data schemas"""
    
    def test_task_creation(self):
        """Test Task schema creation"""
        task = Task(
            title="Implement login",
            description="Create login functionality",
            story_points=5,
            status=TaskStatus.TODO
        )
        
        assert task.title == "Implement login"
        assert task.story_points == 5
        assert task.status == TaskStatus.TODO
        assert task.id.startswith("TASK-")
    
    def test_story_creation(self):
        """Test Story schema creation"""
        story = Story(
            title="User Authentication",
            description="As a user, I want to log in",
            priority=Priority.HIGH,
            story_points=13,
            acceptance_criteria=["Given valid creds, when login, then success"]
        )
        
        assert story.title == "User Authentication"
        assert story.priority == Priority.HIGH
        assert story.story_points == 13
        assert len(story.acceptance_criteria) == 1
        assert story.id.startswith("STORY-")
    
    def test_sprint_creation(self):
        """Test Sprint schema creation"""
        sprint = Sprint(
            number=1,
            name="Sprint 1: Foundation",
            duration_days=7,
            goals=["Setup project", "Create models"],
            total_points=20,
            completed_points=8
        )
        
        assert sprint.number == 1
        assert sprint.duration_days == 7
        assert sprint.progress_percent == 40  # 8/20 = 40%
    
    def test_backlog_properties(self):
        """Test Backlog total/completed points"""
        story1 = Story(title="Story 1", story_points=5, status=TaskStatus.DONE)
        story2 = Story(title="Story 2", story_points=8, status=TaskStatus.TODO)
        
        backlog = Backlog(
            project_id="test_project",
            stories={story1.id: story1, story2.id: story2}
        )
        
        assert backlog.total_points == 13
        assert backlog.completed_points == 5
    
    def test_board_state_move_task(self):
        """Test BoardState task movement"""
        board = BoardState(
            project_id="test_project",
            todo=["TASK-001", "TASK-002"],
            in_progress=[]
        )
        
        board.move_task("TASK-001", TaskStatus.IN_PROGRESS)
        
        assert "TASK-001" not in board.todo
        assert "TASK-001" in board.in_progress
    
    def test_task_status_enum(self):
        """Test TaskStatus enum values"""
        assert TaskStatus.TODO.value == "todo"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.DONE.value == "done"
        assert TaskStatus.BLOCKED.value == "blocked"
    
    def test_priority_enum(self):
        """Test Priority enum values"""
        assert Priority.CRITICAL.value == "critical"
        assert Priority.HIGH.value == "high"
        assert Priority.MEDIUM.value == "medium"
        assert Priority.LOW.value == "low"


class TestSprintPlanner:
    """Test SprintPlanner functionality"""
    
    def test_sprint_creation_basic(self):
        """Test basic sprint creation from tasks"""
        from metagpt.project.sprint_planner import SprintPlanner
        
        # Create test tasks
        tasks = {
            "TASK-001": Task(id="TASK-001", title="Task 1", story_points=5),
            "TASK-002": Task(id="TASK-002", title="Task 2", story_points=8),
            "TASK-003": Task(id="TASK-003", title="Task 3", story_points=3),
        }
        
        stories = {}
        
        planner = SprintPlanner(sprint_duration=7, velocity=15)
        sprints = planner.create_sprints(tasks, stories)
        
        # Should create sprints based on velocity
        assert len(sprints) >= 1
        assert sprints[0].number == 1
    
    def test_sprint_velocity_constraint(self):
        """Test that sprints respect velocity"""
        from metagpt.project.sprint_planner import SprintPlanner
        
        tasks = {
            "TASK-001": Task(id="TASK-001", title="Big Task", story_points=15),
            "TASK-002": Task(id="TASK-002", title="Medium Task", story_points=10),
        }
        
        planner = SprintPlanner(velocity=15)
        sprints = planner.create_sprints(tasks, {})
        
        # Each sprint should not exceed velocity (except single large tasks)
        for sprint in sprints:
            # Allow exceeding if single task is larger than velocity
            if len(sprint.tasks) == 1:
                continue
            assert sprint.total_points <= 15


class TestBacklogManager:
    """Test BacklogManager functionality"""
    
    @pytest.mark.asyncio
    async def test_initialize_backlog(self, tmp_path):
        """Test backlog initialization"""
        from metagpt.project.backlog_manager import BacklogManager
        
        manager = BacklogManager("test_project", storage_root=tmp_path / "test_project")
        
        epics = {"EPIC-001": Epic(id="EPIC-001", title="Core Features")}
        stories = {"STORY-001": Story(id="STORY-001", title="Login", story_points=5)}
        tasks = {"TASK-001": Task(id="TASK-001", title="Create login form")}
        
        backlog = await manager.initialize(epics, stories, tasks)
        
        assert backlog.project_id == "test_project"
        assert "EPIC-001" in backlog.epics
        assert "STORY-001" in backlog.stories
        assert "TASK-001" in backlog.tasks
    
    @pytest.mark.asyncio
    async def test_save_and_load_backlog(self, tmp_path):
        """Test backlog persistence"""
        from metagpt.project.backlog_manager import BacklogManager
        
        manager = BacklogManager("test_project", storage_root=tmp_path / "test_project")
        
        stories = {"STORY-001": Story(id="STORY-001", title="Feature A")}
        tasks = {"TASK-001": Task(id="TASK-001", title="Subtask")}
        
        await manager.initialize({}, stories, tasks)
        
        # Reload
        manager2 = BacklogManager("test_project", storage_root=tmp_path / "test_project")
        loaded_backlog = await manager2.load()
        
        assert loaded_backlog is not None
        assert "STORY-001" in loaded_backlog.stories
    
    @pytest.mark.asyncio
    async def test_update_task_status(self, tmp_path):
        """Test task status update"""
        from metagpt.project.backlog_manager import BacklogManager
        
        manager = BacklogManager("test_project", storage_root=tmp_path / "test_project")
        
        tasks = {"TASK-001": Task(id="TASK-001", title="Work")}
        await manager.initialize({}, {}, tasks)
        
        result = await manager.update_task_status("TASK-001", TaskStatus.IN_PROGRESS)
        
        assert result is True
        assert manager.get_task("TASK-001").status == TaskStatus.IN_PROGRESS


class TestBoardTracker:
    """Test BoardTracker functionality"""
    
    @pytest.mark.asyncio
    async def test_initialize_board(self, tmp_path):
        """Test board initialization"""
        from metagpt.project.board_tracker import BoardTracker
        
        # Create new tracker instance for testing
        tracker = BoardTracker.__new__(BoardTracker)
        tracker._initialized = False
        tracker.__init__()
        
        tasks = {
            "TASK-001": Task(id="TASK-001", title="Task 1"),
            "TASK-002": Task(id="TASK-002", title="Task 2"),
        }
        
        board = await tracker.initialize_board("test_project", tasks)
        
        assert board.project_id == "test_project"
        assert "TASK-001" in board.todo
        assert "TASK-002" in board.todo
    
    def test_get_metrics(self):
        """Test metrics calculation"""
        from metagpt.project.board_tracker import BoardTracker
        from metagpt.project.schemas import BoardState
        
        tracker = BoardTracker.__new__(BoardTracker)
        tracker._initialized = False
        tracker.__init__()
        
        # Setup test data
        tracker._boards["test"] = BoardState(
            project_id="test",
            todo=["TASK-001"],
            done=["TASK-002"]
        )
        tracker._tasks["test"] = {
            "TASK-001": Task(id="TASK-001", title="T1", story_points=5),
            "TASK-002": Task(id="TASK-002", title="T2", story_points=3, status=TaskStatus.DONE)
        }
        
        metrics = tracker.get_metrics("test")
        
        assert metrics.project_id == "test"
        assert metrics.points_completed == 3
        assert metrics.points_remaining == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
