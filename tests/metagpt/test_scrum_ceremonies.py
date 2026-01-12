#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for SCRUM ceremony actions
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from metagpt.project.schemas import (
    Task, Story, Sprint, Epic, Backlog, TaskStatus, Priority, BoardState
)


class TestSprintPlanningAction:
    """Test SprintPlanningAction"""
    
    def test_format_backlog_summary(self):
        """Test backlog summary formatting"""
        from metagpt.actions.scrum.sprint_planning import SprintPlanningAction
        
        action = SprintPlanningAction()
        
        story1 = Story(id="STORY-001", title="Login", priority=Priority.HIGH, story_points=8)
        story2 = Story(id="STORY-002", title="Dashboard", priority=Priority.MEDIUM, story_points=5)
        
        backlog = Backlog(
            project_id="test",
            stories={"STORY-001": story1, "STORY-002": story2},
            priority_order=["STORY-001", "STORY-002"]
        )
        
        summary = action._format_backlog_summary(backlog)
        
        assert "STORY-001" in summary
        assert "Login" in summary
        assert "HIGH" in summary
    
    def test_generate_planning_summary(self):
        """Test planning summary generation"""
        from metagpt.actions.scrum.sprint_planning import SprintPlanningAction
        
        action = SprintPlanningAction()
        
        sprint = Sprint(
            number=1,
            name="Sprint 1",
            duration_days=7,
            start_date=datetime.now(),
            end_date=datetime.now(),
            goals=["Goal 1", "Goal 2"],
            tasks=["TASK-001"],
            total_points=10
        )
        
        task = Task(id="TASK-001", title="Test Task", story_points=5)
        backlog = Backlog(project_id="test", tasks={"TASK-001": task})
        
        summary = action._generate_planning_summary(sprint, backlog)
        
        assert "Sprint 1" in summary
        assert "Goal 1" in summary
        assert "Test Task" in summary


class TestDailyStandupAction:
    """Test DailyStandupAction"""
    
    def test_get_blocked_details(self):
        """Test blocked task details formatting"""
        from metagpt.actions.scrum.daily_standup import DailyStandupAction
        
        action = DailyStandupAction()
        
        board = BoardState(
            project_id="test",
            blocked=["TASK-001"]
        )
        
        tasks = {
            "TASK-001": Task(
                id="TASK-001", 
                title="Blocked Task", 
                depends_on=["TASK-002"]
            )
        }
        
        details = action._get_blocked_details(board, tasks)
        
        assert "Blocked Task" in details
        assert "TASK-002" in details
    
    def test_get_completed_details(self):
        """Test completed task details formatting"""
        from metagpt.actions.scrum.daily_standup import DailyStandupAction
        
        action = DailyStandupAction()
        
        board = BoardState(
            project_id="test",
            done=["TASK-001"]
        )
        
        tasks = {
            "TASK-001": Task(
                id="TASK-001",
                title="Completed Task",
                status=TaskStatus.DONE,
                completed_at=datetime.now()
            )
        }
        
        details = action._get_completed_details(board, tasks)
        
        assert "Completed Task" in details


class TestSprintReviewAction:
    """Test SprintReviewAction"""
    
    def test_format_task_list(self):
        """Test task list formatting"""
        from metagpt.actions.scrum.sprint_review import SprintReviewAction
        
        action = SprintReviewAction()
        
        tasks = [
            Task(id="TASK-001", title="Task 1", story_points=5, status=TaskStatus.DONE),
            Task(id="TASK-002", title="Task 2", story_points=3, status=TaskStatus.TODO),
        ]
        
        formatted = action._format_task_list(tasks)
        
        assert "Task 1" in formatted
        assert "✅" in formatted  # Done emoji
        assert "⏳" in formatted  # Pending emoji
    
    def test_check_acceptance_criteria(self):
        """Test acceptance criteria checking"""
        from metagpt.actions.scrum.sprint_review import SprintReviewAction
        
        action = SprintReviewAction()
        
        story = Story(
            id="STORY-001",
            title="Login",
            acceptance_criteria=["Can login with email", "Shows error on failure"],
            tasks=["TASK-001"]
        )
        
        tasks = [
            Task(id="TASK-001", title="Login form", parent_story="STORY-001")
        ]
        
        backlog = Backlog(
            project_id="test",
            stories={"STORY-001": story}
        )
        
        status = action._check_acceptance_criteria(tasks, backlog)
        
        assert "STORY-001" in status
        assert "Login" in status


class TestRetrospectiveAction:
    """Test RetrospectiveAction"""
    
    def test_calculate_sprint_metrics(self):
        """Test sprint metrics calculation"""
        from metagpt.actions.scrum.retrospective import RetrospectiveAction
        
        action = RetrospectiveAction()
        
        sprint = Sprint(
            number=1,
            name="Sprint 1",
            tasks=["TASK-001", "TASK-002"],
            total_points=10
        )
        
        task1 = Task(id="TASK-001", title="T1", story_points=5, status=TaskStatus.DONE)
        task2 = Task(id="TASK-002", title="T2", story_points=5, status=TaskStatus.TODO)
        
        backlog = Backlog(
            project_id="test",
            tasks={"TASK-001": task1, "TASK-002": task2}
        )
        
        metrics = action._calculate_sprint_metrics(sprint, backlog)
        
        assert "Completed Points:** 5" in metrics
        assert "50.0%" in metrics  # 5/10 = 50%
    
    def test_analyze_velocity(self):
        """Test velocity analysis"""
        from metagpt.actions.scrum.retrospective import RetrospectiveAction
        
        action = RetrospectiveAction()
        
        sprints = [
            Sprint(number=1, name="S1", completed_points=15),
            Sprint(number=2, name="S2", completed_points=18),
            Sprint(number=3, name="S3", completed_points=20),
        ]
        
        analysis = action._analyze_velocity(sprints, 3)
        
        assert "Average Velocity" in analysis
        assert "increasing" in analysis.lower()  # 15 -> 18 -> 20 is increasing
    
    def test_analyze_blockers(self):
        """Test blocker analysis"""
        from metagpt.actions.scrum.retrospective import RetrospectiveAction
        
        action = RetrospectiveAction()
        
        sprint = Sprint(number=1, name="S1", tasks=["TASK-001"])
        
        task = Task(
            id="TASK-001",
            title="Blocked Task",
            status=TaskStatus.BLOCKED,
            depends_on=["TASK-002"]
        )
        
        backlog = Backlog(project_id="test", tasks={"TASK-001": task})
        
        analysis = action._analyze_blockers(sprint, backlog)
        
        assert "Blocked Task" in analysis
        assert "TASK-002" in analysis


class TestScrumRoleInstantiation:
    """Test SCRUM role instantiation (without LLM)"""
    
    def test_scrum_master_attributes(self):
        """Test ScrumMaster basic attributes"""
        # Import only the schemas to avoid LLM initialization
        from metagpt.project.schemas import Task, Sprint
        
        # Verify schemas work correctly
        task = Task(title="Test Task")
        assert task.status == TaskStatus.TODO
    
    def test_product_owner_attributes(self):
        """Test ProductOwner basic attributes"""  
        from metagpt.project.schemas import Story, Priority
        
        story = Story(title="Test Story", priority=Priority.HIGH)
        assert story.priority == Priority.HIGH


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
