#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
from pathlib import Path

import typer

from metagpt.const import CONFIG_ROOT, TEAMLEADER_NAME

app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)


def _build_workspace_constrained_requirement(idea: str, project_root: Path) -> str:
    """Add runtime constraints to force file persistence under the workspace path."""
    return (
        f"{idea}\n\n"
        "[Runtime Constraints]\n"
        f"- Project root path (absolute): {project_root}\n"
        "- All implementation outputs must be persisted as files under this project root.\n"
        "- Do not only print code or plans in chat/console; write real files.\n"
        "- Keep all actions inside this project root unless user explicitly asks otherwise.\n"
    )


def _collect_materialized_files(project_root: Path) -> list[Path]:
    """Collect generated files, excluding git internals and bootstrap-only file."""
    files: list[Path] = []
    for file in project_root.rglob("*"):
        if not file.is_file():
            continue
        if ".git" in file.parts:
            continue
        if file.name == ".gitignore":
            continue
        files.append(file)
    return files


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
    from metagpt.utils.file_repository import FileRepository
    from metagpt.utils.project_repo import ProjectRepo

    config.update_via_cli(project_path, project_name, inc, reqa_file, max_auto_summarize_code)
    ctx = Context(config=config)
    repo = None

    if not recover_path:
        if config.project_path:
            project_root = Path(config.project_path).expanduser().resolve()
        else:
            name = config.project_name or FileRepository.new_filename()
            project_root = (Path(config.workspace.path) / name).expanduser().resolve()
        repo = ProjectRepo(project_root)
        ctx.kwargs.project_path = str(repo.workdir)
        runtime_idea = _build_workspace_constrained_requirement(idea=idea, project_root=repo.workdir)

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
        runtime_idea = company.idea

    company.invest(investment)
    asyncio.run(company.run(n_round=n_round, idea=runtime_idea, send_to=TEAMLEADER_NAME))

    project_path = ctx.kwargs.get("project_path")
    if not project_path:
        raise RuntimeError("Project path is missing after generation. The repository was not initialized.")
    repo = repo or ProjectRepo(project_path)
    if implement:
        files = _collect_materialized_files(repo.workdir)
        if not files:
            raise RuntimeError(
                f"Generation finished without persisted files under {repo.workdir}. "
                "The workflow only produced console/chat output."
            )

    return repo


@app.command("", help="Start a new project.")
def startup(
    idea: str = typer.Argument(None, help="Your innovative idea, such as 'Create a 2048 game.'"),
    investment: float = typer.Option(default=3.0, help="Dollar amount to invest in the AI company."),
    n_round: int = typer.Option(default=5, help="Number of rounds for the simulation."),
    code_review: bool = typer.Option(default=True, help="Whether to use code review."),
    run_tests: bool = typer.Option(default=False, help="Whether to enable QA for adding & running tests."),
    implement: bool = typer.Option(default=True, help="Enable or disable code implementation."),
    project_name: str = typer.Option(default="", help="Unique project name, such as 'game_2048'."),
    inc: bool = typer.Option(default=False, help="Incremental mode. Use it to coop with existing repo."),
    project_path: str = typer.Option(
        default="",
        help="Specify the directory path of the old version project to fulfill the incremental requirements.",
    ),
    reqa_file: str = typer.Option(
        default="", help="Specify the source file name for rewriting the quality assurance code."
    ),
    max_auto_summarize_code: int = typer.Option(
        default=0,
        help="The maximum number of times the 'SummarizeCode' action is automatically invoked, with -1 indicating "
        "unlimited. This parameter is used for debugging the workflow.",
    ),
    recover_path: str = typer.Option(default=None, help="recover the project from existing serialized storage"),
    init_config: bool = typer.Option(default=False, help="Initialize the configuration file for MetaGPT."),
):
    """Run a startup. Be a boss."""
    if init_config:
        copy_config_to()
        return

    if idea is None:
        typer.echo("Missing argument 'IDEA'. Run 'metagpt --help' for more information.")
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
    )


DEFAULT_CONFIG = """# Full Example: https://github.com/geekan/MetaGPT/blob/main/config/config2.example.yaml
# Reflected Code: https://github.com/geekan/MetaGPT/blob/main/metagpt/config2.py
# Config Docs: https://docs.deepwisdom.ai/main/en/guide/get_started/configuration.html
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
        print(f"Existing configuration file backed up at {backup_path}")

    # 复制文件
    target_path.write_text(DEFAULT_CONFIG, encoding="utf-8")
    print(f"Configuration file initialized at {target_path}")


if __name__ == "__main__":
    app()
