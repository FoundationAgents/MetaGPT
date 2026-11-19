#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ResourceReporter must not leave the LLM stream task behind when it is cancelled."""

import asyncio

import pytest

from metagpt.utils.report import BlockType, ResourceReporter


@pytest.mark.asyncio
async def test_cancelled_context_stops_the_llm_stream_task():
    """A cancellation skips the sentinel, so the task has to be cancelled and awaited."""
    reporter = ResourceReporter(block=BlockType.THOUGHT, enable_llm_stream=True, callback_url="")

    async def run() -> None:
        async with reporter:
            await asyncio.sleep(30)

    outer = asyncio.create_task(run())
    await asyncio.sleep(0.05)
    stream_task = reporter._llm_task
    assert stream_task is not None

    outer.cancel()
    with pytest.raises(asyncio.CancelledError):
        await outer

    # Observed inside the loop: the task must already be finished, not left on queue.get().
    assert stream_task.done()
    assert reporter._llm_task is None


@pytest.mark.asyncio
async def test_normal_exit_still_stops_the_llm_stream_task():
    """The sentinel path is unchanged for a regular exit."""
    reporter = ResourceReporter(block=BlockType.THOUGHT, enable_llm_stream=True, callback_url="")

    async with reporter:
        stream_task = reporter._llm_task
        assert stream_task is not None

    assert stream_task.done()
    assert not stream_task.cancelled()
    assert reporter._llm_task is None
