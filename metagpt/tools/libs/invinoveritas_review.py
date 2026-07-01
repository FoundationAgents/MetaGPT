#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from typing import Optional

import httpx

from metagpt.tools.tool_registry import register_tool


@register_tool(tags=["software development", "safety", "get an independent review before an irreversible action"])
async def invinoveritas_review(
    artifact: str,
    artifact_type: str = "general",
    concerns: Optional[str] = None,
) -> dict:
    """
    Gets an independent, recomputable second opinion from invinoveritas
    (https://api.babyblueviper.com) before an irreversible action -- a shell command, a git
    push, a deploy, a config change, or a trade. Returns a structured verdict (approve /
    approve_with_concerns / reject) plus ranked issues. Use this BEFORE Terminal.run_command
    for anything that isn't trivially reversible, and before Deployer.deploy_to_public --
    Terminal's own forbidden_commands list only catches two hardcoded patterns ("run dev",
    "serve "), so this tool is the general-purpose check for everything that list doesn't cover.

    Requires the INVINOVERITAS_API_KEY environment variable. Free registration at
    https://api.babyblueviper.com/register returns an api_key with trial calls per tool; no
    crypto/payment setup is needed to try this.

    Args:
        artifact (str): the exact thing to review -- a shell command, a git diff, a config
            change, or a plan description.
        artifact_type (str): a label for what `artifact` is (e.g. "shell_command", "code_diff",
            "config_change", "plan"). Defaults to "general".
        concerns (Optional[str]): specific things to check for (e.g. "does this touch
            production data?"). Defaults to None (general review).

    Example:
        >>> result = await invinoveritas_review(
        >>>     artifact="rm -rf /var/log/*.log && systemctl restart nginx",
        >>>     artifact_type="shell_command",
        >>> )
        >>> print(result["verdict"], result["summary"])
        reject Broad recursive deletion combined with a service restart risks removing logs
        still being written and disrupting nginx if the restart fails after the delete.
        >>> if result["verdict"] == "reject":
        >>>     raise RuntimeError("invinoveritas rejected this action: " + result["summary"])

    Returns:
        dict: {"verdict": "approve"|"approve_with_concerns"|"reject", "confidence": float,
            "summary": str, "issues": [{"severity": str, "description": str,
            "suggested_fix": str}, ...]}. A missing/failed call returns
            {"verdict": "unavailable", "summary": "<error>", "issues": []} -- treat this the
            same as "approve_with_concerns" (the check couldn't run, it did not pass).
    """
    api_key = os.environ.get("INVINOVERITAS_API_KEY", "").strip()
    if not api_key:
        return {
            "verdict": "unavailable",
            "confidence": 0.0,
            "summary": (
                "INVINOVERITAS_API_KEY is not set -- register free at "
                "https://api.babyblueviper.com/register to get one (trial calls included)."
            ),
            "issues": [],
        }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.babyblueviper.com/review",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"artifact": artifact, "artifact_type": artifact_type, "concerns": concerns or ""},
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as e:
        return {
            "verdict": "unavailable",
            "confidence": 0.0,
            "summary": f"invinoveritas review call failed: {e}",
            "issues": [],
        }

    return {
        "verdict": data.get("verdict", "unavailable"),
        "confidence": data.get("confidence", 0.0),
        "summary": data.get("summary", ""),
        "issues": data.get("issues") or [],
    }
