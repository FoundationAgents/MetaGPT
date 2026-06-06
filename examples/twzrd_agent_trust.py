#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2026/06/06
@Author  : TWZRD
@File    : twzrd_agent_trust.py
@Description: Example showing MetaGPT agents using TWZRD Agent Intel MCP server
              to score Solana AI agent wallets before x402 payments.

MCP server: https://intel.twzrd.xyz/mcp (streamable-HTTP, zero-install)

Requirements:
    pip install metagpt mcp
"""

import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from metagpt.actions import Action
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message


class ScoreAgentWallet(Action):
    """Action that calls TWZRD Agent Intel MCP to score a Solana wallet."""

    name: str = "ScoreAgentWallet"
    i_context: str = ""

    async def run(self, wallet: str) -> dict:
        """Score a Solana agent wallet via TWZRD Agent Intel MCP."""
        async with streamablehttp_client("https://intel.twzrd.xyz/mcp") as (r, w, _):
            async with ClientSession(r, w) as session:
                await session.initialize()

                # Call score_agent tool (free, no API key needed)
                result = await session.call_tool("score_agent", {"wallet": wallet})
                score_data = result.content[0].text

                # Call preflight_check for full due diligence (also free)
                preflight = await session.call_tool("preflight_check", {"wallet": wallet})
                preflight_data = preflight.content[0].text

                return {
                    "wallet": wallet,
                    "score": score_data,
                    "preflight": preflight_data,
                }


class TrustAnalyst(Role):
    """A MetaGPT role that evaluates Solana agent wallets for x402 payment trust."""

    name: str = "TrustAnalyst"
    profile: str = "Solana Agent Trust Analyst"
    goal: str = "Score Solana agent wallets and decide whether to APPROVE x402 payments"
    constraints: str = "Reject any wallet with trust score below 0.5"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([ScoreAgentWallet])

    async def _act(self) -> Message:
        wallet = self.rc.memory.get(k=1)[-1].content
        logger.info(f"Scoring wallet: {wallet}")

        trust_data = await self.rc.todo.run(wallet)
        recommendation = "APPROVE" if "score" in trust_data else "REJECT"
        content = f"Wallet: {wallet}\nScore: {trust_data['score']}\nPreflight: {trust_data['preflight']}\nRecommendation: {recommendation}"
        return Message(content=content, role=self.profile)


async def main():
    # Example: score a known active Solana agent wallet
    wallet = "D1QkbFJKiPsymJ65RKHhF6DFB8sPMfpBaFBzuHKfJGWi"

    analyst = TrustAnalyst()
    result = await analyst.run(wallet)
    print("\n=== Trust Assessment ===")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
