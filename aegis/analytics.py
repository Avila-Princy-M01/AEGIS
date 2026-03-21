"""Analytics module — yield comparison, cross-pool allocation, and backtesting.

Provides three analytical tools for AEGIS LP operators:
- LidoYieldComparator: compares Uniswap V3 LP yield vs pure Lido staking
- CrossPoolAllocator: recommends optimal capital split across monitored pools
- Backtester: simulates historical performance with realistic random-walk data

All classes publish events to SharedMemory and follow the same patterns
used by the Guard and Grow agents.
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from decimal import Decimal
from typing import Any

from aegis.memory import EventType, SharedMemory
from aegis.uniswap import UniswapV3Client

logger = logging.getLogger("aegis.analytics")

# ── Fallback constants ────────────────────────────────────────────

LIDO_STAKING_APR_PCT = Decimal("3.20")
SECONDS_PER_YEAR = Decimal("31536000")
Q128 = Decimal(2**128)


class LidoYieldComparator:
    """Compares Uniswap V3 LP yield against pure Lido staking yield."""

    def __init__(
        self,
        memory: SharedMemory,
        uniswap_client: UniswapV3Client,
    ) -> None:
        self.memory = memory
        self.uniswap = uniswap_client
        self._last_fee_growth_0: int = 0
        self._last_fee_growth_1: int = 0
        self._last_snapshot_time: float = 0.0

    async def compare(self) -> dict[str, Any]:
        """Return LP vs Lido staking yield comparison.

        Returns a dict with: lp_apr_pct, staking_apr_pct, recommendation,
        spread_pct, reasoning.
        """
        try:
            lp_apr = await self._estimate_lp_apr()
            staking_apr = LIDO_STAKING_APR_PCT

            spread = lp_apr - staking_apr
            if lp_apr > staking_apr:
                recommendation = "lp"
                reasoning = (
                    f"LP yield {lp_apr}% exceeds Lido staking {staking_apr}%"
                    f" by {spread}% — favour liquidity provision"
                )
            else:
                recommendation = "stake"
                reasoning = (
                    f"Lido staking {staking_apr}% exceeds LP yield {lp_apr}%"
                    f" by {abs(spread)}% — favour pure staking"
                )

            result: dict[str, Any] = {
                "lp_apr_pct": str(lp_apr),
                "staking_apr_pct": str(staking_apr),
                "recommendation": recommendation,
                "spread_pct": str(spread),
                "reasoning": reasoning,
            }

            self.memory.publish(EventType.LIDO_YIELD_UPDATE, "analytics", {
                "message": f"📊 Yield comparison: LP {lp_apr}% vs Lido {staking_apr}% → {recommendation.upper()}",
                **result,
            })

            logger.info(
                "Yield comparison: LP %s%% vs Lido %s%% → %s",
                lp_apr, staking_apr, recommendation,
            )
            return result

        except Exception as exc:
            logger.warning("Yield comparison failed: %s", exc)
            fallback: dict[str, Any] = {
                "lp_apr_pct": "0.00",
                "staking_apr_pct": str(LIDO_STAKING_APR_PCT),
                "recommendation": "stake",
                "spread_pct": str(-LIDO_STAKING_APR_PCT),
                "reasoning": f"Yield comparison unavailable ({exc}) — defaulting to staking",
            }
            return fallback

    async def _estimate_lp_apr(self) -> Decimal:
        """Estimate annualised LP APR from fee growth data.

        Queries the pool's feeGrowthGlobal values and extrapolates
        the delta to an annual rate. Falls back to a simulated
        estimate when live data is unavailable.
        """
        state = await self.uniswap.get_pool_state()
        if not state:
            return self._simulate_lp_apr()

        now = time.time()

        if self._last_snapshot_time == 0.0:
            # First snapshot — store baseline and return simulated estimate
            self._last_fee_growth_0 = state.fee_growth_global_0
            self._last_fee_growth_1 = state.fee_growth_global_1
            self._last_snapshot_time = now
            return self._simulate_lp_apr()

        elapsed = Decimal(str(now - self._last_snapshot_time))
        if elapsed <= 0:
            return self._simulate_lp_apr()

        delta_0 = state.fee_growth_global_0 - self._last_fee_growth_0
        delta_1 = state.fee_growth_global_1 - self._last_fee_growth_1
        if delta_0 < 0:
            delta_0 = 0
        if delta_1 < 0:
            delta_1 = 0

        self._last_fee_growth_0 = state.fee_growth_global_0
        self._last_fee_growth_1 = state.fee_growth_global_1
        self._last_snapshot_time = now

        fees_0_usd = UniswapV3Client.fee_growth_to_usd(
            delta_0, state.liquidity, Decimal("1"),
        )
        fees_1_usd = UniswapV3Client.fee_growth_to_usd(
            delta_1, state.liquidity, state.eth_price_usd,
        )
        total_fees = fees_0_usd + fees_1_usd

        # Extrapolate to annual rate assuming $1000 position
        position_value = Decimal("1000.00")
        if position_value <= 0:
            return Decimal("0.00")

        annual_fees = total_fees * SECONDS_PER_YEAR / elapsed
        lp_apr = (annual_fees / position_value * Decimal("100")).quantize(Decimal("0.01"))

        return lp_apr

    @staticmethod
    def _simulate_lp_apr() -> Decimal:
        """Generate a simulated LP APR as fallback."""
        return Decimal(str(random.uniform(2.0, 8.0))).quantize(Decimal("0.01"))


class CrossPoolAllocator:
    """Recommends optimal capital allocation across monitored Uniswap V3 pools."""

    def __init__(
        self,
        memory: SharedMemory,
        uniswap_client: UniswapV3Client,
    ) -> None:
        self.memory = memory
        self.uniswap = uniswap_client

    async def allocate(self) -> dict[str, Any]:
        """Return recommended capital allocation across pools.

        Returns a dict with: allocations (list), strategy_name.
        Each allocation entry has: pool, weight_pct, fee_apr, il_risk, reasoning.
        """
        try:
            pools = self.uniswap.available_pools
            if not pools:
                pools = [self.uniswap.token_pair or "ETH/USDC 0.3%"]

            pool_metrics = await self._gather_pool_metrics(pools)
            allocations = self._optimise_weights(pool_metrics)

            strategy_name = self._pick_strategy_name(allocations)

            result: dict[str, Any] = {
                "allocations": allocations,
                "strategy_name": strategy_name,
            }

            self.memory.publish(EventType.CROSS_POOL_ALLOCATION, "analytics", {
                "message": f"📊 Cross-pool allocation: {strategy_name} across {len(allocations)} pool(s)",
                **result,
            })

            logger.info(
                "Cross-pool allocation: %s across %d pool(s)",
                strategy_name, len(allocations),
            )
            return result

        except Exception as exc:
            logger.warning("Cross-pool allocation failed: %s", exc)
            fallback: dict[str, Any] = {
                "allocations": [],
                "strategy_name": "error",
            }
            return fallback

    async def _gather_pool_metrics(
        self, pools: list[str],
    ) -> list[dict[str, Any]]:
        """Fetch or simulate fee APR and IL risk for each pool."""
        metrics: list[dict[str, Any]] = []

        for pool_label in pools:
            state = await self.uniswap.get_pool_state_for(pool_label)

            if state:
                # Estimate fee APR from fee tier
                fee_bps = Decimal(str(state.fee_bps))
                # Rough heuristic: higher fee tier → higher APR but also higher IL risk
                fee_apr = (fee_bps / Decimal("10000") * Decimal("365") * Decimal("2")).quantize(Decimal("0.01"))
                il_risk = self._estimate_il_risk(state.fee_bps)
            else:
                fee_apr = Decimal(str(random.uniform(2.0, 12.0))).quantize(Decimal("0.01"))
                il_risk = Decimal(str(random.uniform(1.0, 8.0))).quantize(Decimal("0.01"))

            metrics.append({
                "pool": pool_label,
                "fee_apr": fee_apr,
                "il_risk": il_risk,
            })

        return metrics

    @staticmethod
    def _estimate_il_risk(fee_bps: int) -> Decimal:
        """Heuristic IL risk score based on pool fee tier.

        Lower fee tiers (0.01%, 0.05%) are usually stable-pair pools → low IL.
        Higher fee tiers (0.3%, 1%) imply volatile pairs → higher IL.
        """
        if fee_bps <= 100:
            return Decimal(str(random.uniform(0.5, 2.0))).quantize(Decimal("0.01"))
        elif fee_bps <= 500:
            return Decimal(str(random.uniform(1.0, 4.0))).quantize(Decimal("0.01"))
        elif fee_bps <= 3000:
            return Decimal(str(random.uniform(3.0, 7.0))).quantize(Decimal("0.01"))
        else:
            return Decimal(str(random.uniform(5.0, 12.0))).quantize(Decimal("0.01"))

    @staticmethod
    def _optimise_weights(
        pool_metrics: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Assign weight to each pool based on risk-adjusted return.

        Uses a simple score = fee_apr / (1 + il_risk) heuristic
        and normalises weights to 100%.
        """
        scored: list[tuple[dict[str, Any], Decimal]] = []
        for m in pool_metrics:
            score = m["fee_apr"] / (Decimal("1") + m["il_risk"])
            scored.append((m, score))

        total_score = sum(s for _, s in scored)
        if total_score <= 0:
            total_score = Decimal("1")

        allocations: list[dict[str, Any]] = []
        for m, score in scored:
            weight = (score / total_score * Decimal("100")).quantize(Decimal("0.1"))
            if weight < Decimal("0.1"):
                weight = Decimal("0.0")

            reasoning = (
                f"fee APR {m['fee_apr']}% | IL risk {m['il_risk']}%"
                f" | risk-adj score {score.quantize(Decimal('0.01'))}"
            )
            allocations.append({
                "pool": m["pool"],
                "weight_pct": str(weight),
                "fee_apr": str(m["fee_apr"]),
                "il_risk": str(m["il_risk"]),
                "reasoning": reasoning,
            })

        return allocations

    @staticmethod
    def _pick_strategy_name(allocations: list[dict[str, Any]]) -> str:
        """Choose a human-readable strategy label."""
        if len(allocations) <= 1:
            return "single-pool"
        weights = [Decimal(a["weight_pct"]) for a in allocations]
        max_weight = max(weights) if weights else Decimal("0")
        if max_weight >= Decimal("70"):
            return "concentrated"
        elif max_weight >= Decimal("40"):
            return "balanced"
        else:
            return "diversified"


