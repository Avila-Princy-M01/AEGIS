import type { AgentIdentityData } from '../types'
import { AnimatedNumber } from './AnimatedNumber'

interface Props {
  data: AgentIdentityData | null
}

function shortenAddress(addr: string): string {
  if (!addr || addr.length < 12) return addr
  return `${addr.slice(0, 6)}…${addr.slice(-4)}`
}

function formatUptime(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}s`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  return `${h}h ${m}m`
}

export function AgentIdentityPanel({ data }: Props) {
  if (!data) return <IdentitySkeleton />

  const m = data.autonomy_metrics

  return (
    <div className="identity-panel-wrapper">
      <div className="panel identity-panel">
        <div className="panel-header">
          <div
            className="panel-icon"
            style={{ background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.25), rgba(139, 92, 246, 0.15))' }}
          >
            🪪
          </div>
          <div>
            <h2>Agent Identity — ERC-8004</h2>
            <span className="panel-label">Protocol Labs · Let the Agent Cook</span>
          </div>
          <div className="identity-track-badge">
            <span className="identity-track-dot" />
            Protocol Labs Track
          </div>
        </div>

        {/* Identity Card */}
        <div className="identity-card">
          <div className="identity-card__header">
            <div className="identity-card__avatar">🛡️</div>
            <div className="identity-card__name-block">
              <span className="identity-card__name">{data.agent_name}</span>
              <span className="identity-card__version">v{data.version}</span>
            </div>
            <div className={`identity-card__status identity-card__status--${data.status}`}>
              <span className="identity-card__status-dot" />
              {data.status === 'active' ? 'Active' : 'Inactive'}
            </div>
          </div>
          <div className="identity-card__fields">
            <div className="identity-card__field">
              <span className="identity-card__field-label">Wallet</span>
              <span className="identity-card__field-value mono">{shortenAddress(data.agent_wallet)}</span>
            </div>
            <div className="identity-card__field">
              <span className="identity-card__field-label">Registry</span>
              <span className="identity-card__field-value">{data.registry_chain}</span>
            </div>
            <div className="identity-card__field">
              <span className="identity-card__field-label">Registration</span>
              <a
                href={data.registration_url}
                target="_blank"
                rel="noopener noreferrer"
                className="identity-card__field-value identity-card__link"
              >
                {shortenAddress(data.registration_tx)} ↗
              </a>
            </div>
            <div className="identity-card__field">
              <span className="identity-card__field-label">Participant</span>
              <span className="identity-card__field-value mono">{data.participant_id.slice(0, 12)}…</span>
            </div>
          </div>
        </div>

        {/* Capabilities */}
        <div className="identity-capabilities">
          <span className="identity-section-label">Capabilities</span>
          <div className="identity-caps-grid">
            {data.capabilities.map((cap) => (
              <div key={cap.name} className={`identity-cap identity-cap--${cap.agent}`}>
                <span className="identity-cap__icon">{cap.icon}</span>
                <span className="identity-cap__name">{cap.name}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Autonomy Metrics */}
        <div className="identity-autonomy">
          <span className="identity-section-label">Autonomy Metrics — "Let the Agent Cook"</span>
          <div className="identity-metrics-grid">
            <div className="identity-metric">
              <span className="identity-metric__value">{formatUptime(m.uptime_seconds)}</span>
              <span className="identity-metric__label">Uptime</span>
            </div>
            <div className="identity-metric">
              <span className="identity-metric__value">{m.total_decisions}</span>
              <span className="identity-metric__label">Autonomous Decisions</span>
            </div>
            <div className="identity-metric">
              <span className="identity-metric__value">{m.cooperation_events}</span>
              <span className="identity-metric__label">Cooperation Events</span>
            </div>
            <div className="identity-metric identity-metric--highlight">
              <span className="identity-metric__value">
                <AnimatedNumber value={m.autonomy_pct} decimals={1} />%
              </span>
              <span className="identity-metric__label">Autonomy Score</span>
            </div>
          </div>
          {/* Autonomy bar */}
          <div className="identity-autonomy-bar">
            <div
              className="identity-autonomy-bar__fill"
              style={{ width: `${Math.min(100, m.autonomy_pct)}%` }}
            />
          </div>
          <div className="identity-autonomy-legend">
            <span>🤖 {m.total_decisions} autonomous</span>
            <span>👤 {m.human_interventions} human</span>
            <span>📊 {m.total_events} total events</span>
          </div>
        </div>

        {/* Trust Model Footer */}
        <div className="identity-trust-footer">
          <span>🔒 {data.trust_model.type}</span>
          <span>🔑 No private keys</span>
          <span>📋 ERC-8004 logged</span>
          <span>🏦 Self-custody</span>
        </div>
      </div>
    </div>
  )
}

function IdentitySkeleton() {
  return (
    <div className="identity-panel-wrapper">
      <div className="panel identity-panel skeleton" style={{ minHeight: 200 }}>
        <div className="panel-header">
          <div className="panel-icon">🪪</div>
          <div>
            <h2>Agent Identity — ERC-8004</h2>
            <span className="panel-label">Loading...</span>
          </div>
        </div>
      </div>
    </div>
  )
}
