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
    POST  /api/simulate/mev        — trigger simulated MEV attack (demo)
    POST  /api/switch-chain        — switch blockchain (ethereum / base)
    POST  /api/demo-speed          — set Legacy timer speed (demo)
    POST  /api/stop                — stop all agents
    GET   /api/analytics/lido      — Lido yield comparison
    GET   /api/analytics/pools     — cross-pool capital allocation
    POST  /api/analytics/backtest  — run historical backtest
    POST  /api/swap-quote          — get real Uniswap Trading API swap quote
    POST  /api/swap-execute         — execute a real swap on Sepolia testnet
    WS    /ws/feed                 — real-time event stream
"""

from __future__ import annotations

import asyncio
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

import logging

import httpx

from aegis.memory import MemoryEvent
from aegis.orchestrator import AegisOrchestrator

logger = logging.getLogger("aegis.server")

KEEP_ALIVE_INTERVAL = 600  # 10 minutes
DEFAULT_COMMAND = "Protect my ETH/USDC position, compound fees weekly, alert on 10% IL, 30 day dead man switch"

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"


class DeployRequest(BaseModel):
    command: str


class SimulateRequest(BaseModel):
    threat_type: str = "price_drop"


class SwitchChainRequest(BaseModel):
    chain: str = "ethereum"


class SimulateMevRequest(BaseModel):
    attack_type: str = "sandwich"


class DemoSpeedRequest(BaseModel):
    multiplier: float = 86400.0


class BacktestRequest(BaseModel):
    days: int = 30


class SwapQuoteRequest(BaseModel):
    token_in: str = "WETH"
    token_out: str = "USDC"
    amount: str = "1000000000000000000"
    chain: str = ""


class SwapExecuteRequest(BaseModel):
    token_in: str = "WETH"
    token_out: str = "USDC"
    amount: str = "100000000000000000"


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


async def _auto_deploy() -> None:
    """Auto-deploy agents on server startup so judges always see live data.

    Retries up to 5 times with increasing delays to handle transient RPC
    failures that are common right after a cold start on Render free tier.
    """
    await asyncio.sleep(3)
    for attempt in range(5):
        if orchestrator._started:
            return
        try:
            api_key = os.environ.get("GROQ_API_KEY", "")
            await orchestrator.deploy(DEFAULT_COMMAND, api_key=api_key)
            logger.info("Auto-deployed agents on startup (attempt %d)", attempt + 1)
            return
        except Exception as exc:
            delay = 5 * (attempt + 1)
            logger.warning(
                "Auto-deploy attempt %d/5 failed: %s — retrying in %ds",
                attempt + 1, exc, delay,
            )
            await asyncio.sleep(delay)
    logger.error("Auto-deploy exhausted all retries")


async def _keep_alive() -> None:
    """Ping our own /api/status every 10 min to prevent Render free-tier sleep.

    Also auto-recovers by re-deploying if agents stopped unexpectedly.
    """
    port = int(os.environ.get("PORT", 8000))
    external = os.environ.get("RENDER_EXTERNAL_URL", f"http://localhost:{port}")
    url = f"{external}/api/status"
    async with httpx.AsyncClient(timeout=15.0) as client:
        while True:
            await asyncio.sleep(KEEP_ALIVE_INTERVAL)
            try:
                await client.get(url)
            except Exception:
                pass
            if not orchestrator._started:
                try:
                    api_key = os.environ.get("GROQ_API_KEY", "")
                    await orchestrator.deploy(DEFAULT_COMMAND, api_key=api_key)
                    logger.info("Auto-recovered: re-deployed agents")
                except Exception:
                    pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    orchestrator.memory.subscribe(_on_memory_event)
    ping_task = asyncio.create_task(_keep_alive())
    deploy_task = asyncio.create_task(_auto_deploy())
    yield
    deploy_task.cancel()
    ping_task.cancel()
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


@app.post("/api/simulate/mev")
async def simulate_mev(req: SimulateMevRequest) -> dict[str, Any]:
    return await orchestrator.simulate_mev_attack(req.attack_type)


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


@app.get("/api/analytics/lido")
async def lido_yield() -> dict[str, Any]:
    """Compare LP yield vs Lido staking yield."""
    return await orchestrator.compare_lido_yield()


@app.get("/api/analytics/pools")
async def pool_allocation() -> dict[str, Any]:
    """Get optimal cross-pool capital allocation."""
    return await orchestrator.allocate_cross_pool()


@app.post("/api/analytics/backtest")
async def run_backtest(req: BacktestRequest) -> dict[str, Any]:
    """Run a historical backtest simulation."""
    return await orchestrator.run_backtest(req.days)


@app.post("/api/swap-quote")
async def swap_quote(req: SwapQuoteRequest) -> dict[str, Any]:
    """Get a real swap quote from the Uniswap Trading API."""
    return await orchestrator.get_swap_quote(
        token_in=req.token_in,
        token_out=req.token_out,
        amount=req.amount,
        chain=req.chain,
    )


@app.post("/api/swap-execute")
async def swap_execute(req: SwapExecuteRequest) -> dict[str, Any]:
    """Execute a real swap on Sepolia testnet via Uniswap Trading API."""
    return await orchestrator.execute_swap(
        token_in=req.token_in,
        token_out=req.token_out,
        amount=req.amount,
    )


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


# ── Serve frontend static files in production ─────────────────────

if FRONTEND_DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="static-assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str) -> FileResponse:
        """Serve the SPA index.html for all non-API routes."""
        file_path = FRONTEND_DIST / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(FRONTEND_DIST / "index.html"))


def run_server() -> None:
    """Start the AEGIS dashboard server."""
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print("\n  🛡️  AEGIS Dashboard Server")
    print(f"  http://localhost:{port}")
    if FRONTEND_DIST.is_dir():
        print("  📦 Serving frontend from frontend/dist/")
    print()
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    run_server()
