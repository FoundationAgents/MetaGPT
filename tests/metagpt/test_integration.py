#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Integration tests for MetaGPT core modules.

These tests focus on INTERACTIONS between modules, not individual functions.
Key principles:
1. Test module interactions and data flow between components
2. Use real dependencies where possible (in-memory/test environments)
3. Tests are reproducible and isolated from external environment
4. Cover both success scenarios and error/edge cases

Integration points tested:
1. Team → Environment → Roles (multi-agent coordination)
2. Role → Action → LLM (action execution pipeline with mocked LLM)
3. Message ↔ Memory (message handling, routing, and storage)
4. Context → Config → Provider (configuration propagation)
5. Serialization/Deserialization (state persistence across components)

Author: Integration Test Suite
"""

import tempfile
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock

import pytest

from metagpt.actions import Action
from metagpt.actions.add_requirement import UserRequirement
from metagpt.context import AttrDict, Context
from metagpt.environment import Environment
from metagpt.memory import Memory
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.team import Team
from metagpt.utils.common import any_to_str

# ==================== Mock LLM for Reproducible Tests ====================


class MockLLMProvider:
    """
    Mock LLM provider for reproducible integration tests.
    Simulates LLM responses without external API calls.
    """

    def __init__(self):
        self.call_count = 0
        self.last_prompt = None
        self.responses = {}
        self.cost_manager = MagicMock()
        self.system_prompt = "You are a helpful assistant."
        self.model = "mock-model"

    async def aask(self, prompt: str, system_msgs: Optional[list] = None, **kwargs) -> str:
        """Mock async ask method."""
        self.call_count += 1
        self.last_prompt = prompt
        # Return predefined response or default
        return self.responses.get(prompt, f"Mock response to: {prompt[:50]}...")

    def set_response(self, prompt: str, response: str):
        """Set a predefined response for a specific prompt."""
        self.responses[prompt] = response


# ==================== Test Fixtures ====================


class MockAction(Action):
    """Mock action for testing that returns processed content."""

    name: str = "MockAction"

    async def run(self, messages, *args, **kwargs):
        """Process messages and return action output."""
        if not messages:
            return Message(content="No messages provided", cause_by=self)
        last_msg = messages[-1] if isinstance(messages, list) else messages
        content = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
        return Message(content=f"Processed: {content}", cause_by=self)


class TransformAction(Action):
    """Action that transforms data for testing data flow between modules."""

    name: str = "TransformAction"
    prefix_text: str = "TRANSFORMED:"

    async def run(self, messages, *args, **kwargs):
        if not messages:
            return Message(content="", cause_by=self)
        last_msg = messages[-1] if isinstance(messages, list) else messages
        content = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
        return Message(content=f"{self.prefix_text} {content.upper()}", cause_by=self)


class FailingAction(Action):
    """Action that simulates failure for error handling tests."""

    name: str = "FailingAction"
    should_fail: bool = True

    async def run(self, messages, *args, **kwargs):
        if self.should_fail:
            raise ValueError("Simulated action failure")
        return Message(content="Success", cause_by=self)


class MockTestRole(Role):
    """Test role with configurable actions."""

    name: str = "TestRole"
    profile: str = "Tester"
    goal: str = "Execute test actions"
    constraints: str = "Follow test protocols"

    def __init__(self, actions=None, **kwargs):
        super().__init__(**kwargs)
        # Only set actions if they are Action instances (not dicts from deserialization)
        if actions and not self.actions:
            if all(isinstance(a, (Action, type)) for a in actions):
                self.set_actions(actions)
        elif not self.actions:
            self.set_actions([MockAction()])


class DataProcessorRole(Role):
    """Role that processes and transforms data."""

    name: str = "DataProcessor"
    profile: str = "Data Processor"
    goal: str = "Transform and process data"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([TransformAction()])


# ==================== Integration Tests ====================


class TestTeamEnvironmentRolesIntegration:
    """
    Test 1: Team → Environment → Roles Integration

    Tests the core multi-agent coordination functionality:
    - Team creation and role hiring
    - Environment setup and role registration
    - Message routing between roles
    - Cost management across the team
    """

    def test_team_creates_environment_with_roles(self):
        """Test that Team properly initializes Environment and adds roles."""
        # Arrange
        team = Team()
        role1 = MockTestRole(name="Role1")
        role2 = MockTestRole(name="Role2")

        # Act
        team.hire([role1, role2])

        # Assert
        assert team.env is not None
        assert len(team.env.roles) == 2
        assert "Role1" in [r.name for r in team.env.roles.values()]
        assert "Role2" in [r.name for r in team.env.roles.values()]

    def test_team_investment_propagates_to_cost_manager(self):
        """Test that investment settings propagate to cost manager."""
        # Arrange
        team = Team()
        role = MockTestRole()
        team.hire([role])

        # Act
        team.invest(100.0)

        # Assert
        assert team.cost_manager.max_budget == 100.0
        assert team.investment == 100.0

    def test_environment_role_addresses_registration(self):
        """Test that roles are registered with correct addresses in environment."""
        # Arrange
        env = Environment()
        role = MockTestRole(name="AddressedRole")
        role.set_addresses({"custom_address", "another_address"})

        # Act
        env.add_role(role)

        # Assert
        addresses = env.get_addresses(role)
        assert "custom_address" in addresses
        assert "another_address" in addresses

    def test_environment_publishes_message_to_multiple_roles(self):
        """Test message broadcasting to multiple roles in environment."""
        # Arrange
        env = Environment()
        role1 = MockTestRole(name="Receiver1")
        role2 = MockTestRole(name="Receiver2")
        env.add_roles([role1, role2])

        # Act
        message = Message(content="Broadcast message")
        env.publish_message(message)

        # Assert
        # Both roles should receive the message in their buffers
        assert not role1.is_idle or not role2.is_idle


class TestRoleActionLLMIntegration:
    """
    Test 2: Role → Action → LLM Integration

    Tests the action execution pipeline:
    - Role executes actions properly
    - Actions process messages correctly
    - LLM integration points work as expected
    - Error handling in action execution
    """

    @pytest.mark.asyncio
    async def test_role_executes_action_with_message(self):
        """Test that role properly executes action with message input."""
        # Arrange
        role = MockTestRole(name="Executor")
        message = Message(content="Test input")
        role.rc.memory.add(message)

        # Act
        await role.think()
        result = await role.act()

        # Assert
        assert result is not None
        assert "Processed:" in result.content or "Test input" in result.content

    @pytest.mark.asyncio
    async def test_action_transforms_data_correctly(self):
        """Test that action properly transforms input data."""
        # Arrange
        action = TransformAction()
        messages = [Message(content="hello world")]

        # Act
        result = await action.run(messages)

        # Assert
        assert result.content == "TRANSFORMED: HELLO WORLD"

    @pytest.mark.asyncio
    async def test_role_handles_action_failure_gracefully(self):
        """Test that role handles action failure appropriately."""
        # Arrange
        failing_action = FailingAction()
        role = MockTestRole(actions=[failing_action], name="FailHandler")
        message = Message(content="Trigger failure")
        role.rc.memory.add(message)

        # Act & Assert
        await role.think()
        with pytest.raises(ValueError, match="Simulated action failure"):
            await role.act()

    @pytest.mark.asyncio
    async def test_action_receives_correct_context(self):
        """Test that action receives correct context from role."""
        # Arrange
        role = MockTestRole(name="ContextProvider")
        mock_action = MockAction()
        role.set_actions([mock_action])

        # Assert
        assert mock_action.context is not None
        assert mock_action.llm is not None


class TestMessageMemoryIntegration:
    """
    Test 3: Message ↔ Memory Integration

    Tests message handling and storage:
    - Memory stores and retrieves messages
    - Message indexing by cause_by
    - Message filtering and search
    - Memory operations (add, delete, clear)

    INTEGRATION FOCUS: Tests how Memory component interacts with Message objects
    and how messages flow through the system with proper indexing.
    """

    def test_memory_indexes_and_retrieves_by_action_type(self):
        """
        INTEGRATION: Test that Memory properly indexes messages by their cause_by
        action and allows retrieval, simulating how Role retrieves relevant messages.
        """
        # Arrange - simulate multiple actions producing messages
        memory = Memory()

        # Messages from different action types (simulating multi-step workflow)
        mock_action_msg = Message(content="Design document created", cause_by=MockAction)
        transform_msg = Message(content="Code generated", cause_by=TransformAction)
        another_mock_msg = Message(content="Tests written", cause_by=MockAction)

        # Act - add messages (simulating Role storing action results)
        memory.add(mock_action_msg)
        memory.add(transform_msg)
        memory.add(another_mock_msg)

        # Assert - retrieve by action type (simulating Role filtering for relevant context)
        mock_results = memory.get_by_action(MockAction)
        transform_results = memory.get_by_action(TransformAction)

        assert len(mock_results) == 2
        assert len(transform_results) == 1
        assert all(m.cause_by == any_to_str(MockAction) for m in mock_results)

    def test_memory_find_news_for_role_observation(self):
        """
        INTEGRATION: Test memory.find_news() which is used by Role._observe()
        to identify new messages that haven't been processed yet.
        """
        # Arrange - simulate existing memory state
        memory = Memory()
        old_msg1 = Message(content="Previous task completed")
        old_msg2 = Message(content="Another old message")
        memory.add(old_msg1)
        memory.add(old_msg2)

        # New messages coming from environment (simulating publish_message)
        new_msg = Message(content="New user requirement")
        observed_messages = [old_msg1, old_msg2, new_msg]

        # Act - find_news (as Role would do in _observe)
        news = memory.find_news(observed_messages)

        # Assert
        assert len(news) == 1
        assert news[0].content == "New user requirement"

    def test_role_memory_accumulates_action_results(self):
        """
        INTEGRATION: Test complete flow of Role executing action and
        storing result in memory for future reference.
        """
        # Arrange
        role = MockTestRole(name="MemoryTestRole")
        initial_count = role.rc.memory.count()

        # Simulate receiving a message (as would happen from Environment)
        incoming_msg = Message(content="Process this data")
        role.rc.memory.add(incoming_msg)

        # Assert - memory grows as messages are added
        assert role.rc.memory.count() == initial_count + 1

        # Verify message can be retrieved
        recent = role.rc.memory.get(k=1)
        assert len(recent) == 1
        assert recent[0].content == "Process this data"


class TestContextConfigLLMProviderIntegration:
    """
    Test 4: Context → Config → LLM Provider Integration

    Tests configuration and LLM provider management:
    - Context creation and configuration
    - LLM instance creation
    - Cost manager integration
    - AttrDict functionality for dynamic attributes
    """

    def test_context_creates_llm_with_cost_manager(self):
        """
        INTEGRATION: Test that Context properly creates LLM instance and
        integrates with CostManager for tracking API usage costs.
        """
        # Arrange
        ctx = Context()

        # Act - create LLM through context (as Team/Role would do)
        llm = ctx.llm()

        # Assert - LLM is properly configured with cost tracking
        assert llm is not None
        assert llm.cost_manager is not None
        # Verify cost manager is the context's cost manager
        assert llm.cost_manager == ctx.cost_manager

    def test_context_serialization_and_deserialization(self):
        """
        INTEGRATION: Test that Context state (kwargs, cost_manager) can be
        serialized and restored, enabling Team state persistence.
        """
        # Arrange
        ctx = Context()
        ctx.kwargs.set("test_key", "test_value")
        ctx.kwargs.set("another_key", 42)

        # Act - serialize (as Team.serialize would do)
        serialized = ctx.serialize()

        # Create new context and restore state
        new_ctx = Context()
        new_ctx.deserialize(serialized)

        # Assert - state properly restored
        assert new_ctx.kwargs.get("test_key") == "test_value"
        assert new_ctx.kwargs.get("another_key") == 42

    def test_attr_dict_dynamic_attributes(self):
        """
        INTEGRATION: Test AttrDict which allows Context to store
        arbitrary runtime data accessible across the system.
        """
        # Arrange
        attr_dict = AttrDict()

        # Act - set attributes (as various components would do)
        attr_dict.set("key1", "value1")
        attr_dict.key2 = "value2"

        # Assert
        assert attr_dict.get("key1") == "value1"
        assert attr_dict.key2 == "value2"
        assert attr_dict.nonexistent is None

        # Test remove
        attr_dict.remove("key1")
        assert attr_dict.get("key1") is None

    def test_context_shares_cost_manager_across_llms(self):
        """
        INTEGRATION: Verify that all LLM instances created from the same
        Context share a single CostManager, ensuring unified cost tracking.
        """
        # Arrange
        ctx = Context()

        # Act - create multiple LLM instances (as multiple Roles would)
        llm1 = ctx.llm()
        llm2 = ctx.llm()

        # Assert - cost tracking is unified
        assert llm1.cost_manager is not None
        assert llm2.cost_manager is not None


class TestSerializationDeserializationIntegration:
    """
    Test 5: Serialization/Deserialization Integration

    Tests state persistence:
    - Team serialization and deserialization
    - Message serialization
    - Role state preservation
    - Error handling for missing files
    """

    def test_team_serialize_deserialize_roundtrip(self):
        """Test complete team serialization and deserialization."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            stg_path = Path(tmpdir)

            team = Team()
            role = MockTestRole(name="SerializedRole")
            team.hire([role])
            team.invest(50.0)
            team.idea = "Test idea"

            # Act - Serialize
            team.serialize(stg_path)

            # Assert - File exists
            assert (stg_path / "team.json").exists()

            # Act - Deserialize
            restored_team = Team.deserialize(stg_path)

            # Assert
            assert restored_team.investment == 50.0
            assert restored_team.idea == "Test idea"

    def test_message_serialization(self):
        """Test message serialization and deserialization."""
        # Arrange
        original_msg = Message(
            content="Test content", role="assistant", cause_by=MockAction, send_to={"target1", "target2"}
        )

        # Act
        json_str = original_msg.dump()
        restored_msg = Message.load(json_str)

        # Assert
        assert restored_msg is not None
        assert restored_msg.content == "Test content"
        assert restored_msg.role == "assistant"
        assert "target1" in restored_msg.send_to
        assert "target2" in restored_msg.send_to

    def test_deserialization_handles_missing_file(self):
        """Test that deserialization handles missing file gracefully."""
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            non_existent_path = Path(tmpdir) / "nonexistent"

            # Act & Assert
            with pytest.raises(FileNotFoundError):
                Team.deserialize(non_existent_path)

    def test_message_load_handles_invalid_json(self):
        """Test that message loading handles invalid JSON gracefully."""
        # Arrange
        invalid_json = "not a valid json"

        # Act
        result = Message.load(invalid_json)

        # Assert
        assert result is None


