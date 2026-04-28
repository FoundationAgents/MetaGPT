#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import platform
from pathlib import Path
from typing import Optional

import typer

from metagpt.const import CONFIG_ROOT
from metagpt.intent_router import (
    extract_paper_research_topic,
    looks_like_paper_research_topic,
    should_trigger_literature_review,
)
from metagpt.logs import logger

app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False, invoke_without_command=True)

PAPER_MODE_COMMAND_CONSTRAINT = """
You are in paper-mode collaboration.
Return ONLY a strict JSON array of commands. Do not output narrative text before or after JSON.
Do not call SearchEnhancedQA.run.
Focus on literature synthesis outputs, not software implementation artifacts.
""".strip()

PAPER_MODE_PM_INSTRUCTION = """
You are the ProductManager for an academic literature synthesis task.
Your output must define:
1) Research objectives and scope
2) Research questions and inclusion/exclusion criteria
3) Report outline for literature review (not market competitor analysis)
4) Evidence table template and expected citation style
Use Editor tools to produce markdown documents.
""".strip()

PAPER_MODE_ARCHITECT_INSTRUCTION = """
You are the Architect for an academic literature synthesis workflow.
Design an analysis framework for evidence synthesis, including:
1) Thematic dimensions
2) Comparison matrix structure
3) Claim-to-evidence mapping
4) Quality/risk assessment rubric
Output markdown structure and mermaid diagrams only when helpful for analysis flow.
Do not design software implementation architecture.
""".strip()


def _ensure_main_event_loop():
    """Ensure there is a current event loop in main thread."""
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)


def _build_hire_roles(collaboration_mode: str, team_leader, product_manager, architect, engineer2, data_analyst):
    """Build role lineup for a collaboration mode within one Team workflow."""
    if collaboration_mode == "paper":
        pm = product_manager(
            instruction=f"{PAPER_MODE_COMMAND_CONSTRAINT}\n\n{PAPER_MODE_PM_INSTRUCTION}",
            tools=["RoleZero", "Browser", "Editor"],
        )
        arch = architect(
            instruction=f"{PAPER_MODE_COMMAND_CONSTRAINT}\n\n{PAPER_MODE_ARCHITECT_INSTRUCTION}",
        )
        return [team_leader(), pm, arch, data_analyst()]
    return [team_leader(), product_manager(), architect(), engineer2(), data_analyst()]


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
    literature_context: Optional[str] = None,
    collaboration_mode: str = "software",
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

    config.update_via_cli(project_path, project_name, inc, reqa_file, max_auto_summarize_code)
    ctx = Context(config=config)
    _ensure_main_event_loop()

    if not recover_path:
        company = Team(context=ctx)
        hire_roles = _build_hire_roles(
            collaboration_mode=collaboration_mode,
            team_leader=TeamLeader,
            product_manager=ProductManager,
            architect=Architect,
            engineer2=Engineer2,
            data_analyst=DataAnalyst,
        )
        company.hire(hire_roles)
    else:
        stg_path = Path(recover_path)
        if not stg_path.exists() or not str(stg_path).endswith("team"):
            raise FileNotFoundError(f"{recover_path} not exists or not endswith `team`")

        company = Team.deserialize(stg_path=stg_path, context=ctx)
        idea = company.idea

    company.invest(investment)
    effective_idea = _compose_idea_with_literature_context(idea, literature_context)
    asyncio.run(company.run(n_round=n_round, idea=effective_idea))

    return ctx.kwargs.get("project_path")


def _compose_idea_with_literature_context(idea: str, literature_context: Optional[str]) -> str:
    """Inject literature context into requirement for PM/Architect traceability."""
    if not literature_context:
        return idea
    return (
        f"{idea}\n\n"
        "## Literature Review Context (for ProductManager and Architect)\n"
        f"{literature_context}\n"
        "## End Literature Review Context\n"
    )


def _compose_paper_collaboration_idea(topic: str, literature_context: Optional[str]) -> str:
    """Build a paper-oriented collaborative requirement for the common Team workflow."""
    base_idea = (
        "Deliver a collaborative academic research report instead of software implementation. "
        f"Research topic: {topic}. "
        "ProductManager should define research objectives and report outline. "
        "Architect should design a clear analysis framework and evidence structure. "
        "DataAnalyst should summarize trends, key methods, strengths/limitations, and practical suggestions. "
        "Output should be in markdown and focused on literature synthesis."
    )
    return _compose_idea_with_literature_context(base_idea, literature_context)


def _render_literature_context(review_result: dict) -> str:
    """Render reusable literature context in a deterministic format."""
    lines = [
        f"- Topic: {review_result.get('topic', '')}",
        "- Summary:",
        review_result.get("summary", ""),
        "",
        "- Key Papers:",
    ]
    papers = review_result.get("papers", [])
    if not papers:
        lines.append("  - No papers extracted.")
        return "\n".join(lines)
    for idx, paper in enumerate(papers, 1):
        lines.append(
            f"  {idx}. {paper.get('title', 'Untitled')} ({paper.get('year', 'N/A')}, {paper.get('venue', 'N/A')})"
        )
        if paper.get("url"):
            lines.append(f"     URL: {paper['url']}")
        if paper.get("abstract"):
            lines.append(f"     Abstract: {paper['abstract']}")
    return "\n".join(lines)


