#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the unittest of Memory

import time

from metagpt.actions import UserRequirement
from metagpt.memory.memory import Memory
from metagpt.schema import Message


def test_memory():
    memory = Memory()

    message1 = Message(content="test message1", role="user1")
    message2 = Message(content="test message2", role="user2")
    message3 = Message(content="test message3", role="user1")
    memory.add(message1)
    assert memory.count() == 1

    memory.delete_newest()
    assert memory.count() == 0

    memory.add_batch([message1, message2])
    assert memory.count() == 2
    assert len(memory.index.get(message1.cause_by)) == 2

    messages = memory.get_by_role("user1")
    assert messages[0].content == message1.content

    messages = memory.get_by_content("test message")
    assert len(messages) == 2

    messages = memory.get_by_action(UserRequirement)
    assert len(messages) == 2

    messages = memory.get_by_actions({UserRequirement})
    assert len(messages) == 2

    messages = memory.try_remember("test message")
    assert len(messages) == 2

    messages = memory.get(k=1)
    assert len(messages) == 1

    messages = memory.get(k=5)
    assert len(messages) == 2

    messages = memory.find_news([message3])
    assert len(messages) == 1

    memory.delete(message1)
    assert memory.count() == 1
    messages = memory.get_by_role("user2")
    assert messages[0].content == message2.content

    memory.clear()
    assert memory.count() == 0
    assert len(memory.index) == 0


def test_message_ttl_and_created_at():
    """Test Message class ttl and created_at fields"""
    # Test default values
    message = Message(content="test message", role="user")
    assert message.ttl == -1
    assert message.created_at > 0
    
    # Test custom ttl
    message_with_ttl = Message(content="test message with ttl", role="user", ttl=60)
    assert message_with_ttl.ttl == 60
    
    # Test is_expired method for ttl=-1 (never expire)
    assert message.is_expired() == False
    
    # Test serialization
    dumped = message.dump()
    loaded = Message.load(dumped)
    assert loaded.ttl == message.ttl
    assert abs(loaded.created_at - message.created_at) < 0.001


def test_message_expiration():
    """Test message expiration functionality"""
    # Create a message that expires in 1 second
    message = Message(content="expiring message", role="user", ttl=1)
    assert message.is_expired() == False
    
    # Wait for message to expire
    time.sleep(1.1)
    assert message.is_expired() == True
    
    # Create a message that never expires
    message_never_expire = Message(content="never expiring message", role="user", ttl=-1)
    assert message_never_expire.is_expired() == False
    
    # Wait and verify it still doesn't expire
    time.sleep(0.5)
    assert message_never_expire.is_expired() == False


def test_memory_filter_expired_messages():
    """Test Memory class filtering expired messages"""
    memory = Memory()
    
    # Create messages with different TTLs
    message1 = Message(content="never expire", role="user1", ttl=-1)
    message2 = Message(content="expire in 1 sec", role="user2", ttl=1)
    message3 = Message(content="never expire too", role="user1", ttl=-1)
    
    # Add all messages to memory
    memory.add_batch([message1, message2, message3])
    assert memory.count() == 3
    
    # Wait for message2 to expire
    time.sleep(1.1)
    
    # Test get() method filters expired messages
    messages = memory.get()
    assert len(messages) == 2
    assert message2 not in messages
    
    # Test get_by_role() method filters expired messages
    messages = memory.get_by_role("user2")
    assert len(messages) == 0
    
    # Test get_by_role() for non-expired messages
    messages = memory.get_by_role("user1")
    assert len(messages) == 2
    
    # Test get_by_content() method filters expired messages
    messages = memory.get_by_content("expire")
    assert len(messages) == 2
    assert message2 not in messages
    
    # Test try_remember() method filters expired messages
    messages = memory.try_remember("expire")
    assert len(messages) == 2
    assert message2 not in messages
    
    # Test get_by_action() method filters expired messages
    messages = memory.get_by_action(UserRequirement)
    assert len(messages) == 2
    assert message2 not in messages
    
    # Test get_by_actions() method filters expired messages
    messages = memory.get_by_actions({UserRequirement})
    assert len(messages) == 2
    assert message2 not in messages
    
    # Test get_by_position() method returns None for expired messages
    # Note: message2 is at position 1 in storage
    message = memory.get_by_position(1)
    assert message is None


def test_memory_backward_compatibility():
    """Test backward compatibility with existing code"""
    memory = Memory()
    
    # Create messages without specifying ttl (should use default -1)
    message1 = Message(content="message1", role="user1")
    message2 = Message(content="message2", role="user2")
    
    # Verify default ttl is -1
    assert message1.ttl == -1
    assert message2.ttl == -1
    
    # Add to memory
    memory.add_batch([message1, message2])
    
    # Verify all retrieval methods work as before
    assert memory.count() == 2
    
    messages = memory.get()
    assert len(messages) == 2
    
    messages = memory.get_by_role("user1")
    assert len(messages) == 1
    assert messages[0].content == "message1"
    
    messages = memory.get_by_content("message")
    assert len(messages) == 2
    
    # Verify messages don't expire
    time.sleep(0.5)
    assert message1.is_expired() == False
    assert message2.is_expired() == False
    
    messages = memory.get()
    assert len(messages) == 2