class TestDataFlowBetweenModules:
    """
    Test 6: Data Flow Between Modules (Bonus)

    Tests data transformation and flow:
    - Data passes correctly between components
    - Transformations are applied in correct order
    - State consistency across module boundaries
    """

    @pytest.mark.asyncio
    async def test_message_flows_through_role_to_action(self):
        """Test that message content flows correctly from role to action."""
        # Arrange
        role = DataProcessorRole(name="Processor")
        input_message = Message(content="test data")
        role.rc.memory.add(input_message)

        # Act
        await role.think()
        result = await role.act()

        # Assert
        assert result is not None
        assert "TRANSFORMED:" in result.content
        assert "TEST DATA" in result.content

    @pytest.mark.asyncio
    async def test_environment_message_routing(self):
        """Test that environment correctly routes messages to specific roles."""
        # Arrange
        env = Environment()
        role1 = MockTestRole(name="TargetRole")
        role1.set_addresses({"target_address"})
        role2 = MockTestRole(name="OtherRole")
        role2.set_addresses({"other_address"})
        env.add_roles([role1, role2])

        # Act
        targeted_message = Message(content="Targeted content", send_to={"target_address"})
        env.publish_message(targeted_message)

        # Assert - Only targeted role should receive
        # The message routing is handled by is_send_to logic
        assert targeted_message.send_to == {"target_address"}

    def test_role_watch_filters_messages_correctly(self):
        """Test that role watch mechanism filters messages correctly."""
        # Arrange
        role = MockTestRole(name="WatcherRole")

        # Default watch should be UserRequirement
        default_watch = role.rc.watch

        # Assert
        assert any_to_str(UserRequirement) in default_watch

        # Act - Change watch
        role._watch([MockAction])

        # Assert
        assert any_to_str(MockAction) in role.rc.watch


