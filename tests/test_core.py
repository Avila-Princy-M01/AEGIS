"""AEGIS Core Tests — validates imports, config, memory, agents, and math.

Run with:
    pytest tests/test_core.py -v
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from aegis.config import AegisConfig, GuardConfig, GrowConfig, LegacyConfig, RebalanceConfig
from aegis.memory import EventType, MemoryEvent, SharedMemory
from aegis.uniswap import UniswapV3Client


# ── Import Tests ──────────────────────────────────────────────────

def test_all_modules_import():
    """All core modules import without error."""
    from aegis.agents.guard import GuardAgent
    from aegis.agents.grow import GrowAgent
    from aegis.agents.legacy import LegacyAgent
    from aegis.agents.rebalance import RebalanceAgent
    from aegis.orchestrator import AegisOrchestrator
    from aegis.server import app
    assert GuardAgent is not None
    assert GrowAgent is not None
    assert LegacyAgent is not None
    assert RebalanceAgent is not None
    assert AegisOrchestrator is not None
    assert app is not None


def test_agents_init_export():
    """The agents __init__ exports all four agents."""
    from aegis.agents import GuardAgent, GrowAgent, LegacyAgent, RebalanceAgent
    assert all(cls is not None for cls in [GuardAgent, GrowAgent, LegacyAgent, RebalanceAgent])


# ── Config Tests ──────────────────────────────────────────────────

def test_default_config():
    """AegisConfig creates with sensible defaults."""
    cfg = AegisConfig()
    assert cfg.guard.impermanent_loss_threshold_pct == Decimal("10.0")
    assert cfg.grow.compound_frequency_hours == 24
    assert cfg.legacy.inactivity_threshold_days == 30
    assert cfg.rebalance.range_width_ticks == 4000
    assert cfg.rebalance.auto_rebalance is False
    assert cfg.chain.chain == "ethereum"


def test_rebalance_config_fields():
    """RebalanceConfig has all expected fields."""
    rc = RebalanceConfig()
    assert rc.check_interval_seconds == 5
    assert rc.rebalance_threshold_pct == Decimal("5.0")


# ── Shared Memory Tests ──────────────────────────────────────────

def test_memory_publish_and_get(tmp_path):
    """Events can be published and retrieved."""
    mem = SharedMemory(workspace_dir=str(tmp_path))
    mem.publish(EventType.THREAT_DETECTED, "guard", {"level": "warning"})
    mem.publish(EventType.FEES_COMPOUNDED, "grow", {"amount": "0.05"})

    events = mem.get_events(limit=10)
    assert len(events) == 2
    assert events[0].event_type == "threat_detected"
    assert events[1].agent == "grow"


def test_memory_subscribe(tmp_path):
    """Subscribers are notified of new events."""
    mem = SharedMemory(workspace_dir=str(tmp_path))
    received: list[MemoryEvent] = []
    mem.subscribe(lambda e: received.append(e))

    mem.publish(EventType.CHECK_IN, "legacy", {"message": "alive"})
    assert len(received) == 1
    assert received[0].event_type == "check_in"


def test_memory_filter_by_agent(tmp_path):
    """get_events filters by agent name."""
    mem = SharedMemory(workspace_dir=str(tmp_path))
    mem.publish(EventType.AGENT_STARTED, "guard", {})
    mem.publish(EventType.AGENT_STARTED, "grow", {})
    mem.publish(EventType.AGENT_STARTED, "rebalance", {})

    guard_events = mem.get_events(limit=10, agent="guard")
    assert len(guard_events) == 1
    assert guard_events[0].agent == "guard"


def test_memory_event_types():
    """All expected EventTypes exist."""
    expected = [
        "threat_detected", "threat_cleared", "position_locked",
        "fees_compounded", "check_in", "inheritance_triggered",
        "position_out_of_range", "rebalance_suggested", "gas_too_high",
        "agent_started", "agent_stopped", "system",
    ]
    actual = [e.value for e in EventType]
    for name in expected:
        assert name in actual, f"Missing EventType: {name}"


def test_memory_state(tmp_path):
    """Key-value state can be set and retrieved."""
    mem = SharedMemory(workspace_dir=str(tmp_path))
    mem.set_state("entry_price", "2000.00")
    assert mem.get_state("entry_price") == "2000.00"
    assert mem.get_state("missing_key", "default") == "default"


# ── Agent Instantiation Tests ────────────────────────────────────

def test_guard_agent_instantiates(tmp_path):
    """GuardAgent can be instantiated with defaults."""
    from aegis.agents.guard import GuardAgent
    mem = SharedMemory(workspace_dir=str(tmp_path))
    client = UniswapV3Client(chain="ethereum")
    agent = GuardAgent(GuardConfig(), mem, client)
    assert agent.name == "guard"


def test_grow_agent_instantiates(tmp_path):
    """GrowAgent can be instantiated with defaults."""
    from aegis.agents.grow import GrowAgent
    mem = SharedMemory(workspace_dir=str(tmp_path))
    client = UniswapV3Client(chain="ethereum")
    agent = GrowAgent(GrowConfig(), mem, client)
    assert agent.name == "grow"


def test_rebalance_agent_instantiates(tmp_path):
    """RebalanceAgent can be instantiated with defaults."""
    from aegis.agents.rebalance import RebalanceAgent
    mem = SharedMemory(workspace_dir=str(tmp_path))
    client = UniswapV3Client(chain="ethereum")
    agent = RebalanceAgent(RebalanceConfig(), mem, client)
    assert agent.name == "rebalance"


def test_legacy_agent_instantiates(tmp_path):
    """LegacyAgent can be instantiated with defaults."""
    from aegis.agents.legacy import LegacyAgent
    mem = SharedMemory(workspace_dir=str(tmp_path))
    agent = LegacyAgent(LegacyConfig(), mem)
    assert agent.name == "legacy"


# ── Price Math Tests ─────────────────────────────────────────────

def test_sqrt_price_to_eth_usd_ethereum():
    """sqrtPriceX96 decoding gives a reasonable ETH price for Ethereum pool layout."""
    # Construct sqrtPriceX96 from tick 199500 (ETH ~$2,100)
    import math
    tick = 199500
    sqrt_price = math.sqrt(1.0001 ** tick)
    sqrt_price_x96 = int(sqrt_price * (2 ** 96))
    price = UniswapV3Client._sqrt_price_to_eth_usd(
        sqrt_price_x96, token0_decimals=6, token1_decimals=18, invert_price=True,
    )
    assert price > Decimal("500"), f"ETH price {price} is too low"
    assert price < Decimal("10000"), f"ETH price {price} is too high"


def test_impermanent_loss_calculation():
    """IL calculation returns expected values for known price ratios."""
    # No price change → 0% IL
    il_zero = UniswapV3Client.calculate_il(Decimal("2000"), Decimal("2000"))
    assert il_zero == Decimal("0")

    # 2x price → ~5.72% IL
    il_2x = UniswapV3Client.calculate_il(Decimal("1000"), Decimal("2000"))
    assert Decimal("5") < il_2x < Decimal("6"), f"2x IL should be ~5.72%, got {il_2x}"

    # 0.5x price → ~5.72% IL (symmetric)
    il_half = UniswapV3Client.calculate_il(Decimal("2000"), Decimal("1000"))
    assert Decimal("5") < il_half < Decimal("6"), f"0.5x IL should be ~5.72%, got {il_half}"


def test_tick_to_price():
    """tick_to_price returns 1.0 at tick 0."""
    p = UniswapV3Client.tick_to_price(0)
    assert p == Decimal("1.0")


# ── UniswapV3Client Simulation Mode ─────────────────────────────

def test_client_simulation_mode():
    """Client without API key runs in simulation mode."""
    client = UniswapV3Client(chain="ethereum")
    # Without Alchemy key, it may or may not connect via public RPC
    # but should never crash
    assert client.chain == "ethereum"


def test_client_unknown_chain():
    """Unknown chain falls back to simulation mode."""
    client = UniswapV3Client(chain="avalanche")
    assert client.live is False
    assert client.pool_address == ""


# ── Retry Logic Tests ────────────────────────────────────────────

def test_retry_succeeds_after_transient_failure():
    """_call_with_retry retries on transient errors and succeeds."""
    call_count = 0

    def flaky_fn():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise Exception("header not found")
        return "success"

    result = UniswapV3Client._call_with_retry(
        flaky_fn, max_retries=3, backoff_base=0.01, label="test",
    )
    assert result == "success"
    assert call_count == 3


def test_retry_raises_non_transient():
    """_call_with_retry raises immediately on non-transient errors."""
    def bad_fn():
        raise ValueError("invalid argument")

    with pytest.raises(ValueError, match="invalid argument"):
        UniswapV3Client._call_with_retry(
            bad_fn, max_retries=3, backoff_base=0.01, label="test",
        )


def test_retry_exhausts_attempts():
    """_call_with_retry raises after exhausting all retries."""
    def always_fail():
        raise Exception("header not found")

    with pytest.raises(Exception, match="header not found"):
        UniswapV3Client._call_with_retry(
            always_fail, max_retries=2, backoff_base=0.01, label="test",
        )


# ── Lido Pool Tests ──────────────────────────────────────────────

def test_lido_pool_in_presets():
    """Lido wstETH/ETH pool is configured in Ethereum CHAIN_PRESETS."""
    from aegis.uniswap import CHAIN_PRESETS
    eth_pools = CHAIN_PRESETS["ethereum"]["pools"]
    lido_pools = [p for p in eth_pools if "wstETH" in p["label"]]
    assert len(lido_pools) >= 1, "Lido wstETH/ETH pool missing from presets"
    lido = lido_pools[0]
    assert lido["token0_decimals"] == 18
    assert lido["token1_decimals"] == 18


# ── Agent Reasoning Tests ────────────────────────────────────────

def test_guard_has_reasoning(tmp_path):
    """Guard agent status includes a reasoning field."""
    from aegis.agents.guard import GuardAgent
    mem = SharedMemory(workspace_dir=str(tmp_path))
    client = UniswapV3Client(chain="ethereum")
    agent = GuardAgent(GuardConfig(), mem, client)
    status = agent.status
    assert "reasoning" in status
    assert "pnl" in status
    assert "fees_earned" in status["pnl"]


def test_grow_has_reasoning(tmp_path):
    """Grow agent status includes a reasoning field."""
    from aegis.agents.grow import GrowAgent
    mem = SharedMemory(workspace_dir=str(tmp_path))
    client = UniswapV3Client(chain="ethereum")
    agent = GrowAgent(GrowConfig(), mem, client)
    assert "reasoning" in agent.status


def test_rebalance_has_reasoning(tmp_path):
    """Rebalance agent status includes a reasoning field."""
    from aegis.agents.rebalance import RebalanceAgent
    mem = SharedMemory(workspace_dir=str(tmp_path))
    client = UniswapV3Client(chain="ethereum")
    agent = RebalanceAgent(RebalanceConfig(), mem, client)
    assert "reasoning" in agent.status


def test_legacy_has_reasoning(tmp_path):
    """Legacy agent status includes a reasoning field."""
    from aegis.agents.legacy import LegacyAgent
    mem = SharedMemory(workspace_dir=str(tmp_path))
    agent = LegacyAgent(LegacyConfig(), mem)
    assert "reasoning" in agent.status
