#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:46
@Author  : alexanderwu
@File    : run_code.py
@Modified By: mashenquan, 2023/11/27.
            1. Mark the location of Console logs in the PROMPT_TEMPLATE with markdown code-block formatting to enhance
            the understanding for the LLM.
            2. Fix bug: Add the "install dependency" operation.
            3. Encapsulate the input of RunCode into RunCodeContext and encapsulate the output of RunCode into
            RunCodeResult to standardize and unify parameter passing between WriteCode, RunCode, and DebugError.
            4. According to section 2.2.3.5.7 of RFC 135, change the method of transferring file content
            (code files, unit test files, log files) from using the message to using the file name.
            5. Merged the `Config` class of send18:dev branch to take over the set/get operations of the Environment
            class.
"""
import json
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Tuple

from pydantic import Field

from metagpt.actions.action import Action
from metagpt.logs import logger
from metagpt.schema import RunCodeContext, RunCodeResult
from metagpt.utils.exceptions import handle_exception

PROMPT_TEMPLATE = """
Role: You are a senior development and qa engineer, your role is summarize the code running result.
If the running result does not include an error, you should explicitly approve the result.
On the other hand, if the running result indicates some error, you should point out which part, the development code or the test code, produces the error,
and give specific instructions on fixing the errors. Here is the code info:
{context}
Now you should begin your analysis
---
## instruction:
Please summarize the cause of the errors and give correction instruction
## File To Rewrite:
Determine the ONE file to rewrite in order to fix the error, for example, xyz.py, or test_xyz.py
## Status:
Determine if all of the code works fine, if so write PASS, else FAIL,
WRITE ONLY ONE WORD, PASS OR FAIL, IN THIS SECTION
## Send To:
Please write NoOne if there are no errors, Engineer if the errors are due to problematic development codes, else QaEngineer,
WRITE ONLY ONE WORD, NoOne OR Engineer OR QaEngineer, IN THIS SECTION.
---
You should fill in necessary instruction, status, send to, and finally return all content between the --- segment line.
"""

TEMPLATE_CONTEXT = """
## Development Code File Name
{code_file_name}
## Development Code
```python
{code}
```
## Test File Name
{test_file_name}
## Test Code
```python
{test_code}
```
## Running Command
{command}
## Running Output
standard output: 
```text
{outs}
```
standard errors: 
```text
{errs}
```
"""

# Wrapper script executed in the sandboxed subprocess. Reads the code to execute
# from stdin and prints a JSON object with ``result`` and ``error`` keys.
_SANDBOX_WRAPPER = textwrap.dedent("""\
    import ast, json, operator, sys

    _BIN_OPS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
    }
    _UNARY_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg, ast.Not: operator.not_}
    _COMPARE_OPS = {
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
    }

    def _safe_eval(node):
        if isinstance(node, ast.Expression):
            return _safe_eval(node.body)
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.List):
            return [_safe_eval(elt) for elt in node.elts]
        if isinstance(node, ast.Tuple):
            return tuple(_safe_eval(elt) for elt in node.elts)
        if isinstance(node, ast.Set):
            return {_safe_eval(elt) for elt in node.elts}
        if isinstance(node, ast.Dict):
            return {_safe_eval(key): _safe_eval(value) for key, value in zip(node.keys, node.values)}
        if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
            return _BIN_OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
            return _UNARY_OPS[type(node.op)](_safe_eval(node.operand))
        if isinstance(node, ast.BoolOp):
            values = [_safe_eval(value) for value in node.values]
            return all(values) if isinstance(node.op, ast.And) else any(values)
        if isinstance(node, ast.Compare):
            left = _safe_eval(node.left)
            for op, comparator in zip(node.ops, node.comparators):
                right = _safe_eval(comparator)
                if type(op) not in _COMPARE_OPS or not _COMPARE_OPS[type(op)](left, right):
                    return False
                left = right
            return True
        raise ValueError("unsupported expression")

    def _evaluate_result(code):
        tree = ast.parse(code, mode="exec")
        result = ""
        for statement in tree.body:
            if not (
                isinstance(statement, ast.Assign)
                and len(statement.targets) == 1
                and isinstance(statement.targets[0], ast.Name)
                and statement.targets[0].id == "result"
            ):
                raise ValueError("only literal or arithmetic assignments to 'result' are supported")
            result = _safe_eval(statement.value)
        return result

    try:
        result = str(_evaluate_result(sys.stdin.read()))
        error = ""
    except Exception as e:
        result = ""
        error = str(e)

    sys.stdout.write(json.dumps({"result": result, "error": error}))
