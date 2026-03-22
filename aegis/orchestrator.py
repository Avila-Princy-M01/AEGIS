"""AEGIS Orchestrator — spawns and coordinates all five agents.

Takes a single natural-language command, parses it into config,
then spawns Guard, Grow, Rebalance, Legacy, and MEV agents with shared memory.
Creates a UniswapV3Client for real on-chain data.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any

from aegis.agents.grow import GrowAgent
from aegis.agents.guard import GuardAgent
from aegis.agents.legacy import LegacyAgent
from aegis.agents.mev import MevAgent
from aegis.agents.rebalance import RebalanceAgent
from aegis.analytics import Backtester, CrossPoolAllocator, LidoYieldComparator
from aegis.config import AegisConfig
from aegis.memory import EventType, SharedMemory
from aegis.nlp_parser import parse_command
from aegis.uniswap import UniswapV3Client
from aegis.uniswap_api import CHAIN_IDS, TOKENS, UniswapTradingAPI
from aegis.wallet import AegisWallet

logger = logging.getLogger("aegis")


class AegisOrchestrator:
    """Top-level orchestrator for the AEGIS multi-agent system."""

    def __init__(self, workspace_dir: str = "./workspace") -> None:
        self.memory = SharedMemory(workspace_dir)
        self.config: AegisConfig | None = None
        self.guard: GuardAgent | None = None
        self.grow: GrowAgent | None = None
        self.legacy: LegacyAgent | None = None
        self.rebalance: RebalanceAgent | None = None
        self.mev: MevAgent | None = None
        self.uniswap: UniswapV3Client | None = None
        self._lido_comparator: LidoYieldComparator | None = None
        self._pool_allocator: CrossPoolAllocator | None = None
        self._backtester: Backtester | None = None
        self._uniswap_api: UniswapTradingAPI | None = None
        self._wallet: AegisWallet | None = None
        self._agent_log: list[dict[str, Any]] = []
        self._tasks: list[asyncio.Task[None]] = []
        self._started = False
        self._price_history: list[dict[str, Any]] = []
        self._block_number: int = 0
        self._gas_price_gwei: str = "0"
        self._eth_price: str = "0"
        self._rpc_status: str = "disconnected"
        self._rpc_failures: int = 0

    @property
    def status(self) -> dict[str, Any]:
        live = self.uniswap.live if self.uniswap else False
        rpc_provider = ""
        if self.uniswap and hasattr(self.uniswap, '_rpc_urls') and self.uniswap._rpc_urls:
            url = self.uniswap._rpc_urls[self.uniswap._rpc_index]
            rpc_provider = url.split("//")[-1].split("/")[0]
        return {
            "started": self._started,
            "live_data": live,
            "chain": self.uniswap.chain if self.uniswap else "",
            "pool_address": self.uniswap.pool_address if self.uniswap else "",
            "token_pair": self.uniswap.token_pair if self.uniswap else "",
            "block_number": self._block_number,
            "gas_price_gwei": self._gas_price_gwei,
            "eth_price": self._eth_price,
            "rpc_status": self._rpc_status,
            "rpc_provider": rpc_provider,
            "agents": {
                "guard": self.guard.status if self.guard else None,
                "grow": self.grow.status if self.grow else None,
                "legacy": self.legacy.status if self.legacy else None,
                "rebalance": self.rebalance.status if self.rebalance else None,
                "mev": self.mev.status if self.mev else None,
            },
            "memory_events": len(self.memory.get_events(limit=999)),
            "available_pools": self.uniswap.available_pools if self.uniswap else [],
            "config": {
                "guard": {
                    "il_threshold": str(self.config.guard.impermanent_loss_threshold_pct),
                    "price_drop_alert": str(self.config.guard.price_drop_alert_pct),
                    "auto_exit": self.config.guard.auto_exit_on_threat,
                } if self.config else None,
                "grow": {
                    "compound_freq_hours": self.config.grow.compound_frequency_hours,
                    "savings_pct": str(self.config.grow.savings_sweep_pct),
                } if self.config else None,
                "legacy": {
                    "inactivity_days": self.config.legacy.inactivity_threshold_days,
                    "beneficiaries": len(self.config.legacy.beneficiaries),
                } if self.config else None,
                "rebalance": {
                    "range_width": self.config.rebalance.range_width_ticks,
                    "auto_rebalance": self.config.rebalance.auto_rebalance,
                } if self.config else None,
            },
        }

    async def deploy(self, command: str, api_key: str = "") -> dict[str, Any]:
        """Parse a command and deploy all four agents."""
        logger.info("Parsing command: %s", command)
        self.config = await parse_command(command, api_key=api_key)

        chain = self.config.chain.chain or os.environ.get("AEGIS_CHAIN", "ethereum")
        alchemy_key = self.config.chain.alchemy_api_key or os.environ.get("ALCHEMY_API_KEY", "")

        self.uniswap = UniswapV3Client(chain=chain, alchemy_key=alchemy_key)
        await self._seed_initial_price()

        uniswap_api_key = os.environ.get("UNISWAP_API_KEY", "")
        self._uniswap_api = UniswapTradingAPI(api_key=uniswap_api_key) if uniswap_api_key else None

        self._wallet = AegisWallet()

        self.guard = GuardAgent(self.config.guard, self.memory, self.uniswap)
        self.grow = GrowAgent(self.config.grow, self.memory, self.uniswap, uniswap_api=self._uniswap_api, wallet=self._wallet)
        self.legacy = LegacyAgent(self.config.legacy, self.memory)
        self.rebalance = RebalanceAgent(self.config.rebalance, self.memory, self.uniswap)
        self.mev = MevAgent(self.config.mev, self.memory, self.uniswap, uniswap_api=self._uniswap_api)

        self._lido_comparator = LidoYieldComparator(self.memory, self.uniswap)
        self._pool_allocator = CrossPoolAllocator(self.memory, self.uniswap)
        self._backtester = Backtester(self.memory)

        self._log_agent_action("orchestrator", "deploy", {
            "command": command, "chain": chain, "live": self.uniswap.live,
            "wallet": self._wallet.address if self._wallet and self._wallet.available else "none",
        })

        source = "🟢 LIVE on-chain" if self.uniswap.live else "🟡 Simulation mode"
        self.memory.publish(EventType.SYSTEM, "orchestrator", {
            "message": f"🚀 AEGIS deployed — 5 agents protecting your wallet — {source}",
            "command": command,
            "live_data": self.uniswap.live,
            "chain": chain,
        })

        self._tasks = [
            asyncio.create_task(self.guard.start()),
            asyncio.create_task(self.grow.start()),
            asyncio.create_task(self.legacy.start()),
            asyncio.create_task(self.rebalance.start()),
            asyncio.create_task(self.mev.start()),
            asyncio.create_task(self._track_price_history()),
        ]
        self._started = True

        logger.info("All 5 AEGIS agents deployed (%s)", source)
        return self.status

    async def stop(self) -> None:
        """Stop all agents gracefully."""
        if self.guard:
            self.guard.stop()
        if self.grow:
            self.grow.stop()
        if self.legacy:
            self.legacy.stop()
        if self.rebalance:
            self.rebalance.stop()
        if self.mev:
            self.mev.stop()

        for task in self._tasks:
            task.cancel()
        self._tasks.clear()
        self._started = False

    async def simulate_threat(self, threat_type: str = "price_drop") -> dict[str, Any]:
        """Trigger a simulated threat for demo."""
        if not self.guard:
            return {"error": "Guard agent not deployed"}
        return await self.guard.simulate_threat(threat_type)

    async def simulate_inheritance(self) -> dict[str, Any]:
        """Trigger simulated inheritance for demo."""
        if not self.legacy:
            return {"error": "Legacy agent not deployed"}
        return await self.legacy.simulate_inheritance()

    def check_in(self) -> dict[str, Any]:
        """Record a user check-in with the Legacy agent."""
        if not self.legacy:
            return {"error": "Legacy agent not deployed"}
        return self.legacy.check_in()

    async def simulate_out_of_range(self) -> dict[str, Any]:
        """Trigger simulated out-of-range for demo."""
        if not self.rebalance:
            return {"error": "Rebalance agent not deployed"}
        return await self.rebalance.simulate_out_of_range()

    async def simulate_mev_attack(self, attack_type: str = "sandwich") -> dict[str, Any]:
        """Trigger a simulated MEV attack for demo."""
        if not self.mev:
            return {"error": "MEV agent not deployed"}
        return await self.mev.simulate_mev_attack(attack_type)

    async def compare_lido_yield(self) -> dict[str, Any]:
        """Compare LP yield vs Lido staking yield."""
        if not self._lido_comparator:
            return {"error": "Analytics not initialized"}
        return await self._lido_comparator.compare()

    async def allocate_cross_pool(self) -> dict[str, Any]:
        """Get optimal cross-pool capital allocation."""
        if not self._pool_allocator:
            return {"error": "Analytics not initialized"}
        return await self._pool_allocator.allocate()

    async def run_backtest(self, days: int = 30) -> dict[str, Any]:
        """Run a historical backtest simulation."""
        if not self._backtester:
            return {"error": "Analytics not initialized"}
        return await self._backtester.run(days)

    async def get_swap_quote(
        self,
        token_in: str = "WETH",
        token_out: str = "USDC",
        amount: str = "1000000000000000000",
        chain: str = "",
    ) -> dict[str, Any]:
        """Get a real swap quote from the Uniswap Trading API."""
        if not self._uniswap_api or not self._uniswap_api.available:
            return {"error": "Uniswap Trading API not configured"}
        active_chain = chain or (self.uniswap.chain if self.uniswap else "ethereum")
        chain_id = CHAIN_IDS.get(active_chain, 1)
        from aegis.uniswap_api import TOKENS
        tokens = TOKENS.get(chain_id, TOKENS[1])
        token_in_addr = tokens.get(token_in, token_in)
        token_out_addr = tokens.get(token_out, token_out)
        return await self._uniswap_api.get_quote(
            token_in=token_in_addr,
            token_out=token_out_addr,
            amount=amount,
            chain_id=chain_id,
        )

    async def switch_chain(self, chain: str) -> dict[str, Any]:
        """Switch to a different chain and re-deploy all agents."""
        if not self._started or not self.config:
            return {"error": "Agents not deployed"}

        await self.stop()

        self._price_history = []
        self._eth_price = "0"
        self._block_number = 0
        self._gas_price_gwei = "0"

        self.config.chain.chain = chain
        alchemy_key = self.config.chain.alchemy_api_key or os.environ.get("ALCHEMY_API_KEY", "")

        self.uniswap = UniswapV3Client(chain=chain, alchemy_key=alchemy_key)
        await self._seed_initial_price()

        uniswap_api_key = os.environ.get("UNISWAP_API_KEY", "")
        self._uniswap_api = UniswapTradingAPI(api_key=uniswap_api_key) if uniswap_api_key else None

        self.guard = GuardAgent(self.config.guard, self.memory, self.uniswap)
        self.grow = GrowAgent(self.config.grow, self.memory, self.uniswap, uniswap_api=self._uniswap_api, wallet=self._wallet)
        self.legacy = LegacyAgent(self.config.legacy, self.memory)
        self.rebalance = RebalanceAgent(self.config.rebalance, self.memory, self.uniswap)
        self.mev = MevAgent(self.config.mev, self.memory, self.uniswap, uniswap_api=self._uniswap_api)

        self._lido_comparator = LidoYieldComparator(self.memory, self.uniswap)
        self._pool_allocator = CrossPoolAllocator(self.memory, self.uniswap)
        self._backtester = Backtester(self.memory)

        source = "🟢 LIVE on-chain" if self.uniswap.live else "🟡 Simulation mode"
        self.memory.publish(EventType.SYSTEM, "orchestrator", {
            "message": f"🔄 Switched to {chain.upper()} — {source}",
            "chain": chain,
            "live_data": self.uniswap.live,
        })

        self._tasks = [
            asyncio.create_task(self.guard.start()),
            asyncio.create_task(self.grow.start()),
            asyncio.create_task(self.legacy.start()),
            asyncio.create_task(self.rebalance.start()),
            asyncio.create_task(self.mev.start()),
            asyncio.create_task(self._track_price_history()),
        ]
        self._started = True

        logger.info("Switched to %s (%s)", chain, source)
        return self.status

    def set_demo_speed(self, multiplier: float) -> None:
        """Speed up Legacy timer for demo."""
        if self.legacy:
            self.legacy.set_demo_speed(multiplier)

    def get_price_history(self) -> list[dict[str, Any]]:
        """Return recent price history for chart rendering."""
        return self._price_history[-100:]

    async def execute_swap(
        self,
        token_in: str = "WETH",
        token_out: str = "USDC",
        amount: str = "100000000000000000",
    ) -> dict[str, Any]:
        """Execute a real swap on Sepolia testnet via Uniswap Trading API."""
        if not self._uniswap_api or not self._uniswap_api.available:
            return {"error": "Uniswap Trading API not configured"}
        if not self._wallet or not self._wallet.available:
            return {"error": "Wallet not available (set WALLET_PRIVATE_KEY)"}

        sepolia_id = CHAIN_IDS.get("sepolia", 11155111)
        tokens = TOKENS.get(sepolia_id, {})
        token_in_addr = tokens.get(token_in, token_in)
        token_out_addr = tokens.get(token_out, token_out)

        swap_result = await self._uniswap_api.execute_swap(
            token_in=token_in_addr,
            token_out=token_out_addr,
            amount=amount,
            wallet_address=self._wallet.address,
            chain_id=sepolia_id,
        )
        if "error" in swap_result:
            self._log_agent_action("orchestrator", "swap_failed", swap_result)
            return swap_result

        swap_tx = swap_result.get("swap", swap_result)
        tx_data = {
            "to": swap_tx.get("to", ""),
            "data": swap_tx.get("data", swap_tx.get("calldata", "0x")),
            "value": swap_tx.get("value", "0"),
            "chainId": sepolia_id,
            "gas": swap_tx.get("gasLimit", swap_tx.get("gas", 300000)),
        }

        if not tx_data["to"]:
            self._log_agent_action("orchestrator", "swap_no_target", swap_result)
            return {"error": "No target address in swap response", "raw": swap_result}

        broadcast = await self._wallet.sign_and_send(tx_data)
        if "error" in broadcast:
            self._log_agent_action("orchestrator", "swap_broadcast_failed", broadcast)
            return broadcast

        self.memory.publish(EventType.SYSTEM, "orchestrator", {
            "message": f"🦄 Swap executed on Sepolia: {broadcast.get('explorer_url', '')}",
            "tx_hash": broadcast.get("tx_hash", ""),
        })

        self._log_agent_action("orchestrator", "swap_executed", {
            "tx_hash": broadcast.get("tx_hash", ""),
            "explorer_url": broadcast.get("explorer_url", ""),
            "token_in": token_in,
            "token_out": token_out,
            "amount": amount,
        })

        result = {**broadcast, "quote": swap_result.get("quote", {})}
        return result

    def _log_agent_action(
        self, agent: str, action: str, data: dict[str, Any],
    ) -> None:
        """Append an entry to the structured agent execution log."""
        entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "agent": agent,
            "action": action,
            "data": data,
        }
        self._agent_log.append(entry)
        self._save_agent_log()

    def _save_agent_log(self) -> None:
        """Persist agent_log.json to disk."""
        import json
        from pathlib import Path
        log_path = Path("agent_log.json")
        try:
            log_path.write_text(
                json.dumps(self._agent_log[-500:], indent=2, default=str),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.debug("Failed to save agent_log.json: %s", exc)

    async def _seed_initial_price(self) -> None:
        """Fetch ETH price immediately so the chart renders without waiting for Guard."""
        if not self.uniswap or not self.uniswap.live:
            return
        try:
            state = await self.uniswap.get_pool_state()
            if state and state.eth_price_usd > 0:
                price_str = str(state.eth_price_usd)
                self._eth_price = price_str
                now = time.time()
                self._price_history = [
                    {"price": price_str, "timestamp": now - 3},
                    {"price": price_str, "timestamp": now},
                ]
                block = await self.uniswap.get_block_number()
                if block > 0:
                    self._block_number = block
                    self._rpc_status = "connected"
                gas = await self.uniswap.get_gas_price_gwei()
                if gas > 0:
                    self._gas_price_gwei = str(gas)
        except Exception as exc:
            logger.debug("Initial price seed failed: %s", exc)

    async def _track_price_history(self) -> None:
        """Background task to record price snapshots and chain stats."""
        while self._started:
            if self.guard and self.guard._last_price > 0:
                self._eth_price = str(self.guard._last_price)
                self._price_history.append({
                    "price": self._eth_price,
                    "timestamp": time.time(),
                })
                if len(self._price_history) > 200:
                    self._price_history = self._price_history[-200:]

            if self.uniswap and self.uniswap.live:
                try:
                    block = await self.uniswap.get_block_number()
                    if block > 0:
                        self._block_number = block
                        self._rpc_failures = 0
                        self._rpc_status = "connected"
                    gas = await self.uniswap.get_gas_price_gwei()
                    if gas > 0:
                        self._gas_price_gwei = str(gas)
                except Exception:
                    self._rpc_failures += 1
                    if self._rpc_failures >= 3:
                        self._rpc_status = "error"
                    else:
                        self._rpc_status = "reconnecting"

            await asyncio.sleep(3)
