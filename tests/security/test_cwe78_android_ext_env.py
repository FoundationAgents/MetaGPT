#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Regression tests for CWE-78 in AndroidExtEnv adb execution."""

import ast
from pathlib import Path

ANDROID_EXT_ENV_PATH = (
    Path(__file__).resolve().parent.parent.parent / "metagpt" / "environment" / "android" / "android_ext_env.py"
)


def _android_ext_env_ast() -> ast.Module:
    return ast.parse(ANDROID_EXT_ENV_PATH.read_text())


def _find_android_method(method_name: str) -> ast.FunctionDef:
    for node in ast.walk(_android_ext_env_ast()):
        if isinstance(node, ast.ClassDef) and node.name == "AndroidExtEnv":
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == method_name:
                    return item
    raise AssertionError(f"Could not find AndroidExtEnv.{method_name}")


def _is_subprocess_run(call: ast.Call) -> bool:
    return (
        isinstance(call.func, ast.Attribute)
        and call.func.attr == "run"
        and isinstance(call.func.value, ast.Name)
        and call.func.value.id == "subprocess"
    )


def test_execute_adb_with_cmd_does_not_invoke_a_shell():
    """ADB commands must not be executed through a host shell."""
    method = _find_android_method("execute_adb_with_cmd")
    run_calls = [node for node in ast.walk(method) if isinstance(node, ast.Call) and _is_subprocess_run(node)]

    assert run_calls, "execute_adb_with_cmd must call subprocess.run"
    for call in run_calls:
        shell_keywords = [kw for kw in call.keywords if kw.arg == "shell"]
        assert shell_keywords, "subprocess.run must set shell explicitly for this security-sensitive call"
        for keyword in shell_keywords:
            assert isinstance(keyword.value, ast.Constant)
            assert keyword.value.value is False, "subprocess.run must use shell=False to prevent CWE-78"


def test_execute_adb_with_cmd_passes_tokenized_argv():
    """The subprocess command must be argv tokens, not a shell command string."""
    method = _find_android_method("execute_adb_with_cmd")
    run_calls = [node for node in ast.walk(method) if isinstance(node, ast.Call) and _is_subprocess_run(node)]

    assert run_calls, "execute_adb_with_cmd must call subprocess.run"
    for call in run_calls:
        assert call.args, "subprocess.run must receive the command as its first positional argument"
        command_arg = call.args[0]
        assert (
            isinstance(command_arg, ast.Call)
            and isinstance(command_arg.func, ast.Attribute)
            and command_arg.func.attr == "split"
            and isinstance(command_arg.func.value, ast.Name)
            and command_arg.func.value.id == "shlex"
        ), "subprocess.run must receive shlex.split(adb_cmd) so shell metacharacters stay literal"


def test_agent_user_input_reaches_adb_execution_sink():
    """Document the external action path: agent input -> user_input -> execute_adb_with_cmd."""
    execute_action = _find_android_method("_execute_env_action")
    user_input = _find_android_method("user_input")

    assert any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "user_input"
        and any(kw.arg == "input_txt" for kw in node.keywords)
        for node in ast.walk(execute_action)
    ), "_execute_env_action must route EnvAction.USER_INPUT input text into user_input"

    assert any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "execute_adb_with_cmd"
        for node in ast.walk(user_input)
    ), "user_input must pass the assembled adb command to execute_adb_with_cmd"
