#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import re

# Common multilingual hints for paper/literature requests.
PAPER_INTENT_KEYWORDS = (
    "paper",
    "papers",
    "essay",
    "survey",
    "literature",
    "literature review",
    "academic",
    "arxiv",
    "scholar",
    "citation",
    "论文",
    "文献",
    "综述",
    "学术",
    "检索",
)

# Trigger words used when literature pre-review mode is set to "keyword".
LITERATURE_REVIEW_HINTS = (
    "research",
    "analysis",
    "survey",
    "state of the art",
    "sota",
    "benchmark",
    "compare methods",
    "论文",
    "文献",
    "综述",
    "调研",
    "对比",
)

# Patterns to extract the probable topical phrase from natural language requests.
TOPIC_EXTRACTION_PATTERNS = (
    r"(?:topic|subject|field)\s*(?:is|:)\s*(?P<topic>[^.?!]+)",
    r"(?:about|on|regarding|related to)\s+(?P<topic>[^.?!]+)",
    r"(?:find|search|look for|retrieve)\s+(?:me\s+)?(?:papers?|essays?)\s+(?:about|on)\s+(?P<topic>[^.?!]+)",
    r"(?:论文|文献|综述)\s*(?:主题|方向)?\s*(?:是|为|关于)?\s*(?P<topic>[^。！？]+)",
)

# Prefix phrases that should be removed if they appear at the beginning of
# extracted topics.
FILLER_PREFIX_PATTERNS = (
    r"^(?:i want to|please|can you|could you|would you|help me|let me)\s+",
    r"^(?:find|search|look for|get|retrieve)\s+",
    r"^(?:me\s+)?(?:the\s+)?(?:papers?|essays?)\s+(?:of|about|on)\s+",
    r"^(?:请|帮我|我想|我需要)\s*",
    r"^(?:请)?帮我(?:找|搜索|检索)?(?:一些|有关|关于)?\s*",
    r"^(?:找|检索|搜索)\s*(?:一些|有关|关于)?\s*",
)

TOPIC_SUFFIX_PATTERNS = (
    r"\s*(?:for me|please)\s*$",
    r"\s*(?:thanks|thank you)\s*$",
)

# Lightweight typo/term normalization for common user inputs.
TOPIC_NORMALIZATION_MAP = {
    "software engining": "software engineering",
    "reinforcment learning": "reinforcement learning",
    "machine learnning": "machine learning",
}


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def _clean_extracted_topic(topic: str) -> str:
    cleaned = _normalize_whitespace(topic).strip(" '\"“”‘’`")
    if not cleaned:
        return cleaned

    lowered = cleaned.lower()
    for pattern in FILLER_PREFIX_PATTERNS:
        lowered = re.sub(pattern, "", lowered, flags=re.IGNORECASE).strip()
    for pattern in TOPIC_SUFFIX_PATTERNS:
        lowered = re.sub(pattern, "", lowered, flags=re.IGNORECASE).strip()

    # Remove trailing intent tokens left by loose extraction/fallback.
    lowered = re.sub(r"\b(?:paper|papers|essay|essays|literature|survey)\b\s*$", "", lowered).strip()
    lowered = re.sub(r"(?:论文|文献|综述)\s*$", "", lowered).strip()

    lowered = lowered.strip(" '\"“”‘’`")
    if lowered in TOPIC_NORMALIZATION_MAP:
        lowered = TOPIC_NORMALIZATION_MAP[lowered]

    return lowered


def looks_like_paper_research_topic(text: str) -> bool:
    """Return True if user input looks like an academic paper request."""
    content = (text or "").lower()
    if not content.strip():
        return False
    return any(keyword in content for keyword in PAPER_INTENT_KEYWORDS)


def should_trigger_literature_review(text: str) -> bool:
    """Return True when input is likely to benefit from literature pre-review."""
    content = (text or "").lower()
    if not content.strip():
        return False
    return any(hint in content for hint in LITERATURE_REVIEW_HINTS)


def extract_paper_research_topic(text: str) -> str:
    """Extract a concise topic phrase from natural language paper requests."""
    source = _normalize_whitespace(text)
    if not source:
        return ""

    for pattern in TOPIC_EXTRACTION_PATTERNS:
        match = re.search(pattern, source, flags=re.IGNORECASE)
        if not match:
            continue
        topic = _clean_extracted_topic(match.group("topic"))
        if topic:
            return topic

    # Fallback: clean the whole input and remove obvious intent tokens.
    fallback = source.lower()
    for keyword in PAPER_INTENT_KEYWORDS:
        fallback = fallback.replace(keyword, " ")
    fallback = _clean_extracted_topic(fallback)
    return fallback or source.lower()
