#!/usr/bin/env python
"""Nory x402 Payment Tools for MetaGPT.

Tools for AI agents to make payments using the x402 HTTP protocol.
Supports Solana and 7 EVM chains with sub-400ms settlement.
"""

from __future__ import annotations

import asyncio
import json
from concurrent import futures
from typing import Literal, Optional

import requests
from pydantic import BaseModel, ConfigDict, Field

from metagpt.tools.tool_registry import register_tool


NORY_API_BASE = "https://noryx402.com"

NoryNetwork = Literal[
    "solana-mainnet",
    "solana-devnet",
    "base-mainnet",
    "polygon-mainnet",
    "arbitrum-mainnet",
    "optimism-mainnet",
    "avalanche-mainnet",
    "sei-mainnet",
    "iotex-mainnet",
]


@register_tool(tags=["payment", "x402", "blockchain", "web3"])
class NoryX402PaymentTools(BaseModel):
    """Tools for making payments using the x402 HTTP protocol via Nory.

    Nory provides payment infrastructure for AI agents, supporting Solana and
    7 EVM chains (Base, Polygon, Arbitrum, Optimism, Avalanche, Sei, IoTeX)
    with sub-400ms settlement times.

    Use these tools when encountering HTTP 402 Payment Required responses.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    api_key: Optional[str] = Field(default=None, description="Nory API key (optional)")
    loop: Optional[asyncio.AbstractEventLoop] = None
    executor: Optional[futures.Executor] = None

    def _get_headers(self, content_type: bool = False) -> dict:
        """Get request headers with optional auth."""
        headers = {}
        if content_type:
            headers["Content-Type"] = "application/json"
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def get_payment_requirements(
        self,
        resource: str,
        amount: str,
        network: Optional[NoryNetwork] = None,
    ) -> dict:
        """Get x402 payment requirements for accessing a paid resource.

        Use this when you encounter an HTTP 402 Payment Required response
        and need to know how much to pay and where to send payment.

        Args:
            resource: The resource path requiring payment (e.g., /api/premium/data).
            amount: Amount in human-readable format (e.g., '0.10' for $0.10 USDC).
            network: Preferred blockchain network (optional).

        Returns:
            Payment requirements including amount, supported networks, and wallet address.
        """
        loop = self.loop or asyncio.get_event_loop()

        def _request():
            params = {"resource": resource, "amount": amount}
            if network:
                params["network"] = network
            response = requests.get(
                f"{NORY_API_BASE}/api/x402/requirements",
                params=params,
                headers=self._get_headers(),
                timeout=30,
            )
            response.raise_for_status()
            return response.json()

        return await loop.run_in_executor(self.executor, _request)

    async def verify_payment(self, payload: str) -> dict:
        """Verify a signed payment transaction before settlement.

        Use this to validate that a payment transaction is correct
        before submitting it to the blockchain.

        Args:
            payload: Base64-encoded payment payload containing signed transaction.

        Returns:
            Verification result including validity and payer info.
        """
        loop = self.loop or asyncio.get_event_loop()

        def _request():
            response = requests.post(
                f"{NORY_API_BASE}/api/x402/verify",
                json={"payload": payload},
                headers=self._get_headers(content_type=True),
                timeout=30,
            )
            response.raise_for_status()
            return response.json()

        return await loop.run_in_executor(self.executor, _request)

    async def settle_payment(self, payload: str) -> dict:
        """Settle a payment on-chain with ~400ms settlement time.

        Use this to submit a verified payment transaction to the blockchain.
        Settlement typically completes in under 400ms.

        Args:
            payload: Base64-encoded payment payload.

        Returns:
            Settlement result including transaction ID and network.
        """
        loop = self.loop or asyncio.get_event_loop()

        def _request():
            response = requests.post(
                f"{NORY_API_BASE}/api/x402/settle",
                json={"payload": payload},
                headers=self._get_headers(content_type=True),
                timeout=30,
            )
            response.raise_for_status()
            return response.json()

        return await loop.run_in_executor(self.executor, _request)

    async def lookup_transaction(
        self,
        transaction_id: str,
        network: NoryNetwork,
    ) -> dict:
        """Look up transaction status.

        Use this to check the status of a previously submitted payment
        including confirmations and current state.

        Args:
            transaction_id: Transaction ID or signature.
            network: Network where the transaction was submitted.

        Returns:
            Transaction status (pending, confirmed, failed) and confirmations.
        """
        loop = self.loop or asyncio.get_event_loop()

        def _request():
            response = requests.get(
                f"{NORY_API_BASE}/api/x402/transactions/{transaction_id}",
                params={"network": network},
                headers=self._get_headers(),
                timeout=30,
            )
            response.raise_for_status()
            return response.json()

        return await loop.run_in_executor(self.executor, _request)

    async def health_check(self) -> dict:
        """Check Nory service health and see supported networks.

        Use this to verify the payment service is operational
        before attempting payments.

        Returns:
            Health status and list of supported blockchain networks.
        """
        loop = self.loop or asyncio.get_event_loop()

        def _request():
            response = requests.get(
                f"{NORY_API_BASE}/api/x402/health",
                timeout=30,
            )
            response.raise_for_status()
            return response.json()

        return await loop.run_in_executor(self.executor, _request)


if __name__ == "__main__":
    import fire

    async def main():
        tools = NoryX402PaymentTools()
        result = await tools.health_check()
        print(json.dumps(result, indent=2))

    fire.Fire(lambda: asyncio.run(main()))
