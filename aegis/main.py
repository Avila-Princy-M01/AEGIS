"""AEGIS — main entry point.

Run standalone:
    python -m aegis.main "Protect my Uniswap positions and send to my family if I disappear"

Or start the full dashboard server:
    python -m aegis.server
"""

from __future__ import annotations

import asyncio
import os
import sys

from dotenv import load_dotenv

from aegis.orchestrator import AegisOrchestrator

load_dotenv()


async def main(command: str | None = None) -> None:
    """Deploy AEGIS from a natural language command."""
    cmd = command or " ".join(sys.argv[1:]) or (
        "Protect my Uniswap positions from crashes, "
        "compound my fees daily, "
        "and if I don't check in for 30 days, "
        "send everything to my family."
    )

    print("\n" + "═" * 60)
    print("  🛡️  AEGIS — Autonomous Wallet Guardian")
    print("═" * 60)
    print(f"\n  Command: \"{cmd}\"\n")
    print("  Deploying 4 agents...\n")

    orchestrator = AegisOrchestrator()
    api_key = os.environ.get("GROQ_API_KEY", "")
    status = await orchestrator.deploy(cmd, api_key=api_key)

    print("  ✅ Guard Agent     — monitoring threats")
    print("  ✅ Grow Agent      — compounding fees")
    print("  ✅ Rebalance Agent — watching tick range")
    print("  ✅ Legacy Agent    — watching inactivity")
    print(f"\n{'═' * 60}")
    print("  All agents running. Press Ctrl+C to stop.")
    print(f"{'═' * 60}\n")

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n  Stopping agents...")
        await orchestrator.stop()
        print("  AEGIS shutdown complete.\n")


if __name__ == "__main__":
    asyncio.run(main())