def _save_literature_context_to_fixed_file(context_text: str) -> Optional[Path]:
    """Persist pre-review context to a deterministic file for easy retrieval."""
    if not context_text:
        return None
    output_path = Path.cwd() / "workspace" / "paper_search_result.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(context_text, encoding="utf-8")
    return output_path


def _run_literature_review_for_software(idea: str, max_results: int = 5) -> Optional[str]:
    """Run optional literature review action and return context text."""

    async def run_review():
        from metagpt.actions.literature_review import LiteratureReviewAction
        from metagpt.config2 import config as metagpt_config
        from metagpt.context import Context

        action = LiteratureReviewAction()
        action.set_context(Context(config=metagpt_config))
        result = await action.run(topic=idea, max_results=max_results)
        return _render_literature_context(result)

    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    result = asyncio.run(run_review())
    _ensure_main_event_loop()
    return result


def _resolve_intent_with_fallback(
    idea: str,
    agent_result: Optional[dict] = None,
    confidence_threshold: float = 0.65,
) -> tuple[bool, str]:
    """Resolve paper/software intent using agent result first, regex as fallback."""
    if agent_result:
        mode = str(agent_result.get("collaboration_mode", "")).strip().lower()
        confidence = float(agent_result.get("confidence") or 0.0)
        topic = str(agent_result.get("topic") or "").strip()
        if mode in {"paper", "software"} and confidence >= confidence_threshold:
            if mode == "paper":
                return True, topic or extract_paper_research_topic(idea)
            return False, idea

    # Deterministic fallback to keep behavior stable.
    is_paper_request = looks_like_paper_research_topic(idea)
    topic = extract_paper_research_topic(idea) if is_paper_request else idea
    return is_paper_request, topic


def _classify_intent_via_agent(idea: str) -> Optional[dict]:
    """Use a lightweight Action to classify user intent. Return None on failure."""

    async def run_classify() -> dict:
        from metagpt.actions.intent_classification import IntentClassificationAction
        from metagpt.config2 import config as metagpt_config
        from metagpt.context import Context

        action = IntentClassificationAction()
        action.set_context(Context(config=metagpt_config))
        return await action.run(user_input=idea)

    try:
        if platform.system() == "Windows":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        result = asyncio.run(run_classify())
        _ensure_main_event_loop()
        return result
    except Exception as exc:
        logger.warning(f"Intent classification action failed, fallback to regex router: {exc}")
        _ensure_main_event_loop()
        return None


@app.callback(invoke_without_command=True)
def startup(
    ctx: typer.Context,
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
    literature_review_mode: str = typer.Option(
        default="off",
        help="Optional literature pre-review mode: off, keyword, always.",
    ),
    literature_top_k: int = typer.Option(default=5, help="Top papers used in pre-review context."),
):
    """Run a startup. Be a boss."""
    if ctx.invoked_subcommand:
        return

    if init_config:
        copy_config_to()
        return

    if idea is None:
        typer.echo("Missing argument 'IDEA'. Run 'metagpt --help' for more information.")
        raise typer.Exit()

    agent_intent = _classify_intent_via_agent(idea)
    is_paper_request, topic = _resolve_intent_with_fallback(idea=idea, agent_result=agent_intent)
    if agent_intent:
        logger.info(
            "Intent classifier result: "
            f"mode={agent_intent.get('collaboration_mode')} "
            f"confidence={float(agent_intent.get('confidence') or 0.0):.2f} "
            f"topic={agent_intent.get('topic')}"
        )

    normalized_mode = literature_review_mode.strip().lower()
    should_review = (
        is_paper_request
        or normalized_mode == "always"
        or (normalized_mode == "keyword" and should_trigger_literature_review(idea))
    )
    literature_context = None
    if should_review:
        typer.echo("\nRunning optional literature pre-review for software collaboration...")
        literature_context = _run_literature_review_for_software(topic, max_results=literature_top_k)
        typer.echo("Literature pre-review context injected into ProductManager/Architect inputs.\n")
        saved_path = _save_literature_context_to_fixed_file(literature_context or "")
        if saved_path:
            typer.echo(f"Pre-review paper result saved to: {saved_path}")

    collaboration_mode = "paper" if is_paper_request else "software"
    effective_idea = idea
    if is_paper_request:
        typer.echo(f"Detected paper request topic: {topic}")
        effective_idea = _compose_paper_collaboration_idea(topic, literature_context)
        literature_context = None

    return generate_repo(
        effective_idea,
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
        literature_context,
        collaboration_mode,
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

    target_path.parent.mkdir(parents=True, exist_ok=True)

    if target_path.exists():
        backup_path = target_path.with_suffix(".bak")
        target_path.rename(backup_path)
        print(f"Existing configuration file backed up at {backup_path}")

    target_path.write_text(DEFAULT_CONFIG, encoding="utf-8")
    print(f"Configuration file initialized at {target_path}")


if __name__ == "__main__":
    app()
