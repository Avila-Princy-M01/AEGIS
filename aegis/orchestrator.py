"""AEGIS Orchestrator — spawns and coordinates all four agents.

Takes a single natural-language command, parses it into config,
then spawns Guard, Grow, Rebalance, and Legacy agents with shared memory.
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
from aegis.agents.rebalance import RebalanceAgent
from aegis.config import AegisConfig
from aegis.memory import EventType, SharedMemory
from aegis.nlp_parser import parse_command
from aegis.uniswap import UniswapV3Client

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
        self.uniswap: UniswapV3Client | None = None
        self._tasks: list[asyncio.Task[None]] = []
        self._started = False
        self._price_history: list[dict[str, Any]] = []
        self._block_number: int = 0
        self._gas_price_gwei: str = "0"
        self._eth_price: str = "0"

    @property
    def status(self) -> dict[str, Any]:
        live = self.uniswap.live if self.uniswap else False
        return {
            "started": self._started,
            "live_data": live,
            "chain": self.uniswap.chain if self.uniswap else "",
            "pool_address": self.uniswap.pool_address if self.uniswap else "",
            "token_pair": self.uniswap.token_pair if self.uniswap else "",
            "block_number": self._block_number,
            "gas_price_gwei": self._gas_price_gwei,
            "eth_price": self._eth_price,
            "agents": {
                "guard": self.guard.status if self.guard else None,
                "grow": self.grow.status if self.grow else None,
                "legacy": self.legacy.status if self.legacy else None,
                "rebalance": self.rebalance.status if self.rebalance else None,
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

        self.guard = GuardAgent(self.config.guard, self.memory, self.uniswap)
        self.grow = GrowAgent(self.config.grow, self.memory, self.uniswap)
        self.legacy = LegacyAgent(self.config.legacy, self.memory)
        self.rebalance = RebalanceAgent(self.config.rebalance, self.memory, self.uniswap)

        source = "🟢 LIVE on-chain" if self.uniswap.live else "🟡 Simulation mode"
        self.memory.publish(EventType.SYSTEM, "orchestrator", {
            "message": f"🚀 AEGIS deployed — 4 agents protecting your wallet — {source}",
            "command": command,
            "live_data": self.uniswap.live,
            "chain": chain,
        })

        self._tasks = [
            asyncio.create_task(self.guard.start()),
            asyncio.create_task(self.grow.start()),
            asyncio.create_task(self.legacy.start()),
            asyncio.create_task(self.rebalance.start()),
            asyncio.create_task(self._track_price_history()),
        ]
        self._started = True

        logger.info("All 4 AEGIS agents deployed (%s)", source)
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

    async def switch_chain(self, chain: str) -> dict[str, Any]:
        """Switch to a different chain and re-deploy all agents."""
        if not self._started or not self.config:
            return {"error": "Agents not deployed"}

        await self.stop()

        self.config.chain.chain = chain
        alchemy_key = self.config.chain.alchemy_api_key or os.environ.get("ALCHEMY_API_KEY", "")

        self.uniswap = UniswapV3Client(chain=chain, alchemy_key=alchemy_key)

        self.guard = GuardAgent(self.config.guard, self.memory, self.uniswap)
        self.grow = GrowAgent(self.config.grow, self.memory, self.uniswap)
        self.legacy = LegacyAgent(self.config.legacy, self.memory)
        self.rebalance = RebalanceAgent(self.config.rebalance, self.memory, self.uniswap)

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
                    gas = await self.uniswap.get_gas_price_gwei()
                    if gas > 0:
                        self._gas_price_gwei = str(gas)
                except Exception:
                    pass

            await asyncio.sleep(3)
