"""AEGIS Wallet — thin wrapper for testnet transaction signing.

Provides transaction signing and broadcasting via web3.py Account.
SAFETY: Only allows transactions on Sepolia testnet (chainId 11155111).
Rejects any mainnet transaction attempts with a hard guard.
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger("aegis.wallet")

SEPOLIA_CHAIN_ID = 11155111
SEPOLIA_RPC = "https://rpc.sepolia.org"
SEPOLIA_RPCS = [
    "https://rpc.sepolia.org",
    "https://ethereum-sepolia-rpc.publicnode.com",
    "https://sepolia.drpc.org",
]

try:
    from web3 import Web3
    from web3.providers import HTTPProvider
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False


class AegisWallet:
    """Testnet-only wallet for signing and broadcasting transactions."""

    def __init__(self, private_key: str = "") -> None:
        self._key = private_key or os.environ.get("WALLET_PRIVATE_KEY", "")
        self._w3: Any = None
        self._account: Any = None
        self.address: str = ""
        self.available = False

        if not WEB3_AVAILABLE:
            logger.warning("web3 not installed — wallet unavailable")
            return

        if not self._key:
            logger.warning("WALLET_PRIVATE_KEY not set — wallet unavailable")
            return

        try:
            w3 = Web3()
            self._account = w3.eth.account.from_key(self._key)
            self.address = self._account.address
            self._connect_sepolia()
            self.available = True
            logger.info("Wallet ready: %s (Sepolia testnet only)", self.address)
        except Exception as exc:
            logger.warning("Wallet init failed: %s", exc)

    def _connect_sepolia(self) -> None:
        for rpc in SEPOLIA_RPCS:
            try:
                self._w3 = Web3(HTTPProvider(rpc, request_kwargs={"timeout": 10}))
                if self._w3.is_connected():
                    logger.info("Connected to Sepolia via %s", rpc)
                    return
            except Exception:
                continue
        logger.warning("Could not connect to any Sepolia RPC")

    def _assert_testnet(self, chain_id: int) -> None:
        if chain_id != SEPOLIA_CHAIN_ID:
            raise ValueError(
                f"SAFETY: Wallet only allows Sepolia testnet (chainId {SEPOLIA_CHAIN_ID}). "
                f"Got chainId {chain_id}. Mainnet transactions are blocked."
            )

    async def get_balance(self) -> str:
        if not self.available or not self._w3:
            return "0"
        try:
            import asyncio
            balance = await asyncio.to_thread(
                self._w3.eth.get_balance, self.address
            )
            return str(balance)
        except Exception as exc:
            logger.warning("Balance check failed: %s", exc)
            return "0"

    @staticmethod
    def _parse_int(val: Any, default: int = 0) -> int:
        """Parse an int from hex string, decimal string, or int."""
        if val is None:
            return default
        if isinstance(val, int):
            return val
        s = str(val).strip()
        if s.startswith("0x") or s.startswith("0X"):
            return int(s, 16)
        return int(s) if s else default

    async def sign_and_send(self, tx_data: dict[str, Any]) -> dict[str, Any]:
        """Sign and broadcast a transaction. Sepolia testnet ONLY.

        Args:
            tx_data: Transaction dict with 'to', 'data', 'value', 'chainId', etc.
                     Must have chainId == 11155111 (Sepolia).

        Returns:
            Dict with 'tx_hash', 'explorer_url', or 'error'.
        """
        if not self.available or not self._w3 or not self._account:
            return {"error": "Wallet not available"}

        chain_id = self._parse_int(tx_data.get("chainId", 0))
        self._assert_testnet(chain_id)

        try:
            import asyncio

            nonce = await asyncio.to_thread(
                self._w3.eth.get_transaction_count, self.address
            )

            gas = self._parse_int(
                tx_data.get("gas", tx_data.get("gasLimit", 300000))
            )

            tx = {
                "from": self.address,
                "to": Web3.to_checksum_address(tx_data["to"]),
                "data": tx_data.get("data", "0x"),
                "value": self._parse_int(tx_data.get("value", 0)),
                "chainId": SEPOLIA_CHAIN_ID,
                "nonce": nonce,
                "gas": gas,
                "maxFeePerGas": self._w3.to_wei("5", "gwei"),
                "maxPriorityFeePerGas": self._w3.to_wei("2", "gwei"),
            }

            if "maxFeePerGas" in tx_data:
                tx["maxFeePerGas"] = self._parse_int(tx_data["maxFeePerGas"])
            if "maxPriorityFeePerGas" in tx_data:
                tx["maxPriorityFeePerGas"] = self._parse_int(tx_data["maxPriorityFeePerGas"])

            signed = self._account.sign_transaction(tx)

            tx_hash = await asyncio.to_thread(
                self._w3.eth.send_raw_transaction, signed.raw_transaction
            )

            hex_hash = tx_hash.hex() if hasattr(tx_hash, "hex") else str(tx_hash)
            explorer_url = f"https://sepolia.etherscan.io/tx/{hex_hash}"

            logger.info("TX broadcast: %s", explorer_url)

            return {
                "tx_hash": hex_hash,
                "explorer_url": explorer_url,
                "chain_id": SEPOLIA_CHAIN_ID,
                "from": self.address,
                "status": "broadcast",
            }
        except ValueError as exc:
            return {"error": str(exc)}
        except Exception as exc:
            logger.warning("Transaction failed: %s", exc)
            return {"error": f"Transaction failed: {exc}"}

    async def wait_for_receipt(self, tx_hash: str, timeout: int = 60) -> dict[str, Any]:
        """Wait for a transaction receipt."""
        if not self._w3:
            return {"error": "Wallet not connected"}
        try:
            import asyncio
            receipt = await asyncio.to_thread(
                self._w3.eth.wait_for_transaction_receipt,
                tx_hash, timeout=timeout,
            )
            return {
                "tx_hash": tx_hash,
                "status": "confirmed" if receipt["status"] == 1 else "failed",
                "block_number": receipt["blockNumber"],
                "gas_used": receipt["gasUsed"],
                "explorer_url": f"https://sepolia.etherscan.io/tx/{tx_hash}",
            }
        except Exception as exc:
            return {"error": f"Receipt wait failed: {exc}"}
