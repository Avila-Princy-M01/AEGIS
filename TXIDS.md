# 🔗 AEGIS — On-Chain Transaction IDs

> Real on-chain artifacts from AEGIS agent operations on Sepolia testnet.

## ERC-8004 Agent Registration (Base Mainnet)

| Item | Value |
|------|-------|
| **Transaction** | [`0x48a190093bad8a57c0e4c4feba3a783f7c2f63625aad4e978db62fce9c625389`](https://basescan.org/tx/0x48a190093bad8a57c0e4c4feba3a783f7c2f63625aad4e978db62fce9c625389) |
| **Participant ID** | `6ff8d7e7ffc942c58400d97b1264e1e0` |
| **Team ID** | `43734f07c3624fed835fd96659e01b24` |
| **Agent Name** | `aegis-guardian` |

## Sepolia Testnet Swap Transactions

> Executed via Uniswap Trading API (`trade-api.gateway.uniswap.org/v1/swap`)
> Wallet: `0x9aC234De759456f2b65FB7C182CFCE013889390A`

| # | Pair | Amount | TxID | Status |
|---|------|--------|------|--------|
| 1 | ETH → USDC | 0.001 ETH (5.55 USDC) | [`0x83087cd184dd637b...`](https://sepolia.etherscan.io/tx/0x83087cd184dd637b85594e10928e2cc9e255cd847c2875e1275c57d1f79591fe) | ✅ Confirmed (block 10491702) |

### How to Execute a Swap

```bash
# 1. Get free Sepolia ETH from a faucet:
#    - https://cloud.google.com/application/web3/faucet/ethereum/sepolia
#    - https://faucet.quicknode.com/ethereum/sepolia
#    - https://www.alchemy.com/faucets/ethereum-sepolia

# 2. Start the AEGIS server
python -m aegis.server

# 3. Execute a swap via the API
curl -X POST http://localhost:8000/api/swap-execute \
  -H "Content-Type: application/json" \
  -d '{"token_in": "WETH", "token_out": "USDC", "amount": "100000000000000000"}'
```

The swap will:
1. Get a quote from the Uniswap Trading API (Sepolia, chainId 11155111)
2. Get swap calldata from `/v1/swap`
3. Sign the transaction with `WALLET_PRIVATE_KEY`
4. Broadcast to Sepolia testnet
5. Return the TxID with Etherscan link

---

*All transactions are on Sepolia testnet — zero real funds required.*
