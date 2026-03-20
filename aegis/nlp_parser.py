"""NLP parser — converts natural language commands into AEGIS config.

Uses the Groq API (llama-3.3-70b) to parse a single English sentence
into structured strategy parameters for the Guard, Grow, and Legacy agents.
"""

from __future__ import annotations

import json
import os
from decimal import Decimal
from typing import Any

import httpx

from aegis.config import AegisConfig, Beneficiary, GrowConfig, GuardConfig, LegacyConfig

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


async def parse_command(command: str, api_key: str | None = None, model: str = "llama-3.3-70b-versatile") -> AegisConfig:
    """Parse a natural language command into an AegisConfig."""
    key = api_key or os.environ.get("GROQ_API_KEY", "")
    if not key:
        return _fallback_parse(command)

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


def _extract_json(text: str) -> dict[str, Any]:
    """Extract a JSON object from LLM output, handling markdown fences."""
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
            return json.loads(text[start:end])
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
    """Simple keyword-based fallback when no API key is available."""
    config = AegisConfig.default()
    lower = command.lower()

    if "aggressive" in lower:
        config.guard.price_drop_alert_pct = Decimal("5.0")
        config.guard.impermanent_loss_threshold_pct = Decimal("5.0")
    elif "conservative" in lower:
        config.guard.price_drop_alert_pct = Decimal("25.0")

    if "daily" in lower:
        config.grow.compound_frequency_hours = 24
    elif "hourly" in lower:
        config.grow.compound_frequency_hours = 1
    elif "weekly" in lower:
        config.grow.compound_frequency_hours = 168

    for word in lower.split():
        if word.startswith("0x") and len(word) >= 42:
            config.legacy.beneficiaries.append(
                Beneficiary(address=word[:42], label="beneficiary")
            )

    return config
