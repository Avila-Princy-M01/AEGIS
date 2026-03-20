import type { GuardStatus, PricePoint } from '../types'
import { PriceChart } from './PriceChart'

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

      <div className="data-source-badge" style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.4rem',
        padding: '0.3rem 0.6rem',
        borderRadius: '6px',
        fontSize: '0.72rem',
        fontWeight: 600,
        marginBottom: '0.75rem',
        background: isLive ? 'rgba(16, 185, 129, 0.1)' : 'rgba(245, 158, 11, 0.1)',
        border: `1px solid ${isLive ? 'rgba(16, 185, 129, 0.25)' : 'rgba(245, 158, 11, 0.25)'}`,
        color: isLive ? '#10b981' : '#f59e0b',
      }}>
        <span style={{
          width: 6, height: 6, borderRadius: '50%',
          background: isLive ? '#10b981' : '#f59e0b',
          boxShadow: isLive ? '0 0 6px rgba(16,185,129,0.5)' : 'none',
          animation: isLive ? 'pulse-dot 2s ease-in-out infinite' : 'none',
        }} />
        {isLive ? `LIVE · ${status.chain?.toUpperCase() ?? 'ETH'}` : 'SIMULATED'}
        {status.token_pair && (
          <span style={{ color: '#8888a0', marginLeft: '0.25rem' }}>
            · {status.token_pair}
          </span>
        )}
      </div>

      <div className="panel-stats">
        <StatItem label="ETH Price" value={`$${parseFloat(status.last_price).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`} />
        <StatItem label="Position Value" value={`$${parseFloat(status.position_value).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`} />
        <StatItem
          label="Impermanent Loss"
          value={`${parseFloat(status.impermanent_loss_pct).toFixed(2)}%`}
          warn={parseFloat(status.impermanent_loss_pct) > 5}
        />
        <StatItem label="Auto-Exit" value={status.config?.auto_exit ? '✅ ON' : '❌ OFF'} />
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
          <PriceChart data={priceHistory} width={320} height={55} />
        </div>
      )}

      {/* P&L Summary */}
      {status.pnl && (
        <div className="pnl-row">
          <span className="pnl-item pnl-positive">Fees: +${parseFloat(status.pnl.fees_earned).toFixed(2)}</span>
          <span className="pnl-item pnl-negative">IL: -${parseFloat(status.pnl.il_loss).toFixed(2)}</span>
          <span className="pnl-item pnl-negative">Gas: -${parseFloat(status.pnl.gas_cost).toFixed(2)}</span>
          <span className={`pnl-item pnl-net ${parseFloat(status.pnl.net) >= 0 ? 'pnl-positive' : 'pnl-negative'}`}>
            Net: {parseFloat(status.pnl.net) >= 0 ? '+' : ''}${parseFloat(status.pnl.net).toFixed(2)}
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

function StatItem({ label, value, warn }: { label: string; value: string; warn?: boolean }) {
  return (
    <div className="stat-item">
      <span className="stat-label">{label}</span>
      <span className={`stat-value ${warn ? 'warn' : ''}`}>{value}</span>
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
