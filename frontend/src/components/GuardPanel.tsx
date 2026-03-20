import type { ReactNode } from 'react'
import type { GuardStatus, PricePoint } from '../types'
import { PriceChart } from './PriceChart'
import { AnimatedNumber } from './AnimatedNumber'

interface Props {
  status: GuardStatus | null
  priceHistory?: PricePoint[]
}

const THREAT_COLORS: Record<string, string> = {
  safe: '#10b981',
  warning: '#f59e0b',
  critical: '#ef4444',
}

export function GuardPanel({ status, priceHistory = [] }: Props) {
  if (!status) return <PanelSkeleton />

  const threatColor = THREAT_COLORS[status.threat_level] ?? '#6b7280'
  const isLive = status.live_data ?? false
  const animClass = status.threat_level === 'critical' ? 'anim-threat-flash' : ''

  return (
    <div className={`panel guard-panel ${animClass}`}>
      <div className="panel-header">
        <div className="panel-icon" style={{ background: threatColor }}>🛡️</div>
        <div>
          <h2>Guard Agent</h2>
          <span className="panel-label">Threat Detection</span>
        </div>
        <div className="threat-badge" style={{ background: threatColor }}>
          {status.threat_level.toUpperCase()}
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
        <StatItem label="ETH Price">
          <AnimatedNumber value={parseFloat(status.last_price)} prefix="$" decimals={2} />
        </StatItem>
        <StatItem label="Position Value">
          <AnimatedNumber value={parseFloat(status.position_value)} prefix="$" decimals={2} />
        </StatItem>
        <StatItem label="Impermanent Loss" warn={parseFloat(status.impermanent_loss_pct) > 5}>
          <AnimatedNumber value={parseFloat(status.impermanent_loss_pct)} suffix="%" decimals={2} />
        </StatItem>
        <StatItem label="Auto-Exit">
          <span>{status.config?.auto_exit ? '✅ ON' : '❌ OFF'}</span>
        </StatItem>
      </div>

      <div className="panel-bar">
        <div className="bar-track">
          <div
            className="bar-fill"
            style={{
              width: `${Math.min(100, parseFloat(status.impermanent_loss_pct) * 10)}%`,
              background: threatColor,
            }}
          />
        </div>
        <span className="bar-label">IL Threshold: {status.config?.il_threshold}%</span>
      </div>

      {priceHistory.length > 0 && (
        <div style={{ marginTop: '0.75rem' }}>
          <div style={{ fontSize: '0.7rem', color: '#55556a', marginBottom: '0.3rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Price History
          </div>
          <PriceChart data={priceHistory} height={55} />
        </div>
      )}

      {status.pnl && (
        <div className="pnl-row">
          <span className="pnl-item pnl-positive">
            Fees: +<AnimatedNumber value={parseFloat(status.pnl.fees_earned)} prefix="$" decimals={2} locale={false} />
          </span>
          <span className="pnl-item pnl-negative">
            IL: -<AnimatedNumber value={parseFloat(status.pnl.il_loss)} prefix="$" decimals={2} locale={false} />
          </span>
          <span className="pnl-item pnl-negative">
            Gas: -<AnimatedNumber value={parseFloat(status.pnl.gas_cost)} prefix="$" decimals={2} locale={false} />
          </span>
          <span className={`pnl-item pnl-net ${parseFloat(status.pnl.net) >= 0 ? 'pnl-positive' : 'pnl-negative'}`}>
            Net: <AnimatedNumber value={Math.abs(parseFloat(status.pnl.net))} prefix={parseFloat(status.pnl.net) >= 0 ? '+$' : '-$'} decimals={2} locale={false} />
          </span>
        </div>
      )}

      {status.pool_address && (
        <div style={{
          marginTop: '0.5rem',
          fontSize: '0.68rem',
          color: '#55556a',
          fontFamily: 'var(--font-mono)',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
        }}>
          Pool: {status.pool_address}
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
    <div className="panel guard-panel skeleton">
      <div className="panel-header">
        <div className="panel-icon">🛡️</div>
        <div>
          <h2>Guard Agent</h2>
          <span className="panel-label">Initializing...</span>
        </div>
      </div>
    </div>
  )
}
