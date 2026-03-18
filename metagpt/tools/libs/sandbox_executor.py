#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2024/3/18
@File    : sandbox_executor.py
@Desc    : OpenSandbox executor for isolated code and command execution.
"""
from __future__ import annotations

import asyncio
from datetime import timedelta
from pathlib import Path
from typing import Optional, Tuple

from metagpt.configs.sandbox_config import SandboxConfig
from metagpt.logs import logger

try:
    from code_interpreter import CodeInterpreter, SupportedLanguage
    from opensandbox import Sandbox
    from opensandbox.config import ConnectionConfig
    from opensandbox.models.execd import RunCommandOpts

    HAS_OPENSANDBOX = True
except ImportError:
    HAS_OPENSANDBOX = False


class SandboxExecutor:
    """Manages an OpenSandbox instance for isolated code and command execution.

    Usage:
        executor = await SandboxExecutor.create(config)
        stdout, stderr = await executor.run_code("print('hello')")
        stdout, stderr, rc = await executor.run_command("ls -la")
        await executor.cleanup()
    """

    def __init__(self):
        self._sandbox: Optional[Sandbox] = None
        self._interpreter: Optional[CodeInterpreter] = None
        self._config: Optional[SandboxConfig] = None
        self._lock = asyncio.Lock()

    @classmethod
    async def create(cls, config: SandboxConfig) -> "SandboxExecutor":
        """Create and initialize a SandboxExecutor with an OpenSandbox instance."""
        if not HAS_OPENSANDBOX:
            raise ImportError(
                "opensandbox and opensandbox-code-interpreter packages are required. "
                "Install with: pip install opensandbox opensandbox-code-interpreter"
            )

        executor = cls()
        executor._config = config
        await executor._ensure_sandbox()
        return executor

    async def _ensure_sandbox(self):
        """Ensure sandbox and interpreter are initialized."""
        async with self._lock:
            if self._sandbox is not None:
                return

            config = self._config
            conn_config = ConnectionConfig(
                domain=config.domain,
                api_key=config.api_key,
            )

            sandbox_kwargs = {
                "connection_config": conn_config,
                "timeout": timedelta(seconds=config.timeout),
                "entrypoint": config.entrypoint,
                "resource": config.resource,
            }
            if config.env:
                sandbox_kwargs["env"] = config.env
            if config.network_policy:
                sandbox_kwargs["network_policy"] = config.network_policy

            logger.info(f"Creating OpenSandbox instance with image={config.image}")
            self._sandbox = await Sandbox.create(config.image, **sandbox_kwargs)
            self._interpreter = await CodeInterpreter.create(sandbox=self._sandbox)
            logger.info(f"OpenSandbox instance created: id={self._sandbox.id}")

    async def run_code(self, code: str, language: str = "python") -> Tuple[str, str]:
        """Execute code in the sandbox via CodeInterpreter.

        Args:
            code: Source code to execute.
            language: Programming language (python, java, go, typescript, bash, javascript).

        Returns:
            Tuple of (stdout, stderr).
        """
        await self._ensure_sandbox()

        execution = await self._interpreter.codes.run(code, language=language)

        stdout = "\n".join(msg.text for msg in execution.logs.stdout)
        stderr = "\n".join(msg.text for msg in execution.logs.stderr)

        if execution.result:
            result_text = "\n".join(r.text for r in execution.result if r.text)
            if result_text:
                stdout = f"{stdout}\n{result_text}" if stdout else result_text

        if execution.error:
            err_msg = f"{execution.error.name}: {execution.error.value}"
            if execution.error.traceback:
                err_msg = "\n".join(execution.error.traceback) + "\n" + err_msg
            stderr = f"{stderr}\n{err_msg}" if stderr else err_msg

        return stdout, stderr

    async def run_command(
        self, cmd: str, timeout: int = 600, working_directory: str = None
    ) -> Tuple[str, str, int]:
        """Execute a shell command in the sandbox.

        Args:
            cmd: Shell command to execute.
            timeout: Timeout in seconds.
            working_directory: Working directory for the command.

        Returns:
            Tuple of (stdout, stderr, returncode).
        """
        await self._ensure_sandbox()

        opts = RunCommandOpts(timeout=timedelta(seconds=timeout))
        if working_directory:
            opts.working_directory = working_directory

        execution = await self._sandbox.commands.run(cmd, opts=opts)

        stdout = "\n".join(msg.text for msg in execution.logs.stdout)
        stderr = "\n".join(msg.text for msg in execution.logs.stderr)

        exit_code = 0
        if execution.error:
            exit_code = 1
            err_msg = f"{execution.error.name}: {execution.error.value}"
            stderr = f"{stderr}\n{err_msg}" if stderr else err_msg

        return stdout, stderr, exit_code

    async def upload_file(self, local_path: str, remote_path: str):
        """Upload a local file to the sandbox.

        Args:
            local_path: Path to the local file.
            remote_path: Destination path inside the sandbox.
        """
        await self._ensure_sandbox()
        content = Path(local_path).read_text()
        await self._sandbox.files.write_file(remote_path, content)

    async def upload_content(self, content: str, remote_path: str):
        """Upload string content to the sandbox as a file.

        Args:
            content: File content to upload.
            remote_path: Destination path inside the sandbox.
        """
        await self._ensure_sandbox()
        await self._sandbox.files.write_file(remote_path, content)

    async def download_file(self, remote_path: str) -> str:
        """Download a file from the sandbox.

        Args:
            remote_path: Path to the file inside the sandbox.

        Returns:
            File content as string.
        """
        await self._ensure_sandbox()
        return await self._sandbox.files.read_file(remote_path)

    async def cleanup(self):
        """Kill the sandbox and release resources."""
        if self._sandbox is not None:
            try:
                await self._sandbox.kill()
                logger.info(f"OpenSandbox instance {self._sandbox.id} killed")
            except Exception as e:
                logger.warning(f"Failed to kill sandbox: {e}")
            finally:
                self._sandbox = None
                self._interpreter = None


# Global singleton for sandbox executor reuse across the session
_global_executor: Optional[SandboxExecutor] = None
_global_lock = asyncio.Lock()


async def get_sandbox_executor(config: SandboxConfig) -> SandboxExecutor:
    """Get or create the global SandboxExecutor singleton.

    Args:
        config: SandboxConfig instance.

    Returns:
        The shared SandboxExecutor instance.
    """
    global _global_executor
    async with _global_lock:
        if _global_executor is None:
            _global_executor = await SandboxExecutor.create(config)
        return _global_executor


async def cleanup_sandbox_executor():
    """Cleanup the global SandboxExecutor."""
    global _global_executor
    async with _global_lock:
        if _global_executor is not None:
            await _global_executor.cleanup()
            _global_executor = None
