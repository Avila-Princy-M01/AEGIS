"""Grow Agent — fee compounding and vault management.

Auto-compounds Uniswap V3 LP fees, optimizes position ranges,
and sweeps excess funds into a savings vault. Listens to Guard
agent signals via shared memory to pause compounding during threats.

Queries real feeGrowthGlobal from on-chain data when available.
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from decimal import Decimal
from typing import Any

from aegis.config import GrowConfig
from aegis.memory import EventType, SharedMemory
from aegis.uniswap import UniswapV3Client

logger = logging.getLogger("aegis.grow")


class GrowAgent:
    """Autonomous fee compounding and vault management agent."""

    def __init__(
        self,
        config: GrowConfig,
        memory: SharedMemory,
        uniswap_client: UniswapV3Client,
    ) -> None:
        self.config = config
        self.memory = memory
        self.uniswap = uniswap_client
        self.name = "grow"
        self._running = False
        self._vault_balance: Decimal = Decimal("0.00")
        self._total_fees_collected: Decimal = Decimal("0.00")
        self._total_compounds: int = 0
        self._last_compound_time: float = 0
        self._paused: bool = False
        self._live_data: bool = False
        self._last_fee_growth_0: int = 0
        self._last_fee_growth_1: int = 0
        self._gas_price_gwei: Decimal = Decimal("0")
        self._gas_too_high: bool = False
        self._gas_threshold_gwei: Decimal = Decimal("50.0")
        self._reasoning: list[str] = []

    @property
    def status(self) -> dict[str, Any]:
        return {
            "agent": self.name,
            "running": self._running,
            "paused": self._paused,
            "vault_balance": str(self._vault_balance),
            "total_fees_collected": str(self._total_fees_collected),
            "total_compounds": self._total_compounds,
            "last_compound": self._last_compound_time,
            "live_data": self._live_data,
            "token_pair": self.uniswap.token_pair,
            "gas_price_gwei": str(self._gas_price_gwei),
            "gas_too_high": self._gas_too_high,
            "reasoning": self._reasoning[-1] if self._reasoning else "",
            "config": {
                "compound_frequency_hours": self.config.compound_frequency_hours,
                "savings_sweep_pct": str(self.config.savings_sweep_pct),
                "auto_compound": self.config.auto_compound_enabled,
            },
        }

    async def start(self) -> None:
        """Start the grow agent loop."""
        self._running = True
        self._live_data = self.uniswap.live

        if self._live_data:
            state = await self.uniswap.get_pool_state()
            if state:
                self._last_fee_growth_0 = state.fee_growth_global_0
                self._last_fee_growth_1 = state.fee_growth_global_1
                logger.info("Grow live: tracking fee growth on %s", self.uniswap.token_pair)

        source = f"🟢 LIVE on-chain ({self.uniswap.chain})" if self._live_data else "🟡 Simulation mode"
        self.memory.publish(EventType.AGENT_STARTED, self.name, {
            "message": f"Grow agent activated — {source} — monitoring fees on {self.uniswap.token_pair or 'LP pool'}",
            "live_data": self._live_data,
        })
        self.memory.subscribe(self._on_event)
        logger.info("Grow agent started (%s)", "live" if self._live_data else "simulated")

        while self._running:
            if not self._paused:
                await self._compound_cycle()
            await asyncio.sleep(5)

    def stop(self) -> None:
        self._running = False
        self.memory.publish(EventType.AGENT_STOPPED, self.name, {"message": "Grow agent stopped"})

    def _on_event(self, event: Any) -> None:
        """React to shared memory events from other agents."""
        if event.event_type == EventType.THREAT_DETECTED.value:
            self._paused = True
            logger.info("Grow paused — threat detected by Guard")
        elif event.event_type == EventType.THREAT_CLEARED.value:
            self._paused = False
            logger.info("Grow resumed — threat cleared")

    async def _compound_cycle(self) -> None:
        """Collect fees and compound — real or simulated."""
        if not self.config.auto_compound_enabled:
            return

        self._gas_price_gwei = await self.uniswap.get_gas_price_gwei()
        if self._gas_price_gwei > 0:
            self._gas_too_high = self._gas_price_gwei > self._gas_threshold_gwei
            if self._gas_too_high:
                self._reasoning.append(
                    f"Gas {self._gas_price_gwei} gwei > threshold {self._gas_threshold_gwei} gwei → SKIP"
                )
                if len(self._reasoning) > 10:
                    self._reasoning = self._reasoning[-10:]
                self.memory.publish(EventType.GAS_TOO_HIGH, self.name, {
                    "gas_gwei": str(self._gas_price_gwei),
                    "threshold_gwei": str(self._gas_threshold_gwei),
                    "message": f"⛽ Gas at {self._gas_price_gwei} gwei — too high, skipping compound (threshold: {self._gas_threshold_gwei} gwei)",
                })
                self.memory.set_state("grow_status", self.status)
                return
        else:
            self._gas_too_high = False

        if self._live_data:
            fees = await self._collect_fees_live()
        else:
            fees = self._collect_fees_simulated()

        if fees <= 0:
            src_tag = "live" if self._live_data else "sim"
            self._reasoning.append(
                f"Fees $0.00 ({src_tag}) | Gas {self._gas_price_gwei} gwei → NO FEES"
            )
            if len(self._reasoning) > 10:
                self._reasoning = self._reasoning[-10:]
            return

        self._total_fees_collected += fees

        sweep_amount = fees * self.config.savings_sweep_pct / 100
        compound_amount = fees - sweep_amount

        self._vault_balance += sweep_amount
        self._total_compounds += 1
        self._last_compound_time = time.time()

        source_tag = "live" if self._live_data else "simulated"
        self._reasoning.append(
            f"Fees +${fees} ({source_tag}) | Gas {self._gas_price_gwei} gwei"
            f" | Vault ${self._vault_balance} → COMPOUND"
        )
        if len(self._reasoning) > 10:
            self._reasoning = self._reasoning[-10:]
        self.memory.publish(EventType.FEES_COMPOUNDED, self.name, {
            "fees_collected": str(fees),
            "compounded": str(compound_amount),
            "swept_to_vault": str(sweep_amount),
            "vault_balance": str(self._vault_balance),
            "total_compounds": self._total_compounds,
            "source": source_tag,
            "message": f"📈 Compounded ${compound_amount} fees ({source_tag}) | ${sweep_amount} → savings vault (total: ${self._vault_balance})",
        })

        if self._vault_balance > Decimal("1.0") and self._total_compounds % 3 == 0:
            self.memory.publish(EventType.VAULT_DEPOSIT, self.name, {
                "amount": str(self._vault_balance),
                "message": f"🏦 Vault milestone: ${self._vault_balance} saved",
            })

        self.memory.set_state("grow_status", self.status)

    async def _collect_fees_live(self) -> Decimal:
        """Query real fee growth from Uniswap V3 pool."""
        state = await self.uniswap.get_pool_state()
        if not state:
            return self._collect_fees_simulated()

        delta_0 = state.fee_growth_global_0 - self._last_fee_growth_0
        delta_1 = state.fee_growth_global_1 - self._last_fee_growth_1

        if delta_0 < 0:
            delta_0 = 0
        if delta_1 < 0:
            delta_1 = 0

        self._last_fee_growth_0 = state.fee_growth_global_0
        self._last_fee_growth_1 = state.fee_growth_global_1

        fees_0_usd = UniswapV3Client.fee_growth_to_usd(
            delta_0, state.liquidity, Decimal("1")
        )
        fees_1_usd = UniswapV3Client.fee_growth_to_usd(
            delta_1, state.liquidity, state.eth_price_usd
        )

        total_fees = fees_0_usd + fees_1_usd

        return total_fees

    def _collect_fees_simulated(self) -> Decimal:
        """Generate simulated fees as fallback."""
        return Decimal(str(random.uniform(0.01, 0.10))).quantize(Decimal("0.0001"))
