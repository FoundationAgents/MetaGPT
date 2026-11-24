"""Regression test for examples/ui_with_chainlit: concurrent sessions must not share one UI message (#2218).

chainlit and the metagpt modules the example imports are replaced with tiny fakes so the test runs without them.
"""

import asyncio
import importlib.util
import sys
import types
from pathlib import Path

import pytest

EXAMPLE = Path(__file__).parents[2] / "examples" / "ui_with_chainlit" / "init_setup.py"


class FakeMessage:
    def __init__(self, content=""):
        self.content = content
        self.sent = False

    async def stream_token(self, token):
        self.content += token

    async def send(self):
        self.sent = True


@pytest.fixture
def init_setup(monkeypatch):
    def module(name, **attrs):
        mod = types.ModuleType(name)
        mod.__dict__.update(attrs)
        monkeypatch.setitem(sys.modules, name, mod)

    stream = {}
    # the streaming callback is synchronous and calls cl.run_sync(coro); the fake coroutines never suspend
    module("chainlit", Message=FakeMessage, run_sync=lambda coro: _drive(coro))
    module("metagpt")
    module("metagpt.environment", Environment=type("Environment", (), {}))
    module("metagpt.logs", logger=types.SimpleNamespace(debug=lambda *_: None))
    sys.modules["metagpt.logs"].set_llm_stream_logfunc = lambda func: stream.update(func=func)
    module("metagpt.roles", Role=object)
    module("metagpt.utils")
    module("metagpt.utils.common", any_to_name=str)

    spec = importlib.util.spec_from_file_location("chainlit_init_setup_under_test", EXAMPLE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.stream = stream["func"]
    return mod


def _drive(coro):
    try:
        coro.send(None)
    except StopIteration:
        pass


class FakeRole:
    """Streams its tokens through the registered callback, yielding to the event loop between tokens."""

    def __init__(self, stream, tokens, gate):
        self.stream, self.tokens, self.gate = stream, tokens, gate
        self._setting = "fake"

    async def run(self):
        for token in self.tokens:
            self.stream(token)
            await self.gate.wait()  # let the other session run in between
        return types.SimpleNamespace(content="done", cause_by="FakeAction")


def test_concurrent_sessions_keep_separate_messages(init_setup, monkeypatch):
    created = []
    real_init = FakeMessage.__init__

    def tracking_init(self, content=""):
        real_init(self, content)
        created.append(self)

    monkeypatch.setattr(FakeMessage, "__init__", tracking_init)

    async def main():
        env = init_setup.ChainlitEnv()
        gate = asyncio.Event()
        a = FakeRole(init_setup.stream, ["A1 ", "A2 ", "A3"], gate)
        b = FakeRole(init_setup.stream, ["B1 ", "B2 ", "B3"], gate)
        # two sessions' on_message handlers are separate tasks on one loop
        tasks = [asyncio.create_task(env._chainlit_role_run(a)), asyncio.create_task(env._chainlit_role_run(b))]
        for _ in range(5):
            await asyncio.sleep(0)
            gate.set()
            gate.clear()
        gate.set()
        await asyncio.gather(*tasks)

    asyncio.run(main())

    msg_a, msg_b = created
    assert msg_a.sent and msg_b.sent
    # text before the "---" footer is exactly what that session streamed
    assert msg_a.content.split("---")[0] == "A1 A2 A3"
    assert msg_b.content.split("---")[0] == "B1 B2 B3"
