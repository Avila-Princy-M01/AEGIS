# AEGIS Demo Script — 30-Second Screen Recording

## Setup Before Recording
1. Start the backend: `python -m aegis.server`
2. Start the frontend: `cd frontend && npm run dev`
3. Open http://localhost:3000 in Chrome (dark mode, full screen)
4. Clear any previous state

## Recording Script (30 seconds)

### 0:00–0:05 — The Landing
- Show the AEGIS landing page (cinematic dark UI)
- Camera holds on the input box

### 0:05–0:10 — Type the Command
- Type: **"Protect my Uniswap positions, compound fees daily, send to my family if I disappear for 30 days"**
- Click **🚀 Deploy Agents**

### 0:10–0:15 — Agents Deploy
- Dashboard appears with 3 panels lighting up
- Activity feed shows agents starting one by one:
  - ✅ Guard Agent activated
  - ✅ Grow Agent activated
  - ✅ Legacy Agent activated

### 0:15–0:20 — Simulate Threat
- Click **⚡ Simulate Crash** button
- Guard panel flashes RED — threat detected
- Activity feed shows: "🚨 CRITICAL: Price dropped 25%"
- Guard auto-locks positions
- Grow pauses compounding

### 0:20–0:25 — Recovery + Growth
- Wait a moment — Grow resumes compounding
- Vault balance increases
- Activity feed shows fee compounds happening

### 0:25–0:30 — Legacy Countdown
- Show Legacy panel with countdown timer
- Click **🏛️ Trigger Inheritance**
- Show assets being distributed to beneficiaries
- Final frame: "✅ Inheritance complete"

## Tweet Template

> I said "protect my wallet" and 3 AI agents deployed:
> 
> 🛡️ Guardian watching for threats
> 📈 Vault growing my savings  
> 🏛️ Digital will for my family
>
> They coordinate through shared memory. Autonomously.
> Zero Solidity. Just Python + @pyvax.
>
> #ClassifiedHack
>
> [30-sec screen recording attached]

## Alt Tweet (shorter)

> One sentence → 3 AI agents → autonomous DeFi protection.
>
> I built AEGIS: type what you want, and AI agents deploy smart contracts, monitor threats, compound fees, and handle inheritance. All in Python.
>
> Zero Solidity. @pyvax + Avalanche.
>
> #ClassifiedHack
