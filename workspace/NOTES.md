# AEGIS Agent Workspace

This workspace is managed by the AEGIS multi-agent system.

## Agents
- **Guard** — Monitors Uniswap LP positions for threats (live IL calculation)
- **Grow** — Auto-compounds fees with gas-aware optimization + Uniswap Trading API route quotes
- **Rebalance** — Detects out-of-range positions and suggests optimal new ranges
- **MEV Shield** — Detects sandwich attacks and front-running via tick swing analysis + safe route recommendations
- **Legacy** — Dead man's switch for digital inheritance with ENS name resolution

## Contracts
- `contracts/guard_vault.py` — Threat-response vault
- `contracts/grow_vault.py` — Auto-compounding vault
- `contracts/legacy_will.py` — Digital will contract
- `contracts/mev_shield.py` — Swap protection layer against MEV extraction

See `contracts/README.md` for details on the PyVax build process.

## Integrations
- **Uniswap V3** — Real on-chain pool data via web3.py (slot0, feeGrowthGlobal, gasPrice)
- **Uniswap Trading API** — Real swap quotes via trade-api.gateway.uniswap.org/v1
- **ENS** — Name resolution for Legacy beneficiaries
- **Lido** — wstETH/ETH + stETH/ETH pool monitoring and yield comparison

---
*Created by `classified-agent init` — aegis-guardian*
