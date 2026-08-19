"""NLP parser — converts natural language commands into AEGIS config.

Uses the Groq API (llama-3.3-70b) to parse a single English sentence
into structured strategy parameters for the Guard, Grow, and Legacy agents.
"""

from __future__ import annotations

import json
import logging
import os
from decimal import Decimal
from typing import Any

import httpx

from aegis.config import AegisConfig, Beneficiary, GrowConfig, GuardConfig, LegacyConfig

logger = logging.getLogger("aegis.nlp")

SYSTEM_PROMPT = """You are AEGIS, an AI that parses natural language into DeFi protection strategies.

Given a user command, extract parameters for three agents:
1. **Guard**: Threat detection for Uniswap LP positions (price drop thresholds, auto-exit rules)
2. **Grow**: Fee compounding and vault management (compound frequency, savings %)
3. **Legacy**: Dead man's switch / digital will (inactivity days, beneficiary addresses)

Respond ONLY with valid JSON matching this schema:
{
  "guard": {
    "impermanent_loss_threshold_pct": <number>,
    "price_drop_alert_pct": <number>,
    "auto_exit_on_threat": <boolean>
  },
  "grow": {
    "auto_compound_enabled": <boolean>,
    "compound_frequency_hours": <number>,
    "savings_sweep_pct": <number>
  },
  "legacy": {
    "inactivity_threshold_days": <number>,
    "beneficiaries": [{"address": "<0x...>", "share_pct": <number>, "label": "<name>"}]
  }
}

Use sensible defaults for any values not explicitly mentioned.
If no beneficiary address is given, use an empty list.
Do NOT include any text outside the JSON object."""


def _get_groq_keys(primary_key: str | None = None) -> list[str]:
    """Collect all available Groq API keys for rotation."""
    keys: list[str] = []
    if primary_key:
        keys.append(primary_key)
    for env_var in ["GROQ_API_KEY", "GROQ_API_KEY_2", "GROQ_API_KEY_3"]:
        k = os.environ.get(env_var, "")
        if k and k not in keys:
            keys.append(k)
    return keys


async def parse_command(command: str, api_key: str | None = None, model: str = "openai/gpt-oss-120b") -> AegisConfig:
    """Parse a natural language command into an AegisConfig.

    Tries multiple Groq API keys on rate-limit (429) errors.
    """
    keys = _get_groq_keys(api_key)
    if not keys:
        return _fallback_parse(command)

    last_exc: Exception | None = None
    for i, key in enumerate(keys):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": command},
                        ],
                        "max_tokens": 1024,
                        "temperature": 0.1,
                    },
                )
                resp.raise_for_status()
                data = resp.json()

            text = data["choices"][0]["message"]["content"].strip()
            parsed = _extract_json(text)
            return _dict_to_config(parsed)
        except httpx.HTTPStatusError as exc:
            last_exc = exc
            status = exc.response.status_code
            logger.warning(
                "Groq HTTP %d on key ...%s (%d/%d) — %s",
                status, key[-4:], i + 1, len(keys),
                "trying next key" if i < len(keys) - 1 else "no more keys",
            )
            continue
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            last_exc = exc
            logger.warning(
                "Groq network error on key ...%s (%d/%d): %s — %s",
                key[-4:], i + 1, len(keys), type(exc).__name__,
                "trying next key" if i < len(keys) - 1 else "no more keys",
            )
            continue
        except Exception as exc:
            last_exc = exc
            logger.warning(
                "Groq unexpected error on key ...%s (%d/%d): %s — %s",
                key[-4:], i + 1, len(keys), exc,
                "trying next key" if i < len(keys) - 1 else "no more keys",
            )
            continue

    logger.warning("All %d Groq API keys exhausted (last error: %s) — falling back to keyword parser", len(keys), last_exc)
    return _fallback_parse(command)


def _extract_json(text: str) -> dict[str, Any]:
    """Extract a JSON object from LLM output, handling markdown fences and bad JSON."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                # Attempt to load the JSON block
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                # If it's hopelessly malformed, don't crash, return empty so defaults are used
                logger.warning("LLM hallucinates bad JSON, falling back to defaults.")
                return {}
        return {}


def _dict_to_config(d: dict[str, Any]) -> AegisConfig:
    """Convert parsed dict into AegisConfig."""
    guard_d = d.get("guard", {})
    grow_d = d.get("grow", {})
    legacy_d = d.get("legacy", {})

    guard = GuardConfig(
        impermanent_loss_threshold_pct=Decimal(str(guard_d.get("impermanent_loss_threshold_pct", 10))),
        price_drop_alert_pct=Decimal(str(guard_d.get("price_drop_alert_pct", 15))),
        auto_exit_on_threat=guard_d.get("auto_exit_on_threat", True),
    )

    grow = GrowConfig(
        auto_compound_enabled=grow_d.get("auto_compound_enabled", True),
        compound_frequency_hours=grow_d.get("compound_frequency_hours", 24),
        savings_sweep_pct=Decimal(str(grow_d.get("savings_sweep_pct", 10))),
    )

    beneficiaries = [
        Beneficiary(
            address=b.get("address", ""),
            share_pct=Decimal(str(b.get("share_pct", 100))),
            label=b.get("label", ""),
        )
        for b in legacy_d.get("beneficiaries", [])
    ]

    legacy = LegacyConfig(
        inactivity_threshold_days=legacy_d.get("inactivity_threshold_days", 30),
        beneficiaries=beneficiaries,
    )

    return AegisConfig(guard=guard, grow=grow, legacy=legacy)


def _fallback_parse(command: str) -> AegisConfig:
    """Keyword-based fallback when no API key is available or all APIs fail."""
    import re
    config = AegisConfig.default()
    lower = command.lower()

    if "aggressive" in lower:
        config.guard.price_drop_alert_pct = Decimal("5.0")
        config.guard.impermanent_loss_threshold_pct = Decimal("5.0")
    elif "conservative" in lower:
        config.guard.price_drop_alert_pct = Decimal("25.0")
        
    # Attempt to extract explicit percentages for thresholds
    pct_matches = re.findall(r'(\d+(?:\.\d+)?)\s*(?:%|percent)', lower)
    if pct_matches:
        try:
            val = Decimal(pct_matches[0])
            if val > 0 and val < 100:
                # Naive assignment to primary thresholds if a percentage is mentioned
                config.guard.price_drop_alert_pct = val
                config.guard.impermanent_loss_threshold_pct = val
                config.grow.savings_sweep_pct = val
        except:
            pass

    if "daily" in lower:
        config.grow.compound_frequency_hours = 24
    elif "hourly" in lower:
        config.grow.compound_frequency_hours = 1
    elif "weekly" in lower:
        config.grow.compound_frequency_hours = 168

    # Extract all ethereum addresses safely
    eth_addresses = re.findall(r'(0x[a-f0-9]{40})', lower)
    for addr in eth_addresses:
        # Check to avoid duplicates
        if not any(b.address.lower() == addr for b in config.legacy.beneficiaries):
            config.legacy.beneficiaries.append(
                Beneficiary(address=addr, label="beneficiary")
            )

    return config
