import type { GrowStatus } from '../types'

interface Props {
  status: GrowStatus | null
}

export function GrowPanel({ status }: Props) {
  if (!status) return <PanelSkeleton />

  const isLive = status.live_data ?? false

  const animClass = (!status.paused && status.total_compounds > 0) ? 'anim-compound-pulse' : ''

  return (
    <div className={`panel grow-panel ${status.paused ? 'paused' : ''} ${animClass}`}>
      <div className="panel-header">
        <div className="panel-icon" style={{ background: status.paused ? '#f59e0b' : '#10b981' }}>📈</div>
        <div>
          <h2>Grow Agent</h2>
          <span className="panel-label">
            {status.paused ? '⏸️ Paused (threat detected)' : 'Fee Compounding'}
          </span>
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
        {isLive ? 'LIVE · Fee Growth Tracking' : 'SIMULATED'}
        {status.token_pair && (
          <span style={{ color: '#8888a0', marginLeft: '0.25rem' }}>
            · {status.token_pair}
          </span>
        )}
      </div>

      <div className="panel-stats">
        <StatItem label="Vault Balance" value={`$${parseFloat(status.vault_balance).toFixed(4)}`} highlight />
        <StatItem label="Fees Collected" value={`$${parseFloat(status.total_fees_collected).toFixed(4)}`} />
        <StatItem label="Compounds" value={`${status.total_compounds}`} />
        <StatItem label="Savings Rate" value={`${status.config?.savings_sweep_pct}%`} />
      </div>

      {/* Gas Price Indicator */}
      {status.gas_price_gwei && parseFloat(status.gas_price_gwei) > 0 && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          padding: '0.5rem 0.65rem',
          borderRadius: '8px',
          marginBottom: '0.75rem',
          background: status.gas_too_high
            ? 'rgba(239, 68, 68, 0.08)'
            : 'rgba(16, 185, 129, 0.08)',
          border: `1px solid ${status.gas_too_high
            ? 'rgba(239, 68, 68, 0.2)'
            : 'rgba(16, 185, 129, 0.2)'}`,
        }}>
          <span style={{ fontSize: '1rem' }}>⛽</span>
          <div style={{ flex: 1 }}>
            <div style={{
              fontSize: '0.78rem',
              fontWeight: 600,
              fontFamily: 'var(--font-mono)',
              color: status.gas_too_high ? '#ef4444' : '#10b981',
            }}>
              {parseFloat(status.gas_price_gwei).toFixed(1)} gwei
            </div>
            <div style={{ fontSize: '0.68rem', color: '#8888a0' }}>
              {status.gas_too_high
                ? 'Too high — skipping compound'
                : 'Compounding profitable ✅'}
            </div>
          </div>
        </div>
      )}

      <div className="vault-visual">
        <div className="vault-bar">
          <div
            className="vault-fill"
            style={{
              width: `${Math.min(100, parseFloat(status.vault_balance) * 10)}%`,
            }}
          />
        </div>
        <div className="vault-label">
          💰 Savings Vault: ${parseFloat(status.vault_balance).toFixed(4)}
        </div>
      </div>

      {status.reasoning && (
        <div className="reasoning-line">🧠 {status.reasoning}</div>
      )}
    </div>
  )
}

function StatItem({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="stat-item">
      <span className="stat-label">{label}</span>
      <span className={`stat-value ${highlight ? 'highlight' : ''}`}>{value}</span>
    </div>
  )
}

function PanelSkeleton() {
  return (
    <div className="panel grow-panel skeleton">
      <div className="panel-header">
        <div className="panel-icon">📈</div>
        <div>
          <h2>Grow Agent</h2>
          <span className="panel-label">Initializing...</span>
        </div>
      </div>
    </div>
  )
}
