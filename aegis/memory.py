"""Shared memory for inter-agent communication.

All five AEGIS agents (Guard, Grow, Rebalance, MEV, Legacy) read and write to
this shared memory store. It provides typed events and a pub/sub mechanism
so agents can react to each other's signals in real time.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable


class EventType(str, Enum):
    THREAT_DETECTED = "threat_detected"
    THREAT_CLEARED = "threat_cleared"
    POSITION_LOCKED = "position_locked"
    POSITION_UNLOCKED = "position_unlocked"
    FEES_COMPOUNDED = "fees_compounded"
    VAULT_DEPOSIT = "vault_deposit"
    CHECK_IN = "check_in"
    INACTIVITY_WARNING = "inactivity_warning"
    INHERITANCE_TRIGGERED = "inheritance_triggered"
    AGENT_STARTED = "agent_started"
    AGENT_STOPPED = "agent_stopped"
    POSITION_OUT_OF_RANGE = "position_out_of_range"
    REBALANCE_SUGGESTED = "rebalance_suggested"
    GAS_TOO_HIGH = "gas_too_high"
    MEV_DETECTED = "mev_detected"
    MEV_CLEARED = "mev_cleared"
    DRY_RUN_TX = "dry_run_tx"
    ENS_RESOLVED = "ens_resolved"
    LIDO_YIELD_UPDATE = "lido_yield_update"
    CROSS_POOL_ALLOCATION = "cross_pool_allocation"
    BACKTEST_RESULT = "backtest_result"
    SYSTEM = "system"


@dataclass
class MemoryEvent:
    """A single event in the shared memory log."""

    event_type: str
    agent: str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> MemoryEvent:
        return cls(**d)


class SharedMemory:
    """File-backed shared memory with pub/sub for inter-agent events.

    Events are persisted to disk so they survive restarts and can
    be displayed in the dashboard via the API.
    """

    def __init__(self, workspace_dir: str | Path = "./workspace") -> None:
        self._workspace = Path(workspace_dir).resolve()
        self._memory_dir = self._workspace / ".aegis_memory"
        self._memory_dir.mkdir(parents=True, exist_ok=True)

        self._events: list[MemoryEvent] = []
        self._subscribers: list[Callable[[MemoryEvent], None]] = []
        self._state: dict[str, Any] = {}

        self._load()

    def publish(self, event_type: EventType | str, agent: str, data: dict[str, Any] | None = None) -> MemoryEvent:
        """Publish an event to shared memory and notify subscribers."""
        event = MemoryEvent(
            event_type=str(event_type.value if isinstance(event_type, EventType) else event_type),
            agent=agent,
            data=data or {},
        )
        self._events.append(event)
        self._save_events()

        for subscriber in self._subscribers:
            try:
                subscriber(event)
            except Exception:
                pass

        return event

    def subscribe(self, callback: Callable[[MemoryEvent], None]) -> None:
        """Register a callback for new events."""
        self._subscribers.append(callback)

    def get_events(self, limit: int = 50, agent: str | None = None, event_type: str | None = None) -> list[MemoryEvent]:
        """Query events with optional filters."""
        events = self._events
        if agent:
            events = [e for e in events if e.agent == agent]
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return events[-limit:]

    def get_latest_event(self, event_type: str) -> MemoryEvent | None:
        """Get the most recent event of a given type."""
        for event in reversed(self._events):
            if event.event_type == event_type:
                return event
        return None

    def set_state(self, key: str, value: Any) -> None:
        """Set a persistent state value."""
        self._state[key] = value
        self._save_state()

    def get_state(self, key: str, default: Any = None) -> Any:
        """Get a persistent state value."""
        return self._state.get(key, default)

    def get_all_state(self) -> dict[str, Any]:
        """Get all state values."""
        return dict(self._state)

    def _save_events(self) -> None:
        path = self._memory_dir / "events.json"
        data = [e.to_dict() for e in self._events[-500:]]
        path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    def _save_state(self) -> None:
        path = self._memory_dir / "state.json"
        path.write_text(json.dumps(self._state, indent=2, default=str), encoding="utf-8")

    def _load(self) -> None:
        events_path = self._memory_dir / "events.json"
        if events_path.exists():
            try:
                raw = json.loads(events_path.read_text(encoding="utf-8"))
                self._events = [MemoryEvent.from_dict(e) for e in raw]
            except (json.JSONDecodeError, KeyError):
                self._events = []

        state_path = self._memory_dir / "state.json"
        if state_path.exists():
            try:
                self._state = json.loads(state_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                self._state = {}
