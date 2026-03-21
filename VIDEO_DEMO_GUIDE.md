# 🎥 AEGIS — Video Demo Recording Guide

> Step-by-step instructions for recording a compelling hackathon demo video.
> Target length: **3–5 minutes**. Judges have limited time — every second should prove something.

---

## 🎯 What Judges Are Looking For

1. **Does it actually work?** — Show real data flowing, not slides
2. **Is the Uniswap API load-bearing?** — Show a real swap with a real TxID
3. **Is there on-chain proof?** — Show Etherscan links that verify your claims
4. **Is it multi-agent?** — Show agents reacting to each other
5. **Is it novel?** — Emphasize what no other project does (5-agent coordination, MEV detection, ENS inheritance)

---

## 📋 Pre-Recording Checklist

Before you hit record, make sure:

- [ ] Backend is running: `python -m aegis.server`
- [ ] Frontend is running: `cd frontend && npm run dev`
- [ ] Dashboard is open at `http://localhost:5173`
- [ ] You can see the **🟢 LIVE** indicator (or 🟡 SIMULATED — both are fine)
- [ ] Your browser is at **100% zoom** (no tiny text)
- [ ] Screen resolution is **1920×1080** or higher
- [ ] Close all other tabs/notifications (focus on AEGIS only)
- [ ] Have Sepolia Etherscan open in a separate tab for the swap proof section

---

## 🎬 Recording Script (Shot by Shot)

### Shot 1: Opening — The Problem (0:00 – 0:20)

**What to say:**
> "AEGIS is an autonomous multi-agent system that protects Uniswap V3 LP positions. LPs face 5 critical problems: impermanent loss blindness, unclaimed fee rot, range drift earning zero fees, MEV sandwich attacks extracting value, and no way to pass on crypto to family. AEGIS solves all five with coordinated AI agents."

**What to show:**
- The landing page with the hero text and 5 agent badges
- Slowly scroll to show the command input

---

### Shot 2: Deploy Agents (0:20 – 0:40)

**What to say:**
> "One natural language command deploys all five agents. Watch."

**What to do:**
1. Type in the command input: `Protect my ETH/USDC position, compound fees, shield from MEV, and if I'm gone 30 days send everything to family.eth`
2. Click **🚀 Deploy Agents**
3. Watch all 5 agent panels spawn with live data

**What to highlight:**
- The live stats bar at the top: `🟢 Block: 22,XXX,XXX · ⛽ Gas: XX gwei · ETH: $X,XXX · Chain: ETHEREUM`
- Say: *"That block number and gas price are live from Ethereum mainnet right now — not simulated."*

---

### Shot 3: Agent Intelligence — Reasoning Lines (0:40 – 1:10)

**What to say:**
> "Each agent explains its reasoning every cycle. This is real intelligence, not just threshold checks."

**What to show (hover/point at each panel):**
- **Guard Panel:** `🧠 ETH $2,141.90 | Δ +0.1% | IL 0.23% (threshold 10%) → SAFE`
- **Grow Panel:** `🧠 Fees +$0.04 (live) | Gas 12.3 gwei | Vault $0.12 → COMPOUND`
- **Rebalance Panel:** `🧠 Tick 199520 in [197500, 201500] | 50.5% utilization → IN RANGE`
- **MEV Panel:** `🧠 Tick Δ3 (live) | Sandwiches 0 | Front-runs 0 → SAFE`
- **Legacy Panel:** Shows beneficiary with ENS name resolved

**Key phrase:** *"Every decision is logged to agent_log.json — fully auditable."*

---

### Shot 4: Multi-Agent Coordination — The Chain Reaction (1:10 – 1:50)

**What to say:**
> "This is what makes AEGIS different from single-agent projects. Watch what happens when I simulate an ETH crash."

**What to do:**
1. Click **⚡ Simulate Crash**
2. Watch the chain reaction:
   - Guard goes **CRITICAL** (red flash animation)
   - Grow **auto-pauses** compounding
   - Rebalance **auto-pauses**
   - MEV increases vigilance
   - P&L updates in real-time

**Key phrase:** *"Five agents. One shared memory bus. When Guard detects danger, every agent reacts instantly."*

3. Click **🥪 Simulate MEV** next
   - MEV goes **CRITICAL** (orange flash)
   - Guard reacts — elevates threat level
   - Shows: *"Sandwich attack detected → Would route via Flashbots Protect"*

4. Click **🎯 Out of Range**
   - Rebalance shakes, shows suggested new range
   - Guard reacts — threat level rises

---

### Shot 5: Real Swap Execution — On-Chain Proof (1:50 – 2:40)

> ⚠️ **THIS IS THE MOST IMPORTANT SECTION FOR JUDGES**

**What to say:**
> "Now I'll show the real on-chain proof. AEGIS doesn't just quote prices — it executes real swaps via the Uniswap Trading API."

