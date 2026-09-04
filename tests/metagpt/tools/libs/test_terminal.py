import asyncio

import pytest

from metagpt.const import DATA_PATH, METAGPT_ROOT
from metagpt.tools.libs.terminal import Terminal


@pytest.mark.asyncio
async def test_terminal():
    terminal = Terminal()

    try:
        await asyncio.wait_for(terminal.run_command(f"cd {METAGPT_ROOT}"), timeout=5)
        output = await asyncio.wait_for(terminal.run_command("pwd"), timeout=5)
        assert output.strip() == str(METAGPT_ROOT)

        # pwd now should be METAGPT_ROOT, cd data should land in DATA_PATH
        await asyncio.wait_for(terminal.run_command("cd data"), timeout=5)
        output = await asyncio.wait_for(terminal.run_command("pwd"), timeout=5)
        assert output.strip() == str(DATA_PATH)
    finally:
        await terminal.close()


if __name__ == "__main__":
    pytest.main([__file__, "-s"])
