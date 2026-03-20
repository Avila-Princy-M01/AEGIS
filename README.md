# 🛡️ AEGIS — Autonomous Wallet Guardian

> **One command. Four AI agents. Real on-chain Uniswap V3 data. Zero Solidity.**

AEGIS deploys 4 coordinated AI agents that **protect**, **grow**, **rebalance**, and **inherit** your Uniswap V3 LP positions — with **live on-chain integration** querying real pool state from Ethereum Mainnet and Base.

```
"Protect my Uniswap positions, compound my fees, and if I disappear for 30 days, send everything to my family."
```

→ Four agents spawn. Real pool data flows. Your wallet is guarded.

## 📸 Demo

| Landing Page | Live Dashboard |
|:---:|:---:|
| ![Landing](assets/landing.png) | ![Dashboard](assets/dashboard.png) |
| **Threat Detection** | **Out-of-Range Alert** |
| ![Threat](assets/threat.png) | ![Out of Range](assets/out-of-range.png) |

### 🎥 Record a 60-Second Demo GIF

> Judges who don't run your code will only see this GIF. Make it count.

**Tools** (pick one):
- [ScreenToGif](https://www.screentogif.com/) (Windows, free)
- [Kap](https://getkap.co/) (Mac, free)
- [Peek](https://github.com/phw/peek) (Linux, free)
- [LICEcap](https://www.cockos.com/licecap/) (cross-platform)

**Recording script (60 seconds):**

| Time | Action | What Judges See |
|------|--------|----------------|
| 0–05s | Open dashboard → show landing page | Problem statement + 4 agent badges |
| 05–10s | Click **🚀 Deploy Agents** | Agents spawn, live stats bar appears |
| 10–20s | Pause on dashboard — let data flow | 🟢 LIVE block number, gas price, ETH price updating |
| 20–25s | Hover over Guard panel → show 🧠 reasoning | `ETH $2,141 \| IL 0.23% → SAFE` |
| 25–35s | Click **⚡ Simulate Crash** | Guard flashes red, Grow pauses, P&L updates |
| 35–45s | Click **🎯 Out of Range** | Rebalance shakes, shows suggested range |
| 45–50s | Click **🔵 Base** chain selector | Live chain switch to Base L2 |
| 50–55s | Click **🏦️ Trigger Inheritance** | Legacy distributes to beneficiaries |
| 55–60s | Scroll to Activity Feed | Full event log showing 4-agent coordination |

**Save as:** `assets/aegis-demo.gif` (aim for < 10MB — resize to 800px wide)

Then add to README:
```markdown
![AEGIS Demo](assets/aegis-demo.gif)
```

---

## 🔗 Real On-Chain Integration

AEGIS is **not a simulation** — it queries live Uniswap V3 pool contracts:

| Feature | On-Chain Source |
|---------|----------------|
| **ETH Price** | `slot0().sqrtPriceX96` from Uniswap V3 pool |
| **Impermanent Loss** | Calculated from real price movement vs entry price |
| **Fee Growth** | `feeGrowthGlobal0X128` / `feeGrowthGlobal1X128` |
| **Position Range** | `NonfungiblePositionManager.positions()` — tick range monitoring |
| **Gas Price** | `eth_gasPrice` — gas-aware compound decisions |
| **Liquidity** | `liquidity()` from pool contract |
| **Multi-Pool** | Monitors ETH/USDC, ETH/USDT, wstETH/ETH, stETH/ETH (Lido) |
| **Block Number** | `eth_blockNumber` — live block tracking |
| **Agent Reasoning** | Structured decision logs per cycle |
| **P&L Tracking** | Fees earned − IL loss − gas cost = net P&L |

Supported chains:
- 🟣 **Ethereum Mainnet** — 5 pools monitored (incl. wstETH/ETH + stETH/ETH Lido)
- 🔵 **Base** — ETH/USDC 0.05% pool
- 🔄 **Live chain switching** in the dashboard UI

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Natural Language Input                     │
│  "Protect my positions, grow fees, 30-day dead man's switch" │
└──────────────────────────┬──────────────────────────────────┘
                           │ NLP Parser (Groq LLM)
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                    AEGIS Orchestrator                         │
│           + UniswapV3Client (web3.py) + Price History         │
│                                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │ 🛡️ Guard │ │ 📈 Grow  │ │ 🎯Rebal  │ │ 🏛️Legacy │        │
│  │  Agent   │ │  Agent   │ │  Agent   │ │  Agent   │        │
│  │ (live IL)│ │(gas-fee) │ │ (range)  │ │ (timer)  │        │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘        │
│       │            │            │            │               │
│       └────────────┼────────────┼────────────┘               │
│                    │            │                             │
│     ┌──────────────▼────────────▼─────────────┐              │
│     │     Shared Memory (pub/sub)             │              │
│     └─────────────────────────────────────────┘              │
└──────────────────────────────────────────────────────────────┘
          │                                    │
          ▼                                    ▼
   Uniswap V3 Pools                    PyVax Contracts
   (Ethereum / Base)                  (Guard/Grow/Legacy Vaults)
```

## 🤖 The Four Agents

| Agent | Role | Key Features |
|-------|------|--------------|
| 🛡️ **Guard** | Threat Detection | **Live** ETH price from `slot0()`, real IL calculation, **P&L tracking**, auto-exits, reacts to out-of-range events, price history sparkline |
| 📈 **Grow** | Fee Compounding | **Live** fee growth tracking, **gas-aware** compounding (skips when gas > fees), savings vault, **agent reasoning logs** |
| 🎯 **Rebalance** | Range Monitoring | Detects **out-of-range** positions (the #1 LP pain point), suggests optimal new ranges, visual range bar, **animated transitions** |
| 🏛️ **Legacy** | Digital Inheritance | Dead man's switch — distributes assets to family if user goes inactive, **structured reasoning** |

All four agents share intelligence through **shared memory**:
- Guard detects a threat → Grow + Rebalance auto-pause
- Rebalance detects out-of-range → Guard increases threat level
- Gas is too high → Grow skips compounding
- Legacy triggers → gracefully exits all positions first

## 🔒 Design Philosophy

**Safety-first, read-only monitoring:**
- **No private keys required** — AEGIS reads on-chain data but never holds or moves funds
- **Suggest, don't execute** — Auto-rebalance is OFF by default; agents suggest optimal actions for human approval
- **Graceful degradation** — If RPC is unavailable, agents fall back to simulation mode seamlessly
- **Gas-aware** — Grow Agent checks if gas cost exceeds expected revenue before compounding

## 🎬 Judge Walkthrough (5-Minute Demo)

> **For hackathon judges:** Follow these steps to see AEGIS in action.

**Step 1 — Start the system** (see Quick Start below), then open `http://localhost:5173`

**Step 2 — Deploy agents:** Type anything or click an example, then click 🚀 Deploy Agents

**Step 3 — Watch the live stats bar:** You'll see real-time data from Ethereum:
```
🟢 Block: 22,145,839 · ⛽ Gas: 12.3 gwei · ETH: $2,141.90 · Chain: ETHEREUM · Pools: 4
```
This proves real on-chain integration — not simulated.

**Step 4 — Observe agent reasoning:** Each panel shows a 🧠 reasoning line explaining the agent's decision:
- Guard: `ETH $2,141.90 | Δ +0.1% | IL 0.23% (threshold 10%) → SAFE`
- Grow: `Fees +$0.04 (live) | Gas 12.3 gwei | Vault $0.12 → COMPOUND`

**Step 5 — Trigger the chain reaction:** Click ⚡ **Simulate Crash**
- Guard detects threat → goes CRITICAL (red flash animation)
- Grow auto-pauses compounding
- Rebalance auto-pauses
- P&L updates in real-time

**Step 6 — Test out-of-range:** Click 🎯 **Out of Range**
- Rebalance detects it → shakes, shows suggested new range
- Guard reacts → elevates threat level
- This solves the #1 Uniswap V3 LP pain point

**Step 7 — Switch chains:** Click **🔵 Base** in the header to live-switch to Base L2

**Step 8 — Test inheritance:** Click 🏛️ **Trigger Inheritance** to see the dead man's switch

### On-Chain Contracts Monitored

| Pool | Address | Track |
|------|---------|-------|
| ETH/USDC 0.3% | [`0x8ad5...eB48`](https://etherscan.io/address/0x8ad599c3A0ff1De082011EFDDc58f1908eb6e6D8) | Uniswap |
| ETH/USDC 0.05% | [`0x88e6...5640`](https://etherscan.io/address/0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640) | Uniswap |
| ETH/USDT 0.3% | [`0x4e68...fa36`](https://etherscan.io/address/0x4e68Ccd3E89f51C3074ca5072bbAC773960dFa36) | Uniswap |
| wstETH/ETH 0.01% | [`0x1098...B9dAa`](https://etherscan.io/address/0x109830a1AAaD605BbF02a9dFA7B0B92EC2FB7dAa) | **Lido** |
| stETH/ETH 1% | [`0x6381...Bd7D`](https://etherscan.io/address/0x63818BbDd21E69bE108A23aC1E84cBf66399Bd7D) | **Lido** |
| ETH/USDC 0.05% (Base) | [`0xd0b5...F224`](https://basescan.org/address/0xd0b53D9277642d899DF5C87A3966A349A798F224) | Base |

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd aegis-uniswap
pip install -r requirements.txt
```

### 2. Get a Free Alchemy API Key (optional but recommended)

1. Go to [dashboard.alchemy.com/signup](https://dashboard.alchemy.com/signup)
2. Create a new app → select **Ethereum Mainnet**
3. Copy your API key

### 3. Set Environment Variables

```bash
# Required for NLP command parsing
export GROQ_API_KEY=your_groq_key

# Optional — enables real on-chain data (falls back to simulation without it)
export ALCHEMY_API_KEY=your_alchemy_key

# Optional — choose chain (default: ethereum)
export AEGIS_CHAIN=ethereum  # or "base"
```

### 4. Start the Dashboard Server

```bash
python -m aegis.server
```

### 5. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

### 6. Open the Dashboard

Visit **http://localhost:5173** and type your command!

You'll see a **🟢 LIVE** indicator when connected to real on-chain data, or **🟡 SIMULATED** as fallback.

## 🧪 Demo Mode

The dashboard includes demo controls to simulate:
- ⚡ **Price crash** — Guard detects threat, locks positions, pauses Grow + Rebalance
- 🎯 **Out of range** — Rebalance detects position leaving its tick range
- 🏛️ **Inheritance trigger** — Legacy distributes to beneficiaries
- ✅ **Check-in** — Resets the inactivity timer

## 🔬 On-Chain Data Details

### Guard Agent — Real IL Calculation + Price History

```
IL = 2 × √(current_price / entry_price) / (1 + current_price / entry_price) − 1
```

Prices decoded from `sqrtPriceX96` with a live sparkline chart tracking price movement.

### Grow Agent — Gas-Aware Fee Compounding

Queries `eth_gasPrice` before each compound cycle. If gas cost exceeds expected fee revenue, the compound is skipped with a `GAS_TOO_HIGH` event — a critical DeFi optimization that saves real money.

### Rebalance Agent — Out-of-Range Detection

Monitors the current pool tick vs the position's tickLower/tickUpper range. When the price moves outside the concentrated liquidity range:
- Emits `POSITION_OUT_OF_RANGE` (the position earns **zero fees**)
- Calculates and suggests an optimal new range centered on current tick
- Guard agent reacts by raising threat level

This solves the **#1 pain point** for Uniswap V3 LPs.

### Multi-Pool Monitoring (incl. Lido stETH)

AEGIS monitors multiple pools simultaneously:
- ETH/USDC 0.3% (main pool)
- ETH/USDT 0.3%
- ETH/USDC 0.05% (high volume)
- **wstETH/ETH 0.01%** (Lido — qualifies for $12K Lido track)
- **stETH/ETH 1%** (Lido — additional Lido pool for deeper coverage)

## 📜 Smart Contracts (PyVax)

All contracts written in Python, compiled to EVM bytecode via PyVax:

- **Guard Vault** — Emergency vault that locks funds during threats
- **Grow Vault** — Auto-compounding savings for LP fees
- **Legacy Will** — Trustless digital will with dead man's switch

## 🏆 Hackathon

Built for the **Classified Hack × Synthesis Hackathon** ($75K in prizes)

- **Tracks**: Uniswap ($25K) + **Lido ($12K)** + Base ($15K)
- **Stack**: Python + web3.py + Uniswap V3 + PyVax + Groq LLM
- **Key differentiator**: 4 agents solving the 4 biggest LP problems with real on-chain data

### The 4 LP Problems AEGIS Solves

| Problem | Impact | Agent |
|---------|--------|-------|
| **IL Blindness** | LPs don't know they're losing money | 🛡️ Guard — real-time IL alerts |
| **Fee Rot** | Unclaimed fees lose value to gas | 📈 Grow — gas-aware compounding |
| **Range Drift** | Out-of-range = earning zero fees | 🎯 Rebalance — tick monitoring |
| **No Succession** | Crypto lost forever when LPs die | 🏛️ Legacy — dead man's switch |

### Key Features Judges Should Notice

- **Live blockchain stats bar** — real block number, gas price, ETH price updating in real-time
- **Agent reasoning logs** — each agent explains *why* it made its decision every cycle
- **P&L tracking** — fees earned, IL loss, gas cost, net profit/loss
- **Multi-chain switching** — switch between Ethereum and Base live in the dashboard
- **4-agent coordination** — agents react to each other through shared memory pub/sub
- **Animated state transitions** — visual feedback when threats are detected or positions go out of range
- **Lido wstETH/ETH pool monitoring** — qualifies for both Uniswap and Lido tracks
- **21 passing tests** — `pytest tests/test_core.py -v`

### Running Tests

```bash
pytest tests/test_core.py -v
```

## 📁 Project Structure

```
aegis-uniswap/
├── classified.toml          # classified-agent config
├── aegis/
│   ├── main.py              # CLI entry point
│   ├── server.py            # FastAPI dashboard backend
│   ├── orchestrator.py      # Agent coordinator + price history
│   ├── uniswap.py           # Uniswap V3 on-chain client (web3.py)
│   ├── nlp_parser.py        # NL → strategy (Groq)
│   ├── memory.py            # Shared memory with pub/sub
│   ├── config.py            # Strategy + chain configuration
│   └── agents/
│       ├── guard.py          # 🛡️ Real pool price + IL monitoring
│       ├── grow.py           # 📈 Gas-aware fee compounding
│       ├── rebalance.py      # 🎯 Out-of-range detection
│       └── legacy.py         # 🏛️ Digital inheritance
├── workspace/
│   └── contracts/            # PyVax smart contracts
│       ├── guard_vault.py
│       ├── grow_vault.py
│       └── legacy_will.py
└── frontend/                 # React + TypeScript dashboard
    └── src/
        ├── App.tsx
        └── components/
            ├── GuardPanel.tsx      # + Price sparkline chart
            ├── GrowPanel.tsx       # + Gas price indicator
            ├── RebalancePanel.tsx  # Range visualization bar
            ├── LegacyPanel.tsx
            ├── PriceChart.tsx      # SVG sparkline component
            ├── ActivityFeed.tsx
            ├── CommandInput.tsx
            └── DemoControls.tsx
```

## 📄 License

MIT

---

*Built with ❤️ by the AEGIS team — powered by [PyVax](https://pyvax.xyz) + [Uniswap V3](https://uniswap.org)*
