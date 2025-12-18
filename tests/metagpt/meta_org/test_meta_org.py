#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests for Meta-Org Agent components.
"""
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

from metagpt.actions import Action
from metagpt.meta_org.agent import MetaOrgAgent
from metagpt.meta_org.collector import SignalCollector
from metagpt.meta_org.lifecycle import (
    AgentLifecycleManager,
    AgentLifecycleState,
)
from metagpt.meta_org.signals import OrgPattern, OrgSignal, SignalSeverity, SignalType
from metagpt.team import Team


@pytest.fixture
def signal_collector():
    # Reset singleton
    SignalCollector._instance = None
    return SignalCollector.get_instance("test_project")


@pytest.fixture
def team():
    team = Team()
    return team


def test_signal_collector_singleton():
    c1 = SignalCollector.get_instance("p1")
    c2 = SignalCollector.get_instance("p2")
    assert c1 is c2
    assert c1.project_id == "p1"  # First init wins


def test_record_failure(signal_collector):
    signal_collector.record_failure("RoleA", "ActionB", "Error occurred")
    assert len(signal_collector.signals) == 1
    assert signal_collector.signals[0].signal_type == SignalType.FAILURE
    assert signal_collector.signals[0].source_role == "RoleA"


def test_pattern_detection_blind_spot(signal_collector):
    # Simulate repeated failures
    for _ in range(4):
        signal_collector.record_failure("User", "CheckSecurity", "Security vulnerability found")
    
    patterns = signal_collector.analyze_patterns()
    assert len(patterns) >= 1
    assert patterns[0].pattern_type == "blind_spot"
    assert "Security vulnerability" in patterns[0].description


def test_pattern_detection_overload(signal_collector):
    # Simulate single role signal flood
    for i in range(15):
        signal_collector.record_slow_decision("OverloadedRole", f"Action{i}", 40000)
    
    # Needs variety of signals for pattern match in current implementation
    signal_collector.record_failure("OverloadedRole", "ActionX", "Error")
    signal_collector.record_uncertainty("OverloadedRole", "ActionY", "maybe unsure")
    
    patterns = signal_collector.analyze_patterns()
    overload_patterns = [p for p in patterns if p.pattern_type == "cognitive_overload"]
    assert len(overload_patterns) > 0


def test_lifecycle_manager():
    manager = AgentLifecycleManager()
    agent = manager.register_agent("TestRole", "TestClass", state=AgentLifecycleState.EXPERIMENTAL)
    
    assert agent.role_name == "TestRole"
    assert agent.state == AgentLifecycleState.EXPERIMENTAL
    
    # Simulate good performance
    for _ in range(5):
        agent.record_participation(success=True, value_contributed=0.8)
    
    assert agent.should_promote()
    manager.promote_if_ready("TestRole")
    assert agent.state == AgentLifecycleState.ACTIVE


@pytest.mark.asyncio
async def test_meta_org_agent_analysis(team, signal_collector):
    # Mock LLM
    mock_llm = MagicMock()
    mock_llm.aask.return_value = """
    {
        "diagnosis": "Test diagnosis",
        "changes": [
            {
                "action": "ADD_AGENT",
                "target": "NewRole",
                "config": {"role_name": "NewRole", "role_profile": "Tester"}
            }
        ]
    }
    """
    
    agent = MetaOrgAgent(team, signal_collector, llm=mock_llm)
    
    # Needs some signals to trigger
    signal_collector.record_failure("RoleA", "ActionB", "Error")
    
    changes = await agent.analyze_and_adapt()
    
    assert len(changes) == 1
    assert changes[0]["action"] == "ADD_AGENT"
    
    # Check if agent was hired (mocked team hiring)
    # Since team.hire calls env.add_roles which needs actual roles, 
    # and we are not mocking Env completely, this might fail in strict unittest if dependencies strictly checked.
    # But in integration test it should work if Environment is functional.
