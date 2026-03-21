# AEGIS Demo Script — 60-Second Screen Recording

## Setup Before Recording
1. Start the backend: `python -m aegis.server`
2. Start the frontend: `cd frontend && npm run dev`
3. Open http://localhost:5173 in Chrome (dark mode, full screen)
4. Clear any previous state

## Recording Script (60 seconds)

### 0:00–0:05 — The Landing
- Show the AEGIS landing page (cinematic dark UI)
- Camera holds on the input box

### 0:05–0:10 — Type the Command
- Type: **"Protect my Uniswap positions, compound fees daily, detect MEV attacks, send to my family if I disappear for 30 days"**
- Click **🚀 Deploy Agents**

### 0:10–0:18 — Agents Deploy
- Dashboard appears with 5 panels lighting up
- Activity feed shows agents starting one by one:
  - ✅ Guard Agent activated
  - ✅ Grow Agent activated
  - ✅ Rebalance Agent activated
  - ✅ Legacy Agent activated
  - ✅ MEV Protection Agent activated

### 0:18–0:25 — Simulate Threat
- Click **⚡ Simulate Crash** button
- Guard panel flashes RED — threat detected
- Activity feed shows: "🚨 CRITICAL: Price dropped 25%"
- Guard auto-locks positions
- Grow pauses compounding

### 0:25–0:32 — MEV Attack Detection
- Click **🥪 Simulate MEV** button
- MEV panel flashes — sandwich attack detected
- Activity feed shows: "🚨 SANDWICH ATTACK DETECTED"
- Guard elevates threat level in response
- Dry-run TX: "Would route swap via Flashbots Protect"

### 0:32–0:40 — Recovery + Growth
- Wait a moment — Grow resumes compounding
- Vault balance increases
- Activity feed shows fee compounds happening

### 0:40–0:48 — Out of Range
- Click **🎯 Out of Range** button
- Rebalance panel shakes — position out of range
- Shows suggested new tick range
- Guard reacts — elevates threat level

### 0:48–0:55 — Legacy Countdown
- Show Legacy panel with countdown timer
- Click **🏛️ Trigger Inheritance**
- Show assets being distributed to beneficiaries
- Final frame: "✅ Inheritance complete"

### 0:55–0:60 — Chain Switch
- Click **🔵 Base** to live-switch chains
- All 5 agents restart on Base L2
- Show live data flowing

## Tweet Template

> I said "protect my wallet" and 5 AI agents deployed:
>
> 🛡️ Guardian watching for threats
> 📈 Vault growing my savings
> 🎯 Rebalancer monitoring tick range
> 🥪 MEV Shield detecting sandwich attacks
> 🏛️ Digital will for my family
>
> They coordinate through shared memory. Autonomously.
> Real on-chain Uniswap V3 data. Zero Solidity. Just Python + @pyvax.
>
> #ClassifiedHack @synthesis_md
>
> [60-sec screen recording attached]

## Alt Tweet (shorter)

> One sentence → 5 AI agents → autonomous DeFi protection.
>
> I built AEGIS: type what you want, and AI agents monitor live Uniswap V3 pools, detect MEV sandwich attacks, compound fees, rebalance positions, and handle digital inheritance.
>
> Real on-chain data. Zero Solidity. @pyvax + Uniswap.
>
> #ClassifiedHack @synthesis_md
