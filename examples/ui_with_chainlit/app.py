from __future__ import annotations

from pathlib import Path

import chainlit as cl
import os
from init_setup import ChainlitEnv

from metagpt.roles import (
    Architect,
    Engineer,
    ProductManager,
    ProjectManager,
    QaEngineer,
)
from metagpt.team import Team


# https://docs.chainlit.io/concepts/authentication
@cl.password_auth_callback
def auth_callback(username: str, password: str) -> cl.User | None:
    """Validate credentials from environment variables.

    Reads CHAINLIT_USERNAME and CHAINLIT_PASSWORD from the environment.
    Falls back to a simple demo credential if neither is set.
    """
    expected_user = os.environ.get("CHAINLIT_USERNAME", "admin")
    expected_pass = os.environ.get("CHAINLIT_PASSWORD", "admin")
    if username == expected_user and password == expected_pass:
        return cl.User(identifier=username)
    return None


# https://docs.chainlit.io/concepts/starters
@cl.set_chat_profiles
async def chat_profile() -> list[cl.ChatProfile]:
    """Generates a chat profile containing starter messages which can be triggered to run MetaGPT

    Returns:
        list[chainlit.ChatProfile]: List of Chat Profile
    """
    return [
        cl.ChatProfile(
            name="MetaGPT",
            icon="/public/MetaGPT-new-log.jpg",
            markdown_description="It takes a **one line requirement** as input and outputs **user stories / competitive analysis / requirements / data structures / APIs / documents, etc.**, But `everything in UI`.",
            starters=[
                cl.Starter(
                    label="Create a 2048 Game",
                    message="Create a 2048 game",
                    icon="/public/2048.jpg",
                ),
                cl.Starter(
                    label="Write a cli Blackjack Game",
                    message="Write a cli Blackjack Game",
                    icon="/public/blackjack.jpg",
                ),
            ],
        )
    ]


# https://docs.chainlit.io/concepts/message
@cl.on_message
async def startup(message: cl.Message) -> None:
    """On Message in UI, Create a MetaGPT software company

    Args:
        message (chainlit.Message): message by chainlist
    """
    idea = message.content
    company = Team(env=ChainlitEnv())

    # Similar to software_company.py
    company.hire(
        [
            ProductManager(),
            Architect(),
            ProjectManager(),
            Engineer(n_borg=5, use_code_review=True),
            QaEngineer(),
        ]
    )

    company.invest(investment=3.0)
    company.run_project(idea=idea)

    await company.run(n_round=5)

    workdir = Path(company.env.context.config.project_path)
    files = [file.name for file in workdir.iterdir() if file.is_file()]
    files = "\n".join([f"{workdir}/{file}" for file in files if not file.startswith(".git")])

    await cl.Message(
        content=f"""
Codes can be found here:
{files}

---

Total cost: `{company.cost_manager.total_cost}`
"""
    ).send()
