# -*- coding: utf-8 -*-
"""
Regression test for metagpt-eval-exec-tot-generate-thoughts-eval.

ThoughtSolverBase.generate_thoughts used to `eval()` the model's generated
thought block, which allowed arbitrary code execution from model output.
It now uses `ast.literal_eval`, which only accepts literal data structures.

These tests verify:
  * a benign list-of-dicts thought block is still parsed correctly, and
  * a malicious (non-literal) payload does NOT execute and is ignored.

The Tree-of-Thoughts solver is exercised with a fully mocked LLM. The real
``metagpt.llm.LLM`` factory builds a provider from ``Config`` (api key, proxy,
base url, ...), which touches a real configuration and the network. To stay
config-independent and offline, the mock LLM is passed straight into the
constructor: ``ThoughtSolverBase.llm`` declares ``default_factory=LLM``, and
pydantic only calls that factory when no value is supplied, so providing
``llm=`` means the real factory is never invoked (assigning ``solver.llm``
afterwards would be too late -- the factory runs during ``__init__``).
Following the existing suite (e.g. ``tests/metagpt/test_role.py``) the mock is a
``MagicMock(spec=BaseLLM)`` with an ``AsyncMock`` ``aask`` returning canned text.
As a safety net ``create_llm_instance`` is patched to fail loudly if anything
still tries to build a real provider.
"""

import ast
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from metagpt.config2 import config
from metagpt.provider.base_llm import BaseLLM
from metagpt.strategy.base import BaseParser, ThoughtNode, ThoughtTree
from metagpt.strategy.tot import ThoughtSolverBase
from metagpt.strategy.tot_schema import ThoughtSolverConfig


@pytest.fixture(autouse=True, scope="module")
def _restore_global_llm_proxy():
    """Keep the global ``config.llm.proxy`` sane while this module runs.

    The session-wide autouse ``llm_mock`` fixture (tests/conftest.py) builds a
    real ``MockLLM`` -> ``OpenAILLM`` for *every* test, which constructs an httpx
    client and validates ``config.llm.proxy``. Some earlier-collected test
    modules assign a non-URL object straight onto the shared ``config.llm``
    instance (e.g. ``config.get_openai_llm().proxy = mocker.PropertyMock(...)``);
    that assignment is a plain attribute write, so it is never rolled back and
    leaks into later modules. When ``llm_mock`` then runs for our tests the bad
    proxy makes httpx raise ``ValueError: Proxy protocol must be ...``.

    Being module-scoped, this autouse fixture is set up before the function-scoped
    ``llm_mock``, so it neutralises any such leaked value before ``MockLLM`` is
    built, and restores the original afterwards. It does not change behaviour for
    any other test module.
    """
    saved_proxy = config.llm.proxy
    if not isinstance(config.llm.proxy, str):
        config.llm.proxy = None
    yield
    config.llm.proxy = saved_proxy


class _StubParser(BaseParser):
    def propose(self, current_state: str, **kwargs) -> str:
        return "propose"


@pytest.fixture
def no_real_llm(mocker):
    """Guarantee no real LLM provider is constructed (no Config/proxy/network)."""

    def _boom(*args, **kwargs):
        raise AssertionError("create_llm_instance must not be called: real LLM was built")

    mocker.patch("metagpt.provider.llm_provider_registry.create_llm_instance", side_effect=_boom)
    mocker.patch("metagpt.context.create_llm_instance", side_effect=_boom)


def _make_solver(response: str) -> ThoughtSolverBase:
    """Build a solver whose LLM is fully mocked.

    The mock is passed via the ``llm=`` constructor argument so pydantic never
    falls back to ``default_factory=LLM`` -- i.e. no real provider, Config,
    proxy resolution, or network access happens at construction time.
    """
    mock_llm = MagicMock(spec=BaseLLM)
    mock_llm.aask = AsyncMock(return_value=response)
    mock_llm.use_system_prompt = True

    solver = ThoughtSolverBase(llm=mock_llm, config=ThoughtSolverConfig(parser=_StubParser()))
    assert solver.llm is mock_llm  # guard: the real LLM factory was never used
    solver.thought_tree = ThoughtTree(ThoughtNode(name="root"))
    return solver


@pytest.mark.asyncio
async def test_generate_thoughts_parses_benign_list(no_real_llm):
    response = (
        "```json\n"
        '[{"node_id": "1", "node_state_instruction": "first thought"},\n'
        ' {"node_id": "2", "node_state_instruction": "second thought"}]\n'
        "```"
    )
    solver = _make_solver(response)
    nodes = await solver.generate_thoughts(current_state="", current_node=None)
    assert [n.name for n in nodes] == ["first thought", "second thought"]
    assert [n.id for n in nodes] == [1, 2]


@pytest.mark.asyncio
async def test_generate_thoughts_does_not_execute_model_code(no_real_llm, tmp_path: Path):
    sentinel = tmp_path / "tot_pwned"
    # A literal-only parser must refuse to run this; with eval() it would execute.
    payload = f"```python\n[__import__('os').system('touch {sentinel}')]\n```"
    solver = _make_solver(payload)

    # Swallow any downstream error so the discriminating signal is purely the
    # side effect: on the vulnerable (eval) code path the sentinel file is
    # created before any exception; on the fixed (ast.literal_eval) path it is not.
    try:
        nodes = await solver.generate_thoughts(current_state="", current_node=None)
    except Exception:
        nodes = None

    assert not sentinel.exists(), "model-supplied code was executed (eval sink still live)"
    assert nodes == []


def test_literal_eval_rejects_code():
    # Guard the underlying primitive directly.
    with pytest.raises((ValueError, SyntaxError)):
        ast.literal_eval("__import__('os').system('id')")
