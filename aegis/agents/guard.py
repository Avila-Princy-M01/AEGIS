"""Guard Agent — threat detection and position protection.

Monitors Uniswap V3 LP positions for:
- Impermanent loss exceeding threshold (real on-chain IL calculation)
- Suspicious outflows or interactions with flagged contracts
- Sudden price drops (potential rug pull / MEV attack)

Queries live pool data from Ethereum Mainnet or Base via web3.py.
Falls back to simulation mode if RPC is unavailable.
"""

from __future__ import annotations

import asyncio
import logging
import random
from decimal import Decimal
from typing import Any

from aegis.config import GuardConfig
from aegis.memory import EventType, SharedMemory
from aegis.uniswap import PoolState, UniswapV3Client

logger = logging.getLogger("aegis.guard")


class GuardAgent:
    """Autonomous threat detection agent for Uniswap V3 LP positions."""

    def __init__(
        self,
        config: GuardConfig,
        memory: SharedMemory,
        uniswap_client: UniswapV3Client,
        uniswap_api: Any = None,
        wallet: Any = None,
    ) -> None:
        self.config = config
        self.memory = memory
        self.uniswap = uniswap_client
        self.uniswap_api = uniswap_api
        self.wallet = wallet
        self.name = "guard"
        self._running = False
        self._threat_level: str = "safe"  # safe | warning | critical
        self._last_price: Decimal = Decimal("0")
        self._entry_price: Decimal = Decimal("0")
        self._position_value: Decimal = Decimal("1000.00")
        self._il_pct: Decimal = Decimal("0.0")
        self._live_data: bool = False
        self._pool_address: str = ""
        self._chain: str = ""
        self._token_pair: str = ""
        self._last_pool_state: PoolState | None = None
        self._reasoning: list[str] = []
        self._fees_earned: Decimal = Decimal("0.00")
        self._il_loss_usd: Decimal = Decimal("0.00")
        self._gas_spent_usd: Decimal = Decimal("0.00")

    @property
    def status(self) -> dict[str, Any]:
        net = self._fees_earned - self._il_loss_usd - self._gas_spent_usd
        return {
            "agent": self.name,
            "running": self._running,
            "threat_level": self._threat_level,
            "last_price": str(self._last_price),
            "position_value": str(self._position_value),
            "impermanent_loss_pct": str(self._il_pct),
            "live_data": self._live_data,
            "pool_address": self._pool_address,
            "chain": self._chain,
            "token_pair": self._token_pair,
            "reasoning": self._reasoning[-1] if self._reasoning else "",
            "pnl": {
                "fees_earned": str(self._fees_earned),
                "il_loss": str(self._il_loss_usd),
                "gas_cost": str(self._gas_spent_usd),
                "net": str(net.quantize(Decimal("0.01"))),
            },
            "config": {
                "il_threshold": str(self.config.impermanent_loss_threshold_pct),
                "price_drop_alert": str(self.config.price_drop_alert_pct),
                "auto_exit": self.config.auto_exit_on_threat,
            },
        }

    async def start(self) -> None:
        """Start the guard monitoring loop."""
        self._running = True
        self._live_data = self.uniswap.live
        self._pool_address = self.uniswap.pool_address
        self._chain = self.uniswap.chain
        self._token_pair = self.uniswap.token_pair

        self.memory.subscribe(self._on_event)

        if self._live_data:
            state = await self.uniswap.get_pool_state()
            if state:
                self._last_price = state.eth_price_usd
                self._entry_price = state.eth_price_usd
                self._position_value = Decimal("1000.00")
                self._last_pool_state = state
                logger.info(
                    "Guard live: ETH = $%s from %s on %s",
                    self._last_price, self._token_pair, self._chain,
                )

        if not self._live_data or self._last_price == 0:
            self._last_price = Decimal("2500.00")
            self._entry_price = Decimal("2500.00")
            self._position_value = Decimal("1000.00")

        source = f"🟢 LIVE on-chain ({self._chain})" if self._live_data else "🟡 Simulation mode"
        self.memory.publish(EventType.AGENT_STARTED, self.name, {
            "message": f"Guard agent activated — {source} — monitoring {self._token_pair or 'LP positions'}",
            "live_data": self._live_data,
            "chain": self._chain,
            "pool": self._pool_address,
        })
        logger.info("Guard agent started (%s)", "live" if self._live_data else "simulated")

        while self._running:
            await self._monitor_cycle()
            await asyncio.sleep(3)

    def _on_event(self, event: Any) -> None:
        """React to shared memory events."""
        if event.event_type == EventType.POSITION_OUT_OF_RANGE.value:
            if self._threat_level != "critical":
                self._threat_level = "warning"
                self.memory.publish(EventType.THREAT_DETECTED, self.name, {
                    "type": "out_of_range",
                    "source": "rebalance_agent",
                    "message": "⚠️ Guard: Position out of range — increasing threat level",
                })
        elif event.event_type == EventType.MEV_DETECTED.value:
            mev_type = event.data.get("type", "unknown")
            if mev_type == "sandwich" and self._threat_level != "critical":
                self._threat_level = "warning"
                self.memory.publish(EventType.THREAT_DETECTED, self.name, {
                    "type": "mev_sandwich",
                    "source": "mev_agent",
                    "message": "⚠️ Guard: MEV sandwich attack detected — elevating threat level",
                })
        elif event.event_type == EventType.FEES_COMPOUNDED.value:
            fees_str = event.data.get("fees_collected", "0")
            try:
                self._fees_earned += Decimal(fees_str)
            except (ValueError, ArithmeticError):
                pass

    def stop(self) -> None:
        self._running = False
        self.memory.publish(EventType.AGENT_STOPPED, self.name, {"message": "Guard agent stopped"})

    async def simulate_threat(self, threat_type: str = "price_drop") -> dict[str, Any]:
        """Simulate a threat for demo purposes."""
        if threat_type == "price_drop":
            drop_pct = Decimal(str(random.uniform(15, 35)))
            old_price = self._last_price
            self._last_price = old_price * (1 - drop_pct / 100)
            self._threat_level = "critical"

            self._il_pct = UniswapV3Client.calculate_il(self._entry_price, self._last_price)

            event_data = {
                "type": "price_drop",
                "old_price": str(old_price),
                "new_price": str(self._last_price),
                "drop_pct": str(drop_pct.quantize(Decimal("0.1"))),
                "il_pct": str(self._il_pct),
                "action": "auto_exit" if self.config.auto_exit_on_threat else "alert_only",
                "message": f"🚨 CRITICAL: ETH dropped {drop_pct.quantize(Decimal('0.1'))}% to ${self._last_price} — IL at {self._il_pct}% — {'auto-exiting positions' if self.config.auto_exit_on_threat else 'alerting owner'}",
            }
            self.memory.publish(EventType.THREAT_DETECTED, self.name, event_data)

            if self.config.auto_exit_on_threat:
                await self._execute_protective_swap("simulated")
                await asyncio.sleep(1)
                self.memory.publish(EventType.POSITION_LOCKED, self.name, {
                    "message": "🔒 Positions locked — funds moved to Guard Vault",
                    "vault_balance": str(self._position_value),
                })
                self.memory.set_state("positions_locked", True)

            return event_data

        elif threat_type == "suspicious_activity":
            self._threat_level = "warning"
            event_data = {
                "type": "suspicious_activity",
                "message": "⚠️ Suspicious contract interaction detected on monitored pool",
                "contract": "0x" + "a" * 40,
                "action": "monitoring",
            }
            self.memory.publish(EventType.THREAT_DETECTED, self.name, event_data)
            return event_data

        return {}

    def _update_pnl(self) -> None:
        """Update P&L tracking from shared memory."""
        self._il_loss_usd = (
            self._il_pct * self._position_value / Decimal("100")
        ).quantize(Decimal("0.01"))
        grow_status = self.memory.get_state("grow_status")
        if isinstance(grow_status, dict):
            compounds = grow_status.get("total_compounds", 0)
            self._gas_spent_usd = (
                Decimal(str(compounds)) * Decimal("0.50")
            ).quantize(Decimal("0.01"))

    def _build_reasoning(self, price_change_pct: Decimal | None = None) -> None:
        """Build a structured reasoning string for this cycle."""
        delta_str = ""
        if price_change_pct is not None:
            sign = "+" if price_change_pct >= 0 else ""
            delta_str = f" | Δ {sign}{price_change_pct.quantize(Decimal('0.1'))}%"
        verdict = self._threat_level.upper()
        line = (
            f"ETH ${self._last_price}{delta_str}"
            f" | IL {self._il_pct}% (threshold {self.config.impermanent_loss_threshold_pct}%)"
            f" → {verdict}"
        )
        self._reasoning.append(line)
        if len(self._reasoning) > 10:
            self._reasoning = self._reasoning[-10:]

    async def _monitor_cycle(self) -> None:
        """Single monitoring cycle — query real pool data or simulate."""
        if self._live_data:
            await self._monitor_live()
        else:
            await self._monitor_simulated()

        self._update_pnl()
        self.memory.set_state("guard_status", self.status)

    async def _monitor_live(self) -> None:
        """Monitor using real on-chain Uniswap V3 data."""
        state = await self.uniswap.get_pool_state()
        if not state:
            logger.warning("Live query failed, falling back to simulation this cycle")
            await self._monitor_simulated()
            return

        old_price = self._last_price
        self._last_price = state.eth_price_usd
        self._last_pool_state = state

        self._il_pct = UniswapV3Client.calculate_il(self._entry_price, self._last_price)

        if old_price > 0:
            price_change_pct_abs = abs((self._last_price - old_price) / old_price * 100)
            if self._last_price < old_price and price_change_pct_abs > self.config.price_drop_alert_pct:
                self._threat_level = "critical"
                self.memory.publish(EventType.THREAT_DETECTED, self.name, {
                    "type": "price_drop",
                    "old_price": str(old_price),
                    "new_price": str(self._last_price),
                    "drop_pct": str(price_change_pct_abs.quantize(Decimal("0.1"))),
                    "il_pct": str(self._il_pct),
                    "source": "on-chain",
                    "message": f"🚨 LIVE: ETH dropped {price_change_pct_abs.quantize(Decimal('0.1'))}% to ${self._last_price} — IL: {self._il_pct}%",
                })
                
                if self.config.auto_exit_on_threat:
                    await self._execute_protective_swap("on-chain")
                    await asyncio.sleep(1)
                    self.memory.publish(EventType.POSITION_LOCKED, self.name, {
                        "message": "🔒 Positions locked — protective hedge executed",
                        "vault_balance": str(self._position_value),
                    })
                    self.memory.set_state("positions_locked", True)

        price_change_pct: Decimal | None = None
        if old_price > 0:
            price_change_pct = ((self._last_price - old_price) / old_price * 100)

        if self._il_pct > self.config.impermanent_loss_threshold_pct:
            self._threat_level = "warning"
            self.memory.publish(EventType.THREAT_DETECTED, self.name, {
                "type": "impermanent_loss",
                "il_pct": str(self._il_pct),
                "threshold": str(self.config.impermanent_loss_threshold_pct),
                "eth_price": str(self._last_price),
                "entry_price": str(self._entry_price),
                "source": "on-chain",
                "message": f"⚠️ LIVE IL at {self._il_pct}% (entry: ${self._entry_price} → now: ${self._last_price})",
            })
        elif self._threat_level == "warning" and self._il_pct < self.config.impermanent_loss_threshold_pct * Decimal("0.5"):
            self._threat_level = "safe"
            self.memory.publish(EventType.THREAT_CLEARED, self.name, {
                "message": f"✅ Threat cleared — IL at {self._il_pct}%, ETH at ${self._last_price}",
            })

        self._build_reasoning(price_change_pct)

    async def _monitor_simulated(self) -> None:
        """Fallback simulated monitoring when RPC is unavailable."""
        old_price = self._last_price
        noise = Decimal(str(random.uniform(-2.0, 2.0)))
        self._last_price += noise / 100 * self._last_price

        self._il_pct = UniswapV3Client.calculate_il(self._entry_price, self._last_price)

        price_change_pct: Decimal | None = None
        if old_price > 0:
            price_change_pct = ((self._last_price - old_price) / old_price * 100)

        if self._il_pct > self.config.impermanent_loss_threshold_pct:
            self._threat_level = "warning"
            self.memory.publish(EventType.THREAT_DETECTED, self.name, {
                "type": "impermanent_loss",
                "il_pct": str(self._il_pct),
                "threshold": str(self.config.impermanent_loss_threshold_pct),
                "source": "simulated",
                "message": f"⚠️ Impermanent loss at {self._il_pct}% — approaching threshold",
            })
        elif self._threat_level == "warning" and self._il_pct < self.config.impermanent_loss_threshold_pct * Decimal("0.5"):
            self._threat_level = "safe"
            self.memory.publish(EventType.THREAT_CLEARED, self.name, {
                "message": "✅ Threat cleared — impermanent loss back within safe range",
            })

        self._build_reasoning(price_change_pct)

    async def _execute_protective_swap(self, source: str = "on-chain") -> None:
        """Execute a live hedge swap to protect against downside."""
        if not self.uniswap_api or not getattr(self.uniswap_api, "available", False):
            logger.debug("Cannot execute protective swap: Uniswap API unavailable")
            return
        if not self.wallet or not getattr(self.wallet, "available", False):
            logger.debug("Cannot execute protective swap: Wallet unavailable")
            return

        try:
            from aegis.uniswap_api import CHAIN_IDS, TOKENS
            sepolia_id = CHAIN_IDS.get("sepolia", 11155111)
            tokens = TOKENS.get(sepolia_id, {})
            weth = tokens.get("WETH", "")
            usdc = tokens.get("USDC", "")
            if not weth or not usdc:
                return

            # Hedge amount (simulated as 1 WETH for testing)
            amount_wei = "1000000000000000000"

            swap_result = await self.uniswap_api.execute_swap(
                token_in=weth,
                token_out=usdc,
                amount=amount_wei,
                wallet_address=self.wallet.address,
                chain_id=sepolia_id,
            )
            if "error" in swap_result:
                logger.warning("Protective swap quote failed: %s", swap_result["error"])
                return

            swap_tx = swap_result.get("swap", swap_result)
            tx_data = {
                "to": swap_tx.get("to", ""),
                "data": swap_tx.get("data", swap_tx.get("calldata", "0x")),
                "value": swap_tx.get("value", "0"),
                "chainId": sepolia_id,
                "gas": swap_tx.get("gasLimit", swap_tx.get("gas", 300000)),
            }

            if not tx_data["to"]:
                return

            broadcast = await self.wallet.sign_and_send(tx_data)
            if "error" in broadcast:
                logger.warning("Protective swap broadcast failed: %s", broadcast["error"])
                return

            self._reasoning.append(
                f"🛡️ Hedged WETH to USDC: {broadcast.get('explorer_url', '')}"
            )
            logger.info("Protective swap executed: %s", broadcast.get("explorer_url", ""))
            
            # Publish event for dashboard
            self.memory.publish(EventType.SYSTEM, self.name, {
                "message": f"🛡️ LIVE PROTECT: Executed defensive swap on Sepolia: {broadcast.get('explorer_url', '')}",
                "tx_hash": broadcast.get("tx_hash", ""),
            })
        except Exception as exc:
            logger.error("Protective swap execution failed: %s", exc)
