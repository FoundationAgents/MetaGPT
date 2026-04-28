#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
from typing import Any

from metagpt.actions import Action
from metagpt.logs import logger

INTENT_CLASSIFIER_PROMPT = """
You are an intent classifier for MetaGPT startup requests.
Classify whether the user input is mainly asking for academic paper/literature research or software building tasks.

Return ONLY a JSON object with this schema:
{
  "collaboration_mode": "paper" | "software",
  "topic": "string",
  "confidence": 0.0-1.0,
  "reason": "short reason"
}

Rules:
- Use "paper" when the input asks for papers, essays, literature review, survey, citations, arXiv, scholarly analysis.
- Use "software" for coding/product/system-building tasks.
- topic should be concise; for software mode, topic can be the original request.
- Do not include markdown code fences.
""".strip()


def _extract_first_json_payload(text: str) -> str:
    source = (text or "").strip()
    if not source:
        return source
    decoder = json.JSONDecoder()
    for index, char in enumerate(source):
        if char not in "[{":
            continue
        candidate = source[index:]
        try:
            _, end = decoder.raw_decode(candidate)
            return candidate[:end]
        except json.JSONDecodeError:
            continue
    return source


class IntentClassificationAction(Action):
    """Classify startup idea into paper/software collaboration mode."""

    name: str = "IntentClassificationAction"

    async def run(self, user_input: str) -> dict[str, Any]:
        prompt = f"{INTENT_CLASSIFIER_PROMPT}\n\nUser input:\n{user_input}"
        rsp = await self._aask(prompt)
        data = self._parse_response(rsp)

        mode = str(data.get("collaboration_mode", "software")).strip().lower()
        if mode not in {"paper", "software"}:
            mode = "software"

        topic = str(data.get("topic") or user_input).strip() or user_input
        reason = str(data.get("reason", "")).strip()
        confidence = self._safe_confidence(data.get("confidence"))
        return {
            "collaboration_mode": mode,
            "topic": topic,
            "confidence": confidence,
            "reason": reason,
        }

    @staticmethod
    def _safe_confidence(raw: Any) -> float:
        try:
            value = float(raw)
        except (TypeError, ValueError):
            return 0.0
        return max(0.0, min(1.0, value))

    @staticmethod
    def _parse_response(rsp: str) -> dict[str, Any]:
        payload = _extract_first_json_payload(rsp)
        try:
            data = json.loads(payload)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            logger.warning("Intent classifier JSON parse failed; fallback will be used.")
        return {}
