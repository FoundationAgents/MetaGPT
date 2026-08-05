"""CCS Security Guard for MetaGPT shell execution.

Integrates CCS (Cross-framework Command Security) verification into MetaGPT's
shell_execute() function to provide runtime verification against:
- Remote Code Execution (RCE) attacks
- Server-Side Request Forgery (SSRF)
- Credential/secret leakage
- Path traversal and command injection

Usage:
    from examples.ccs_security.ccs_guard import safe_shell_execute
    stdout, stderr, rc = await safe_shell_execute("ls -la")
"""
import logging
from typing import Dict, List, Tuple, Union
from pathlib import Path

try:
    from ccs_verifier import Verifier, Command
    from ccs_verifier.builtin_rules import RCERule, SSRFRule, CredentialLeakRule
    CCS_AVAILABLE = True
except ImportError:
    CCS_AVAILABLE = False

logger = logging.getLogger(__name__)

_VERIFIER = None

def _get_verifier() -> "Verifier | None":
    """Lazy-initialize CCS verifier with built-in security rules."""
    global _VERIFIER
    if not CCS_AVAILABLE:
        logger.warning("ccs-verifier not installed. Install with: pip install ccs-verifier")
        return None
    if _VERIFIER is None:
        _VERIFIER = Verifier(rules=[RCERule(), SSRFRule(), CredentialLeakRule()])
    return _VERIFIER


async def safe_shell_execute(
    command: Union[List[str], str],
    cwd: str | Path = None,
    env: Dict = None,
    timeout: int = 600,
    agent_id: str = "metagpt-agent",
) -> Tuple[str, str, int]:
    """CCS-verified shell execution for MetaGPT.

    Wraps MetaGPT's shell_execute() with CCS runtime verification.
    Commands are verified in-process (~7.5μs P50) before execution.

    Args:
        command: Command to execute (string for shell, list for direct exec).
        cwd: Working directory.
        env: Environment variables.
        timeout: Timeout in seconds.
        agent_id: Agent identifier for CCS audit trail.

    Returns:
        Tuple of (stdout, stderr, returncode).
        Returns ("", "[CCS] Command denied: {reason}", -1) if blocked.
    """
    verifier = _get_verifier()
    cmd_str = command if isinstance(command, str) else " ".join(command)

    if verifier is not None:
        ccs_cmd = Command(
            agent_id=agent_id,
            tool="shell",
            params={"command": cmd_str, "cwd": str(cwd) if cwd else None},
        )
        result = verifier.verify(ccs_cmd)
        if result.verdict.value == "deny":
            reason = getattr(result, "reason", "unknown") or "policy violation"
            logger.warning(f"[CCS] Command denied: {cmd_str[:80]}... | reason={reason}")
            return "", f"[CCS] Command denied: {reason}", -1

    # Delegate to MetaGPT's original shell_execute
    from metagpt.tools.libs.shell import shell_execute
    return await shell_execute(command=command, cwd=cwd, env=env, timeout=timeout)
