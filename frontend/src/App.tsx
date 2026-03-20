import { useCallback, useEffect, useRef, useState } from 'react'
import type { MemoryEvent, PricePoint, SystemStatus } from './types'
import * as api from './api'
import { CommandInput } from './components/CommandInput'
import { GuardPanel } from './components/GuardPanel'
import { GrowPanel } from './components/GrowPanel'
import { LegacyPanel } from './components/LegacyPanel'
import { RebalancePanel } from './components/RebalancePanel'
import { ActivityFeed } from './components/ActivityFeed'
import { DemoControls } from './components/DemoControls'

export default function App() {
  const [status, setStatus] = useState<SystemStatus | null>(null)
  const [events, setEvents] = useState<MemoryEvent[]>([])
  const [deployed, setDeployed] = useState(false)
  const [deploying, setDeploying] = useState(false)
  const [priceHistory, setPriceHistory] = useState<PricePoint[]>([])
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
      <div className="app landing">
        <div className="landing-content">
          <div className="logo-glow" />
          <h1 className="title">
            <span className="shield">🛡️</span> AEGIS
          </h1>
          <p className="subtitle">Autonomous Wallet Guardian</p>
          <p className="tagline">
            One command deploys 4 AI agents to <strong>protect</strong>,{' '}
            <strong>grow</strong>, <strong>rebalance</strong>, and <strong>inherit</strong> your Uniswap positions.
            <br />
            Zero Solidity. Pure Python. Powered by PyVax.
          </p>

          <div className="problem-statement">
            <p className="problem-intro">$5B+ in Uniswap V3 TVL. LPs face 4 unsolved problems:</p>
            <div className="problem-grid">
              <div className="problem-item">
                <span className="problem-icon">🛡️</span>
                <span className="problem-text"><strong>IL Blindness</strong> — no real-time impermanent loss alerts</span>
              </div>
              <div className="problem-item">
                <span className="problem-icon">📈</span>
                <span className="problem-text"><strong>Fee Rot</strong> — unclaimed fees losing value to gas costs</span>
              </div>
              <div className="problem-item">
                <span className="problem-icon">🎯</span>
                <span className="problem-text"><strong>Range Drift</strong> — out-of-range positions earning zero fees</span>
              </div>
              <div className="problem-item">
                <span className="problem-icon">🏛️</span>
                <span className="problem-text"><strong>No Succession</strong> — no way to pass positions to family</span>
              </div>
            </div>
            <p className="problem-solve">AEGIS solves all four.</p>
          </div>

          <CommandInput onDeploy={handleDeploy} deploying={deploying} />
          <div className="agent-badges">
            <span className="badge guard">🛡️ Guard</span>
            <span className="badge grow">📈 Grow</span>
            <span className="badge rebalance">🎯 Rebalance</span>
            <span className="badge legacy">🏛️ Legacy</span>
          </div>
          <div className="safety-labels">
            <span className="safety-tag">🔒 Read-only — no private keys required</span>
            <span className="safety-tag">🛡️ Safety-first — suggests actions, never executes unsupervised</span>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="app dashboard">
      <header className="dash-header">
        <div className="header-left">
          <h1>🛡️ AEGIS</h1>
          <span className="status-dot active" />
          <span className="status-text">4 Agents Active</span>
          {status?.live_data !== undefined && (
            <span style={{
              marginLeft: '0.5rem',
              padding: '0.2rem 0.6rem',
              borderRadius: '4px',
              fontSize: '0.7rem',
              fontWeight: 700,
              letterSpacing: '0.03em',
              background: status.live_data
                ? 'rgba(16, 185, 129, 0.15)'
                : 'rgba(245, 158, 11, 0.15)',
              color: status.live_data ? '#10b981' : '#f59e0b',
              border: `1px solid ${status.live_data ? 'rgba(16,185,129,0.3)' : 'rgba(245,158,11,0.3)'}`,
            }}>
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
            <span className="chain-stat-dot" />
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
            <span className="chain-stat-value chain-stat-price">${parseFloat(status.eth_price ?? '0').toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
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
        </div>
      )}

      <div className="panels">
        <GuardPanel status={status?.agents?.guard ?? null} priceHistory={priceHistory} />
        <GrowPanel status={status?.agents?.grow ?? null} />
        <LegacyPanel status={status?.agents?.legacy ?? null} />
        <RebalancePanel status={status?.agents?.rebalance ?? null} />
      </div>

      <ActivityFeed events={events} />
    </div>
  )
}
