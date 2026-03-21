"""AEGIS Core Tests — validates imports, config, memory, agents, and math.

Run with:
    pytest tests/test_core.py -v
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from aegis.config import AegisConfig, GuardConfig, GrowConfig, LegacyConfig, MevConfig, RebalanceConfig
from aegis.memory import EventType, MemoryEvent, SharedMemory
from aegis.uniswap import UniswapV3Client
from aegis.uniswap_api import UniswapTradingAPI, CHAIN_IDS, TOKENS


# ── Import Tests ──────────────────────────────────────────────────

def test_all_modules_import():
    """All core modules import without error."""
    from aegis.agents.guard import GuardAgent
    from aegis.agents.grow import GrowAgent
    from aegis.agents.legacy import LegacyAgent
    from aegis.agents.rebalance import RebalanceAgent
    from aegis.agents.mev import MevAgent
    from aegis.orchestrator import AegisOrchestrator
    from aegis.server import app
    from aegis.ens import ENSResolver, is_ens_name
    from aegis.analytics import LidoYieldComparator, CrossPoolAllocator, Backtester
    assert GuardAgent is not None
    assert GrowAgent is not None
    assert LegacyAgent is not None
    assert RebalanceAgent is not None
    assert MevAgent is not None
    assert AegisOrchestrator is not None
    assert app is not None
    assert ENSResolver is not None
    assert is_ens_name is not None
    assert LidoYieldComparator is not None
    assert CrossPoolAllocator is not None
    assert Backtester is not None


def test_agents_init_export():
    """The agents __init__ exports all five agents."""
    from aegis.agents import GuardAgent, GrowAgent, LegacyAgent, MevAgent, RebalanceAgent
    assert all(cls is not None for cls in [GuardAgent, GrowAgent, LegacyAgent, MevAgent, RebalanceAgent])


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
    assert cfg.mev.sandwich_detection_enabled is True
    assert cfg.mev.price_impact_threshold_pct == Decimal("0.5")
    assert cfg.mev.frontrun_window_blocks == 2


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
        "mev_detected", "mev_cleared", "dry_run_tx",
        "ens_resolved", "lido_yield_update", "cross_pool_allocation",
        "backtest_result",
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

    client = UniswapV3Client.__new__(UniswapV3Client)
    client._rpc_urls = []
    client._rpc_index = 0
    result = client._call_with_retry(
        flaky_fn, max_retries=3, backoff_base=0.01, label="test",
    )
    assert result == "success"
    assert call_count == 3


def test_retry_raises_non_transient():
    """_call_with_retry raises immediately on non-transient errors."""
    def bad_fn():
        raise ValueError("invalid argument")

    client = UniswapV3Client.__new__(UniswapV3Client)
    client._rpc_urls = []
    client._rpc_index = 0
    with pytest.raises(ValueError, match="invalid argument"):
        client._call_with_retry(
            bad_fn, max_retries=3, backoff_base=0.01, label="test",
        )


def test_retry_exhausts_attempts():
    """_call_with_retry raises after exhausting all retries."""
    def always_fail():
        raise Exception("header not found")

    client = UniswapV3Client.__new__(UniswapV3Client)
    client._rpc_urls = []
    client._rpc_index = 0
    with pytest.raises(Exception, match="header not found"):
        client._call_with_retry(
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


# ── MEV Agent Tests ──────────────────────────────────────────────

def test_mev_agent_instantiates(tmp_path):
    """MevAgent can be instantiated with defaults."""
    from aegis.agents.mev import MevAgent
    mem = SharedMemory(workspace_dir=str(tmp_path))
    client = UniswapV3Client(chain="ethereum")
    agent = MevAgent(MevConfig(), mem, client)
    assert agent.name == "mev"


def test_mev_agent_status_fields(tmp_path):
    """MevAgent status includes all expected fields."""
    from aegis.agents.mev import MevAgent
    mem = SharedMemory(workspace_dir=str(tmp_path))
    client = UniswapV3Client(chain="ethereum")
    agent = MevAgent(MevConfig(), mem, client)
    status = agent.status
    assert "mev_level" in status
    assert "sandwich_count" in status
    assert "frontrun_count" in status
    assert "total_mev_detected" in status
    assert "estimated_mev_cost_usd" in status
    assert "reasoning" in status
    assert status["mev_level"] == "safe"
    assert status["sandwich_count"] == 0


def test_mev_config_defaults():
    """MevConfig has all expected default fields."""
    cfg = MevConfig()
    assert cfg.sandwich_detection_enabled is True
    assert cfg.price_impact_threshold_pct == Decimal("0.5")
    assert cfg.frontrun_window_blocks == 2
    assert cfg.alert_on_detection is True
    assert cfg.known_mev_bots == []


# ── Uniswap Trading API Tests ──


def test_uniswap_api_no_key(monkeypatch):
    """UniswapTradingAPI without key is not available."""
    monkeypatch.delenv("UNISWAP_API_KEY", raising=False)
    api = UniswapTradingAPI(api_key="")
    assert not api.available


def test_uniswap_api_with_key():
    """UniswapTradingAPI with key is available."""
    api = UniswapTradingAPI(api_key="test_key_123")
    assert api.available


def test_uniswap_api_chain_ids():
    """Chain IDs are correctly mapped."""
    assert CHAIN_IDS["ethereum"] == 1
    assert CHAIN_IDS["base"] == 8453


def test_uniswap_api_tokens():
    """Token addresses are defined for Ethereum and Base."""
    assert "WETH" in TOKENS[1]
    assert "USDC" in TOKENS[1]
    assert "wstETH" in TOKENS[1]
    assert "WETH" in TOKENS[8453]
    assert "USDC" in TOKENS[8453]


def test_uniswap_api_parse_quote():
    """Quote parsing extracts the right fields."""
    api = UniswapTradingAPI(api_key="test")
    raw = {
        "quote": {
            "input": {"amount": "1000000000000000000"},
            "output": {"amount": "2151230000"},
            "gasUseEstimate": "150000",
            "gasUseEstimateUSD": "3.45",
            "priceImpact": "0.01",
            "slippage": {"tolerance": 0.5},
            "route": [[
                {
                    "type": "v3-pool",
                    "address": "0x8ad599c3A0ff1De082011EFDDc58f1908eb6e6D8",
                    "fee": "3000",
                    "tokenIn": {"symbol": "WETH"},
                    "tokenOut": {"symbol": "USDC"},
                }
            ]],
        },
        "routing": "CLASSIC",
    }
    parsed = api._parse_quote(raw, "0xWETH", "0xUSDC", 1)
    assert parsed["amount_in"] == "1000000000000000000"
    assert parsed["amount_out"] == "2151230000"
    assert parsed["gas_usd"] == "3.45"
    assert parsed["routing"] == "CLASSIC"
    assert parsed["source"] == "uniswap_trading_api"
    assert len(parsed["route"]) == 1
    assert parsed["route"][0]["type"] == "v3-pool"


@pytest.mark.asyncio
async def test_uniswap_api_quote_no_key(monkeypatch):
    """get_quote returns error when no API key."""
    monkeypatch.delenv("UNISWAP_API_KEY", raising=False)
    api = UniswapTradingAPI(api_key="")
    result = await api.get_quote("0xA", "0xB", "1000")
    assert "error" in result


# ── ENS Tests ────────────────────────────────────────────────────

def test_ens_is_ens_name():
    """is_ens_name correctly identifies ENS names."""
    from aegis.ens import is_ens_name
    assert is_ens_name("vitalik.eth") is True
    assert is_ens_name("family.eth") is True
    assert is_ens_name("a.b.eth") is True
    assert is_ens_name(".eth") is False
    assert is_ens_name("notens") is False
    assert is_ens_name("0x1234") is False
    assert is_ens_name("") is False
    assert is_ens_name(None) is False  # type: ignore[arg-type]


def test_ens_resolver_no_web3(tmp_path):
    """ENSResolver gracefully handles missing web3."""
    from aegis.ens import ENSResolver
    resolver = ENSResolver(chain="ethereum")
    assert resolver.cache_size == 0


# ── Analytics Tests ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_backtester_produces_valid_result(tmp_path):
    """Backtester returns all expected fields."""
    from aegis.analytics import Backtester
    mem = SharedMemory(workspace_dir=str(tmp_path))
    bt = Backtester(mem)
    result = await bt.run(days=7)
    assert "period_days" in result
    assert result["period_days"] == 7
    assert "total_fees_earned" in result
    assert "total_il_loss" in result
    assert "gas_costs" in result
    assert "net_pnl" in result
    assert "max_drawdown_pct" in result
    assert "sharpe_ratio" in result
    assert "reasoning" in result


@pytest.mark.asyncio
async def test_lido_yield_comparator_simulated(tmp_path):
    """LidoYieldComparator returns valid result in simulation mode."""
    from aegis.analytics import LidoYieldComparator
    mem = SharedMemory(workspace_dir=str(tmp_path))
    client = UniswapV3Client(chain="ethereum")
    comparator = LidoYieldComparator(mem, client)
    result = await comparator.compare()
    assert "lp_apr_pct" in result
    assert "staking_apr_pct" in result
    assert "recommendation" in result
    assert result["recommendation"] in ("lp", "stake")
    assert "spread_pct" in result
    assert "reasoning" in result


@pytest.mark.asyncio
async def test_cross_pool_allocator_simulated(tmp_path):
    """CrossPoolAllocator returns valid result in simulation mode."""
    from aegis.analytics import CrossPoolAllocator
    mem = SharedMemory(workspace_dir=str(tmp_path))
    client = UniswapV3Client(chain="ethereum")
    allocator = CrossPoolAllocator(mem, client)
    result = await allocator.allocate()
    assert "allocations" in result
    assert "strategy_name" in result


# ── Dry-Run TX Event Tests ───────────────────────────────────────

def test_dry_run_tx_event_type_exists():
    """DRY_RUN_TX event type exists in EventType enum."""
    assert EventType.DRY_RUN_TX.value == "dry_run_tx"


def test_mev_detected_event_type_exists():
    """MEV_DETECTED event type exists in EventType enum."""
    assert EventType.MEV_DETECTED.value == "mev_detected"


def test_mev_cleared_event_type_exists():
    """MEV_CLEARED event type exists in EventType enum."""
    assert EventType.MEV_CLEARED.value == "mev_cleared"


def test_backtest_result_event_type_exists():
    """BACKTEST_RESULT event type exists in EventType enum."""
    assert EventType.BACKTEST_RESULT.value == "backtest_result"


def test_ens_resolved_event_type_exists():
    """ENS_RESOLVED event type exists in EventType enum."""
    assert EventType.ENS_RESOLVED.value == "ens_resolved"


# ── Wallet Tests ─────────────────────────────────────────────────

def test_wallet_imports():
    """Wallet module imports without error."""
    from aegis.wallet import AegisWallet, SEPOLIA_CHAIN_ID
    assert AegisWallet is not None
    assert SEPOLIA_CHAIN_ID == 11155111


def test_wallet_no_key(monkeypatch):
    """AegisWallet without private key is not available."""
    monkeypatch.delenv("WALLET_PRIVATE_KEY", raising=False)
    from aegis.wallet import AegisWallet
    wallet = AegisWallet(private_key="")
    assert not wallet.available
    assert wallet.address == ""


def test_wallet_rejects_mainnet():
    """AegisWallet rejects transactions with mainnet chainId."""
    from aegis.wallet import AegisWallet
    wallet = AegisWallet.__new__(AegisWallet)
    wallet._key = ""
    wallet._w3 = None
    wallet._account = None
    wallet.address = ""
    wallet.available = False
    with pytest.raises(ValueError, match="SAFETY"):
        wallet._assert_testnet(1)


def test_wallet_allows_sepolia():
    """AegisWallet allows Sepolia chainId."""
    from aegis.wallet import AegisWallet
    wallet = AegisWallet.__new__(AegisWallet)
    wallet._assert_testnet(11155111)


# ── Swap Execution Tests ─────────────────────────────────────────

def test_grow_agent_has_swap_fields(tmp_path):
    """Grow agent status includes swap execution fields."""
    from aegis.agents.grow import GrowAgent
    mem = SharedMemory(workspace_dir=str(tmp_path))
    client = UniswapV3Client(chain="ethereum")
    agent = GrowAgent(GrowConfig(), mem, client)
    status = agent.status
    assert "last_swap_tx" in status
    assert "total_swaps_executed" in status
    assert status["total_swaps_executed"] == 0


def test_sepolia_in_chain_ids():
    """Sepolia is in CHAIN_IDS mapping."""
    assert "sepolia" in CHAIN_IDS
    assert CHAIN_IDS["sepolia"] == 11155111


def test_sepolia_tokens_defined():
    """Sepolia tokens are defined in TOKENS."""
    assert 11155111 in TOKENS
    assert "WETH" in TOKENS[11155111]
    assert "USDC" in TOKENS[11155111]


def test_agent_json_exists():
    """agent.json manifest exists and has required fields."""
    import json
    from pathlib import Path
    agent_json = Path("agent.json")
    assert agent_json.exists(), "agent.json missing"
    data = json.loads(agent_json.read_text())
    assert "name" in data
    assert "description" in data
    assert "agentWallet" in data
    assert "agents" in data
    assert len(data["agents"]) == 5


@pytest.mark.asyncio
async def test_execute_swap_no_api():
    """execute_swap returns error when API not configured."""
    from aegis.orchestrator import AegisOrchestrator
    orch = AegisOrchestrator()
    result = await orch.execute_swap()
    assert "error" in result
