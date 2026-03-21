"""Uniswap Trading API client — real swap quotes via Uniswap Developer Platform.

Integrates with trade-api.gateway.uniswap.org to provide:
- Real-time swap quotes with optimal routing (v3-pool, v4-pool)
- Gas estimates and price impact calculations
- Multi-chain support (Ethereum, Base)

Authentication: x-api-key header with Uniswap Developer Platform key.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("aegis.uniswap_api")

UNISWAP_API_BASE = "https://trade-api.gateway.uniswap.org/v1"

CHAIN_IDS: dict[str, int] = {
    "ethereum": 1,
    "base": 8453,
    "sepolia": 11155111,
}

TOKENS: dict[int, dict[str, str]] = {
    1: {
        "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "wstETH": "0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0",
        "stETH": "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84",
    },
    8453: {
        "WETH": "0x4200000000000000000000000000000000000006",
        "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    },
    11155111: {
        "WETH": "0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14",
        "USDC": "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238",
    },
}

DEFAULT_SWAPPER = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"


class UniswapTradingAPI:
    """Client for the Uniswap Trading API (trade-api.gateway.uniswap.org)."""

    def __init__(self, api_key: str = "") -> None:
        self.api_key = api_key or os.environ.get("UNISWAP_API_KEY", "")
        self._client = httpx.AsyncClient(timeout=15.0)

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    async def get_quote(
        self,
        token_in: str,
        token_out: str,
        amount: str,
        chain_id: int = 1,
        swapper: str = DEFAULT_SWAPPER,
        slippage: float = 0.5,
    ) -> dict[str, Any]:
        """Get a swap quote from the Uniswap Trading API."""
        if not self.available:
            return {"error": "UNISWAP_API_KEY not configured"}

        payload = {
            "type": "EXACT_INPUT",
            "amount": amount,
            "tokenInChainId": chain_id,
            "tokenOutChainId": chain_id,
            "tokenIn": token_in,
            "tokenOut": token_out,
            "swapper": swapper,
            "slippageTolerance": slippage,
        }

        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
        }

        try:
            resp = await self._client.post(
                f"{UNISWAP_API_BASE}/quote",
                json=payload,
                headers=headers,
            )
            data = resp.json()

            if resp.status_code != 200:
                logger.warning("Uniswap API error %d: %s", resp.status_code, data)
                return {"error": f"API error: {resp.status_code}", "detail": str(data)}

            return self._parse_quote(data, token_in, token_out, chain_id)
        except Exception as exc:
            logger.warning("Uniswap API request failed: %s", exc)
            return {"error": str(exc)}

    def _parse_quote(
        self,
        raw: dict[str, Any],
        token_in: str,
        token_out: str,
        chain_id: int,
    ) -> dict[str, Any]:
        """Parse the raw API response into a clean quote format."""
        quote = raw.get("quote", raw)
        routing = raw.get("routing", "UNKNOWN")

        route_info: list[dict[str, str]] = []
        if "route" in quote:
            for route_path in quote["route"]:
                for pool in route_path:
                    route_info.append({
                        "type": pool.get("type", "v3-pool"),
                        "address": pool.get("address", ""),
                        "fee": str(pool.get("fee", "")),
                        "tokenIn": pool.get("tokenIn", {}).get("symbol", ""),
                        "tokenOut": pool.get("tokenOut", {}).get("symbol", ""),
                    })

        amount_in = quote.get("input", {}).get("amount", quote.get("amountIn", "0"))
        amount_out = quote.get("output", {}).get("amount", quote.get("amountOut", "0"))
        gas_estimate = quote.get("gasUseEstimate", quote.get("gasFee", "0"))
        gas_usd = quote.get("gasUseEstimateUSD", quote.get("gasFeeUSD", "0"))
        price_impact = quote.get("priceImpact", "0")

        return {
            "token_in": token_in,
            "token_out": token_out,
            "chain_id": chain_id,
            "amount_in": str(amount_in),
            "amount_out": str(amount_out),
            "gas_estimate": str(gas_estimate),
            "gas_usd": str(gas_usd),
            "price_impact": str(price_impact),
            "routing": routing,
            "route": route_info,
            "slippage": quote.get("slippage", {}).get("tolerance", 0.5),
            "source": "uniswap_trading_api",
        }

    async def get_eth_to_usdc_quote(
        self,
        amount_wei: str = "1000000000000000000",
        chain_id: int = 1,
    ) -> dict[str, Any]:
        """Convenience: get a quote for swapping ETH → USDC."""
        tokens = TOKENS.get(chain_id, TOKENS[1])
        return await self.get_quote(
            token_in=tokens["WETH"],
            token_out=tokens["USDC"],
            amount=amount_wei,
            chain_id=chain_id,
        )

    async def get_wsteth_to_eth_quote(
        self,
        amount_wei: str = "1000000000000000000",
    ) -> dict[str, Any]:
        """Convenience: get a quote for swapping wstETH → WETH (Lido)."""
        return await self.get_quote(
            token_in=TOKENS[1]["wstETH"],
            token_out=TOKENS[1]["WETH"],
            amount=amount_wei,
            chain_id=1,
        )

    async def check_approval(
        self,
        token: str,
        amount: str,
        wallet_address: str,
        chain_id: int = 11155111,
    ) -> dict[str, Any]:
        """Check if the Permit2 contract is approved to spend the token."""
        if not self.available:
            return {"error": "UNISWAP_API_KEY not configured"}

        payload = {
            "token": token,
            "amount": amount,
            "chainId": chain_id,
            "walletAddress": wallet_address,
        }
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
        }
        try:
            resp = await self._client.post(
                f"{UNISWAP_API_BASE}/check_approval",
                json=payload,
                headers=headers,
            )
            data = resp.json()
            if resp.status_code != 200:
                return {"error": f"Approval check error: {resp.status_code}", "detail": str(data)}
            return data
        except Exception as exc:
            logger.warning("Approval check failed: %s", exc)
            return {"error": str(exc)}

    async def get_swap(
        self,
        token_in: str,
        token_out: str,
        amount: str,
        wallet_address: str,
        chain_id: int = 11155111,
        slippage: float = 0.5,
    ) -> dict[str, Any]:
        """Get swap calldata from the Uniswap Trading API.

        Returns transaction data (to, data, value, gasLimit) ready for signing.
        """
        if not self.available:
            return {"error": "UNISWAP_API_KEY not configured"}

        payload = {
            "type": "EXACT_INPUT",
            "amount": amount,
            "tokenInChainId": chain_id,
            "tokenOutChainId": chain_id,
            "tokenIn": token_in,
            "tokenOut": token_out,
            "swapper": wallet_address,
            "slippageTolerance": slippage,
        }
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
        }
        try:
            resp = await self._client.post(
                f"{UNISWAP_API_BASE}/swap",
                json=payload,
                headers=headers,
            )
            data = resp.json()
            if resp.status_code != 200:
                logger.warning("Swap API error %d: %s", resp.status_code, data)
                return {"error": f"Swap API error: {resp.status_code}", "detail": str(data)}
            return data
        except Exception as exc:
            logger.warning("Swap API request failed: %s", exc)
            return {"error": str(exc)}

    async def execute_swap(
        self,
        token_in: str,
        token_out: str,
        amount: str,
        wallet_address: str,
        chain_id: int = 11155111,
    ) -> dict[str, Any]:
        """Full swap flow: quote → swap calldata. Caller signs and broadcasts.

        Returns the swap transaction data or an error.
        """
        quote = await self.get_quote(
            token_in=token_in,
            token_out=token_out,
            amount=amount,
            chain_id=chain_id,
            swapper=wallet_address,
        )
        if "error" in quote:
            return quote

        swap_data = await self.get_swap(
            token_in=token_in,
            token_out=token_out,
            amount=amount,
            wallet_address=wallet_address,
            chain_id=chain_id,
        )
        if "error" in swap_data:
            return {"error": swap_data["error"], "quote": quote}

        swap_data["quote"] = quote
        return swap_data

    async def close(self) -> None:
        await self._client.aclose()
