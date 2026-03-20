# AEGIS Agent Workspace

This workspace is managed by the AEGIS multi-agent system.

## Agents
- **Guard** — Monitors Uniswap LP positions for threats (live IL calculation)
- **Grow** — Auto-compounds fees with gas-aware optimization
- **Rebalance** — Detects out-of-range positions and suggests optimal new ranges
- **Legacy** — Dead man's switch for digital inheritance

## Contracts
- `contracts/guard_vault.py` — Threat-response vault
- `contracts/grow_vault.py` — Auto-compounding vault
- `contracts/legacy_will.py` — Digital will contract

See `contracts/README.md` for details on the PyVax build process.

---
*Created by `classified-agent init` — aegis-guardian*
