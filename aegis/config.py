"""AEGIS configuration — strategy parameters parsed from natural language."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any


@dataclass
class ChainConfig:
    """Blockchain connection configuration."""

    chain: str = "ethereum"
    alchemy_api_key: str = ""


@dataclass
class GuardConfig:
    """Guard agent parameters."""

    impermanent_loss_threshold_pct: Decimal = Decimal("10.0")
    price_drop_alert_pct: Decimal = Decimal("15.0")
    suspicious_outflow_threshold: Decimal = Decimal("0.5")
    auto_exit_on_threat: bool = True
    monitored_pools: list[str] = field(default_factory=list)


@dataclass
class GrowConfig:
    """Grow agent parameters."""

    auto_compound_enabled: bool = True
    compound_frequency_hours: int = 24
    min_fee_threshold: Decimal = Decimal("0.01")
    savings_sweep_pct: Decimal = Decimal("10.0")
    max_position_size: Decimal = Decimal("1.0")


@dataclass
class Beneficiary:
    """A wallet address that receives assets on inactivity."""

    address: str
    share_pct: Decimal = Decimal("100.0")
    label: str = ""


@dataclass
class RebalanceConfig:
    """Rebalance agent parameters."""

    check_interval_seconds: int = 5
    range_width_ticks: int = 4000
    auto_rebalance: bool = False
    rebalance_threshold_pct: Decimal = Decimal("5.0")


@dataclass
class LegacyConfig:
    """Legacy agent (dead man's switch) parameters."""

    inactivity_threshold_days: int = 30
    check_in_interval_hours: int = 24
    beneficiaries: list[Beneficiary] = field(default_factory=list)
    graceful_exit_before_distribute: bool = True


@dataclass
class MevConfig:
    """MEV Protection agent parameters."""

    sandwich_detection_enabled: bool = True
    price_impact_threshold_pct: Decimal = Decimal("0.5")
    frontrun_window_blocks: int = 2
    alert_on_detection: bool = True
    known_mev_bots: list[str] = field(default_factory=list)


@dataclass
class AegisConfig:
    """Root configuration for the AEGIS multi-agent system."""

    guard: GuardConfig = field(default_factory=GuardConfig)
    grow: GrowConfig = field(default_factory=GrowConfig)
    legacy: LegacyConfig = field(default_factory=LegacyConfig)
    rebalance: RebalanceConfig = field(default_factory=RebalanceConfig)
    mev: MevConfig = field(default_factory=MevConfig)
    chain: ChainConfig = field(default_factory=ChainConfig)
    owner_address: str = ""
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    @classmethod
    def default(cls) -> AegisConfig:
        return cls()