**What to do (Option A — Show existing TxIDs):**
1. Open Sepolia Etherscan in a new tab
2. Navigate to: `https://sepolia.etherscan.io/tx/0x83087cd184dd637b85594e10928e2cc9e255cd847c2875e1275c57d1f79591fe`
3. Show the confirmed transaction: 0.001 ETH → 5.55 USDC
4. Navigate to: `https://sepolia.etherscan.io/tx/0xdc3ab4f3e67ce95fda153bcba84454dfcbf782cd20bbcfd73a14946650621acb`
5. Show the second swap: 0.002 ETH → USDC

**What to do (Option B — Execute a LIVE swap on camera):**
1. Open the SwapQuotePanel in the dashboard
2. Enter amount: `0.001` ETH
3. Click **Get Quote** — show the live Uniswap Trading API response
4. Click **Execute Swap** — show the TxID appear
5. Click the Etherscan link — show the confirmed transaction

**Key phrase:** *"Real TxIDs. Real on-chain. Verified on Etherscan. This is the Uniswap Trading API integration — not a mock."*

---

### Shot 6: ERC-8004 On-Chain Identity (2:40 – 3:00)

**What to say:**
> "AEGIS has a permanent on-chain identity via ERC-8004 on Base Mainnet."

**What to show:**
1. Open Base Mainnet Etherscan: `https://basescan.org/tx/0x48a190093bad8a57c0e4c4feba3a783f7c2f63625aad4e978db62fce9c625389`
2. Show the agent registration transaction
3. Briefly show `agent.json` in the repo — the ERC-8004 manifest

**Key phrase:** *"Verifiable, portable agent identity — independent of any platform."*

---

### Shot 7: Chain Switching & Lido Comparison (3:00 – 3:20)

**What to say:**
> "AEGIS monitors multiple chains and compares LP yields against Lido staking."

**What to do:**
1. Click **🔵 Base** in the chain selector → show data switching to Base L2
2. Click back to **🟣 Ethereum**
3. Scroll to Analytics section — show Lido yield comparison (LP APR vs staking APR)
4. Show the Backtest panel with historical simulation results

---

### Shot 8: Legacy & ENS (3:20 – 3:40)

**What to say:**
> "The Legacy Agent is a dead man's switch. If you go inactive for 30 days, it resolves ENS names and distributes your funds."

**What to do:**
1. Click **🏛️ Trigger Inheritance**
2. Show beneficiary with ENS name resolved to address
3. Show the structured execution log

**Key phrase:** *"family.eth resolves to a real Ethereum address. No hex addresses needed."*

---

### Shot 9: Code & Architecture (3:40 – 4:00)

**What to say:**
> "Under the hood: Python backend with web3.py, React TypeScript frontend, 54 passing tests, 4 PyVax smart contracts, and full structured logging."

**What to show (quick flashes):**
1. Terminal: `python -m pytest tests/test_core.py -v` → show 54 passing
2. Quick scroll through `agent_log.json` in the repo
3. Show `TXIDS.md` with both confirmed transactions

---

### Shot 10: Closing — Summary (4:00 – 4:15)

**What to say:**
> "AEGIS: 5 coordinated AI agents. Real on-chain data. Real Sepolia swaps with real TxIDs. ERC-8004 identity on Base. Lido yield comparison. ENS resolution. 54 tests. One command to deploy. Thank you."

**What to show:**
- The dashboard in its full glory — all 5 panels running, live data flowing
- Fade out or stop recording

---

## 🛠️ Recording Tools

Pick one:
| Tool | Platform | Notes |
|------|----------|-------|
| [OBS Studio](https://obsproject.com/) | Win/Mac/Linux | Free, best quality, record as MP4 |
| [ScreenToGif](https://www.screentogif.com/) | Windows | Free, great for GIFs |
| [Loom](https://www.loom.com/) | Browser | Free tier, easy sharing, has webcam overlay |
| [Kap](https://getkap.co/) | Mac | Free, lightweight |

**Recommended settings:**
- Resolution: 1920×1080
- FPS: 30
- Format: MP4 (H.264)
- Audio: Record your voice narrating (judges prefer narrated demos)

---

## 📤 Where to Upload

1. **YouTube** (unlisted) — most reliable, paste link in README
2. **Loom** — auto-generates shareable link
3. **Google Drive** — set sharing to "anyone with link"

Then add to README:
```markdown
### 🎥 Demo Video
[![AEGIS Demo](assets/video-thumbnail.png)](YOUR_VIDEO_LINK_HERE)
```

---

## 💡 Pro Tips

- **Talk while you demo** — narration makes it 10x more compelling than silent screen recording
- **Show Etherscan early** — judges want on-chain proof fast
- **Don't rush** — let data load, let animations play, let agents react
- **Show the agent_log.json** — proves autonomous execution, not scripted responses
- **End with the live dashboard** — leave a lasting visual impression
- **Keep it under 5 minutes** — judges won't watch a 15-minute video

---

*This guide was prepared as part of the AEGIS hackathon submission documentation.*
