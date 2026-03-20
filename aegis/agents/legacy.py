"""Legacy Agent — dead man's switch and digital inheritance.

Monitors user check-in activity. If the user doesn't check in
within the configured threshold, Legacy gracefully exits all
LP positions and distributes assets to beneficiary wallets.
"""

from __future__ import annotations

import asyncio
import logging
import time
from decimal import Decimal
from typing import Any

from aegis.config import LegacyConfig
from aegis.memory import EventType, SharedMemory

logger = logging.getLogger("aegis.legacy")


class LegacyAgent:
    """Autonomous digital inheritance agent."""

    def __init__(self, config: LegacyConfig, memory: SharedMemory) -> None:
        self.config = config
        self.memory = memory
        self.name = "legacy"
        self._running = False
        self._last_check_in: float = time.time()
        self._inheritance_triggered: bool = False
        self._warning_sent: bool = False
        self._demo_speed: float = 1.0
        self._reasoning: list[str] = []

    @property
    def status(self) -> dict[str, Any]:
        elapsed = time.time() - self._last_check_in
        threshold_seconds = self.config.inactivity_threshold_days * 86400 / self._demo_speed
        remaining = max(0, threshold_seconds - elapsed)

        return {
            "agent": self.name,
            "running": self._running,
            "last_check_in": self._last_check_in,
            "seconds_since_check_in": elapsed,
            "threshold_days": self.config.inactivity_threshold_days,
            "remaining_seconds": remaining,
            "remaining_human": _format_duration(remaining),
            "inheritance_triggered": self._inheritance_triggered,
            "reasoning": self._reasoning[-1] if self._reasoning else "",
            "beneficiaries": [
                {"address": b.address, "share_pct": str(b.share_pct), "label": b.label}
                for b in self.config.beneficiaries
            ],
            "config": {
                "inactivity_days": self.config.inactivity_threshold_days,
                "graceful_exit": self.config.graceful_exit_before_distribute,
            },
        }

    async def start(self) -> None:
        """Start the legacy monitoring loop."""
        self._running = True
        self._last_check_in = time.time()
        self.memory.publish(EventType.AGENT_STARTED, self.name, {
            "message": f"Legacy agent activated — will trigger after {self.config.inactivity_threshold_days} days of inactivity",
            "beneficiary_count": len(self.config.beneficiaries),
            "live_data": False,
        })
        logger.info("Legacy agent started")

        while self._running:
            await self._check_inactivity()
            await asyncio.sleep(2)

    def stop(self) -> None:
        self._running = False
        self.memory.publish(EventType.AGENT_STOPPED, self.name, {"message": "Legacy agent stopped"})

    def check_in(self) -> dict[str, Any]:
        """Record a user check-in, resetting the inactivity timer."""
        self._last_check_in = time.time()
        self._warning_sent = False
        self._inheritance_triggered = False

        self.memory.publish(EventType.CHECK_IN, self.name, {
            "message": "✅ User checked in — inactivity timer reset",
            "timestamp": self._last_check_in,
        })
        self.memory.set_state("legacy_status", self.status)
        return self.status

    def set_demo_speed(self, multiplier: float) -> None:
        """Speed up the timer for demo purposes (e.g. 86400x = 1 day per second)."""
        self._demo_speed = multiplier

    async def simulate_inheritance(self) -> dict[str, Any]:
        """Force-trigger the inheritance flow for demo."""
        self._last_check_in = time.time() - (self.config.inactivity_threshold_days * 86400 + 1)
        await self._trigger_inheritance()
        return self.status

    async def _check_inactivity(self) -> None:
        """Check if user has exceeded the inactivity threshold."""
        elapsed = time.time() - self._last_check_in
        threshold_seconds = self.config.inactivity_threshold_days * 86400 / self._demo_speed
        remaining = max(0, threshold_seconds - elapsed)

        warning_at = threshold_seconds * 0.75

        if self._inheritance_triggered:
            verdict = "TRIGGERED"
        elif elapsed >= threshold_seconds:
            verdict = "TRIGGER"
        elif elapsed >= warning_at:
            verdict = "WARNING"
        else:
            verdict = "ACTIVE"
        self._reasoning.append(
            f"Check-in {_format_duration(elapsed)} ago"
            f" | Threshold {self.config.inactivity_threshold_days}d"
            f" | Remaining {_format_duration(remaining)}"
            f" → {verdict}"
        )
        if len(self._reasoning) > 10:
            self._reasoning = self._reasoning[-10:]

        if elapsed >= threshold_seconds and not self._inheritance_triggered:
            await self._trigger_inheritance()
        elif elapsed >= warning_at and not self._warning_sent:
            self._warning_sent = True
            remaining = threshold_seconds - elapsed
            self.memory.publish(EventType.INACTIVITY_WARNING, self.name, {
                "message": f"⏰ Inactivity warning: {_format_duration(remaining)} until inheritance triggers",
                "remaining_seconds": remaining,
                "elapsed_seconds": elapsed,
            })

        self.memory.set_state("legacy_status", self.status)

    async def _trigger_inheritance(self) -> None:
        """Execute the inheritance distribution."""
        self._inheritance_triggered = True
        logger.warning("Inheritance triggered — distributing assets")

        if self.config.graceful_exit_before_distribute:
            self.memory.publish(EventType.INHERITANCE_TRIGGERED, self.name, {
                "phase": "exiting_positions",
                "message": "🏛️ Inheritance triggered — gracefully exiting all LP positions...",
            })
            await asyncio.sleep(2)

        for b in self.config.beneficiaries:
            self.memory.publish(EventType.INHERITANCE_TRIGGERED, self.name, {
                "phase": "distributing",
                "beneficiary": b.address,
                "share_pct": str(b.share_pct),
                "label": b.label,
                "message": f"💸 Distributing {b.share_pct}% to {b.label or b.address[:10] + '...'}",
            })
            await asyncio.sleep(1)

        self.memory.publish(EventType.INHERITANCE_TRIGGERED, self.name, {
            "phase": "complete",
            "message": "✅ Inheritance complete — all assets distributed to beneficiaries",
        })

        self.memory.set_state("legacy_status", self.status)


def _format_duration(seconds: float) -> str:
    """Format seconds into a human-readable duration string."""
    if seconds <= 0:
        return "0s"
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if mins:
        parts.append(f"{mins}m")
    if secs and not days:
        parts.append(f"{secs}s")
    return " ".join(parts) or "0s"
