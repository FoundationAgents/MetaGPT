#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import os
from pathlib import Path

import typer

from metagpt.const import CONFIG_ROOT
from metagpt.locale import init_locale, set_language, t

init_locale()

app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)


def generate_repo(
    idea,
    investment=3.0,
    n_round=5,
    code_review=True,
    run_tests=False,
    implement=True,
    project_name="",
    inc=False,
    project_path="",
    reqa_file="",
    max_auto_summarize_code=0,
    recover_path=None,
    language=None,
):
    """Run the startup logic. Can be called from CLI or other Python scripts."""
    from metagpt.config2 import config
    from metagpt.context import Context
    from metagpt.roles import (
        Architect,
        DataAnalyst,
        Engineer2,
        ProductManager,
        TeamLeader,
    )
    from metagpt.team import Team

    if language:
        config.language = set_language(language)
    else:
        init_locale(config.language)

    config.update_via_cli(project_path, project_name, inc, reqa_file, max_auto_summarize_code)
    ctx = Context(config=config)
    ctx.kwargs.set("language", config.language)

    if not recover_path:
        company = Team(context=ctx)
        company.hire(
            [
                TeamLeader(),
                ProductManager(),
                Architect(),
                Engineer2(),
                # ProjectManager(),
                DataAnalyst(),
            ]
        )

        # if implement or code_review:
        #     company.hire([Engineer(n_borg=5, use_code_review=code_review)])
        #
        # if run_tests:
        #     company.hire([QaEngineer()])
        #     if n_round < 8:
        #         n_round = 8  # If `--run-tests` is enabled, at least 8 rounds are required to run all QA actions.
    else:
        stg_path = Path(recover_path)
        if not stg_path.exists() or not str(stg_path).endswith("team"):
            raise FileNotFoundError(f"{recover_path} not exists or not endswith `team`")

        company = Team.deserialize(stg_path=stg_path, context=ctx)
        idea = company.idea

    company.invest(investment)
    asyncio.run(company.run(n_round=n_round, idea=idea))

    return ctx.kwargs.get("project_path")


@app.command("", help=t("cli_startup_help"))
def startup(
    idea: str = typer.Argument(None, help=t("cli_idea_help")),
    investment: float = typer.Option(default=3.0, help=t("cli_investment_help")),
    n_round: int = typer.Option(default=5, help=t("cli_n_round_help")),
    code_review: bool = typer.Option(default=True, help=t("cli_code_review_help")),
    run_tests: bool = typer.Option(default=False, help=t("cli_run_tests_help")),
    implement: bool = typer.Option(default=True, help=t("cli_implement_help")),
    project_name: str = typer.Option(default="", help=t("cli_project_name_help")),
    inc: bool = typer.Option(default=False, help=t("cli_inc_help")),
    project_path: str = typer.Option(default="", help=t("cli_project_path_help")),
    reqa_file: str = typer.Option(default="", help=t("cli_reqa_file_help")),
    max_auto_summarize_code: int = typer.Option(default=0, help=t("cli_max_auto_summarize_help")),
    recover_path: str = typer.Option(default=None, help=t("cli_recover_path_help")),
    init_config: bool = typer.Option(default=False, help=t("cli_init_config_help")),
    language: str = typer.Option(
        default=os.environ.get("METAGPT_LANG", ""),
        help=t("cli_language_help"),
    ),
):
    """Run a startup. Be a boss."""
    if language:
        set_language(language)

    if init_config:
        copy_config_to()
        return

    if idea is None:
        typer.echo(t("missing_idea"))
        raise typer.Exit()

    return generate_repo(
        idea,
        investment,
        n_round,
        code_review,
        run_tests,
        implement,
        project_name,
        inc,
        project_path,
        reqa_file,
        max_auto_summarize_code,
        recover_path,
        language=language or None,
    )


DEFAULT_CONFIG = """# Full Example: https://github.com/geekan/MetaGPT/blob/main/config/config2.example.yaml
# Reflected Code: https://github.com/geekan/MetaGPT/blob/main/metagpt/config2.py
# Config Docs: https://docs.deepwisdom.ai/main/en/guide/get_started/configuration.html
language: "English"  # English | Persian | Chinese | French | Japanese

llm:
  api_type: "openai"  # or azure / ollama / groq etc.
  model: "gpt-4-turbo"  # or gpt-3.5-turbo
  base_url: "https://api.openai.com/v1"  # or forward url / other llm url
  api_key: "YOUR_API_KEY"
"""


def copy_config_to():
    """Initialize the configuration file for MetaGPT."""
    target_path = CONFIG_ROOT / "config2.yaml"

    # 创建目标目录（如果不存在）
    target_path.parent.mkdir(parents=True, exist_ok=True)

    # 如果目标文件已经存在，则重命名为 .bak
    if target_path.exists():
        backup_path = target_path.with_suffix(".bak")
        target_path.rename(backup_path)
        print(t("config_backed_up", path=backup_path))

    # 复制文件
    target_path.write_text(DEFAULT_CONFIG, encoding="utf-8")
    print(t("config_initialized", path=target_path))


if __name__ == "__main__":
    app()
