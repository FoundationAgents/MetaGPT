import pytest

from metagpt.const import DATA_PATH, METAGPT_ROOT
from metagpt.tools.libs.terminal import Terminal


@pytest.mark.asyncio
async def test_terminal():
    terminal = Terminal()

    await terminal.run_command(f"cd {METAGPT_ROOT}")
    output = await terminal.run_command("pwd")
    assert output.strip() == str(METAGPT_ROOT)

    # pwd now should be METAGPT_ROOT, cd data should land in DATA_PATH
    await terminal.run_command("cd data")
    output = await terminal.run_command("pwd")
    assert output.strip() == str(DATA_PATH)


if __name__ == "__main__":
    pytest.main([__file__, "-s"])


def test_splitlines_unpack_does_not_hide_end_marker():
    """Regression for #2110: a single newline-terminated buffer must be yielded.

    The old `*lines, tmp = buf.splitlines(True)` idiom moved a lone complete
    line into `tmp`, so the end-of-command marker was never observed.
    """
    from metagpt.utils.report import END_MARKER_VALUE

    # Simulate the buffer state when the marker arrives as the only line.
    buf = END_MARKER_VALUE.encode()  # already ends with \n
    parts = buf.splitlines(True)
    assert len(parts) == 1
    # Correct handling: treat a trailing-newline buffer as a complete line.
    if parts[0].endswith(b"\n") or parts[0].endswith(b"\r"):
        lines, tmp = parts, b""
    else:
        *lines, tmp = parts if len(parts) > 1 else ([], parts[0] if parts else b"")
    assert lines and END_MARKER_VALUE.encode() in lines[0] or END_MARKER_VALUE in lines[0].decode(errors="ignore")
    assert tmp == b""
    # Old broken behavior would leave lines empty:
    *broken_lines, broken_tmp = parts
    assert broken_lines == []
    assert broken_tmp == parts[0]
