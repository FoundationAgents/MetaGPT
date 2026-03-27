#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Security tests for CWE-95: Verify that RunCode.run_text() does not execute
untrusted Python statements from the host process.
"""

import pytest

from metagpt.actions.run_code import RunCode


@pytest.mark.asyncio
async def test_run_text_rejects_stacked_statements():
    """Code execution primitives such as imports/calls must be rejected."""
    malicious_code = """
import os
os.environ["_METAGPT_MUTATION_TEST"] = "MUTATED"
result = "done"
"""
    out, err = await RunCode.run_text(malicious_code)
    assert out == ""
    assert "only literal or arithmetic assignments" in err


@pytest.mark.asyncio
async def test_run_text_rejects_call_expressions():
    """A result assignment cannot invoke functions or builtins."""
    out, err = await RunCode.run_text("result = __import__('os').getcwd()")
    assert out == ""
    assert "unsupported expression" in err


@pytest.mark.asyncio
async def test_run_text_rejects_attribute_access():
    """Attribute access must not be evaluated."""
    out, err = await RunCode.run_text("result = ().__class__.__mro__")
    assert out == ""
    assert "unsupported expression" in err


@pytest.mark.asyncio
async def test_run_text_basic_functionality():
    """Basic run_text functionality should still work after the fix."""
    out, err = await RunCode.run_text("result = 1 + 1")
    assert out == "2"
    assert err == ""

    out, err = await RunCode.run_text("result = 'helloworld'")
    assert out == "helloworld"
    assert err == ""

    out, err = await RunCode.run_text("result = 1 / 0")
    assert out == ""
    assert "division by zero" in err


@pytest.mark.asyncio
async def test_run_text_returns_string():
    """After sandboxing, run_text returns string representations of results."""
    out, err = await RunCode.run_text("result = [1, 2, 3]")
    assert out == "[1, 2, 3]"
    assert err == ""
