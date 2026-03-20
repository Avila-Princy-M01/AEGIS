"""AEGIS Dashboard API — FastAPI server with WebSocket support.

Endpoints:
    POST  /api/deploy              — deploy agents from natural language command
    GET   /api/status              — full system status
    GET   /api/events              — recent memory events
    GET   /api/price-history       — recent ETH price snapshots for chart
    POST  /api/check-in            — user check-in (resets Legacy timer)
    POST  /api/simulate/threat     — trigger simulated threat (demo)
    POST  /api/simulate/inherit    — trigger simulated inheritance (demo)
    POST  /api/simulate/rebalance  — trigger simulated out-of-range (demo)
    POST  /api/switch-chain        — switch blockchain (ethereum / base)
    POST  /api/demo-speed          — set Legacy timer speed (demo)
    POST  /api/stop                — stop all agents
    WS    /ws/feed                 — real-time event stream
"""

from __future__ import annotations

import asyncio
import json
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from aegis.memory import MemoryEvent
from aegis.orchestrator import AegisOrchestrator


class DeployRequest(BaseModel):
    command: str


class SimulateRequest(BaseModel):
    threat_type: str = "price_drop"


class SwitchChainRequest(BaseModel):
    chain: str = "ethereum"


class DemoSpeedRequest(BaseModel):
    multiplier: float = 86400.0


class ConnectionManager:
    """Manages WebSocket connections for real-time event streaming."""

    def __init__(self) -> None:
        self.connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.connections.append(ws)

    def disconnect(self, ws: WebSocket) -> None:
        if ws in self.connections:
            self.connections.remove(ws)

    async def broadcast(self, data: dict[str, Any]) -> None:
        dead: list[WebSocket] = []
        for ws in self.connections:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


ws_manager = ConnectionManager()
orchestrator = AegisOrchestrator()


def _on_memory_event(event: MemoryEvent) -> None:
    """Push memory events to all WebSocket clients."""
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(ws_manager.broadcast(event.to_dict()))
    except RuntimeError:
        pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    orchestrator.memory.subscribe(_on_memory_event)
    yield
    await orchestrator.stop()


app = FastAPI(
    title="AEGIS Dashboard API",
    description="Autonomous Wallet Guardian — real-time multi-agent dashboard",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/deploy")
async def deploy(req: DeployRequest) -> dict[str, Any]:
    """Deploy all AEGIS agents from a natural language command."""
    if orchestrator._started:
        await orchestrator.stop()
    api_key = os.environ.get("GROQ_API_KEY", "")
    status = await orchestrator.deploy(req.command, api_key=api_key)
    return {"success": True, "status": status}


@app.get("/api/status")
async def get_status() -> dict[str, Any]:
    return orchestrator.status


@app.get("/api/events")
async def get_events(limit: int = 50, agent: str | None = None) -> list[dict[str, Any]]:
    events = orchestrator.memory.get_events(limit=limit, agent=agent)
    return [e.to_dict() for e in events]


@app.post("/api/check-in")
async def check_in() -> dict[str, Any]:
    return orchestrator.check_in()


@app.post("/api/simulate/threat")
async def simulate_threat(req: SimulateRequest) -> dict[str, Any]:
    return await orchestrator.simulate_threat(req.threat_type)


@app.post("/api/simulate/inherit")
async def simulate_inherit() -> dict[str, Any]:
    return await orchestrator.simulate_inheritance()


@app.post("/api/simulate/rebalance")
async def simulate_out_of_range() -> dict[str, Any]:
    return await orchestrator.simulate_out_of_range()


@app.get("/api/price-history")
async def get_price_history() -> list[dict[str, Any]]:
    return orchestrator.get_price_history()


@app.post("/api/switch-chain")
async def switch_chain(req: SwitchChainRequest) -> dict[str, Any]:
    """Switch to a different blockchain and re-deploy all agents."""
    return await orchestrator.switch_chain(req.chain)


@app.post("/api/demo-speed")
async def set_demo_speed(req: DemoSpeedRequest) -> dict[str, Any]:
    orchestrator.set_demo_speed(req.multiplier)
    return {"multiplier": req.multiplier}


@app.post("/api/stop")
async def stop_agents() -> dict[str, Any]:
    await orchestrator.stop()
    return {"stopped": True}


@app.websocket("/ws/feed")
async def websocket_feed(ws: WebSocket) -> None:
    await ws_manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(ws)
    except Exception:
        ws_manager.disconnect(ws)


def run_server() -> None:
    """Start the AEGIS dashboard server."""
    import uvicorn
    print("\n  🛡️  AEGIS Dashboard Server")
    print("  http://localhost:8000\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


if __name__ == "__main__":
    run_server()
