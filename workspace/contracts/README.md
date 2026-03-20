# 📜 PyVax Smart Contracts

These are **PyVax contract definitions** — Python source files that define EVM smart contract logic using the PyVax DSL.

## How They Work

PyVax contracts are **not** standard Python scripts. They use the `from pyvax import ...` syntax to define Solidity-equivalent smart contracts in pure Python. The `classified-agent run` CLI compiles them to EVM bytecode via the PyVax toolchain.

**Do not run these files directly with `python`** — they are compiled by the PyVax compiler:

```bash
classified-agent run   # Compiles → EVM bytecode → deploys
```

## Contracts

| Contract | Purpose | Agent |
|----------|---------|-------|
| `guard_vault.py` | Emergency vault — locks funds during detected threats | 🛡️ Guard |
| `grow_vault.py` | Auto-compounding savings for LP fees | 📈 Grow |
| `legacy_will.py` | Trustless digital will with dead man's switch | 🏛️ Legacy |

## Architecture

Each contract corresponds to an AEGIS agent:

- **Guard Agent** → `GuardVault` — receives funds on threat detection, locks until cleared
- **Grow Agent** → `GrowVault` — accumulates compounded LP fees, tracks savings
- **Legacy Agent** → `LegacyWill` — distributes assets to beneficiaries after inactivity threshold