""")


class RunCode(Action):
    name: str = "RunCode"
    i_context: RunCodeContext = Field(default_factory=RunCodeContext)

    @classmethod
    async def run_text(cls, code) -> Tuple[str, str]:
        """Execute *code* in an isolated subprocess and return ``(result, error)``.

        The code is **not** executed via ``exec()``. Instead it is parsed in a
        short-lived Python subprocess and limited to simple assignments to the
        ``result`` variable using literal values and arithmetic expressions.
        """
        try:
            process = subprocess.run(
                [sys.executable, "-c", _SANDBOX_WRAPPER],
                input=code,
                capture_output=True,
                text=True,
                timeout=30,
            )
            # Parse the JSON payload written by the wrapper on stdout.
            stdout = process.stdout.strip()
            if stdout:
                payload = json.loads(stdout)
                result = payload.get("result", "")
                error = payload.get("error", "")
            else:
                # Wrapper produced no output – likely a crash.
                result = ""
                error = process.stderr.strip() or "No output from sandbox subprocess"
        except subprocess.TimeoutExpired:
            return "", "Code execution timed out"
        except Exception as e:
            return "", str(e)
        return result, error

    async def run_script(self, working_directory, additional_python_paths=[], command=[]) -> Tuple[str, str]:
        working_directory = str(working_directory)
        additional_python_paths = [str(path) for path in additional_python_paths]

        # Copy the current environment variables
        env = self.context.new_environ()

        # Modify the PYTHONPATH environment variable
        additional_python_paths = [working_directory] + additional_python_paths
        additional_python_paths = ":".join(additional_python_paths)
        env["PYTHONPATH"] = additional_python_paths + ":" + env.get("PYTHONPATH", "")
        RunCode._install_dependencies(working_directory=working_directory, env=env)

        # Start the subprocess
        process = subprocess.Popen(
            command, cwd=working_directory, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env
        )
        logger.info(" ".join(command))

        try:
            # Wait for the process to complete, with a timeout
            stdout, stderr = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            logger.info("The command did not complete within the given timeout.")
            process.kill()  # Kill the process if it times out
            stdout, stderr = process.communicate()
        return stdout.decode("utf-8"), stderr.decode("utf-8")

    async def run(self, *args, **kwargs) -> RunCodeResult:
        logger.info(f"Running {' '.join(self.i_context.command)}")
        if self.i_context.mode == "script":
            outs, errs = await self.run_script(
                command=self.i_context.command,
                working_directory=self.i_context.working_directory,
                additional_python_paths=self.i_context.additional_python_paths,
            )
        elif self.i_context.mode == "text":
            outs, errs = await self.run_text(code=self.i_context.code)

        logger.info(f"{outs=}")
        logger.info(f"{errs=}")

        context = TEMPLATE_CONTEXT.format(
            code=self.i_context.code,
            code_file_name=self.i_context.code_filename,
            test_code=self.i_context.test_code,
            test_file_name=self.i_context.test_filename,
            command=" ".join(self.i_context.command),
            outs=outs[:500],  # outs might be long but they are not important, truncate them to avoid token overflow
            errs=errs[:10000],  # truncate errors to avoid token overflow
        )

        prompt = PROMPT_TEMPLATE.format(context=context)
        rsp = await self._aask(prompt)
        return RunCodeResult(summary=rsp, stdout=outs, stderr=errs)

    @staticmethod
    @handle_exception(exception_type=subprocess.CalledProcessError)
    def _install_via_subprocess(cmd, check, cwd, env):
        return subprocess.run(cmd, check=check, cwd=cwd, env=env)

    @staticmethod
    def _install_requirements(working_directory, env):
        file_path = Path(working_directory) / "requirements.txt"
        if not file_path.exists():
            return
        if file_path.stat().st_size == 0:
            return
        install_command = ["python", "-m", "pip", "install", "-r", "requirements.txt"]
        logger.info(" ".join(install_command))
        RunCode._install_via_subprocess(install_command, check=True, cwd=working_directory, env=env)

    @staticmethod
    def _install_pytest(working_directory, env):
        install_pytest_command = ["python", "-m", "pip", "install", "pytest"]
        logger.info(" ".join(install_pytest_command))
        RunCode._install_via_subprocess(install_pytest_command, check=True, cwd=working_directory, env=env)

    @staticmethod
    def _install_dependencies(working_directory, env):
        RunCode._install_requirements(working_directory, env)
        RunCode._install_pytest(working_directory, env)
