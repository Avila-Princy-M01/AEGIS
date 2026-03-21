"""MEV Protection Agent — sandwich attack and front-running detection.

Monitors Uniswap V3 pools for signs of MEV exploitation:
- Sandwich attacks: rapid price swings (buy → victim swap → sell)
- Abnormal fee growth spikes indicating high MEV activity
- Large tick movements within short windows
- Price impact analysis for swap protection

Queries live pool data from Ethereum Mainnet or Base via web3.py.
Falls back to simulation mode if RPC is unavailable.
"""

from __future__ import annotations

import asyncio
import logging
import random
from decimal import Decimal
from typing import Any

from aegis.config import MevConfig
from aegis.memory import EventType, SharedMemory
from aegis.uniswap import PoolState, UniswapV3Client

if __import__("typing").TYPE_CHECKING:
    from aegis.uniswap_api import UniswapTradingAPI

logger = logging.getLogger("aegis.mev")

KNOWN_MEV_BOT_PREFIXES = [
    "0x0000",
    "0x0001",
    "0x8888",
    "0xdead",
]


class MevAgent:
    """Autonomous MEV protection agent for Uniswap V3 LP positions."""

    def __init__(
        self,
        config: MevConfig,
        memory: SharedMemory,
        uniswap_client: UniswapV3Client,
        uniswap_api: UniswapTradingAPI | None = None,
    ) -> None:
        self.config = config
        self.memory = memory
        self.uniswap = uniswap_client
        self.uniswap_api = uniswap_api
        self.name = "mev"
        self._running = False
        self._live_data: bool = False
        self._chain: str = ""
        self._token_pair: str = ""

        self._mev_level: str = "safe"  # safe | warning | critical
        self._sandwich_count: int = 0
        self._frontrun_count: int = 0
        self._total_mev_detected: int = 0
        self._estimated_mev_cost_usd: Decimal = Decimal("0.00")
        self._last_tick: int = 0
        self._tick_history: list[int] = []
        self._fee_growth_history: list[int] = []
        self._last_fee_growth_0: int = 0
        self._last_pool_state: PoolState | None = None
        self._reasoning: list[str] = []
        self._last_alert: str = ""
        self._paused: bool = False
        self._safe_route: dict[str, Any] = {}

    @property
    def status(self) -> dict[str, Any]:
        return {
            "agent": self.name,
            "running": self._running,
            "paused": self._paused,
            "mev_level": self._mev_level,
            "live_data": self._live_data,
            "chain": self._chain,
            "token_pair": self._token_pair,
            "sandwich_count": self._sandwich_count,
            "frontrun_count": self._frontrun_count,
            "total_mev_detected": self._total_mev_detected,
            "estimated_mev_cost_usd": str(self._estimated_mev_cost_usd),
            "last_alert": self._last_alert,
            "reasoning": self._reasoning[-1] if self._reasoning else "",
            "safe_route": self._safe_route,
            "config": {
                "sandwich_detection": self.config.sandwich_detection_enabled,
                "price_impact_threshold": str(self.config.price_impact_threshold_pct),
                "frontrun_window": self.config.frontrun_window_blocks,
            },
        }

    async def start(self) -> None:
        """Start the MEV protection monitoring loop."""
        self._running = True
        self._live_data = self.uniswap.live
        self._chain = self.uniswap.chain
        self._token_pair = self.uniswap.token_pair

        if self._live_data:
            state = await self.uniswap.get_pool_state()
            if state:
                self._last_tick = state.tick
                self._last_fee_growth_0 = state.fee_growth_global_0
                self._last_pool_state = state
                logger.info(
                    "MEV live: monitoring tick=%d on %s",
                    state.tick, self._chain,
                )

        if not self._live_data or self._last_tick == 0:
            self._last_tick = 199500

        source = f"🟢 LIVE on-chain ({self._chain})" if self._live_data else "🟡 Simulation mode"
        self.memory.publish(EventType.AGENT_STARTED, self.name, {
            "message": f"MEV Protection agent activated — {source} — scanning for sandwich attacks on {self._token_pair or 'LP pools'}",
            "live_data": self._live_data,
            "chain": self._chain,
        })
        self.memory.subscribe(self._on_event)
        logger.info("MEV agent started (%s)", "live" if self._live_data else "simulated")

        while self._running:
            if not self._paused:
                await self._monitor_cycle()
            await asyncio.sleep(4)

    def stop(self) -> None:
        self._running = False
        self.memory.publish(EventType.AGENT_STOPPED, self.name, {"message": "MEV Protection agent stopped"})

    def _on_event(self, event: Any) -> None:
        """React to shared memory events."""
        if event.event_type == EventType.THREAT_DETECTED.value:
            threat_type = event.data.get("type", "")
            if threat_type == "price_drop":
                self._mev_level = "warning"
                self._reasoning.append(
                    "Price drop detected by Guard → increasing MEV vigilance"
                )
                if len(self._reasoning) > 10:
                    self._reasoning = self._reasoning[-10:]
        elif event.event_type == EventType.THREAT_CLEARED.value:
            if self._mev_level == "warning":
                self._mev_level = "safe"

    async def simulate_mev_attack(self, attack_type: str = "sandwich") -> dict[str, Any]:
        """Simulate a MEV attack for demo purposes."""
        if attack_type == "sandwich":
            self._sandwich_count += 1
            self._total_mev_detected += 1
            cost = Decimal(str(random.uniform(5, 50))).quantize(Decimal("0.01"))
            self._estimated_mev_cost_usd += cost
            self._mev_level = "critical"
            self._last_alert = f"🥪 Sandwich attack: ~${cost} extracted"

            event_data = {
                "type": "sandwich",
                "estimated_cost_usd": str(cost),
                "attacker_pattern": "0x" + "a" * 8 + "..." + "f" * 4,
                "message": f"🚨 SANDWICH ATTACK DETECTED — estimated ${cost} extracted from pool swaps — MEV bot pattern identified",
            }
            self.memory.publish(EventType.MEV_DETECTED, self.name, event_data)

            safe_route = await self._fetch_safe_route()

            await asyncio.sleep(1)
            dry_run_data: dict[str, Any] = {
                "tx_type": "flashbots_protect",
                "action": "Route swap through Uniswap Trading API for MEV protection",
                "to": "0x00000000000000000000FlashbotsProtect",
                "data": "0xsubmit_private_tx(...)",
                "estimated_gas": "150000",
                "message": "🔐 DRY-RUN: Would route next swap via Uniswap Trading API + Flashbots Protect to avoid sandwich",
            }
            if safe_route:
                dry_run_data["safe_route"] = safe_route
            self.memory.publish(EventType.DRY_RUN_TX, self.name, dry_run_data)

            return event_data

        elif attack_type == "frontrun":
            self._frontrun_count += 1
            self._total_mev_detected += 1
            cost = Decimal(str(random.uniform(2, 20))).quantize(Decimal("0.01"))
            self._estimated_mev_cost_usd += cost
            self._mev_level = "warning"
            self._last_alert = f"⚡ Front-run detected: ~${cost} impact"

            event_data = {
                "type": "frontrun",
                "estimated_cost_usd": str(cost),
                "message": f"⚠️ FRONT-RUN DETECTED — large swap observed before your pending tx — ~${cost} price impact",
            }
            self.memory.publish(EventType.MEV_DETECTED, self.name, event_data)
            return event_data

        return {}

    async def _monitor_cycle(self) -> None:
        """Single monitoring cycle."""
        if self._live_data:
            await self._monitor_live()
        else:
            await self._monitor_simulated()

        self.memory.set_state("mev_status", self.status)

    async def _monitor_live(self) -> None:
        """Monitor using real on-chain pool data for MEV patterns."""
        state = await self.uniswap.get_pool_state()
        if not state:
            await self._monitor_simulated()
            return

        old_tick = self._last_tick
        self._last_tick = state.tick
        self._last_pool_state = state

        self._tick_history.append(state.tick)
        if len(self._tick_history) > 20:
            self._tick_history = self._tick_history[-20:]

        fg_delta = state.fee_growth_global_0 - self._last_fee_growth_0
        self._last_fee_growth_0 = state.fee_growth_global_0
        self._fee_growth_history.append(fg_delta)
        if len(self._fee_growth_history) > 20:
            self._fee_growth_history = self._fee_growth_history[-20:]

        tick_delta = abs(state.tick - old_tick)
        sandwich_detected = False
        frontrun_detected = False

        if len(self._tick_history) >= 3:
            recent = self._tick_history[-3:]
            swing_1 = recent[1] - recent[0]
            swing_2 = recent[2] - recent[1]
            if abs(swing_1) > 50 and abs(swing_2) > 50 and (swing_1 * swing_2 < 0):
                sandwich_detected = True

        if len(self._fee_growth_history) >= 3:
            recent_fees = self._fee_growth_history[-3:]
            avg_fee = sum(self._fee_growth_history[:-1]) / max(1, len(self._fee_growth_history) - 1)
            if avg_fee > 0 and recent_fees[-1] > avg_fee * 5:
                frontrun_detected = True

        if sandwich_detected and self.config.sandwich_detection_enabled:
            self._sandwich_count += 1
            self._total_mev_detected += 1
            cost = Decimal(str(abs(tick_delta) * 0.1)).quantize(Decimal("0.01"))
            self._estimated_mev_cost_usd += cost
            self._mev_level = "critical"
            self._last_alert = f"🥪 Sandwich: tick swing {tick_delta} (~${cost})"
            self.memory.publish(EventType.MEV_DETECTED, self.name, {
                "type": "sandwich",
                "tick_delta": tick_delta,
                "estimated_cost_usd": str(cost),
                "source": "on-chain",
                "message": f"🚨 LIVE: Sandwich pattern detected — tick swing ±{tick_delta} — ~${cost} estimated extraction",
            })
        elif frontrun_detected:
            self._frontrun_count += 1
            self._total_mev_detected += 1
            self._mev_level = "warning"
            self._last_alert = "⚡ Abnormal fee spike — possible front-run"
            self.memory.publish(EventType.MEV_DETECTED, self.name, {
                "type": "frontrun",
                "source": "on-chain",
                "message": "⚠️ LIVE: Abnormal fee growth spike detected — possible front-running activity",
            })
        elif self._mev_level != "safe" and tick_delta < 10:
            self._mev_level = "safe"
            self.memory.publish(EventType.MEV_CLEARED, self.name, {
                "message": "✅ MEV threat cleared — pool activity normalized",
            })

        src = "live"
        verdict = self._mev_level.upper()
        self._reasoning.append(
            f"Tick Δ{tick_delta} ({src})"
            f" | Sandwiches {self._sandwich_count}"
            f" | Front-runs {self._frontrun_count}"
            f" | MEV cost ${self._estimated_mev_cost_usd}"
            f" → {verdict}"
        )
        if len(self._reasoning) > 10:
            self._reasoning = self._reasoning[-10:]

    async def _fetch_safe_route(self) -> dict[str, Any]:
        """Fetch a safe swap route from the Uniswap Trading API."""
        if not self.uniswap_api or not self.uniswap_api.available:
            return {}
        try:
            from aegis.uniswap_api import CHAIN_IDS
            chain_id = CHAIN_IDS.get(self.uniswap.chain, 1)
            quote = await self.uniswap_api.get_eth_to_usdc_quote(
                amount_wei="1000000000000000000",
                chain_id=chain_id,
            )
            if "error" not in quote:
                self._safe_route = quote
                return quote
        except Exception as exc:
            logger.debug("Safe route fetch failed: %s", exc)
        return {}

    async def _monitor_simulated(self) -> None:
        """Simulated MEV monitoring for demo/fallback."""
        old_tick = self._last_tick
        drift = random.randint(-20, 20)
        self._last_tick += drift

        self._tick_history.append(self._last_tick)
        if len(self._tick_history) > 20:
            self._tick_history = self._tick_history[-20:]

        tick_delta = abs(drift)

        if random.random() < 0.03 and self.config.sandwich_detection_enabled:
            self._sandwich_count += 1
            self._total_mev_detected += 1
            cost = Decimal(str(random.uniform(1, 15))).quantize(Decimal("0.01"))
            self._estimated_mev_cost_usd += cost
            self._mev_level = "critical"
            self._last_alert = f"🥪 Sandwich detected (~${cost})"
            self.memory.publish(EventType.MEV_DETECTED, self.name, {
                "type": "sandwich",
                "estimated_cost_usd": str(cost),
                "source": "simulated",
                "message": f"🚨 Sandwich attack pattern detected — ~${cost} estimated extraction",
            })
        elif random.random() < 0.02:
            self._frontrun_count += 1
            self._total_mev_detected += 1
            self._mev_level = "warning"
            self._last_alert = "⚡ Possible front-run activity"
            self.memory.publish(EventType.MEV_DETECTED, self.name, {
                "type": "frontrun",
                "source": "simulated",
                "message": "⚠️ Potential front-running activity detected on monitored pool",
            })
        elif self._mev_level != "safe" and random.random() < 0.2:
            self._mev_level = "safe"
            self.memory.publish(EventType.MEV_CLEARED, self.name, {
                "message": "✅ MEV threat cleared — pool activity normalized",
            })

        src = "sim"
        verdict = self._mev_level.upper()
        self._reasoning.append(
            f"Tick Δ{tick_delta} ({src})"
            f" | Sandwiches {self._sandwich_count}"
            f" | Front-runs {self._frontrun_count}"
            f" | MEV cost ${self._estimated_mev_cost_usd}"
            f" → {verdict}"
        )
        if len(self._reasoning) > 10:
            self._reasoning = self._reasoning[-10:]