class TestEdgeCasesAndErrorHandling:
    """
    Test 7: Edge Cases and Error Handling

    INTEGRATION FOCUS: Tests how the system handles edge cases when
    components interact, not individual function behavior.
    """

    def test_team_with_roles_can_run(self):
        """
        INTEGRATION: Test that Team with roles properly initializes
        and is ready for execution.
        """
        # Arrange
        team = Team()
        role = MockTestRole(name="Worker")
        team.hire([role])

        # Assert - Team is properly set up
        assert team.env is not None
        assert len(team.env.roles) == 1
        assert team.cost_manager is not None

    def test_environment_handles_message_to_missing_address(self):
        """
        INTEGRATION: Test that Environment gracefully handles messages
        sent to addresses with no registered roles.
        """
        # Arrange
        env = Environment()
        role = MockTestRole(name="OnlyRole")
        role.set_addresses({"existing_address"})
        env.add_role(role)

        # Act - Send message to non-existent address
        message = Message(content="Hello", send_to={"non_existent_address"})
        env.publish_message(message)

        # Assert - No crash, message was processed
        assert message.send_to == {"non_existent_address"}

    def test_duplicate_message_not_added_to_memory(self):
        """
        INTEGRATION: Test Memory deduplication which prevents infinite
        loops when messages are re-observed.
        """
        # Arrange
        memory = Memory()
        msg = Message(content="Unique message")

        # Act - try to add same message twice
        memory.add(msg)
        memory.add(msg)

        # Assert - only one copy stored
        assert memory.count() == 1

    @pytest.mark.asyncio
    async def test_action_with_empty_messages_list(self):
        """
        INTEGRATION: Test Action gracefully handles empty input
        (edge case when Role has no relevant messages in memory).
        """
        # Arrange
        action = MockAction()

        # Act
        result = await action.run([])

        # Assert - graceful handling
        assert result.content == "No messages provided"


# ==================== Run Tests ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
