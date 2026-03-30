#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import re
from typing import Optional
from pydantic import BaseModel, Field

from metagpt.actions import CollectLinks, ConductResearch, WebBrowseAndSummarize
from metagpt.actions.research import get_research_system_text
from metagpt.const import RESEARCH_PATH
from metagpt.logs import logger
from metagpt.prompts.di.role_zero import ROLE_INSTRUCTION
from metagpt.roles.di.role_zero import RoleZero
from metagpt.schema import Message
from metagpt.tools.tool_registry import register_tool


class Report(BaseModel):
    topic: str
    links: Optional[dict[str, list[str]]] = None
    summaries: Optional[list[tuple[str, str]]] = None
    content: str = ""


@register_tool(
    include_functions=[
        "collect_links",
        "web_browse_and_summarize",
        "conduct_research",
    ]
)
class Researcher2(RoleZero):
    name: str = "David"
    profile: str = "Researcher"
    goal: str = "Gather information and conduct research"
    constraints: str = "Ensure accuracy and relevance of information"
    language: str = "en-us"
    enable_concurrency: bool = False  # Temporarily disabled for debugging hang issues
    per_page_timeout: float = 30.0
    summarize_timeout: float = 30.0  # Reduced for testing timeout handling
    tool_timeout: float = 300.0
    tools: list[str] = ["RoleZero", "Researcher2"]
    instruction: str = (
        ROLE_INSTRUCTION
        + "\nFor the research workflow, never emit more than one dependent research command in a single turn. "
        + "Run the pipeline strictly across multiple turns: first Researcher2.collect_links(topic), then after links exist in memory run Researcher2.web_browse_and_summarize(topic, links), then after summaries exist in memory run Researcher2.conduct_research(topic, summaries). "
        + "Do not call summarize without real links from prior command output. Do not call conduct_research without real summaries from prior command output."
        + "\nAFTER conduct_research completes and the report is written, you MUST:"
        + "\n1. Use RoleZero.reply_to_human to send the full report content to the user."
        + "\n2. Use RoleZero.ask_human to ask the user to review and confirm the report (e.g. 'Report is ready at <path>. Please review. Any feedback or should I finalize?')."
        + "\n3. Only use 'end' AFTER the user confirms the report is acceptable."
        + "\nIf web_browse_and_summarize fails or times out, still attempt conduct_research with whatever partial data you have. If no data at all, reply_to_human explaining the failure and ask_human for next steps."
    )

    def _update_tool_execution(self):
        self.tool_execution_map.update(
            {
                "Researcher2.collect_links": self.collect_links,
                "Researcher2.web_browse_and_summarize": self.web_browse_and_summarize,
                "Researcher2.conduct_research": self.conduct_research,
                # Backward-compatible aliases for any existing prompts/examples.
                "CollectLinks": self.collect_links,
                "WebBrowseAndSummarize": self.web_browse_and_summarize,
                "ConductResearch": self.conduct_research,
            }
        )

    async def collect_links(self, topic: str) -> dict[str, list[str]]:
        """Collect relevant links for a given topic."""
        action = CollectLinks(context=self.context)
        links = await action.run(topic, 2, 2)
        return links

    async def web_browse_and_summarize(
        self, topic: str, links: dict[str, list[str]]
    ) -> list[tuple[str, str]]:
        """Browse web pages and summarize their content."""
        logger.info(f"[DEBUG] Researcher2.web_browse_and_summarize START - topic={topic}, query_count={len(links)}, per_page_timeout={self.per_page_timeout}, summarize_timeout={self.summarize_timeout}")
        if not links or not any(links.values()):
            logger.warning("No links found from collect_links. Returning empty summaries for fallback.")
            return []
        action = WebBrowseAndSummarize(context=self.context)
        system_text = get_research_system_text(topic, self.language)

        all_summaries = []
        for query, url in links.items():
            if not url:
                continue
            try:
                result = await asyncio.wait_for(
                    action.run(
                        *url,
                        query=query,
                        system_text=system_text,
                        per_page_timeout=self.per_page_timeout,
                        summarize_timeout=self.summarize_timeout,
                    ),
                    timeout=self.summarize_timeout * len(url) + 60,
                )
                all_summaries.append(result)
            except (asyncio.TimeoutError, Exception) as e:
                logger.warning(f"web_browse_and_summarize failed for query '{query}': {e}. Continuing with partial results.")
                continue

        summaries = list(
            (url, summary) for i in all_summaries for (url, summary) in i.items() if summary
        )
        if not summaries:
            logger.warning("All web browse attempts failed or timed out. Returning empty summaries.")
        return summaries

    async def conduct_research(
        self, topic: str, summaries: list[tuple[str, str]]
    ) -> str:
        """Conduct research and generate a report based on summaries."""
        if not summaries:
            logger.warning("conduct_research called with empty summaries — generating partial report from topic only.")
            summaries = [("N/A", f"No web data could be retrieved for topic: {topic}. Please provide a summary based on general knowledge.")]
        action = ConductResearch(context=self.context)
        system_text = get_research_system_text(topic, self.language)
        summary_text = "\n---\n".join(
            f"url: {url}\nsummary: {summary}" for (url, summary) in summaries
        )
        content = await action.run(topic, summary_text, system_text=system_text)
        self._write_report(topic, content)
        return content

    def _write_report(self, topic: str, content: str):
        filename = re.sub(r'[\\/:"*?<>|]+', " ", topic)
        filename = filename.replace("\n", "")
        if not RESEARCH_PATH.exists():
            RESEARCH_PATH.mkdir(parents=True)
        filepath = RESEARCH_PATH / f"{filename}.md"
        filepath.write_text(content, encoding="utf-8")
        logger.info(f"Report written to {filepath}")
        return str(filepath)
