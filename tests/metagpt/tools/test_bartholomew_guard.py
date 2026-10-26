#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2025/10/26
@Author  : Bartholomew Trust Protocol & MetaGPT Team
@File    : test_bartholomew_guard.py
@Desc    : Unit tests for Bartholomew deterministic AST security guard for MetaGPT.
"""

import unittest
import sys
from pathlib import Path

# Add metagpt/tools to path to enable running unit tests in isolation
tools_dir = Path(__file__).resolve().parent.parent.parent.parent / "metagpt" / "tools"
sys.path.insert(0, str(tools_dir))

try:
    import bartholomew_guard

    BartholomewSecurityGuard = bartholomew_guard.BartholomewSecurityGuard
except ImportError:
    from metagpt.tools.bartholomew_guard import BartholomewSecurityGuard


class TestBartholomewSecurityGuard(unittest.TestCase):
    def setUp(self):
        self.guard = BartholomewSecurityGuard(role_name="MetaGPT-Engineer", fail_closed=True)

    def test_safe_code_emission(self):
        code = "def calculate_velocity(distance, time):\n    return distance / time\n"
        is_safe, reason, receipt = self.guard.validate_code(code)
        self.assertTrue(is_safe)
        self.assertEqual(receipt["verdict"], "ALLOW")
        self.assertTrue("receipt_hash" in receipt)
        self.assertLess(receipt["latency_us"], 5000)

    def test_destructive_rm_rf_veto(self):
        code = "import os\nos.system('rm -rf / --no-preserve-root')"
        with self.assertRaises(PermissionError) as ctx:
            self.guard.validate_code(code)
        self.assertIn("BTP-METAGPT-VETO", str(ctx.exception))
        self.assertIn("BTP-AST-001", str(ctx.exception))

    def test_command_veto(self):
        with self.assertRaises(PermissionError) as ctx:
            self.guard.validate_command("rm -rf /etc")
        self.assertIn("BTP-SHELL-001", str(ctx.exception))

    def test_credential_leak_veto(self):
        code = "token = 'ghp_123456789012345678901234567890123456'"
        with self.assertRaises(PermissionError) as ctx:
            self.guard.validate_code(code)
        self.assertIn("BTP-CRED-001", str(ctx.exception))

    def test_wrap_action(self):
        class MockAction:
            name = "MockDevAction"

            def run(self, cmd: str):
                return f"executed: {cmd}"

        action = self.guard.wrap_action(MockAction())
        self.assertEqual(action.run("git status"), "executed: git status")

        with self.assertRaises(PermissionError):
            action.run("rm -rf /var/log")


if __name__ == "__main__":
    unittest.main()
