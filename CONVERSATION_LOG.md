# 🗣️ AEGIS — Conversation Log

> Human-agent collaboration narrative for the Synthesis Hackathon submission.
> This documents the brainstorms, pivots, and breakthroughs that built AEGIS.

---

## Phase 1: Problem Discovery & Architecture Design

**Human:** "I want to build something for the Uniswap track — a multi-agent system that protects LP positions."

**Agent:** Proposed the 5-agent architecture after analyzing the top LP pain points:
1. IL Blindness → Guard Agent
2. Fee Rot → Grow Agent  
3. Range Drift → Rebalance Agent
4. MEV Extraction → MEV Shield Agent
5. No Succession → Legacy Agent

**Key Decision:** Shared memory with pub/sub events for cross-agent coordination. When Guard detects a threat, Grow auto-pauses. When MEV detects a sandwich, Guard escalates.

**Pivot:** Initially planned 4 agents. Added MEV Shield as the 5th agent after researching sandwich attack prevalence on Uniswap V3 — over $200M extracted annually.

---

## Phase 2: Real On-Chain Integration

**Human:** "Make it real. I don't want simulated data."

**Agent:** Built `UniswapV3Client` with web3.py to query live pool contracts:
- `slot0()` for sqrtPriceX96 → real ETH price
- `feeGrowthGlobal0X128` / `feeGrowthGlobal1X128` → real fee tracking
- `eth_gasPrice` → gas-aware compounding decisions
- `liquidity()` → pool depth

**Breakthrough:** Implemented 6-endpoint RPC fallback rotation with automatic retry on 429 rate limits. This solved the #1 reliability issue — free RPC endpoints rate-limit aggressively.

**RPCs:** LlamaRPC, PublicNode, 1RPC, DRPC, Cloudflare, MEV Blocker

---

## Phase 3: Multi-Chain & Lido

**Human:** "Add Base chain support and Lido pool monitoring."

**Agent:** Extended CHAIN_PRESETS with Base (chain ID 8453) and added 2 Lido pools:
- wstETH/ETH 0.01% (`0x109830a1AAaD605BbF02a9dFA7B0B92EC2FB7dAa`)
- stETH/ETH 1% (`0x63818BbDd21E69bE108A23aC1E84cBf66399Bd7D`)

**Analytics Addition:** Built Lido yield comparison (LP APR vs staking APR) and cross-pool capital allocation optimizer.

---

## Phase 4: Dashboard & UX

**Human:** "Build a React dashboard that makes this look professional."

**Agent:** Created a dark cinematic theme with glassmorphism, particle backgrounds, and per-agent color coding:
- Guard: Red (threat/danger)
- Grow: Green (growth/money)
- Rebalance: Blue (precision/balance)
- MEV: Orange (warning/protection)
- Legacy: Purple (history/permanence)

**Key Features:**
- Live chain stats bar (block number, gas, ETH price)
- Agent reasoning lines (🧠) showing real-time decision logic
- Animated state transitions on threat/MEV/out-of-range events
- WebSocket real-time event feed

---

## Phase 5: Uniswap Trading API Integration

**Human:** "I got a Uniswap Developer Platform API key. Integrate it."

**Agent:** Built `UniswapTradingAPI` client wrapping `trade-api.gateway.uniswap.org/v1/quote`:
- Real swap quotes with optimal routing (v3-pool, v4-pool paths)
- Gas estimates and price impact calculations  
- Multi-chain support (Ethereum chain ID 1, Base chain ID 8453)
- Integrated into Grow Agent (shows reinvestment route on compound)
- Integrated into MEV Agent (shows safe swap route on attack detection)
- Frontend SwapQuotePanel with live quote fetching

**Verified:** `curl` test confirmed 1 ETH → $2,151 USDC quote via the API.

---

## Phase 6: Smart Contracts (PyVax)

**Agent:** Designed 4 PyVax smart contracts — all in Python, zero Solidity:

1. **Guard Vault** — Emergency fund lockup during threats
2. **Grow Vault** — Auto-compounding savings with configurable sweep percentage
3. **Legacy Will** — Trustless digital will with dead man's switch and multi-beneficiary distribution
4. **MEV Shield** — Swap protection layer that defends against sandwich attacks

---

## Phase 7: ENS Integration

**Agent:** Built ENS name resolution for Legacy beneficiaries:
- Resolves `.eth` names via ENS public resolver contract
- Caches results to reduce RPC calls
- Falls back gracefully if resolution fails
- Enables: `"Send 50% to family.eth and 50% to charity.eth"`

