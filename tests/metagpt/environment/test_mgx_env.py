import pytest

from metagpt.environment.mgx.mgx_env import MGXEnv
from metagpt.schema import Message


def test_publish_message_without_team_leader_falls_back_and_records_history():
    env = MGXEnv()
    before_count = env.history.count()

    msg = Message(content="hi", role="user")

    # Should not raise and should return True
    assert env.publish_message(msg) is True

    # History should increase (once in base env, and once in MGXEnv)
    assert env.history.count() >= before_count + 1

    # The transformed message (from _publish_message) should be present in history
    # It includes the sender/receiver info moved into content
    assert any(
        "[Message] from" in m.content and "to" in m.content for m in env.history.storage
    )


def test_user_defined_recipient_with_missing_role_is_safe_and_no_direct_chat_added():
    env = MGXEnv()
    before_count = env.history.count()

    # Direct chat to a non-existent role should not crash and should not add to direct_chat_roles
    msg = Message(content="ping", role="user")
    msg.send_to = {"NonExistentRole"}

    assert env.publish_message(msg, user_defined_recipient="NonExistentRole") is True

    # No direct chat role should be recorded for a missing role
    assert "NonExistentRole" not in env.direct_chat_roles

    # Still publishes and records in history
    assert env.history.count() >= before_count + 1


def test_user_defined_recipient_with_existing_role_does_not_error():
    env = MGXEnv()

    # Define a minimal role by name and add to env
    from metagpt.roles import Role

    class DummyRole(Role):
        name: str = "Alice"
        profile: str = "DummyRole"

    env.add_roles([DummyRole()])

    msg = Message(content="hello", role="user")
    msg.send_to = {"Alice"}

    # Should not raise and should return True
    assert env.publish_message(msg, user_defined_recipient="Alice") is True


