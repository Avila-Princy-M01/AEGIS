import { useCallback, useEffect, useRef, useState } from 'react'
import type { BacktestResult, LidoYieldData, PoolAllocationData, MemoryEvent, PricePoint, SystemStatus } from './types'
import * as api from './api'
import { CommandInput } from './components/CommandInput'
import { GuardPanel } from './components/GuardPanel'
import { GrowPanel } from './components/GrowPanel'
import { LegacyPanel } from './components/LegacyPanel'
import { RebalancePanel } from './components/RebalancePanel'
import { MevPanel } from './components/MevPanel'
import { BacktestPanel } from './components/BacktestPanel'
import { AnalyticsPanel } from './components/AnalyticsPanel'
import { SwapQuotePanel } from './components/SwapQuotePanel'
import { ActivityFeed } from './components/ActivityFeed'
import { DemoControls } from './components/DemoControls'
import { ParticleBackground } from './components/ParticleBackground'
import { AnimatedNumber } from './components/AnimatedNumber'

export default function App() {
  const [status, setStatus] = useState<SystemStatus | null>(null)
  const [events, setEvents] = useState<MemoryEvent[]>([])
  const [deployed, setDeployed] = useState(false)
  const [deploying, setDeploying] = useState(false)
  const [priceHistory, setPriceHistory] = useState<PricePoint[]>([])
  const [backtestResults, setBacktestResults] = useState<BacktestResult | null>(null)
  const [lidoYield, setLidoYield] = useState<LidoYieldData | null>(null)
  const [poolAllocation, setPoolAllocation] = useState<PoolAllocationData | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const addEvent = useCallback((event: MemoryEvent) => {
    setEvents(prev => [...prev.slice(-99), event])
  }, [])

  const handleDeploy = async (command: string) => {
    setDeploying(true)
    try {
      const res = await api.deploy(command)
      setStatus(res.status)
      setDeployed(true)

      wsRef.current = api.connectWebSocket(addEvent)

      pollRef.current = setInterval(async () => {
        try {
          const [s, ph] = await Promise.all([
            api.getStatus(),
            api.getPriceHistory(),
          ])
          setStatus(s)
          setPriceHistory(ph)
        } catch { /* ignore */ }
      }, 2000)

      const existingEvents = await api.getEvents(50)
      setEvents(existingEvents)

      api.runBacktest(30).then(setBacktestResults).catch(() => {})
      api.getLidoYield().then(setLidoYield).catch(() => {})
      api.getPoolAllocation().then(setPoolAllocation).catch(() => {})
    } catch (err) {
      console.error('Deploy failed:', err)
    } finally {
      setDeploying(false)
    }
  }

  useEffect(() => {
    return () => {
      wsRef.current?.close()
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [])

  if (!deployed) {
    return (
      <>
      <ParticleBackground />
      <div className="app landing">
        {/* ── Hero Section ── */}
        <section className="hero-section">
          <div className="landing-content">
            <div className="logo-glow" />
            <h1 className="title">
              <span className="shield">🛡️</span> AEGIS
            </h1>
            <p className="subtitle">Autonomous Wallet Guardian</p>
            <p className="tagline">
              One command deploys 5 AI agents to <strong>protect</strong>,{' '}
              <strong>grow</strong>, <strong>rebalance</strong>, <strong>shield</strong>, and <strong>inherit</strong> your Uniswap positions.
              <br />
              Zero Solidity. Pure Python. Powered by PyVax.
            </p>

            <div className="problem-statement">
              <div className="problem-header">
                <span className="problem-header-tag">THE CHALLENGE</span>
                <h2 className="problem-headline">$5B+ in Uniswap V3 TVL.<br />LPs face 5 unsolved problems:</h2>
              </div>
              <div className="problem-grid">
                <div className="problem-card problem-card--guard">
                  <div className="problem-card__glow" />
                  <div className="problem-card__icon-wrap">
                    <span className="problem-card__icon">🛡️</span>
                  </div>
                  <div className="problem-card__content">
                    <div className="problem-card__title-row">
                      <span className="problem-card__status" />
                      <h3 className="problem-card__title">IL Blindness</h3>
                    </div>
                    <p className="problem-card__desc">No real-time impermanent loss alerts — LPs discover losses after the damage is done</p>
                  </div>
                  <div className="problem-card__severity">
                    <span className="severity-bar"><span className="severity-fill severity-fill--high" /></span>
                    <span className="severity-label">Critical</span>
                  </div>
                </div>

                <div className="problem-card problem-card--grow">
                  <div className="problem-card__glow" />
                  <div className="problem-card__icon-wrap">
                    <span className="problem-card__icon">📈</span>
                  </div>
                  <div className="problem-card__content">
                    <div className="problem-card__title-row">
                      <span className="problem-card__status" />
                      <h3 className="problem-card__title">Fee Rot</h3>
                    </div>
                    <p className="problem-card__desc">Unclaimed fees silently lose value to gas costs, eroding yield over time</p>
                  </div>
                  <div className="problem-card__severity">
                    <span className="severity-bar"><span className="severity-fill severity-fill--high" /></span>
                    <span className="severity-label">Critical</span>
                  </div>
                </div>

                <div className="problem-card problem-card--rebalance">
                  <div className="problem-card__glow" />
                  <div className="problem-card__icon-wrap">
                    <span className="problem-card__icon">🎯</span>
                  </div>
                  <div className="problem-card__content">
                    <div className="problem-card__title-row">
                      <span className="problem-card__status" />
                      <h3 className="problem-card__title">Range Drift</h3>
                    </div>
                    <p className="problem-card__desc">Out-of-range positions earn zero fees while capital sits completely idle</p>
                  </div>
                  <div className="problem-card__severity">
                    <span className="severity-bar"><span className="severity-fill severity-fill--med" /></span>
                    <span className="severity-label">High</span>
                  </div>
                </div>

                <div className="problem-card problem-card--mev">
                  <div className="problem-card__glow" />
                  <div className="problem-card__icon-wrap">
                    <span className="problem-card__icon">🥪</span>
                  </div>
                  <div className="problem-card__content">
                    <div className="problem-card__title-row">
                      <span className="problem-card__status" />
                      <h3 className="problem-card__title">MEV Extraction</h3>
                    </div>
                    <p className="problem-card__desc">Sandwich attacks and front-running silently extract value from every swap you make</p>
                  </div>
                  <div className="problem-card__severity">
                    <span className="severity-bar"><span className="severity-fill severity-fill--high" /></span>
                    <span className="severity-label">Critical</span>
                  </div>
                </div>

                <div className="problem-card problem-card--legacy">
                  <div className="problem-card__glow" />
                  <div className="problem-card__icon-wrap">
                    <span className="problem-card__icon">🏛️</span>
                  </div>
                  <div className="problem-card__content">
                    <div className="problem-card__title-row">
                      <span className="problem-card__status" />
                      <h3 className="problem-card__title">No Succession</h3>
                    </div>
                    <p className="problem-card__desc">No built-in way to transfer or inherit positions — assets can be permanently lost</p>
                  </div>
                  <div className="problem-card__severity">
                    <span className="severity-bar"><span className="severity-fill severity-fill--med" /></span>
                    <span className="severity-label">High</span>
                  </div>
                </div>
              </div>
              <div className="problem-solve-wrap">
                <div className="solve-line" />
                <p className="problem-solve">
                  <span className="solve-icon">✦</span> AEGIS solves all five.
                </p>
              </div>
            </div>

            <CommandInput onDeploy={handleDeploy} deploying={deploying} />
            <div className="agent-badges">
              <span className="badge guard">🛡️ Guard</span>
              <span className="badge grow">📈 Grow</span>
              <span className="badge rebalance">🎯 Rebalance</span>
              <span className="badge mev">🥪 MEV Shield</span>
              <span className="badge legacy">🏛️ Legacy</span>
            </div>
            <div className="safety-labels">
              <span className="safety-tag">🔒 Read-only — no private keys required</span>
              <span className="safety-tag">🛡️ Safety-first — suggests actions, never executes unsupervised</span>
            </div>
          </div>
        </section>

        {/* ── How It Works ── */}
        <section className="how-it-works">
          <h2 className="section-title">How It Works</h2>
          <p className="section-subtitle">From natural language to autonomous protection in seconds</p>
          <div className="steps-container">
            <div className="step-card">
              <div className="step-number">01</div>
              <div className="step-icon-wrap">
                <span className="step-icon">💬</span>
              </div>
              <h3>Describe Your Strategy</h3>
              <p>Type what you want in plain English. "Protect my LP, compound fees, 30-day dead man's switch."</p>
            </div>
            <div className="step-connector">
              <div className="connector-line" />
              <span className="connector-arrow">→</span>
            </div>
            <div className="step-card">
              <div className="step-number">02</div>
              <div className="step-icon-wrap">
                <span className="step-icon">🤖</span>
              </div>
              <h3>Agents Deploy</h3>
              <p>Groq AI parses your intent. Five specialized agents spawn and begin monitoring real pools.</p>
            </div>
            <div className="step-connector">
              <div className="connector-line" />
              <span className="connector-arrow">→</span>
            </div>
            <div className="step-card">
              <div className="step-number">03</div>
              <div className="step-icon-wrap">
                <span className="step-icon">🛡️</span>
              </div>
              <h3>Portfolio Protected</h3>
              <p>Real-time IL alerts, auto-compounding, range rebalancing, and inheritance — all autonomous.</p>
            </div>
          </div>
        </section>

        {/* ── Architecture ── */}
        <section className="architecture-section">
          <h2 className="section-title">Multi-Agent Architecture</h2>
          <p className="section-subtitle">Five coordinated agents with shared memory and real-time on-chain data</p>
          <div className="arch-diagram">
            <div className="arch-row arch-input">
              <div className="arch-node arch-nlp">
                <span className="arch-node-icon">🧠</span>
                <span className="arch-node-label">NLP Parser</span>
                <span className="arch-node-detail">Groq LLM</span>
              </div>
            </div>
            <div className="arch-flow-line" />
            <div className="arch-row arch-orch">
              <div className="arch-node arch-orchestrator">
                <span className="arch-node-icon">⚙️</span>
                <span className="arch-node-label">Orchestrator</span>
                <span className="arch-node-detail">Coordinates all agents</span>
              </div>
            </div>
            <div className="arch-flow-line arch-flow-split" />
            <div className="arch-row arch-agents">
              <div className="arch-node arch-agent-guard">
                <span className="arch-node-icon">🛡️</span>
                <span className="arch-node-label">Guard</span>
              </div>
              <div className="arch-node arch-agent-grow">
                <span className="arch-node-icon">📈</span>
                <span className="arch-node-label">Grow</span>
              </div>
              <div className="arch-node arch-agent-rebalance">
                <span className="arch-node-icon">🎯</span>
                <span className="arch-node-label">Rebalance</span>
              </div>
              <div className="arch-node arch-agent-mev">
                <span className="arch-node-icon">🥪</span>
                <span className="arch-node-label">MEV Shield</span>
              </div>
              <div className="arch-node arch-agent-legacy">
                <span className="arch-node-icon">🏛️</span>
                <span className="arch-node-label">Legacy</span>
              </div>
            </div>
            <div className="arch-flow-line arch-flow-merge" />
            <div className="arch-row arch-data">
              <div className="arch-node arch-memory">
                <span className="arch-node-icon">💾</span>
                <span className="arch-node-label">Shared Memory</span>
                <span className="arch-node-detail">Cross-agent events</span>
              </div>
              <div className="arch-node arch-chain">
                <span className="arch-node-icon">⛓️</span>
                <span className="arch-node-label">On-Chain Data</span>
                <span className="arch-node-detail">Uniswap V3 · Lido</span>
              </div>
            </div>
          </div>
        </section>

        {/* ── Tech Stack ── */}
        <section className="tech-stack-section">
          <h2 className="section-title">Built With</h2>
          <p className="section-subtitle">Production-grade tools for DeFi automation</p>
          <div className="tech-grid">
            <div className="tech-badge-card">
              <span className="tech-icon">🦄</span>
              <span className="tech-name">Uniswap V3 + API</span>
              <span className="tech-desc">Trading API + 5 live pools</span>
            </div>
            <div className="tech-badge-card">
              <span className="tech-icon">🔵</span>
              <span className="tech-name">Lido stETH</span>
              <span className="tech-desc">wstETH/ETH + stETH/ETH</span>
            </div>
            <div className="tech-badge-card">
              <span className="tech-icon">🔷</span>
              <span className="tech-name">Base L2</span>
              <span className="tech-desc">Multi-chain support</span>
            </div>
            <div className="tech-badge-card">
              <span className="tech-icon">🐍</span>
              <span className="tech-name">Python / PyVax</span>
              <span className="tech-desc">Zero Solidity contracts</span>
            </div>
            <div className="tech-badge-card">
              <span className="tech-icon">⚡</span>
              <span className="tech-name">Groq AI</span>
              <span className="tech-desc">NLP command parsing</span>
            </div>
            <div className="tech-badge-card">
              <span className="tech-icon">🔗</span>
              <span className="tech-name">Multi-RPC</span>
              <span className="tech-desc">6 fallback endpoints</span>
            </div>
          </div>
        </section>

        <footer className="landing-footer">
          <p>Built for the <strong>Classified Hack × Synthesis Hackathon</strong> · Uniswap + Lido + Base Tracks · 2026</p>
        </footer>
      </div>
      </>
    )
  }

  const totalValue = status?.agents?.guard
    ? parseFloat(status.agents.guard.position_value || '0')
    : 0
  const netPnl = status?.agents?.guard?.pnl
    ? parseFloat(status.agents.guard.pnl.net || '0')
    : 0
  const activeAgents = [
    status?.agents?.guard?.running,
    status?.agents?.grow?.running,
    status?.agents?.rebalance?.running,
    status?.agents?.mev?.running,
    status?.agents?.legacy?.running,
  ].filter(Boolean).length

  return (
    <>
    <ParticleBackground />
    <div className="app dashboard">
      <header className="dash-header">
        <div className="header-left">
          <h1 className="dash-brand">🛡️ AEGIS</h1>
          <span className="status-dot active" />
          <span className="status-text">{activeAgents} Agents Active</span>
          {status?.live_data !== undefined && (
            <span className={`live-badge ${status.live_data ? 'live' : 'sim'}`}>
              {status.live_data
                ? `🟢 LIVE · ${status.chain?.toUpperCase() ?? 'ON-CHAIN'}`
                : '🟡 SIMULATED'}
            </span>
          )}
          <div className="chain-selector">
            {['ethereum', 'base'].map((chain) => (
              <button
                key={chain}
                className={`chain-pill ${status?.chain === chain ? 'active' : ''}`}
                onClick={async () => {
                  if (status?.chain === chain) return
                  setPriceHistory([])
                  try {
                    const s = await api.switchChain(chain)
                    setStatus(s)
                  } catch { /* ignore */ }
                }}
              >
                {chain === 'ethereum' ? '🟣 Ethereum' : '🔵 Base'}
              </button>
            ))}
          </div>
        </div>
        <DemoControls />
      </header>

      {status?.live_data && (
        <div className="chain-stats-bar">
          <div className="chain-stat">
            <span className={`chain-stat-dot${status.rpc_status === 'error' ? ' rpc-error' : status.rpc_status === 'reconnecting' ? ' rpc-warn' : ''}`} />
            <span className="chain-stat-label">Block</span>
            <span className="chain-stat-value">{(status.block_number ?? 0).toLocaleString()}</span>
          </div>
          <div className="chain-stat-divider" />
          <div className="chain-stat">
            <span className="chain-stat-label">⛽ Gas</span>
            <span className="chain-stat-value">{parseFloat(status.gas_price_gwei ?? '0').toFixed(1)} gwei</span>
          </div>
          <div className="chain-stat-divider" />
          <div className="chain-stat">
            <span className="chain-stat-label">ETH</span>
            <span className="chain-stat-value chain-stat-price">
              <AnimatedNumber value={parseFloat(status.eth_price ?? '0')} prefix="$" decimals={2} />
            </span>
          </div>
          <div className="chain-stat-divider" />
          <div className="chain-stat">
            <span className="chain-stat-label">Chain</span>
            <span className="chain-stat-value">{status.chain?.toUpperCase() ?? 'ETH'}</span>
          </div>
          <div className="chain-stat-divider" />
          <div className="chain-stat">
            <span className="chain-stat-label">Pools</span>
            <span className="chain-stat-value">{status.available_pools?.length ?? 0}</span>
          </div>
          <div className="chain-stat-divider" />
          <div className="chain-stat">
            <span className={`rpc-badge rpc-${status.rpc_status ?? 'disconnected'}`}>
              {status.rpc_status === 'connected' && '🟢 RPC'}
              {status.rpc_status === 'reconnecting' && '⚡ Reconnecting...'}
              {status.rpc_status === 'error' && '🔴 RPC Error'}
              {(!status.rpc_status || status.rpc_status === 'disconnected') && '⚪ Offline'}
            </span>
            {status.rpc_provider && status.rpc_status === 'connected' && (
              <span className="chain-stat-value rpc-provider">{status.rpc_provider}</span>
            )}
          </div>
        </div>
      )}

      {/* ── Portfolio Overview ── */}
      {status?.agents?.guard && (
      <div className="portfolio-overview">
        <div className="portfolio-card">
          <div className="portfolio-icon">💰</div>
          <div className="portfolio-info">
            <span className="portfolio-label">Total Position Value</span>
            <span className="portfolio-value">
              <AnimatedNumber value={totalValue} prefix="$" decimals={2} />
            </span>
          </div>
        </div>
        <div className="portfolio-card">
          <div className="portfolio-icon">{netPnl >= 0 ? '📈' : '📉'}</div>
          <div className="portfolio-info">
            <span className="portfolio-label">Net P&L</span>
            <span className={`portfolio-value ${netPnl >= 0 ? 'pnl-positive' : 'pnl-negative'}`}>
              <AnimatedNumber value={Math.abs(netPnl)} prefix={netPnl >= 0 ? '+$' : '-$'} decimals={2} />
            </span>
          </div>
        </div>
        <div className="portfolio-card">
          <div className="portfolio-icon">🤖</div>
          <div className="portfolio-info">
            <span className="portfolio-label">Active Agents</span>
            <span className="portfolio-value">{activeAgents}/5</span>
          </div>
        </div>
        <div className="portfolio-card">
          <div className="portfolio-icon">⛓️</div>
          <div className="portfolio-info">
            <span className="portfolio-label">Network</span>
            <span className="portfolio-value">{status?.chain === 'base' ? 'Base L2' : 'Ethereum'}</span>
          </div>
        </div>
        <div className="portfolio-card">
          <div className="portfolio-icon">🏊</div>
          <div className="portfolio-info">
            <span className="portfolio-label">Pools Monitored</span>
            <span className="portfolio-value">{status?.available_pools?.length ?? 0}</span>
          </div>
        </div>
      </div>
      )}

      <div className="panels">
        <GuardPanel status={status?.agents?.guard ?? null} priceHistory={priceHistory} />
        <GrowPanel status={status?.agents?.grow ?? null} />
        <RebalancePanel status={status?.agents?.rebalance ?? null} />
        <MevPanel status={status?.agents?.mev ?? null} />
        <LegacyPanel status={status?.agents?.legacy ?? null} />
      </div>

      <SwapQuotePanel chain={status?.chain ?? 'ethereum'} />

      <AnalyticsPanel lidoYield={lidoYield} poolAllocation={poolAllocation} />

      <BacktestPanel results={backtestResults} />

      <ActivityFeed events={events} />
    </div>
    </>
  )
}