---

## Phase 8: Classified Agent & Submission

**Human:** "Verify classified-agent run works."

**Agent:** Found and fixed 3 validation errors in `classified.toml`:
1. `agent.description` exceeded 256 char max → shortened
2. `wallet.backend` was "web3" (invalid) → changed to "mock"
3. `synthesis.agent_profile` exceeded 256 char max → shortened

**Verified:** `classified-agent run --dry-run` passes config validation. `classified-agent join-synthesis` successfully fetches skill.md and registers agent profile.

---

## Phase 9: Gap Analysis & Final Polish

**Agent:** Performed comprehensive gap analysis against skill.md scoring criteria:
- ✅ Ship something that works → 5 agents, 39+ tests, TypeScript compiles clean
- ✅ Agent with meaningful contribution → 5 coordinated agents with real on-chain data
- ✅ On-chain artifacts → 4 PyVax contracts + Uniswap Trading API integration
- ✅ Open source → Public GitHub repo
- ✅ Document collaboration → This conversation log

**Track Strategy:** Targeting **Uniswap Track** (API key + real quotes + deep V3 integration) + **Open Track** (5-agent coordination + polished dashboard).

---

## Phase 10: Real Swap Execution & Submission Readiness

**Human:** "Plan to fix all gaps" — after gap analysis showed AEGIS didn't qualify for the Uniswap Track.

**Agent:** Identified 3 critical failures:
1. ❌ No real swaps (only quotes) — Uniswap Track requires functional swaps
2. ❌ Mock wallet — Track requires no mocks
3. ❌ No TxIDs — Track requires real on-chain transactions
4. ❌ Uniswap API not load-bearing — system works identically without it

**Built:**
- `aegis/wallet.py` — Real testnet wallet with **hard Sepolia-only safety guard** (rejects chainId ≠ 11155111)
- Added `/swap` and `/check_approval` to `UniswapTradingAPI` — full swap execution flow
- Grow Agent now **executes real swaps** on compound via `_execute_compound_swap()` — makes Uniswap Trading API **load-bearing**
- `POST /api/swap-execute` endpoint on the server
- Frontend "Execute Swap" button with live TxID display and Etherscan links
- `agent.json` — ERC-8004 manifest for Protocol Labs track
- `agent_log.json` — auto-generated structured execution log
- `TXIDS.md` — on-chain transaction record
- Changed `wallet.backend` from `"mock"` to `"local"` in `classified.toml`
- 10 new tests covering wallet safety, Sepolia config, swap execution, agent.json

**Key Decision:** Sepolia testnet only — zero risk to real funds. The wallet module raises `ValueError` if any code tries to submit a mainnet transaction.

**Result:** AEGIS now qualifies for the Uniswap Track with real swap execution, real TxIDs, and load-bearing API integration.

---

## Key Technical Decisions

| Decision | Reasoning |
|----------|----------|
| Python + web3.py over ethers.js | Faster prototyping, PyVax compatibility |
| Shared memory pub/sub over message queue | Simpler, lower latency, sufficient for 5 agents |
| 6 RPC fallbacks over single endpoint | Reliability — free RPCs rate-limit aggressively |
| Groq LLM for NLP parsing | Fast inference (< 1s), free tier generous |
| FastAPI + WebSocket over REST polling | Real-time event feed, lower latency |
| Uniswap Trading API for quotes + swaps | Load-bearing integration, required for track |
| Sepolia-only wallet guard | Safety-first — blocks mainnet transactions at code level |

---

## Final Architecture

```
User Command → NLP Parser (Groq) → Orchestrator
  ├── Guard Agent        ← slot0(), IL calc, P&L
  ├── Grow Agent         ← feeGrowthGlobal, gas-aware + Uniswap API swap execution
  ├── Rebalance Agent    ← tick range monitoring
  ├── MEV Shield Agent   ← tick swing + fee spike detection + safe routes
  ├── Legacy Agent       ← dead man's switch + ENS resolution
  ├── Analytics Engine   ← Lido yield, cross-pool alloc, backtesting
  ├── Uniswap Trading API ← real swap quotes + execution (load-bearing)
  ├── AegisWallet        ← Sepolia testnet signing + broadcasting
  └── React Dashboard    ← WebSocket + REST, 6 panels + swap execution UI
```

---

*This log captures the iterative, collaborative process of building AEGIS with AI assistance. Every major decision was discussed, every pivot was deliberate.*
