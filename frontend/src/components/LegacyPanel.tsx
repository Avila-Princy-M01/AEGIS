import type { LegacyStatus } from '../types'

interface Props {
  status: LegacyStatus | null
}

export function LegacyPanel({ status }: Props) {
  if (!status) return <PanelSkeleton />

  const pct = status.remaining_seconds > 0
    ? ((status.threshold_days * 86400 - status.remaining_seconds) / (status.threshold_days * 86400)) * 100
    : 100

  const animClass = status.inheritance_triggered ? 'anim-legacy-glow' : ''

  return (
    <div className={`panel legacy-panel ${status.inheritance_triggered ? 'triggered' : ''} ${animClass}`}>
      <div className="panel-header">
        <div
          className="panel-icon"
          style={{ background: status.inheritance_triggered ? '#ef4444' : '#8b5cf6' }}
        >
          🏛️
        </div>
        <div>
          <h2>Legacy Agent</h2>
          <span className="panel-label">
            {status.inheritance_triggered ? '⚡ Inheritance Triggered' : 'Dead Man\'s Switch'}
          </span>
        </div>
      </div>

      <div className="countdown-section">
        <div className="countdown-value">
          {status.inheritance_triggered ? 'TRIGGERED' : status.remaining_human || 'Calculating...'}
        </div>
        <div className="countdown-label">
          {status.inheritance_triggered
            ? 'Assets being distributed to beneficiaries'
            : `until inheritance (${status.threshold_days} day threshold)`}
        </div>
        <div className="countdown-bar">
          <div
            className="countdown-fill"
            style={{
              width: `${Math.min(100, pct)}%`,
              background: pct > 75 ? '#ef4444' : pct > 50 ? '#f59e0b' : '#8b5cf6',
            }}
          />
        </div>
      </div>

      {status.beneficiaries.length > 0 && (
        <div className="beneficiaries">
          <h3>Beneficiaries</h3>
          {status.beneficiaries.map((b, i) => (
            <div key={i} className="beneficiary-row">
              <span className="beneficiary-label">{b.label || 'Wallet'}</span>
              <span className="beneficiary-addr">{b.address.slice(0, 6)}...{b.address.slice(-4)}</span>
              <span className="beneficiary-share">{b.share_pct}%</span>
            </div>
          ))}
        </div>
      )}

      {status.reasoning && (
        <div className="reasoning-line">🧠 {status.reasoning}</div>
      )}
    </div>
  )
}

function PanelSkeleton() {
  return (
    <div className="panel legacy-panel skeleton">
      <div className="panel-header">
        <div className="panel-icon">🏛️</div>
        <div>
          <h2>Legacy Agent</h2>
          <span className="panel-label">Initializing...</span>
        </div>
      </div>
    </div>
  )
}
