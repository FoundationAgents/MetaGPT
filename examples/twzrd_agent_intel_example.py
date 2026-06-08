#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/06/08
@File    : twzrd_agent_intel_example.py
@Description: TWZRD Agent Intel MCP integration for MetaGPT.

Demonstrates how to use the TWZRD Agent Intel MCP server to verify agent trust
scores before authorizing x402 micropayments in a MetaGPT multi-agent system.

The TWZRD Agent Intel server provides:
  - score_agent(wallet)       — 0-100 trust score + risk flags (free)
  - preflight_check(wallet)   — PASS/FAIL gate for x402 payments (free)
  - get_trust_receipt(wallet) — signed trust receipt (HTTP 402 paid)

MCP endpoint: https://intel.twzrd.xyz/mcp  (streamable-http, no auth required)

Install:
    pip install metagpt mcp

Usage:
    python examples/twzrd_agent_intel_example.py
"""
import asyncio
import json
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from metagpt.actions import Action
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.logs import logger

TWZRD_MCP_URL = "https://intel.twzrd.xyz/mcp"


class CheckAgentTrust(Action):
    """Action: verify an agent's trust score via TWZRD Agent Intel."""

    name: str = "CheckAgentTrust"

    async def run(self, wallet: str) -> dict:
        """
        Call TWZRD Agent Intel MCP tools to score the agent.

        Args:
            wallet: Solana wallet address of the agent to check.

        Returns:
            dict with keys: score (int), preflight (str), risk_flags (list)
        """
        logger.info(f"Checking TWZRD trust for wallet {wallet[:8]}...")
        async with streamablehttp_client(TWZRD_MCP_URL) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()

                score_result = await session.call_tool(
                    "score_agent", {"wallet": wallet}
                )
                preflight_result = await session.call_tool(
                    "preflight_check", {"wallet": wallet}
                )

        score_text = score_result.content[0].text if score_result.content else "{}"
        preflight_text = preflight_result.content[0].text if preflight_result.content else ""

        try:
            score_data = json.loads(score_text)
        except (json.JSONDecodeError, AttributeError):
            score_data = {}

        return {
            "score": score_data.get("score", 0),
            "preflight": preflight_text,
            "risk_flags": score_data.get("risk_flags", []),
        }


class TrustVerifier(Role):
    """
    MetaGPT Role: verifies agent trust before authorizing x402 payments.

    In a multi-agent MetaGPT system, place this role as a gatekeeper before
    any agent that needs to make autonomous micropayments via x402.
    """

    name: str = "TrustVerifier"
    profile: str = "Trust Gatekeeper"
    goal: str = "Verify agent trust scores before authorizing x402 payments"
    constraints: str = "Reject agents with trust score < 60 or preflight FAIL"
    trust_threshold: int = 60

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._init_actions([CheckAgentTrust])

    async def _act(self) -> Message:
        msg = self.rc.history[-1]
        wallet = msg.content

        trust_action = CheckAgentTrust()
        result = await trust_action.run(wallet)

        score = result["score"]
        preflight = result["preflight"]
        risk_flags = result["risk_flags"]

        if score >= self.trust_threshold and "PASS" in preflight.upper():
            decision = "AUTHORIZED"
            reason = f"Trust score {score} >= {self.trust_threshold}, preflight PASS"
        else:
            decision = "REJECTED"
            reason = (
                f"Trust score {score} (threshold: {self.trust_threshold}), "
                f"preflight: {preflight}"
                + (f", risks: {risk_flags}" if risk_flags else "")
            )

        logger.info(f"Trust decision for {wallet[:8]}...: {decision} — {reason}")
        return Message(content=f"{decision}: {reason}", role=self.profile)


async def main():
    # Example: verify an agent wallet before allowing it to use x402 APIs
    verifier = TrustVerifier()

    # Simulate an incoming request to authorize a wallet
    agent_wallet = "4LkEFjHsF2ubC8K4oF2r3rCFqPZQVGBjL9mV6xkNPZdf"

    verifier.recv(Message(content=agent_wallet, role="user"))
    result = await verifier._act()
    print(f"\nResult: {result.content}")


if __name__ == "__main__":
    asyncio.run(main())
