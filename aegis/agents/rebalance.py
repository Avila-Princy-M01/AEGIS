"""Rebalance Agent — position range monitoring and rebalancing.

Monitors Uniswap V3 LP positions to detect when the current price
moves outside the concentrated liquidity range (tickLower–tickUpper).
Suggests optimal new ranges and coordinates with Guard agent.

The #1 pain point for Uniswap V3 LPs — positions going out of range
and earning zero fees.
"""

from __future__ import annotations

import asyncio
import logging
import random
from decimal import Decimal
from typing import Any

from aegis.config import RebalanceConfig
from aegis.memory import EventType, SharedMemory
from aegis.uniswap import PoolState, UniswapV3Client

logger = logging.getLogger("aegis.rebalance")


class RebalanceAgent:
    """Monitors LP position ranges and suggests rebalancing when out of range."""

    def __init__(
        self,
        config: RebalanceConfig,
        memory: SharedMemory,
        uniswap_client: UniswapV3Client,
    ) -> None:
        self.config = config
        self.memory = memory
        self.uniswap = uniswap_client
        self.name = "rebalance"
        self._running = False
        self._live_data: bool = False
        self._chain: str = ""
        self._token_pair: str = ""

        self._current_tick: int = 0
        self._tick_lower: int = -887220
        self._tick_upper: int = 887220
        self._in_range: bool = True
        self._range_utilization_pct: Decimal = Decimal("50.0")
        self._suggested_lower: int = 0
        self._suggested_upper: int = 0
        self._rebalance_count: int = 0
        self._last_pool_state: PoolState | None = None
        self._paused: bool = False
        self._reasoning: list[str] = []

    @property
    def status(self) -> dict[str, Any]:
        return {
            "agent": self.name,
            "running": self._running,
            "paused": self._paused,
            "live_data": self._live_data,
            "chain": self._chain,
            "token_pair": self._token_pair,
            "current_tick": self._current_tick,
            "tick_lower": self._tick_lower,
            "tick_upper": self._tick_upper,
            "in_range": self._in_range,
            "range_utilization_pct": str(self._range_utilization_pct),
            "suggested_lower": self._suggested_lower,
            "suggested_upper": self._suggested_upper,
            "rebalance_count": self._rebalance_count,
            "reasoning": self._reasoning[-1] if self._reasoning else "",
            "config": {
                "range_width_ticks": self.config.range_width_ticks,
                "auto_rebalance": self.config.auto_rebalance,
                "threshold_pct": str(self.config.rebalance_threshold_pct),
            },
        }

    async def start(self) -> None:
        """Start the rebalance monitoring loop."""
        self._running = True
        self._live_data = self.uniswap.live
        self._chain = self.uniswap.chain
        self._token_pair = self.uniswap.token_pair

        if self._live_data:
            state = await self.uniswap.get_pool_state()
            if state:
                self._current_tick = state.tick
                half_width = self.config.range_width_ticks // 2
                self._tick_lower = state.tick - half_width
                self._tick_upper = state.tick + half_width
                self._last_pool_state = state
                logger.info(
                    "Rebalance live: tick=%d range=[%d, %d] on %s",
                    state.tick, self._tick_lower, self._tick_upper, self._chain,
                )

        if not self._live_data or self._current_tick == 0:
            self._current_tick = 199500
            half_width = self.config.range_width_ticks // 2
            self._tick_lower = self._current_tick - half_width
            self._tick_upper = self._current_tick + half_width

        source = f"🟢 LIVE on-chain ({self._chain})" if self._live_data else "🟡 Simulation mode"
        self.memory.publish(EventType.AGENT_STARTED, self.name, {
            "message": f"Rebalance agent activated — {source} — monitoring range [{self._tick_lower}, {self._tick_upper}]",
            "live_data": self._live_data,
            "chain": self._chain,
        })
        self.memory.subscribe(self._on_event)
        logger.info("Rebalance agent started (%s)", "live" if self._live_data else "simulated")

        while self._running:
            if not self._paused:
                await self._monitor_cycle()
            await asyncio.sleep(self.config.check_interval_seconds)

    def stop(self) -> None:
        self._running = False
        self.memory.publish(EventType.AGENT_STOPPED, self.name, {"message": "Rebalance agent stopped"})

    def _on_event(self, event: Any) -> None:
        """React to shared memory events from other agents."""
        if event.event_type == EventType.THREAT_DETECTED.value:
            self._paused = True
            logger.info("Rebalance paused — threat detected by Guard")
        elif event.event_type == EventType.THREAT_CLEARED.value:
            self._paused = False
            logger.info("Rebalance resumed — threat cleared")

    async def _monitor_cycle(self) -> None:
        """Single monitoring cycle."""
        if self._live_data:
            await self._monitor_live()
        else:
            await self._monitor_simulated()

        self.memory.set_state("rebalance_status", self.status)

    async def _monitor_live(self) -> None:
        """Monitor using real on-chain pool tick data."""
        state = await self.uniswap.get_pool_state()
        if not state:
            await self._monitor_simulated()
            return

        self._current_tick = state.tick
        self._last_pool_state = state
        self._evaluate_range()

    async def _monitor_simulated(self) -> None:
        """Simulated tick drift for demo."""
        drift = random.randint(-15, 15)
        self._current_tick += drift
        self._evaluate_range()

    def _evaluate_range(self) -> None:
        """Check if the current tick is within position range."""
        was_in_range = self._in_range
        self._in_range = self._tick_lower <= self._current_tick <= self._tick_upper

        tick_range = self._tick_upper - self._tick_lower
        if tick_range > 0:
            position_in_range = (self._current_tick - self._tick_lower) / tick_range
            self._range_utilization_pct = Decimal(str(
                max(0.0, min(100.0, position_in_range * 100))
            )).quantize(Decimal("0.1"))
        else:
            self._range_utilization_pct = Decimal("0")

        edge_pct = Decimal("100") - self.config.rebalance_threshold_pct
        near_lower_edge = self._range_utilization_pct < self.config.rebalance_threshold_pct
        near_upper_edge = self._range_utilization_pct > edge_pct

        src = "live" if self._live_data else "sim"
        verdict = "IN RANGE" if self._in_range else "OUT OF RANGE"
        if self._in_range and (near_lower_edge or near_upper_edge):
            verdict = "NEAR EDGE"
        self._reasoning.append(
            f"Tick {self._current_tick} ({src})"
            f" | Range [{self._tick_lower}–{self._tick_upper}]"
            f" | Util {self._range_utilization_pct}%"
            f" → {verdict}"
        )
        if len(self._reasoning) > 10:
            self._reasoning = self._reasoning[-10:]

        if not self._in_range and was_in_range:
            half_width = self.config.range_width_ticks // 2
            self._suggested_lower = self._current_tick - half_width
            self._suggested_upper = self._current_tick + half_width
            self._rebalance_count += 1

            source = "on-chain" if self._live_data else "simulated"
            self.memory.publish(EventType.POSITION_OUT_OF_RANGE, self.name, {
                "current_tick": self._current_tick,
                "tick_lower": self._tick_lower,
                "tick_upper": self._tick_upper,
                "source": source,
                "message": f"🔴 POSITION OUT OF RANGE ({source}) — tick {self._current_tick} outside [{self._tick_lower}, {self._tick_upper}] — earning ZERO fees!",
            })
            self.memory.publish(EventType.REBALANCE_SUGGESTED, self.name, {
                "suggested_lower": self._suggested_lower,
                "suggested_upper": self._suggested_upper,
                "current_tick": self._current_tick,
                "message": f"💡 Suggested new range: [{self._suggested_lower}, {self._suggested_upper}] centered on tick {self._current_tick}",
            })

        elif self._in_range and (near_lower_edge or near_upper_edge):
            edge = "lower" if near_lower_edge else "upper"
            self.memory.publish(EventType.REBALANCE_SUGGESTED, self.name, {
                "type": "approaching_edge",
                "edge": edge,
                "utilization_pct": str(self._range_utilization_pct),
                "message": f"⚠️ Position near {edge} edge ({self._range_utilization_pct}%) — consider rebalancing soon",
            })

    async def simulate_out_of_range(self) -> dict[str, Any]:
        """Force position out of range for demo."""
        direction = random.choice([-1, 1])
        tick_range = self._tick_upper - self._tick_lower
        self._current_tick = (
            self._tick_upper + tick_range // 4
            if direction > 0
            else self._tick_lower - tick_range // 4
        )
        self._evaluate_range()
        return self.status
