#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any

from metagpt.actions import Action
from metagpt.logs import logger

ARXIV_API_ENDPOINT = "http://export.arxiv.org/api/query"


@dataclass
class ArxivPaper:
    title: str
    summary: str
    url: str
    published_year: str
    venue: str = "arXiv"


class LiteratureReviewAction(Action):
    """
    Prepare lightweight literature context for software/paper collaboration.

    This action intentionally keeps output compact and deterministic, because the
    result is injected into Team prompts and also written to a fixed markdown file.
    """

    name: str = "LiteratureReviewAction"

    async def run(self, topic: str, max_results: int = 5) -> dict[str, Any]:
        topic = (topic or "").strip()
        if not topic:
            return {
                "topic": "",
                "summary": "No topic provided; skipped literature pre-review.",
                "papers": [],
            }

        try:
            papers = self._search_arxiv(topic=topic, max_results=max_results)
        except Exception as exc:  # pragma: no cover
            logger.warning(f"Literature search failed for topic '{topic}': {exc}")
            papers = []

        return {
            "topic": topic,
            "summary": self._build_summary(topic, papers),
            "papers": [self._paper_to_dict(paper) for paper in papers],
        }

    @staticmethod
    def _paper_to_dict(paper: ArxivPaper) -> dict[str, str]:
        return {
            "title": paper.title,
            "abstract": paper.summary,
            "url": paper.url,
            "year": paper.published_year,
            "venue": paper.venue,
        }

    def _search_arxiv(self, topic: str, max_results: int) -> list[ArxivPaper]:
        query = urllib.parse.urlencode(
            {
                "search_query": f"all:{topic}",
                "start": 0,
                "max_results": max_results,
                "sortBy": "relevance",
                "sortOrder": "descending",
            }
        )
        url = f"{ARXIV_API_ENDPOINT}?{query}"
        with urllib.request.urlopen(url, timeout=15) as response:
            xml_text = response.read().decode("utf-8", errors="replace")
        return self._parse_arxiv_feed(xml_text)

    def _parse_arxiv_feed(self, xml_text: str) -> list[ArxivPaper]:
        namespace = {"atom": "http://www.w3.org/2005/Atom"}
        root = ET.fromstring(xml_text)
        papers: list[ArxivPaper] = []

        for entry in root.findall("atom:entry", namespace):
            title = self._safe_text(entry.find("atom:title", namespace))
            summary = self._safe_text(entry.find("atom:summary", namespace))
            published = self._safe_text(entry.find("atom:published", namespace))
            published_year = published[:4] if len(published) >= 4 else "N/A"

            url = ""
            for link in entry.findall("atom:link", namespace):
                href = link.attrib.get("href")
                rel = link.attrib.get("rel", "")
                if href and rel in ("alternate", ""):
                    url = href
                    break

            papers.append(
                ArxivPaper(
                    title=title or "Untitled",
                    summary=summary or "",
                    url=url,
                    published_year=published_year,
                )
            )
        return papers

    @staticmethod
    def _safe_text(node: ET.Element | None) -> str:
        if node is None or node.text is None:
            return ""
        return " ".join(node.text.split())

    @staticmethod
    def _build_summary(topic: str, papers: list[ArxivPaper]) -> str:
        if not papers:
            return (
                f"Collected 0 papers for '{topic}'. "
                "Continue with domain reasoning and explicitly state limited evidence."
            )

        years = [paper.published_year for paper in papers if paper.published_year.isdigit()]
        if years:
            earliest, latest = min(years), max(years)
            year_span = f"{earliest}-{latest}"
        else:
            year_span = "N/A"

        return (
            f"Collected {len(papers)} arXiv papers for '{topic}'. "
            f"Coverage year span: {year_span}. "
            "Use these as evidence seeds, then synthesize themes, methods, strengths, and limitations."
        )
