#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Unit tests for SandboxExecutor with mocked OpenSandbox SDK.

All metagpt imports are avoided at module level to prevent the conftest.py
autouse llm_mock fixture from triggering httpx proxy initialization in CI.
The sandbox_executor module is loaded in complete isolation via exec().
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import BaseModel

_PROJECT_ROOT = Path(__file__).resolve().parents[4]


# ---------------------------------------------------------------------------
# Standalone SandboxConfig replica (avoids importing metagpt at all)
# ---------------------------------------------------------------------------

class SandboxConfigForTest(BaseModel):
    """Mirror of metagpt.configs.sandbox_config.SandboxConfig for testing."""

    enabled: bool = False
    domain: str = ""
    api_key: str = ""
    image: str = "opensandbox/code-interpreter:v1.0.2"
    entrypoint: List[str] = ["/opt/opensandbox/code-interpreter.sh"]
    timeout: int = 600
    resource: Dict[str, str] = {"cpu": "1", "memory": "2Gi"}
    env: Dict[str, str] = {}
    network_policy: Optional[Dict] = None


# ---------------------------------------------------------------------------
# Isolated module loading for sandbox_executor
# ---------------------------------------------------------------------------

def _exec_file_isolated(filepath: Path, global_overrides: dict = None):
    """Execute a Python file in an isolated namespace and return it."""
    ns = {"__name__": filepath.stem, "__file__": str(filepath)}
    if global_overrides:
        ns.update(global_overrides)
    code = filepath.read_text()
    exec(compile(code, str(filepath), "exec"), ns)
    return ns


def _build_sandbox_executor_module():
    """Build sandbox_executor module without importing metagpt.tools."""
    import sys

    mock_logger = MagicMock()

    # Provide minimal fakes for metagpt dependencies
    fake_sandbox_config = type("module", (), {"SandboxConfig": object})()
    fake_logs = type("module", (), {"logger": mock_logger})()

    # Fake opensandbox SDK
    fake_opensandbox = MagicMock()
    fake_code_interpreter = MagicMock()

    inject = {
        "metagpt.configs.sandbox_config": fake_sandbox_config,
        "metagpt.logs": fake_logs,
        "opensandbox": fake_opensandbox,
        "opensandbox.config": MagicMock(),
        "opensandbox.models.execd": MagicMock(),
        "code_interpreter": fake_code_interpreter,
        "code_interpreter.models.code": MagicMock(),
    }

    saved = {}
    for k, v in inject.items():
        if k in sys.modules:
            saved[k] = sys.modules[k]
        sys.modules[k] = v
    try:
        ns = _exec_file_isolated(_PROJECT_ROOT / "metagpt" / "tools" / "libs" / "sandbox_executor.py")
    finally:
        for k in inject:
            if k in saved:
                sys.modules[k] = saved[k]
            else:
                sys.modules.pop(k, None)

    return ns


# ---------------------------------------------------------------------------
# Module-scoped fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def se():
    return _build_sandbox_executor_module()


# ---------------------------------------------------------------------------
# Per-test fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sandbox_config():
    return SandboxConfigForTest(
        enabled=True,
        domain="localhost:8080",
        api_key="test-key",
        image="opensandbox/code-interpreter:v1.0.2",
        timeout=600,
    )


@pytest.fixture
def executor_factory(se):
    """Returns an async factory that creates a SandboxExecutor with mocked SDK."""

    async def _create(config):
        mock_sandbox = AsyncMock()
        mock_sandbox.id = "test-sandbox-123"
        mock_sandbox.commands = AsyncMock()
        mock_sandbox.files = AsyncMock()
        mock_sandbox.kill = AsyncMock()

        mock_interpreter = AsyncMock()
        mock_interpreter.codes = AsyncMock()

        se["HAS_OPENSANDBOX"] = True
        se["Sandbox"] = MagicMock()
        se["Sandbox"].create = AsyncMock(return_value=mock_sandbox)
        se["CodeInterpreter"] = MagicMock()
        se["CodeInterpreter"].create = AsyncMock(return_value=mock_interpreter)
        se["ConnectionConfig"] = MagicMock()
        se["RunCommandOpts"] = MagicMock()
        se["_global_executor"] = None

        SandboxExecutor = se["SandboxExecutor"]
        executor = await SandboxExecutor.create(config)
        return executor, mock_sandbox, mock_interpreter

    return _create


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_output_message(text):
    msg = MagicMock()
    msg.text = text
    return msg


