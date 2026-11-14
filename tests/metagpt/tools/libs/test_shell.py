#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio
import sys

import pytest

from metagpt.tools.libs.shell import shell_execute


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["command", "expect_stdout", "expect_stderr"],
    [
        (["file", f"{__file__}"], "Python script text executable, ASCII text", ""),
        (f"file {__file__}", "Python script text executable, ASCII text", ""),
    ],
)
async def test_shell(command, expect_stdout, expect_stderr):
    stdout, stderr, returncode = await shell_execute(command)
    assert returncode == 0
    assert expect_stdout in stdout
    assert stderr == expect_stderr


@pytest.mark.asyncio
async def test_shell_execute_does_not_block_event_loop():
    """A running command must not starve the event loop, concurrent coroutines keep running."""
    ticks = 0
    stop = asyncio.Event()

    async def tick():
        nonlocal ticks
        while not stop.is_set():
            ticks += 1
            await asyncio.sleep(0.01)

    ticker = asyncio.create_task(tick())
    await asyncio.sleep(0.05)  # let the ticker run a few times first

    ticks_before = ticks
    await shell_execute([sys.executable, "-c", "import time; time.sleep(0.5)"])
    ticks_during_command = ticks - ticks_before

    stop.set()
    await ticker

    # 0.5s of command with a 10ms ticker is about 50 ticks; a blocking call yields (almost) none.
    assert ticks_during_command >= 20, f"event loop blocked while the command ran: {ticks_during_command} ticks"


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
