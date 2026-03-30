#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Optional
from pydantic import BaseModel, Field

from metagpt.actions import DebugError, RunCode, WriteTest
from metagpt.actions.summarize_code import SummarizeCode
from metagpt.const import MESSAGE_ROUTE_TO_NONE, MESSAGE_ROUTE_TO_SELF
from metagpt.logs import logger
from metagpt.roles.di.role_zero import RoleZero
from metagpt.schema import AIMessage, Document, Message, RunCodeContext, TestingContext
from metagpt.tools.tool_registry import register_tool
from metagpt.utils.common import (
    any_to_str,
    get_project_srcs_path,
    init_python_folder,
    parse_recipient,
)
from metagpt.utils.project_repo import ProjectRepo
from metagpt.utils.report import EditorReporter

@register_tool(
    include_functions=[
        "write_test",
        "run_code",
        "debug_error",
    ]
)
class QaEngineer2(RoleZero):
    name: str = "Edward"
    profile: str = "QaEngineer"
    goal: str = (
        "Write comprehensive and robust tests to ensure codes will work as expected without bugs"
    )
    constraints: str = (
        "The test code you write should conform to code standard like PEP8, be modular, easy to read and maintain."
        "Use same language as user requirement"
    )
    test_round_allowed: int = 5
    test_round: int = 0
    repo: Optional[ProjectRepo] = Field(default=None, exclude=True)
    input_args: Optional[BaseModel] = Field(default=None, exclude=True)
    tools: list[str] = ["RoleZero", "QaEngineer2"]

    def _update_tool_execution(self):
        self.tool_execution_map.update(
            {
                "QaEngineer2.write_test": self.write_test,
                "QaEngineer2.run_code": self.run_code,
                "QaEngineer2.debug_error": self.debug_error,
                # Backward-compatible aliases for any existing prompts/examples.
                "WriteTest": self.write_test,
                "RunCode": self.run_code,
                "DebugError": self.debug_error,
            }
        )

    async def write_test(self, *args, **kwargs) -> str:
        """Write unit tests for the code."""
        if not self.repo:
            return "Error: Project repository not initialized. Need to receive SummarizeCode message first."

        reqa_file = self.context.kwargs.reqa_file or self.config.reqa_file
        changed_files = (
            {reqa_file} if reqa_file else set(self.repo.srcs.changed_files.keys())
        )
        results = []
        for filename in changed_files:
            if not filename or "test" in filename:
                continue
            code_doc = await self.repo.srcs.get(filename)
            if not code_doc or not code_doc.content:
                continue
            if not code_doc.filename.endswith(".py"):
                continue
            test_doc = await self.repo.tests.get("test_" + code_doc.filename)
            if not test_doc:
                test_doc = Document(
                    root_path=str(self.repo.tests.root_path),
                    filename="test_" + code_doc.filename,
                    content="",
                )
            logger.info(f"Writing {test_doc.filename}..")
            context = TestingContext(
                filename=test_doc.filename, test_doc=test_doc, code_doc=code_doc
            )

            context = await WriteTest(
                i_context=context, context=self.context, llm=self.llm
            ).run()
            async with EditorReporter(enable_llm_stream=True) as reporter:
                await reporter.async_report(
                    {"type": "test", "filename": test_doc.filename}, "meta"
                )
                doc = await self.repo.tests.save_doc(
                    doc=context.test_doc,
                    dependencies=[context.code_doc.root_relative_path],
                )
                await reporter.async_report(
                    self.repo.workdir / doc.root_relative_path, "path"
                )

            results.append(
                f"Successfully wrote test for {filename} at {test_doc.filename}"
            )

        return "\n".join(results) if results else "No files found to write tests for."

    async def run_code(self, code_filename: str, test_filename: str) -> str:
        """Run the unit tests."""
        if not self.repo:
            return "Error: Project repository not initialized."

        run_code_context = RunCodeContext(
            command=["python", f"tests/{test_filename}"],
            code_filename=code_filename,
            test_filename=test_filename,
            working_directory=str(self.repo.workdir),
            additional_python_paths=[str(self.repo.srcs.workdir)],
        )

        src_doc = await self.repo.srcs.get(run_code_context.code_filename)
        if not src_doc:
            return f"Error: Source file {code_filename} not found."
        test_doc = await self.repo.tests.get(run_code_context.test_filename)
        if not test_doc:
            return f"Error: Test file {test_filename} not found."

        run_code_context.code = src_doc.content
        run_code_context.test_code = test_doc.content
        result = await RunCode(
            i_context=run_code_context, context=self.context, llm=self.llm
        ).run()

        run_code_context.output_filename = run_code_context.test_filename + ".json"
        await self.repo.test_outputs.save(
            filename=run_code_context.output_filename,
            content=result.model_dump_json(),
            dependencies=[src_doc.root_relative_path, test_doc.root_relative_path],
        )

        return f"Test results for {test_filename}:\nSummary: {result.summary}\nStdout: {result.stdout}\nStderr: {result.stderr}"

    async def debug_error(
        self, code_filename: str, test_filename: str, error_msg: str
    ) -> str:
        """Debug and fix errors in tests."""
        if not self.repo:
            return "Error: Project repository not initialized."

        run_code_context = RunCodeContext(
            command=["python", f"tests/{test_filename}"],
            code_filename=code_filename,
            test_filename=test_filename,
            working_directory=str(self.repo.workdir),
            additional_python_paths=[str(self.repo.srcs.workdir)],
            stderr=error_msg,
        )

        code = await DebugError(
            i_context=run_code_context,
            repo=self.repo,
            input_args=self.input_args,
            context=self.context,
            llm=self.llm,
        ).run()
        await self.repo.tests.save(
            filename=run_code_context.test_filename, content=code
        )

        return f"Reproduced and attempted to fix errors in {test_filename}."

    async def _observe(self) -> int:
        num_msgs = await super()._observe()
        for msg in self.rc.news:
            # Initialize from SummarizeCode (Legacy SOP) or instruct_content with path
            if msg.cause_by == any_to_str(SummarizeCode) or (
                msg.instruct_content and hasattr(msg.instruct_content, "project_path")
            ):
                self.input_args = msg.instruct_content
                if (
                    self.input_args
                    and hasattr(self.input_args, "project_path")
                    and self.input_args.project_path
                ):
                    self.repo = ProjectRepo(self.input_args.project_path)
                    if self.repo.src_relative_path is None:
                        path = get_project_srcs_path(self.repo.workdir)
                        self.repo.with_src_path(path)
                    await init_python_folder(self.repo.tests.workdir)
        return num_msgs