def _make_execution(stdout_texts=None, stderr_texts=None, result_texts=None, error=None):
    execution = MagicMock()
    execution.logs = MagicMock()
    execution.logs.stdout = [_make_output_message(t) for t in (stdout_texts or [])]
    execution.logs.stderr = [_make_output_message(t) for t in (stderr_texts or [])]
    execution.result = []
    if result_texts:
        for t in result_texts:
            r = MagicMock()
            r.text = t
            execution.result.append(r)
    execution.error = error
    return execution


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sandbox_config_defaults():
    """Verify the test config mirror matches expected defaults."""
    config = SandboxConfigForTest()
    assert config.enabled is False
    assert config.domain == ""
    assert config.api_key == ""
    assert config.image == "opensandbox/code-interpreter:v1.0.2"
    assert config.timeout == 600
    assert config.resource == {"cpu": "1", "memory": "2Gi"}


@pytest.mark.asyncio
async def test_create_executor(sandbox_config, executor_factory, se):
    executor, sandbox, interpreter = await executor_factory(sandbox_config)

    se["Sandbox"].create.assert_called_once()
    se["CodeInterpreter"].create.assert_called_once()
    assert executor._sandbox is not None
    assert executor._interpreter is not None

    await executor.cleanup()


@pytest.mark.asyncio
async def test_run_code_success(sandbox_config, executor_factory):
    executor, sandbox, interpreter = await executor_factory(sandbox_config)

    execution = _make_execution(stdout_texts=["hello world"], result_texts=["42"])
    interpreter.codes.run = AsyncMock(return_value=execution)

    stdout, stderr = await executor.run_code("print('hello world')\n42")

    assert "hello world" in stdout
    assert "42" in stdout
    assert stderr == ""

    await executor.cleanup()


@pytest.mark.asyncio
async def test_run_code_error(sandbox_config, executor_factory):
    executor, sandbox, interpreter = await executor_factory(sandbox_config)

    error = MagicMock()
    error.name = "NameError"
    error.value = "name 'x' is not defined"
    error.traceback = ["Traceback (most recent call last):", "  File ...", "NameError: name 'x' is not defined"]

    execution = _make_execution(error=error)
    interpreter.codes.run = AsyncMock(return_value=execution)

    stdout, stderr = await executor.run_code("print(x)")

    assert "NameError" in stderr
    assert "name 'x' is not defined" in stderr

    await executor.cleanup()


@pytest.mark.asyncio
async def test_run_command_success(sandbox_config, executor_factory):
    executor, sandbox, interpreter = await executor_factory(sandbox_config)

    execution = _make_execution(stdout_texts=["file1.py\nfile2.py"])
    sandbox.commands.run = AsyncMock(return_value=execution)

    stdout, stderr, rc = await executor.run_command("ls *.py")

    assert "file1.py" in stdout
    assert rc == 0

    await executor.cleanup()


@pytest.mark.asyncio
async def test_upload_and_download_file(sandbox_config, executor_factory):
    executor, sandbox, interpreter = await executor_factory(sandbox_config)

    sandbox.files.read_file = AsyncMock(return_value="file content")

    await executor.upload_content("test content", "/workspace/test.py")
    sandbox.files.write_file.assert_called_with("/workspace/test.py", "test content")

    content = await executor.download_file("/workspace/test.py")
    assert content == "file content"

    await executor.cleanup()


@pytest.mark.asyncio
async def test_cleanup(sandbox_config, executor_factory):
    executor, sandbox, interpreter = await executor_factory(sandbox_config)

    await executor.cleanup()

    sandbox.kill.assert_called_once()
    assert executor._sandbox is None
    assert executor._interpreter is None


@pytest.mark.asyncio
async def test_singleton_executor(sandbox_config, se):
    se["_global_executor"] = None

    mock_sandbox = AsyncMock()
    mock_sandbox.id = "test-singleton"
    mock_sandbox.commands = AsyncMock()
    mock_sandbox.files = AsyncMock()
    mock_sandbox.kill = AsyncMock()

    mock_interpreter = AsyncMock()
    mock_interpreter.codes = AsyncMock()

    se["HAS_OPENSANDBOX"] = True
    se["Sandbox"] = MagicMock()
    se["Sandbox"].create = AsyncMock(return_value=mock_sandbox)
    se["CodeInterpreter"] = MagicMock()
    se["CodeInterpreter"].create = AsyncMock(return_value=mock_interpreter)
    se["ConnectionConfig"] = MagicMock()
    se["RunCommandOpts"] = MagicMock()

    get_sandbox_executor = se["get_sandbox_executor"]
    cleanup_sandbox_executor = se["cleanup_sandbox_executor"]

    executor1 = await get_sandbox_executor(sandbox_config)
    executor2 = await get_sandbox_executor(sandbox_config)
    assert executor1 is executor2

    await cleanup_sandbox_executor()
    assert se["_global_executor"] is None
