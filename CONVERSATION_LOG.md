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

## Phase 11: Self-Custody Transfer & ERC-8004 Registration

**Agent:** Completed the hackathon registration flow:
- Called Synthesis API to initiate self-custody transfer to wallet `0x9aC234De759456f2b65FB7C182CFCE013889390A`
- Confirmed transfer — ERC-8004 NFT minted on Base Mainnet
- TxHash: `0x83ab89d5cbcd811230cdf85af79f023bdb3cfd20b0e5472e55f1669771f1bcae`
- Registered agent identity as `aegis-guardian` with participant ID `6ff8d7e7ffc942c58400d97b1264e1e0`
- Created `agent.json` manifest following ERC-8004 registration-v1 spec
- Created `agent_log.json` structured execution log with seeded entries

**Key Artifact:** On-chain agent identity — permanent, verifiable, independent of any platform.

---

## Phase 12: Real Testnet Swap Execution

**Human:** "Get Sepolia ETH and execute real swap"

**Agent:** Orchestrated the full swap flow:
1. User funded wallet with 0.05 Sepolia ETH from Google Cloud faucet
2. Fixed `wallet.py` to handle hex string values from Uniswap API (added `_parse_int()` method)
3. Discovered native ETH (zero address) must be used as tokenIn for automatic WRAP_ETH
4. **Swap 1:** 0.001 ETH → 5.55 USDC — TxHash: `0x83087cd184dd637b85594e10928e2cc9e255cd847c2875e1275c57d1f79591fe` (block 10491702)
5. **Swap 2:** 0.002 ETH → USDC — TxHash: `0xdc3ab4f3e67ce95fda153bcba84454dfcbf782cd20bbcfd73a14946650621acb` (block 10491851)

**Breakthrough:** The Uniswap Trading API returns `value` as hex strings (e.g., `0x038d7ea4c68000`), but web3.py expects integers. The `_parse_int()` utility transparently handles hex/decimal/int conversion.

**Result:** 2 real, confirmed, on-chain swap transactions on Sepolia — verifiable by anyone on Etherscan.

---

## Phase 13: Project Submission & Track Registration

**Agent:** Created the project on the Synthesis hackathon platform:
- Project UUID: `463b2d38fe8d4a00a446d61856b228d6`
- Registered for 5 tracks: Uniswap API, Open Track, Student Founder's Bet, ERC-8004, Agent Cook
- Git committed 41 files (4977 insertions) and pushed to GitHub
- All code, manifests, logs, and transaction records are public

**Note:** Project created as draft — not yet published pending final README polish and video demo.

---

## Phase 14: Final Documentation & Video Preparation

**Human:** "Make the README comprehensive with hackathon theme alignment, swap proof, and video guide"

**Agent:** Rewrote README.md to be hackathon-focused:
- Added On-Chain Proof section with all 5 verifiable transaction hashes
- Added Theme Alignment section mapping AEGIS to all 3 Synthesis themes
- Added Sponsor Track Integration table (Uniswap, Protocol Labs, Lido, ENS, Open)
- Added comparison table showing AEGIS vs typical hackathon projects
- Added image placeholders for screenshots and video demo link
- Created VIDEO_DEMO_GUIDE.md with shot-by-shot recording script
- Updated CONVERSATION_LOG.md to document the full collaboration narrative

**Philosophy:** Judges who don't run the code should still be able to verify everything from the README alone — every claim is backed by an on-chain link.

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
  │     ├── /quote       ← optimal routing across v3/v4 pools
  │     ├── /swap        ← calldata generation for on-chain execution
  │     └── /check_approval ← token allowance verification
  ├── AegisWallet        ← Sepolia testnet signing + broadcasting
  │     ├── _parse_int() ← hex/decimal/int transparent conversion
  │     ├── send_transaction() ← builds, signs, broadcasts via web3.py
  │     └── Sepolia guard ← hard reject if chainId ≠ 11155111
  ├── ERC-8004 Identity  ← on-chain agent registration on Base Mainnet
  └── React Dashboard    ← WebSocket + REST, 6 panels + swap execution UI
```

**Swap Execution Flow:**
```
Grow Agent compound trigger
  → Uniswap Trading API /quote (get optimal route)
  → Uniswap Trading API /swap (get calldata + tx params)
  → AegisWallet._parse_int() (normalize hex values)
  → AegisWallet.send_transaction() (sign + broadcast)
  → Sepolia RPC (confirm on-chain)
  → TxHash logged to TXIDS.md + agent_log.json
```

---

*This log captures the iterative, collaborative process of building AEGIS with AI assistance. Every major decision was discussed, every pivot was deliberate.*
