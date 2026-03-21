"""ENS (Ethereum Name Service) name resolution for AEGIS.

Resolves .eth names to Ethereum addresses using the ENS public resolver.
Falls back gracefully if web3 is not installed or ENS resolution fails.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any

try:
    from web3 import Web3
    from web3.providers import HTTPProvider

    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False

logger = logging.getLogger("aegis.ens")

# ── Well-known addresses ──────────────────────────────────────────

ENS_REGISTRY = "0x00000000000C2E074eC69A0dFb2997BA6C7d2e1e"
ENS_PUBLIC_RESOLVER = "0x231b0Ee14048e9dCcD1d247744d114a4EB5E8E63"

CHAIN_RPC: dict[str, dict[str, Any]] = {
    "ethereum": {
        "rpc_public": "https://eth.llamarpc.com",
        "rpc_fallbacks": [
            "https://eth.llamarpc.com",
            "https://ethereum-rpc.publicnode.com",
            "https://1rpc.io/eth",
            "https://eth.drpc.org",
            "https://cloudflare-eth.com",
            "https://rpc.mevblocker.io",
        ],
    },
}

DEFAULT_CACHE_TTL = 300


@dataclass
class _CacheEntry:
    """A single cached ENS resolution result."""

    address: str | None
    timestamp: float


class ENSResolver:
    """Resolves ENS names to Ethereum addresses with caching.

    Falls back gracefully if web3 is not installed or RPC is unreachable.
    """

    def __init__(
        self,
        chain: str = "ethereum",
        alchemy_key: str = "",
        cache_ttl: int = DEFAULT_CACHE_TTL,
    ) -> None:
        self.chain = chain
        self.live = False
        self._w3: Any = None
        self._ens: Any = None
        self._cache: dict[str, _CacheEntry] = {}
        self._cache_ttl = cache_ttl
        self._rpc_urls: list[str] = []
        self._rpc_index: int = 0

        if not WEB3_AVAILABLE:
            logger.warning("web3 not installed — ENS resolution unavailable")
            return

        preset = CHAIN_RPC.get(chain)
        if not preset:
            logger.warning("Unknown chain '%s' — ENS resolution unavailable", chain)
            return

        if alchemy_key:
            alchemy_url = f"https://eth-mainnet.g.alchemy.com/v2/{alchemy_key}"
            self._rpc_urls = [alchemy_url]
            self._rpc_urls.extend(preset.get("rpc_fallbacks", [preset["rpc_public"]]))
        else:
            self._rpc_urls = list(preset.get("rpc_fallbacks", [preset["rpc_public"]]))

        rpc_url = self._rpc_urls[0]

        try:
            self._w3 = Web3(HTTPProvider(rpc_url, request_kwargs={"timeout": 10}))
            if self._w3.is_connected():
                from web3 import Web3 as _W3

                self._ens = _W3(HTTPProvider(rpc_url, request_kwargs={"timeout": 10})).ens
                self.live = True
                logger.info(
                    "ENS resolver connected to %s [%d RPC fallbacks]",
                    chain,
                    len(self._rpc_urls),
                )
            else:
                logger.warning("RPC not reachable — ENS resolution unavailable")
        except Exception as exc:
            logger.warning("Failed to connect to %s RPC: %s — ENS unavailable", chain, exc)

    def _rotate_rpc(self) -> None:
        """Switch to the next fallback RPC endpoint on rate-limit errors."""
        if len(self._rpc_urls) <= 1:
            return
        self._rpc_index = (self._rpc_index + 1) % len(self._rpc_urls)
        new_url = self._rpc_urls[self._rpc_index]
        logger.info("⚡ Rotating RPC → %s", new_url)
        try:
            self._w3 = Web3(HTTPProvider(new_url, request_kwargs={"timeout": 10}))
            self._ens = self._w3.ens
        except Exception as exc:
            logger.warning("RPC rotation failed for %s: %s", new_url, exc)

    def _call_with_retry(
        self,
        fn: Any,
        *args: Any,
        max_retries: int = 3,
        backoff_base: float = 0.5,
        label: str = "ENS call",
    ) -> Any:
        """Call *fn* with exponential backoff on transient RPC errors.

        On 429 (rate limit) errors, rotates to the next fallback RPC
        endpoint before retrying.
        """
        rate_limit_patterns = ("429", "rate limit", "too many requests", "unauthorized")
        transient_patterns = (
            "header not found", "request failed", "connection",
            "timeout", "rate limit", "429", "502", "503",
            "unauthorized",
        )
        last_exc: Exception | None = None

        for attempt in range(max_retries):
            try:
                return fn(*args)
            except Exception as exc:
                last_exc = exc
                err_str = str(exc).lower()
                is_rate_limited = any(p in err_str for p in rate_limit_patterns)
                is_transient = any(p in err_str for p in transient_patterns)

                if not is_transient:
                    raise

                if attempt < max_retries - 1:
                    if is_rate_limited:
                        self._rotate_rpc()
                        delay = 0.3
                    else:
                        delay = backoff_base * (2 ** attempt)
                    logger.debug(
                        "%s attempt %d/%d failed (%s) — retrying in %.1fs",
                        label, attempt + 1, max_retries, exc, delay,
                    )
                    time.sleep(delay)
                else:
                    logger.warning(
                        "%s failed after %d attempts: %s",
                        label, max_retries, exc,
                    )

        raise last_exc  # type: ignore[misc]

    def _get_cached(self, name: str) -> str | None | bool:
        """Return cached address or False if not cached / expired."""
        entry = self._cache.get(name)
        if entry is None:
            return False
        if time.time() - entry.timestamp > self._cache_ttl:
            del self._cache[name]
            return False
        return entry.address

    def _set_cached(self, name: str, address: str | None) -> None:
        self._cache[name] = _CacheEntry(address=address, timestamp=time.time())

    def resolve_sync(self, name: str) -> str | None:
        """Resolve an ENS name to an address synchronously."""
        if not self.live or not self._ens:
            return None

        name = name.lower().strip()
        if not is_ens_name(name):
            return None

        cached = self._get_cached(name)
        if cached is not False:
            logger.debug("ENS cache hit: %s → %s", name, cached)
            return cached  # type: ignore[return-value]

        try:
            address = self._call_with_retry(
                self._ens.address,
                name,
                label=f"ens.address({name})",
            )
            result = str(address) if address else None
            self._set_cached(name, result)
            logger.info("Resolved %s → %s", name, result or "None")
            return result
        except Exception as exc:
            logger.warning("ENS resolution failed for '%s': %s", name, exc)
            self._set_cached(name, None)
            return None

    async def resolve(self, name: str) -> str | None:
        """Resolve an ENS name to an address asynchronously."""
        return await asyncio.to_thread(self.resolve_sync, name)

    def clear_cache(self) -> None:
        """Clear all cached ENS resolutions."""
        self._cache.clear()
        logger.debug("ENS cache cleared")

    @property
    def cache_size(self) -> int:
        return len(self._cache)


# ── Module-level singleton ────────────────────────────────────────

_default_resolver: ENSResolver | None = None


def _get_resolver() -> ENSResolver:
    global _default_resolver
    if _default_resolver is None:
        _default_resolver = ENSResolver()
    return _default_resolver


def is_ens_name(name: str) -> bool:
    """Check if a string looks like an ENS name."""
    if not name or not isinstance(name, str):
        return False
    name = name.strip().lower()
    return name.endswith(".eth") and len(name) > 4 and "." in name


async def resolve_ens_name(name: str, chain: str = "ethereum") -> str | None:
    """Resolve an ENS name to an Ethereum address.

    Uses a module-level resolver with caching. Returns None if
    resolution fails or web3 is not available.
    """
    global _default_resolver
    resolver = _get_resolver()
    if resolver.chain != chain:
        _default_resolver = ENSResolver(chain=chain)
        resolver = _default_resolver
    return await resolver.resolve(name)