class Backtester:
    """Simulates historical LP performance with random-walk data."""

    def __init__(
        self,
        memory: SharedMemory,
    ) -> None:
        self.memory = memory

    async def run(self, days: int = 30) -> dict[str, Any]:
        """Run a backtest simulation over *days* of historical data.

        Returns a dict with: period_days, total_fees_earned, total_il_loss,
        gas_costs, net_pnl, max_drawdown_pct, sharpe_ratio, reasoning.
        """
        try:
            prices = self._generate_price_series(days)
            daily_results = self._simulate_daily_pnl(prices)

            total_fees = sum(d["fees"] for d in daily_results)
            total_il = sum(d["il"] for d in daily_results)
            gas_costs = self._estimate_gas_costs(days)
            net_pnl = total_fees - total_il - gas_costs

            max_drawdown = self._calculate_max_drawdown(daily_results)
            sharpe = self._calculate_sharpe(daily_results)

            if net_pnl > 0:
                reasoning = (
                    f"Backtest positive: +${net_pnl} net over {days}d"
                    f" | fees ${total_fees} - IL ${total_il} - gas ${gas_costs}"
                    f" | Sharpe {sharpe} | max DD {max_drawdown}%"
                )
            else:
                reasoning = (
                    f"Backtest negative: ${net_pnl} net over {days}d"
                    f" | fees ${total_fees} - IL ${total_il} - gas ${gas_costs}"
                    f" | Sharpe {sharpe} | max DD {max_drawdown}%"
                )

            result: dict[str, Any] = {
                "period_days": days,
                "total_fees_earned": str(total_fees),
                "total_il_loss": str(total_il),
                "gas_costs": str(gas_costs),
                "net_pnl": str(net_pnl),
                "max_drawdown_pct": str(max_drawdown),
                "sharpe_ratio": str(sharpe),
                "reasoning": reasoning,
            }

            self.memory.publish(EventType.BACKTEST_RESULT, "analytics", {
                "message": f"📊 Backtest ({days}d): net PnL ${net_pnl} | Sharpe {sharpe} | max DD {max_drawdown}%",
                **result,
            })

            logger.info(
                "Backtest %dd: net $%s | Sharpe %s | DD %s%%",
                days, net_pnl, sharpe, max_drawdown,
            )
            return result

        except Exception as exc:
            logger.warning("Backtest failed: %s", exc)
            fallback: dict[str, Any] = {
                "period_days": days,
                "total_fees_earned": "0.00",
                "total_il_loss": "0.00",
                "gas_costs": "0.00",
                "net_pnl": "0.00",
                "max_drawdown_pct": "0.00",
                "sharpe_ratio": "0.00",
                "reasoning": f"Backtest failed: {exc}",
            }
            return fallback

    @staticmethod
    def _generate_price_series(days: int) -> list[Decimal]:
        """Generate a realistic ETH price random walk.

        Uses geometric Brownian motion with:
        - daily drift μ ≈ 0.02% (≈7% annual)
        - daily volatility σ ≈ 3%
        """
        prices: list[Decimal] = []
        price = Decimal("2500.00")
        mu = 0.0002  # daily drift
        sigma = 0.03  # daily volatility

        for _ in range(days):
            prices.append(price)
            # Geometric Brownian motion step
            shock = random.gauss(mu, sigma)
            price = (price * Decimal(str(1 + shock))).quantize(Decimal("0.01"))
            if price < Decimal("100.00"):
                price = Decimal("100.00")

        return prices

    @staticmethod
    def _simulate_daily_pnl(
        prices: list[Decimal],
    ) -> list[dict[str, Decimal]]:
        """Simulate daily fees earned and IL incurred."""
        results: list[dict[str, Decimal]] = []
        entry_price = prices[0] if prices else Decimal("2500.00")

        for i, price in enumerate(prices):
            # Daily fee income: rough estimate ~0.01–0.03% of position value per day
            daily_fee_rate = Decimal(str(random.uniform(0.0001, 0.0003)))
            position_value = Decimal("1000.00")
            fees = (position_value * daily_fee_rate).quantize(Decimal("0.0001"))

            # IL from entry
            il_pct = UniswapV3Client.calculate_il(entry_price, price)
            il_loss = (position_value * il_pct / Decimal("100")).quantize(Decimal("0.0001"))

            # Net daily PnL
            net = fees - il_loss

            results.append({
                "day": Decimal(str(i + 1)),
                "price": price,
                "fees": fees,
                "il": il_loss,
                "net": net,
            })

        return results

    @staticmethod
    def _estimate_gas_costs(days: int) -> Decimal:
        """Estimate total gas costs over the backtest period.

        Assumes ~1 compound per day at random gas prices.
        """
        total_gas = Decimal("0.00")
        for _ in range(days):
            # Simulate daily gas cost between $0.50 and $5.00
            daily_gas = Decimal(str(random.uniform(0.50, 5.00)))
            total_gas += daily_gas

        return total_gas.quantize(Decimal("0.01"))

    @staticmethod
    def _calculate_max_drawdown(
        daily_results: list[dict[str, Decimal]],
    ) -> Decimal:
        """Calculate maximum drawdown percentage from cumulative PnL."""
        if not daily_results:
            return Decimal("0.00")

        cumulative = Decimal("0.00")
        peak = Decimal("0.00")
        max_dd = Decimal("0.00")

        for d in daily_results:
            cumulative += d["net"]
            if cumulative > peak:
                peak = cumulative
            drawdown = peak - cumulative
            if drawdown > max_dd:
                max_dd = drawdown

        position_value = Decimal("1000.00")
        dd_pct = (max_dd / position_value * Decimal("100")).quantize(Decimal("0.01"))
        return dd_pct

    @staticmethod
    def _calculate_sharpe(
        daily_results: list[dict[str, Decimal]],
    ) -> Decimal:
        """Calculate annualised Sharpe ratio from daily net returns.

        Sharpe = (mean_daily_return / std_daily_return) * sqrt(365)
        Risk-free rate is assumed to be 0 for simplicity.
        """
        if len(daily_results) < 2:
            return Decimal("0.00")

        position_value = Decimal("1000.00")
        returns = [
            float(d["net"] / position_value) for d in daily_results
        ]

        mean_ret = sum(returns) / len(returns)

        variance = sum((r - mean_ret) ** 2 for r in returns) / (len(returns) - 1)
        std_ret = variance ** 0.5

        if std_ret == 0:
            return Decimal("0.00")

        sharpe = (mean_ret / std_ret) * (365 ** 0.5)
        return Decimal(str(sharpe)).quantize(Decimal("0.01"))
