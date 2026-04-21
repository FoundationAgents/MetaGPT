#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/20 12:15
@Author  : alexanderwu
@File    : memory.py
@Modified By: mashenquan, 2023-11-1. According to RFC 116: Updated the type of index key.
@Modified By: 2026-04-21. Added TTL (Time-To-Live) support for messages with automatic cleanup.
"""
import asyncio
from collections import defaultdict
from typing import DefaultDict, Iterable, Optional, Set

from pydantic import BaseModel, Field, PrivateAttr, SerializeAsAny

from metagpt.const import IGNORED_MESSAGE_ID
from metagpt.schema import Message
from metagpt.utils.common import any_to_str, any_to_str_set
from metagpt.utils.exceptions import handle_exception


class Memory(BaseModel):
    """The most basic memory: super-memory"""

    storage: list[SerializeAsAny[Message]] = []
    index: DefaultDict[str, list[SerializeAsAny[Message]]] = Field(default_factory=lambda: defaultdict(list))
    ignore_id: bool = False

    _cleanup_task: Optional[asyncio.Task] = PrivateAttr(default=None)
    _is_running: bool = PrivateAttr(default=False)

    def _cleanup_expired_messages(self) -> int:
        """Remove all expired messages from storage and index.
        
        Returns:
            int: The number of expired messages that were removed.
        """
        expired_messages = [message for message in self.storage if message.is_expired()]
        
        for message in expired_messages:
            self.storage.remove(message)
            if message.cause_by and message in self.index[message.cause_by]:
                self.index[message.cause_by].remove(message)
        
        return len(expired_messages)

    def add(self, message: Message):
        """Add a new message to storage, while updating the index"""
        if self.ignore_id:
            message.id = IGNORED_MESSAGE_ID
        if message in self.storage:
            return
        self.storage.append(message)
        if message.cause_by:
            self.index[message.cause_by].append(message)

    def add_batch(self, messages: Iterable[Message]):
        for message in messages:
            self.add(message)

    def get_by_role(self, role: str) -> list[Message]:
        """Return all messages of a specified role"""
        self._cleanup_expired_messages()
        return [message for message in self.storage if message.role == role]

    def get_by_content(self, content: str) -> list[Message]:
        """Return all messages containing a specified content"""
        self._cleanup_expired_messages()
        return [message for message in self.storage if content in message.content]

    def delete_newest(self) -> "Message":
        """delete the newest message from the storage"""
        if len(self.storage) > 0:
            newest_msg = self.storage.pop()
            if newest_msg.cause_by and newest_msg in self.index[newest_msg.cause_by]:
                self.index[newest_msg.cause_by].remove(newest_msg)
        else:
            newest_msg = None
        return newest_msg

    def delete(self, message: Message):
        """Delete the specified message from storage, while updating the index"""
        if self.ignore_id:
            message.id = IGNORED_MESSAGE_ID
        self.storage.remove(message)
        if message.cause_by and message in self.index[message.cause_by]:
            self.index[message.cause_by].remove(message)

    def clear(self):
        """Clear storage and index"""
        self.storage = []
        self.index = defaultdict(list)

    def count(self) -> int:
        """Return the number of messages in storage"""
        self._cleanup_expired_messages()
        return len(self.storage)

    def try_remember(self, keyword: str) -> list[Message]:
        """Try to recall all messages containing a specified keyword"""
        self._cleanup_expired_messages()
        return [message for message in self.storage if keyword in message.content]

    def get(self, k=0) -> list[Message]:
        """Return the most recent k memories, return all when k=0"""
        self._cleanup_expired_messages()
        return self.storage[-k:]

    def find_news(self, observed: list[Message], k=0) -> list[Message]:
        """find news (previously unseen messages) from the most recent k memories, from all memories when k=0"""
        already_observed = self.get(k)
        news: list[Message] = []
        for i in observed:
            if i in already_observed:
                continue
            news.append(i)
        return news

    def get_by_action(self, action) -> list[Message]:
        """Return all messages triggered by a specified Action"""
        self._cleanup_expired_messages()
        index = any_to_str(action)
        return self.index[index]

    def get_by_actions(self, actions: Set) -> list[Message]:
        """Return all messages triggered by specified Actions"""
        self._cleanup_expired_messages()
        rsp = []
        indices = any_to_str_set(actions)
        for action in indices:
            if action not in self.index:
                continue
            rsp += self.index[action]
        return rsp

    @handle_exception
    def get_by_position(self, position: int) -> Optional[Message]:
        """Returns the message at the given position if valid and not expired, otherwise returns None"""
        self._cleanup_expired_messages()
        if position < 0 or position >= len(self.storage):
            return None
        return self.storage[position]

    async def _periodic_cleanup(self, interval: int = 60):
        """Asynchronous background task that periodically cleans up expired messages.
        
        Args:
            interval: The time in seconds between each cleanup check.
        """
        while self._is_running:
            try:
                self._cleanup_expired_messages()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error in periodic cleanup: {e}")
                await asyncio.sleep(interval)

    def start(self, cleanup_interval: int = 60):
        """Start the background periodic cleanup task.
        
        Args:
            cleanup_interval: The time in seconds between each cleanup check. Defaults to 60.
        """
        if self._is_running:
            return
        
        self._is_running = True
        
        try:
            loop = asyncio.get_running_loop()
            self._cleanup_task = loop.create_task(self._periodic_cleanup(cleanup_interval))
        except RuntimeError:
            import threading
            from metagpt.utils.async_helper import run_coroutine_in_new_loop
            
            def run_cleanup():
                asyncio.run(self._periodic_cleanup(cleanup_interval))
            
            thread = threading.Thread(target=run_cleanup, daemon=True)
            thread.start()

    def stop(self):
        """Stop the background periodic cleanup task gracefully."""
        self._is_running = False
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None
