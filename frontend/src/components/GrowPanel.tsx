import type { ReactNode } from 'react'
import type { GrowStatus } from '../types'
import { AnimatedNumber } from './AnimatedNumber'

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

      <div className={`data-source-badge ${isLive ? 'live' : 'simulated'}`}>
        <span className="badge-dot" />
        {isLive ? 'LIVE · Fee Growth Tracking' : 'SIMULATED'}
        {status.token_pair && (
          <span style={{ color: '#8888a0', marginLeft: '0.25rem' }}>
            · {status.token_pair}
          </span>
        )}
      </div>

      <div className="panel-stats">
        <StatItem label="Vault Balance" highlight>
          <AnimatedNumber value={parseFloat(status.vault_balance)} prefix="$" decimals={4} />
        </StatItem>
        <StatItem label="Fees Collected">
          <AnimatedNumber value={parseFloat(status.total_fees_collected)} prefix="$" decimals={4} />
        </StatItem>
        <StatItem label="Compounds">
          <span>{status.total_compounds}</span>
        </StatItem>
        <StatItem label="Savings Rate">
          <span>{status.config?.savings_sweep_pct}%</span>
        </StatItem>
      </div>

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
          transition: 'all 0.3s ease',
        }}>
          <span style={{ fontSize: '1rem' }}>⛽</span>
          <div style={{ flex: 1 }}>
            <div style={{
              fontSize: '0.78rem',
              fontWeight: 600,
              fontFamily: 'var(--font-mono)',
              color: status.gas_too_high ? '#ef4444' : '#10b981',
            }}>
              <AnimatedNumber value={parseFloat(status.gas_price_gwei)} decimals={1} suffix=" gwei" locale={false} />
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
          💰 Savings Vault: $<AnimatedNumber value={parseFloat(status.vault_balance)} decimals={4} locale={false} />
        </div>
      </div>

      {status.swap_route && status.swap_route.source && (
        <div style={{
          marginTop: '0.5rem',
          padding: '0.5rem 0.65rem',
          borderRadius: '8px',
          background: 'rgba(255, 0, 122, 0.04)',
          border: '1px solid rgba(255, 0, 122, 0.12)',
          fontSize: '0.72rem',
          fontFamily: 'var(--font-mono)',
        }}>
          <div style={{ color: '#ff007a', fontWeight: 700, marginBottom: '0.25rem' }}>
            🦄 Uniswap Swap Route
          </div>
          <div style={{ color: '#8888a0' }}>
            {status.swap_route.routing} · Gas ~${parseFloat(status.swap_route.gas_usd || '0').toFixed(2)}
            {status.swap_route.route?.length > 0 && (
              <span> · {status.swap_route.route.map((r: { tokenIn: string; tokenOut: string }) => `${r.tokenIn}→${r.tokenOut}`).join(' → ')}</span>
            )}
          </div>
        </div>
      )}

      {status.reasoning && (
        <div className="reasoning-line">🧠 {status.reasoning}</div>
      )}
    </div>
  )
}

function StatItem({ label, children, highlight }: { label: string; children: ReactNode; highlight?: boolean }) {
  return (
    <div className="stat-item">
      <span className="stat-label">{label}</span>
      <span className={`stat-value ${highlight ? 'highlight' : ''}`}>{children}</span>
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
