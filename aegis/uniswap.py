"""Uniswap V3 on-chain client — real pool queries via web3.py.

Queries live Uniswap V3 pool state (prices, liquidity, fees) from
Ethereum Mainnet and Base. Falls back gracefully to simulation
mode if RPC is unavailable.
"""

from __future__ import annotations

import asyncio
import logging
import math
import time
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Callable, TypeVar

T = TypeVar("T")

try:
    from web3 import Web3
    from web3.providers import HTTPProvider

    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False

logger = logging.getLogger("aegis.uniswap")

# ── Minimal ABIs ──────────────────────────────────────────────────

POOL_ABI: list[dict[str, Any]] = [
    {
        "inputs": [],
        "name": "slot0",
        "outputs": [
            {"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"},
            {"internalType": "int24", "name": "tick", "type": "int24"},
            {"internalType": "uint16", "name": "observationIndex", "type": "uint16"},
            {"internalType": "uint16", "name": "observationCardinality", "type": "uint16"},
            {"internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16"},
            {"internalType": "uint8", "name": "feeProtocol", "type": "uint8"},
            {"internalType": "bool", "name": "unlocked", "type": "bool"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "liquidity",
        "outputs": [{"internalType": "uint128", "name": "", "type": "uint128"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "fee",
        "outputs": [{"internalType": "uint24", "name": "", "type": "uint24"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "feeGrowthGlobal0X128",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "feeGrowthGlobal1X128",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "token0",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "token1",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
]

FACTORY_ABI: list[dict[str, Any]] = [
    {
        "inputs": [
            {"internalType": "address", "name": "tokenA", "type": "address"},
            {"internalType": "address", "name": "tokenB", "type": "address"},
            {"internalType": "uint24", "name": "fee", "type": "uint24"},
        ],
        "name": "getPool",
        "outputs": [{"internalType": "address", "name": "pool", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
]

POSITION_MANAGER_ABI: list[dict[str, Any]] = [
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "positions",
        "outputs": [
            {"internalType": "uint96", "name": "nonce", "type": "uint96"},
            {"internalType": "address", "name": "operator", "type": "address"},
            {"internalType": "address", "name": "token0", "type": "address"},
            {"internalType": "address", "name": "token1", "type": "address"},
            {"internalType": "uint24", "name": "fee", "type": "uint24"},
            {"internalType": "int24", "name": "tickLower", "type": "int24"},
            {"internalType": "int24", "name": "tickUpper", "type": "int24"},
            {"internalType": "uint128", "name": "liquidity", "type": "uint128"},
            {"internalType": "uint256", "name": "feeGrowthInside0LastX128", "type": "uint256"},
            {"internalType": "uint256", "name": "feeGrowthInside1LastX128", "type": "uint256"},
            {"internalType": "uint128", "name": "tokensOwed0", "type": "uint128"},
            {"internalType": "uint128", "name": "tokensOwed1", "type": "uint128"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
]

# ── Well-known addresses ──────────────────────────────────────────

UNISWAP_V3_FACTORY = "0x1F98431c8aD98523631AE4a59f267346ea31F984"
NONFUNGIBLE_POSITION_MANAGER = "0xC36442b4a4522E871399CD717aBDD847Ab11FE88"

DEMO_POSITION_IDS: dict[str, list[int]] = {
    "ethereum": [728370, 727643, 726000],
    "base": [100000],
    "sepolia": [],
}

CHAIN_PRESETS: dict[str, dict[str, Any]] = {
    "ethereum": {
        "rpc_public": "https://eth.llamarpc.com",
        "rpc_fallbacks": [
            "https://eth.llamarpc.com",
            "https://ethereum-rpc.publicnode.com",
            "https://1rpc.io/eth",
            "https://eth.drpc.org",
            "https://cloudflare-eth.com",
            "https://rpc.mevblocker.io",
        ],
        "rpc_alchemy": "https://eth-mainnet.g.alchemy.com/v2/{key}",
        "factory": UNISWAP_V3_FACTORY,
        "nft_manager": NONFUNGIBLE_POSITION_MANAGER,
        "weth": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "usdc": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "usdt": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "dai": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
        "default_pool": "0x8ad599c3A0ff1De082011EFDDc58f1908eb6e6D8",
        "pools": [
            {"address": "0x8ad599c3A0ff1De082011EFDDc58f1908eb6e6D8", "label": "ETH/USDC 0.3%", "token0_decimals": 6, "token1_decimals": 18, "invert_price": True},
            {"address": "0x4e68Ccd3E89f51C3074ca5072bbAC773960dFa36", "label": "ETH/USDT 0.3%", "token0_decimals": 18, "token1_decimals": 6, "invert_price": False},
            {"address": "0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640", "label": "ETH/USDC 0.05%", "token0_decimals": 6, "token1_decimals": 18, "invert_price": True},
            {"address": "0x109830a1AAaD605BbF02a9dFA7B0B92EC2FB7dAa", "label": "wstETH/ETH 0.01%", "token0_decimals": 18, "token1_decimals": 18, "invert_price": True},
            {"address": "0x63818BbDd21E69bE108A23aC1E84cBf66399Bd7D", "label": "stETH/ETH 1%", "token0_decimals": 18, "token1_decimals": 18, "invert_price": False},
        ],
        "pool_label": "ETH/USDC 0.3%",
        "token0_decimals": 6,
        "token1_decimals": 18,
        "invert_price": True,
    },
    "base": {
        "rpc_public": "https://mainnet.base.org",
        "rpc_fallbacks": [
            "https://mainnet.base.org",
            "https://base.llamarpc.com",
            "https://base-rpc.publicnode.com",
            "https://1rpc.io/base",
            "https://base.drpc.org",
        ],
        "rpc_alchemy": "https://base-mainnet.g.alchemy.com/v2/{key}",
        "factory": UNISWAP_V3_FACTORY,
        "nft_manager": NONFUNGIBLE_POSITION_MANAGER,
        "weth": "0x4200000000000000000000000000000000000006",
        "usdc": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "default_pool": "0xd0b53D9277642d899DF5C87A3966A349A798F224",
        "pools": [
            {"address": "0xd0b53D9277642d899DF5C87A3966A349A798F224", "label": "ETH/USDC 0.05%", "token0_decimals": 18, "token1_decimals": 6, "invert_price": False},
        ],
        "pool_label": "ETH/USDC 0.05%",
        "token0_decimals": 18,
        "token1_decimals": 6,
        "invert_price": False,
    },
    "sepolia": {
        "rpc_public": "https://rpc.sepolia.org",
        "rpc_fallbacks": [
            "https://rpc.sepolia.org",
            "https://ethereum-sepolia-rpc.publicnode.com",
            "https://sepolia.drpc.org",
        ],
        "rpc_alchemy": "https://eth-sepolia.g.alchemy.com/v2/{key}",
        "factory": "0x0227628f3F023bb0B980b67D528571c95c6DaC1c",
        "nft_manager": "0x1238536071E1c677A632429e3655c799b22cDA52",
        "weth": "0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14",
        "usdc": "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238",
        "default_pool": "0x6418EEC70f50913ff0d756B48d32Ce7C02b47C47",
        "pools": [
            {"address": "0x6418EEC70f50913ff0d756B48d32Ce7C02b47C47", "label": "WETH/USDC (Sepolia)", "token0_decimals": 18, "token1_decimals": 6, "invert_price": False},
        ],
        "pool_label": "WETH/USDC (Sepolia)",
        "token0_decimals": 18,
        "token1_decimals": 6,
        "invert_price": False,
    },
}

Q96 = Decimal(2**96)
Q128 = Decimal(2**128)


@dataclass
class PoolState:
    """Snapshot of a Uniswap V3 pool's on-chain state."""

    pool_address: str
    chain: str
    token_pair: str
    sqrt_price_x96: int
    tick: int
    liquidity: int
    fee_bps: int
    fee_growth_global_0: int
    fee_growth_global_1: int
    eth_price_usd: Decimal
    token0_decimals: int
    token1_decimals: int


@dataclass
class PositionState:
    """Snapshot of a Uniswap V3 LP position from NonfungiblePositionManager."""

    token_id: int
    token0: str
    token1: str
    fee: int
    tick_lower: int
    tick_upper: int
    liquidity: int
    tokens_owed_0: int
    tokens_owed_1: int
    in_range: bool


class UniswapV3Client:
    """Queries live Uniswap V3 pool data via web3.py.

    Falls back gracefully if web3 is not installed or RPC is unreachable.
    """

    def __init__(self, chain: str = "ethereum", alchemy_key: str = "") -> None:
        self.chain = chain
        self.live = False
        self._w3: Any = None
        self._pool_contract: Any = None
        self._pool_contracts: dict[str, Any] = {}
        self._pool_configs: dict[str, dict[str, Any]] = {}
        self._position_manager: Any = None
        self._pool_address: str = ""
        self._token_pair: str = ""
        self._token0_decimals: int = 6
        self._token1_decimals: int = 18
        self._invert_price: bool = True
        self._rpc_urls: list[str] = []
        self._rpc_index: int = 0

        if not WEB3_AVAILABLE:
            logger.warning("web3 not installed — running in simulation mode")
            return

        preset = CHAIN_PRESETS.get(chain)
        if not preset:
            logger.warning("Unknown chain '%s' — running in simulation mode", chain)
            return

        if alchemy_key:
            self._rpc_urls = [preset["rpc_alchemy"].format(key=alchemy_key)]
            self._rpc_urls.extend(preset.get("rpc_fallbacks", [preset["rpc_public"]]))
        else:
            self._rpc_urls = list(preset.get("rpc_fallbacks", [preset["rpc_public"]]))

        connected = False
        for idx, rpc_url in enumerate(self._rpc_urls):
            try:
                self._w3 = Web3(HTTPProvider(rpc_url, request_kwargs={"timeout": 15}))
                if self._w3.is_connected():
                    self._rpc_index = idx
                    connected = True
                    break
                else:
                    logger.debug("RPC %s not reachable — trying next", rpc_url)
            except Exception as exc:
                logger.debug("RPC %s failed: %s — trying next", rpc_url, exc)

        if connected:
            self.live = True
            self._pool_address = preset["default_pool"]
            self._token_pair = preset["pool_label"]
            self._token0_decimals = preset["token0_decimals"]
            self._token1_decimals = preset["token1_decimals"]
            self._invert_price = preset.get("invert_price", True)
            self._rebuild_contracts(preset)
            logger.info(
                "Connected to %s via %s — monitoring %s (%s) + %d pools [%d RPC fallbacks]",
                chain,
                self._rpc_urls[self._rpc_index],
                self._token_pair,
                self._pool_address[:10] + "...",
                len(self._pool_contracts),
                len(self._rpc_urls),
            )
        else:
            logger.warning(
                "All %d RPC endpoints unreachable for %s — running in simulation mode",
                len(self._rpc_urls), chain,
            )

    def _rebuild_contracts(self, preset: dict[str, Any] | None = None) -> None:
        """Rebuild all contract instances from the current Web3 provider."""
        if preset is None:
            preset = CHAIN_PRESETS.get(self.chain, {})
        self._pool_contract = self._w3.eth.contract(
            address=Web3.to_checksum_address(self._pool_address),
            abi=POOL_ABI,
        )
        self._pool_contracts.clear()
        for pcfg in preset.get("pools", []):
            label = pcfg["label"]
            addr = Web3.to_checksum_address(pcfg["address"])
            self._pool_contracts[label] = self._w3.eth.contract(
                address=addr, abi=POOL_ABI,
            )
            self._pool_configs[label] = pcfg
        pm_addr = preset.get("nft_manager", NONFUNGIBLE_POSITION_MANAGER)
        self._position_manager = self._w3.eth.contract(
            address=Web3.to_checksum_address(pm_addr),
            abi=POSITION_MANAGER_ABI,
        )

    def _rotate_rpc(self) -> None:
        """Switch to the next fallback RPC endpoint on rate-limit errors."""
        if len(self._rpc_urls) <= 1:
            return
        self._rpc_index = (self._rpc_index + 1) % len(self._rpc_urls)
        new_url = self._rpc_urls[self._rpc_index]
        logger.info("⚡ Rotating RPC → %s", new_url)
        try:
            self._w3 = Web3(HTTPProvider(new_url, request_kwargs={"timeout": 10}))
            if self._pool_address:
                self._rebuild_contracts()
        except Exception as exc:
            logger.warning("RPC rotation failed for %s: %s", new_url, exc)

    # ── Retry logic with RPC rotation ─────────────────────────────

    def _call_with_retry(
        self,
        fn: Callable[..., T],
        *args: Any,
        max_retries: int = 3,
        backoff_base: float = 0.5,
        label: str = "RPC call",
    ) -> T:
        """Call *fn* with exponential backoff on transient RPC errors.

        On 429 (rate limit) errors, rotates to the next fallback RPC
        endpoint before retrying. Other transient errors use standard
        exponential backoff.
        """
        rate_limit_patterns = ("429", "rate limit", "too many requests", "unauthorized")
        transient_patterns = ("header not found", "request failed", "connection",
                              "timeout", "rate limit", "429", "502", "503",
                              "unauthorized")
        last_exc: Exception | None = None

        for attempt in range(max_retries):
            try:
                return fn(*args)
            except Exception as exc:
                last_exc = exc
                err_str = str(exc).lower()
                is_rate_limited = any(p in err_str for p in rate_limit_patterns)
                is_transient = any(p in err_str for p in transient_patterns)

                if not is_transient:
                    raise  # non-transient → fail fast

                if attempt < max_retries - 1:
                    if is_rate_limited:
                        self._rotate_rpc()
                        delay = 0.3
                    else:
                        delay = backoff_base * (2 ** attempt)
                    logger.debug(
                        "%s attempt %d/%d failed (%s) — retrying in %.1fs",
                        label, attempt + 1, max_retries, exc, delay,
                    )
                    time.sleep(delay)
                else:
                    logger.warning(
                        "%s failed after %d attempts: %s",
                        label, max_retries, exc,
                    )

        raise last_exc  # type: ignore[misc]

    @property
    def pool_address(self) -> str:
        return self._pool_address

    @property
    def token_pair(self) -> str:
        return self._token_pair

    async def get_pool_state(self) -> PoolState | None:
        """Fetch current pool state from chain. Returns None on failure."""
        if not self.live or not self._pool_contract:
            return None

        try:
            state = await asyncio.to_thread(
                self._call_with_retry,
                self._fetch_pool_state_sync,
                label="get_pool_state",
            )
            return state
        except Exception as exc:
            logger.warning("Pool query failed: %s", exc)
            return None

    def _fetch_pool_state_sync(self) -> PoolState:
        """Synchronous pool state fetch (run in thread)."""
        contract = self._pool_contract

        slot0 = contract.functions.slot0().call()
        liquidity = contract.functions.liquidity().call()
        fee = contract.functions.fee().call()
        fg0 = contract.functions.feeGrowthGlobal0X128().call()
        fg1 = contract.functions.feeGrowthGlobal1X128().call()

        sqrt_price_x96 = slot0[0]
        tick = slot0[1]

        eth_price = self._sqrt_price_to_eth_usd(
            sqrt_price_x96, self._token0_decimals, self._token1_decimals,
            self._invert_price,
        )

        return PoolState(
            pool_address=self._pool_address,
            chain=self.chain,
            token_pair=self._token_pair,
            sqrt_price_x96=sqrt_price_x96,
            tick=tick,
            liquidity=liquidity,
            fee_bps=fee,
            fee_growth_global_0=fg0,
            fee_growth_global_1=fg1,
            eth_price_usd=eth_price,
            token0_decimals=self._token0_decimals,
            token1_decimals=self._token1_decimals,
        )

    @staticmethod
    def _sqrt_price_to_eth_usd(
        sqrt_price_x96: int, token0_decimals: int, token1_decimals: int,
        invert_price: bool = True,
    ) -> Decimal:
        """Convert sqrtPriceX96 to human-readable ETH/USD price.

        Uniswap V3 stores sqrt(price) * 2^96 where price = token1/token0 in raw units.
        On Ethereum (USDC=token0, WETH=token1): invert to get USD per ETH.
        On Base (WETH=token0, USDC=token1): human_price is already USD per ETH.
        """
        sqrt_price = Decimal(sqrt_price_x96) / Q96
        raw_price = sqrt_price ** 2

        decimal_adjustment = Decimal(10 ** (token0_decimals - token1_decimals))
        human_price = raw_price * decimal_adjustment

        if human_price <= 0:
            return Decimal("0")

        if invert_price:
            eth_price_usd = (Decimal(1) / human_price).quantize(Decimal("0.01"))
        else:
            eth_price_usd = human_price.quantize(Decimal("0.01"))

        return eth_price_usd

    @staticmethod
    def calculate_il(entry_price: Decimal, current_price: Decimal) -> Decimal:
        """Calculate impermanent loss percentage for a full-range V2-style position.

        IL = 2 * sqrt(r) / (1 + r) - 1
        where r = current_price / entry_price
        """
        if entry_price <= 0 or current_price <= 0:
            return Decimal("0")

        r = float(current_price / entry_price)
        if r <= 0:
            return Decimal("0")

        il = 2 * math.sqrt(r) / (1 + r) - 1
        return Decimal(str(abs(il) * 100)).quantize(Decimal("0.01"))

    @staticmethod
    def calculate_il_v3(
        entry_price: Decimal,
        current_price: Decimal,
        tick_lower: int,
        tick_upper: int,
    ) -> Decimal:
        """Calculate IL for a concentrated liquidity position in range [tick_lower, tick_upper].

        V3 IL is amplified relative to V2 by the concentration factor.
        """
        if entry_price <= 0 or current_price <= 0:
            return Decimal("0")

        price_lower = Decimal(str(1.0001 ** tick_lower))
        price_upper = Decimal(str(1.0001 ** tick_upper))

        if price_upper <= price_lower:
            return Decimal("0")

        v2_il = UniswapV3Client.calculate_il(entry_price, current_price)

        sqrt_pl = Decimal(str(math.sqrt(float(price_lower))))
        sqrt_pu = Decimal(str(math.sqrt(float(price_upper))))
        concentration = (sqrt_pu + sqrt_pl) / (sqrt_pu - sqrt_pl) if sqrt_pu > sqrt_pl else Decimal("1")

        return (v2_il * concentration).quantize(Decimal("0.01"))

    async def get_multi_pool_states(self) -> list[PoolState]:
        """Fetch state for all configured pools on this chain.

        Adds a small delay between queries to avoid hammering a single RPC.
        """
        if not self.live or not self._w3:
            return []

        preset = CHAIN_PRESETS.get(self.chain)
        if not preset or "pools" not in preset:
            state = await self.get_pool_state()
            return [state] if state else []

        states: list[PoolState] = []
        for i, pool_info in enumerate(preset["pools"]):
            try:
                state = await asyncio.to_thread(
                    self._call_with_retry,
                    self._fetch_pool_by_address,
                    pool_info["address"],
                    pool_info["label"],
                    pool_info["token0_decimals"],
                    pool_info["token1_decimals"],
                    pool_info.get("invert_price", True),
                    label=f"multi_pool({pool_info['label']})",
                )
                states.append(state)
            except Exception as exc:
                logger.warning("Multi-pool query failed for %s: %s", pool_info["label"], exc)
            if i < len(preset["pools"]) - 1:
                await asyncio.sleep(0.25)

        return states

    def _fetch_pool_by_address(
        self,
        address: str,
        label: str,
        t0_decimals: int,
        t1_decimals: int,
        invert: bool,
    ) -> PoolState:
        """Fetch state for a specific pool address."""
        contract = self._w3.eth.contract(
            address=Web3.to_checksum_address(address),
            abi=POOL_ABI,
        )
        slot0 = contract.functions.slot0().call()
        liquidity = contract.functions.liquidity().call()
        fee = contract.functions.fee().call()
        fg0 = contract.functions.feeGrowthGlobal0X128().call()
        fg1 = contract.functions.feeGrowthGlobal1X128().call()

        eth_price = self._sqrt_price_to_eth_usd(
            slot0[0], t0_decimals, t1_decimals, invert,
        )

        return PoolState(
            pool_address=address,
            chain=self.chain,
            token_pair=label,
            sqrt_price_x96=slot0[0],
            tick=slot0[1],
            liquidity=liquidity,
            fee_bps=fee,
            fee_growth_global_0=fg0,
            fee_growth_global_1=fg1,
            eth_price_usd=eth_price,
            token0_decimals=t0_decimals,
            token1_decimals=t1_decimals,
        )

    @property
    def available_pools(self) -> list[str]:
        """Return labels of all available pools on this chain."""
        return list(self._pool_configs.keys())

    async def get_pool_state_for(self, pool_label: str) -> PoolState | None:
        """Fetch state for a specific named pool."""
        if not self.live or pool_label not in self._pool_contracts:
            return None
        try:
            contract = self._pool_contracts[pool_label]
            pcfg = self._pool_configs[pool_label]
            return await asyncio.to_thread(
                self._call_with_retry,
                self._fetch_pool_state_for_sync,
                contract, pcfg, pool_label,
                label=f"pool({pool_label})",
            )
        except Exception as exc:
            logger.warning("Pool query failed for %s: %s", pool_label, exc)
            return None

    def _fetch_pool_state_for_sync(
        self, contract: Any, pcfg: dict[str, Any], label: str,
    ) -> PoolState:
        slot0 = contract.functions.slot0().call()
        liquidity = contract.functions.liquidity().call()
        fee = contract.functions.fee().call()
        fg0 = contract.functions.feeGrowthGlobal0X128().call()
        fg1 = contract.functions.feeGrowthGlobal1X128().call()
        t0d = pcfg["token0_decimals"]
        t1d = pcfg["token1_decimals"]
        inv = pcfg.get("invert_price", True)
        eth_price = self._sqrt_price_to_eth_usd(slot0[0], t0d, t1d, inv)
        return PoolState(
            pool_address=pcfg["address"],
            chain=self.chain,
            token_pair=label,
            sqrt_price_x96=slot0[0],
            tick=slot0[1],
            liquidity=liquidity,
            fee_bps=fee,
            fee_growth_global_0=fg0,
            fee_growth_global_1=fg1,
            eth_price_usd=eth_price,
            token0_decimals=t0d,
            token1_decimals=t1d,
        )

    async def get_block_number(self) -> int:
        """Return the latest block number. Returns 0 if unavailable."""
        if not self.live or not self._w3:
            return 0
        try:
            return await asyncio.to_thread(
                self._call_with_retry,
                lambda: self._w3.eth.block_number,
                label="block_number",
            )
        except Exception:
            return 0

    async def get_gas_price_gwei(self) -> Decimal:
        """Return current gas price in gwei. Returns 0 if unavailable."""
        if not self.live or not self._w3:
            return Decimal("0")
        try:
            wei = await asyncio.to_thread(
                self._call_with_retry,
                lambda: self._w3.eth.gas_price,
                label="gas_price",
            )
            return (Decimal(wei) / Decimal(10**9)).quantize(Decimal("0.1"))
        except Exception:
            return Decimal("0")

    async def get_position(self, token_id: int) -> PositionState | None:
        """Read an LP position from the NonfungiblePositionManager."""
        if not self.live or not self._position_manager:
            return None
        try:
            return await asyncio.to_thread(
                self._call_with_retry,
                self._fetch_position_sync,
                token_id,
                label=f"position(#{token_id})",
            )
        except Exception as exc:
            logger.warning("Position query failed for #%d: %s", token_id, exc)
            return None

    def _fetch_position_sync(self, token_id: int) -> PositionState:
        pos = self._position_manager.functions.positions(token_id).call()
        current_tick = self._pool_contract.functions.slot0().call()[1]
        tick_lower = pos[5]
        tick_upper = pos[6]
        return PositionState(
            token_id=token_id,
            token0=pos[2],
            token1=pos[3],
            fee=pos[4],
            tick_lower=tick_lower,
            tick_upper=tick_upper,
            liquidity=pos[7],
            tokens_owed_0=pos[10],
            tokens_owed_1=pos[11],
            in_range=tick_lower <= current_tick <= tick_upper,
        )

    @staticmethod
    def tick_to_price(tick: int) -> Decimal:
        """Convert a Uniswap V3 tick to a price ratio."""
        return Decimal(str(1.0001 ** tick))

    @staticmethod
    def fee_growth_to_usd(
        fg_delta: int, liquidity: int, eth_price_usd: Decimal
    ) -> Decimal:
        """Convert a feeGrowthGlobal delta to approximate USD value."""
        if liquidity <= 0:
            return Decimal("0")
        raw_fees = Decimal(fg_delta) * Decimal(liquidity) / Q128
        fee_eth = raw_fees / Decimal(10**18)
        return (fee_eth * eth_price_usd).quantize(Decimal("0.0001"))
