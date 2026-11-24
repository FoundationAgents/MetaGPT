import asyncio
from contextvars import ContextVar

import chainlit as cl

from metagpt.environment import Environment
from metagpt.logs import logger, set_llm_stream_logfunc
from metagpt.roles import Role
from metagpt.utils.common import any_to_name

# One message per role run: each session's on_message and each gathered role task has its own context,
# so concurrent sessions and roles no longer stream into (or send) each other's message.
chainlit_message: ContextVar[cl.Message] = ContextVar("chainlit_message")


def log_llm_stream_chainlit(msg):
    # Stream the message token into Chainlit UI.
    cl.run_sync(chainlit_message.get().stream_token(msg))


set_llm_stream_logfunc(func=log_llm_stream_chainlit)


class ChainlitEnv(Environment):
    """Chainlit Environment for UI Integration"""

    async def run(self, k=1):
        """处理一次所有信息的运行
        Process all Role runs at once
        """
        for _ in range(k):
            futures = []
            for role in self.roles.values():
                # Call role.run with chainlit configuration
                future = self._chainlit_role_run(role=role)
                futures.append(future)

            await asyncio.gather(*futures)
            logger.debug(f"is idle: {self.is_idle}")

    async def _chainlit_role_run(self, role: Role) -> None:
        """To run the role with chainlit config

        Args:
            role (Role): metagpt.role.Role
        """
        ui_message = cl.Message(content="")
        chainlit_message.set(ui_message)

        message = await role.run()
        # If message is from role._act() publish to UI.
        if message is not None and message.content != "No actions taken yet":
            # Convert a message from action node in json format
            ui_message.content = await self._convert_message_to_markdownjson(message=ui_message.content)

            # message content from which role and its action...
            ui_message.content += f"---\n\nAction: `{any_to_name(message.cause_by)}` done by `{role._setting}`."

            await ui_message.send()

    # for clean view in UI
    async def _convert_message_to_markdownjson(self, message: str) -> str:
        """If the message is from MetaGPT Action Node output, then
        convert it into markdown json for clear view in UI.

        Args:
            message (str): message by role._act

        Returns:
            str: message in mardown from
        """
        if message.startswith("[CONTENT]"):
            return f"```json\n{message}\n```\n"
        return message
