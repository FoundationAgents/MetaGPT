"""Override the global autouse llm_mock fixture for tests in metagpt/utils/.

The global tests/conftest.py defines an autouse=True fixture `llm_mock`
that initialises MockLLM (and its underlying AsyncHttpxClientWrapper).
On CI runners that set HTTP_PROXY / HTTPS_PROXY environment variables,
httpx rejects the proxy scheme, breaking every test in this package.

Since our tests are pure-Python (no LLM dependency needed), override
the fixture with a noop to bypass the problematic initialisation.
"""
import pytest


@pytest.fixture(scope="function", autouse=True)
def llm_mock():
    """Noop override — these tests don't need LLM mocking."""
    yield None
