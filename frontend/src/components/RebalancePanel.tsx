import type { RebalanceStatus } from '../types'

interface Props {
  status: RebalanceStatus | null
}

export function RebalancePanel({ status }: Props) {
  if (!status) return <PanelSkeleton />

  const isLive = status.live_data ?? false
  const inRange = status.in_range
  const utilization = parseFloat(status.range_utilization_pct)

  const rangeColor = !inRange
    ? '#ef4444'
    : utilization < 10 || utilization > 90
      ? '#f59e0b'
      : '#10b981'

  const animClass = !inRange ? 'anim-range-shake' : ''

  return (
    <div className={`panel rebalance-panel ${!inRange ? 'out-of-range' : ''} ${animClass}`}>
      <div className="panel-header">
        <div className="panel-icon" style={{ background: rangeColor }}>🎯</div>
        <div>
          <h2>Rebalance Agent</h2>
          <span className="panel-label">
            {status.paused ? '⏸️ Paused (threat detected)' : 'Range Monitoring'}
          </span>
        </div>
        <div className="threat-badge" style={{ background: rangeColor }}>
          {inRange ? 'IN RANGE' : 'OUT OF RANGE'}
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

      {/* Range Visualization */}
      <div className="range-visualization">
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          fontSize: '0.65rem',
          color: '#55556a',
          fontFamily: 'var(--font-mono)',
          marginBottom: '4px',
        }}>
          <span>{status.tick_lower}</span>
          <span style={{ color: '#8888a0' }}>tick {status.current_tick}</span>
          <span>{status.tick_upper}</span>
        </div>
        <div style={{
          position: 'relative',
          height: '28px',
          background: 'rgba(255, 255, 255, 0.03)',
          borderRadius: '8px',
          overflow: 'hidden',
          border: `1px solid ${rangeColor}22`,
        }}>
          {/* Range area gradient */}
          <div style={{
            position: 'absolute',
            left: 0,
            right: 0,
            top: 0,
            bottom: 0,
            background: `linear-gradient(90deg, ${rangeColor}05, ${rangeColor}12, ${rangeColor}05)`,
          }} />
          {/* Tick position indicator */}
          <div style={{
            position: 'absolute',
            left: `${Math.max(0, Math.min(100, utilization))}%`,
            top: '2px',
            bottom: '2px',
            width: '3px',
            background: rangeColor,
            borderRadius: '2px',
            boxShadow: `0 0 10px ${rangeColor}, 0 0 20px ${rangeColor}50`,
            transform: 'translateX(-50%)',
            transition: 'left 1s ease',
          }} />
          {/* Center line */}
          <div style={{
            position: 'absolute',
            left: '50%',
            top: '4px',
            bottom: '4px',
            width: '1px',
            background: 'rgba(255, 255, 255, 0.06)',
          }} />
        </div>
        <div style={{
          textAlign: 'center',
          marginTop: '4px',
          fontSize: '0.72rem',
          fontWeight: 600,
          color: rangeColor,
        }}>
          {inRange
            ? `${utilization.toFixed(1)}% through range`
            : '⚠️ Earning ZERO fees!'}
        </div>
      </div>

      <div className="panel-stats" style={{ marginTop: '0.75rem' }}>
        <StatItem label="Range Width" value={`${status.config?.range_width_ticks ?? 0} ticks`} />
        <StatItem label="Rebalances" value={`${status.rebalance_count}`} />
        <StatItem label="Auto-Rebalance" value={status.config?.auto_rebalance ? '✅ ON' : '🔒 Suggest Only'} />
        <StatItem
          label="Utilization"
          value={`${utilization.toFixed(1)}%`}
          warn={utilization < 10 || utilization > 90}
        />
      </div>

      {status.suggested_lower !== 0 && !inRange && (
        <div style={{
          marginTop: '0.75rem',
          padding: '0.6rem',
          borderRadius: '8px',
          background: 'rgba(245, 158, 11, 0.06)',
          border: '1px solid rgba(245, 158, 11, 0.15)',
          fontSize: '0.78rem',
          animation: 'fadeInUp 0.4s ease',
        }}>
          <div style={{ color: '#f59e0b', fontWeight: 700, marginBottom: '0.25rem' }}>
            💡 Suggested Rebalance
          </div>
          <div style={{ color: '#8888a0', fontFamily: 'var(--font-mono)', fontSize: '0.72rem' }}>
            New range: [{status.suggested_lower}, {status.suggested_upper}]
          </div>
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
    <div className="panel rebalance-panel skeleton">
      <div className="panel-header">
        <div className="panel-icon">🎯</div>
        <div>
          <h2>Rebalance Agent</h2>
          <span className="panel-label">Initializing...</span>
        </div>
      </div>
    </div>
  )
}
