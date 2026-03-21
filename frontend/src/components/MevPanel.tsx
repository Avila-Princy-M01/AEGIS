import type { ReactNode } from 'react'
import type { MevStatus } from '../types'
import { AnimatedNumber } from './AnimatedNumber'

interface Props {
  status: MevStatus | null
}

const MEV_COLORS: Record<string, string> = {
  safe: '#10b981',
  warning: '#f59e0b',
  critical: '#ef4444',
}

const THEME_COLOR = '#f97316'

export function MevPanel({ status }: Props) {
  if (!status) return <PanelSkeleton />

  const mevColor = MEV_COLORS[status.mev_level] ?? '#6b7280'
  const isLive = status.live_data ?? false
  const animClass = status.mev_level === 'critical' ? 'anim-mev-flash' : ''
  const estimatedCost = parseFloat(status.estimated_mev_cost_usd)
  const costBarWidth = Math.min(100, estimatedCost / 10)

  return (
    <div className={`panel mev-panel ${animClass}`}>
      <div className="panel-header">
        <div className="panel-icon" style={{ background: THEME_COLOR }}>🥪</div>
        <div>
          <h2>MEV Agent</h2>
          <span className="panel-label">
            {status.paused ? '⏸️ Paused (threat detected)' : 'MEV Detection'}
          </span>
        </div>
        <div className="threat-badge" style={{ background: mevColor }}>
          {status.mev_level.toUpperCase()}
        </div>
      </div>

      <div className={`data-source-badge ${isLive ? 'live' : 'simulated'}`}>
        <span className="badge-dot" />
        {isLive ? `LIVE · ${status.chain?.toUpperCase() ?? 'ETH'}` : 'SIMULATED'}
        {status.token_pair && (
          <span style={{ color: '#8888a0', marginLeft: '0.25rem' }}>
            · {status.token_pair}
          </span>
        )}
      </div>

      <div className="panel-stats">
        <StatItem label="Sandwich Attacks">
          <span>{status.sandwich_count}</span>
        </StatItem>
        <StatItem label="Front-runs">
          <span>{status.frontrun_count}</span>
        </StatItem>
        <StatItem label="Total Detected" warn={status.total_mev_detected > 10}>
          <span>{status.total_mev_detected}</span>
        </StatItem>
        <StatItem label="Est. MEV Cost">
          <AnimatedNumber value={estimatedCost} prefix="$" decimals={2} />
        </StatItem>
      </div>

      <div className="panel-bar">
        <div className="bar-track">
          <div
            className="bar-fill"
            style={{
              width: `${costBarWidth}%`,
              background: mevColor,
            }}
          />
        </div>
        <span className="bar-label">
          MEV Cost Accumulation · ${estimatedCost.toFixed(2)}
        </span>
      </div>

      {status.last_alert && (
        <div style={{
          marginTop: '0.75rem',
          padding: '0.6rem',
          borderRadius: '8px',
          background: 'rgba(249, 115, 22, 0.06)',
          border: '1px solid rgba(249, 115, 22, 0.15)',
          fontSize: '0.78rem',
          animation: 'fadeInUp 0.4s ease',
        }}>
          <div style={{ color: THEME_COLOR, fontWeight: 700, marginBottom: '0.25rem' }}>
            🚨 Last Alert
          </div>
          <div style={{ color: '#8888a0', fontFamily: 'var(--font-mono)', fontSize: '0.72rem' }}>
            {status.last_alert}
          </div>
        </div>
      )}

      {status.safe_route && status.safe_route.source && (
        <div style={{
          marginTop: '0.75rem',
          padding: '0.6rem',
          borderRadius: '8px',
          background: 'rgba(255, 0, 122, 0.04)',
          border: '1px solid rgba(255, 0, 122, 0.12)',
          fontSize: '0.72rem',
          fontFamily: 'var(--font-mono)',
        }}>
          <div style={{ color: '#ff007a', fontWeight: 700, marginBottom: '0.25rem' }}>
            🦄 Safe Route (Uniswap Trading API)
          </div>
          <div style={{ color: '#8888a0' }}>
            {status.safe_route.routing}
            {status.safe_route.route?.length > 0 && (
              <span> · {status.safe_route.route.map((r: { tokenIn: string; tokenOut: string }) => `${r.tokenIn}→${r.tokenOut}`).join(' → ')}</span>
            )}
            <span> · Gas ~${parseFloat(status.safe_route.gas_usd || '0').toFixed(2)}</span>
          </div>
        </div>
      )}

      {status.config && (
        <div style={{
          marginTop: '0.5rem',
          fontSize: '0.68rem',
          color: '#55556a',
          fontFamily: 'var(--font-mono)',
          display: 'flex',
          gap: '0.75rem',
          flexWrap: 'wrap',
        }}>
          <span>Sandwich: {status.config.sandwich_detection ? '✅' : '❌'}</span>
          <span>Impact Threshold: {status.config.price_impact_threshold}</span>
          <span>Frontrun Window: {status.config.frontrun_window}ms</span>
        </div>
      )}

      {status.reasoning && (
        <div className="reasoning-line">🧠 {status.reasoning}</div>
      )}
    </div>
  )
}

function StatItem({ label, children, warn }: { label: string; children: ReactNode; warn?: boolean }) {
  return (
    <div className="stat-item">
      <span className="stat-label">{label}</span>
      <span className={`stat-value ${warn ? 'warn' : ''}`}>{children}</span>
    </div>
  )
}

function PanelSkeleton() {
  return (
    <div className="panel mev-panel skeleton">
      <div className="panel-header">
        <div className="panel-icon">🥪</div>
        <div>
          <h2>MEV Agent</h2>
          <span className="panel-label">Initializing...</span>
        </div>
      </div>
    </div>
  )
}
