import type { MemoryEvent } from '../types'

interface Props {
  events: MemoryEvent[]
}

const AGENT_COLORS: Record<string, string> = {
  guard: '#ef4444',
  grow: '#10b981',
  legacy: '#8b5cf6',
  rebalance: '#3b82f6',
  mev: '#f97316',
  orchestrator: '#6366f1',
}

const AGENT_ICONS: Record<string, string> = {
  guard: '🛡️',
  grow: '📈',
  legacy: '🏛️',
  rebalance: '🎯',
  mev: '🥪',
  orchestrator: '⚙️',
}

const COOPERATION_PATTERNS: { trigger: string; responders: string[]; label: string }[] = [
  { trigger: 'guard', responders: ['mev', 'rebalance'], label: 'Threat Detection Chain' },
  { trigger: 'mev', responders: ['guard', 'grow'], label: 'MEV Response Chain' },
  { trigger: 'rebalance', responders: ['guard', 'grow'], label: 'Rebalance Coordination' },
  { trigger: 'orchestrator', responders: ['guard', 'grow', 'rebalance', 'mev', 'legacy'], label: 'System Coordination' },
]

function classifyCooperation(events: MemoryEvent[]): { chain: string; events: MemoryEvent[] }[] {
  if (events.length < 2) return []

  const chains: { chain: string; events: MemoryEvent[] }[] = []
  const used = new Set<number>()

  for (let i = 0; i < events.length; i++) {
    if (used.has(i)) continue
    const trigger = events[i]
    const pattern = COOPERATION_PATTERNS.find(p => p.trigger === trigger.agent)
    if (!pattern) continue

    const group: MemoryEvent[] = [trigger]
    used.add(i)

    for (let j = i + 1; j < events.length && j < i + 8; j++) {
      if (used.has(j)) continue
      if (Math.abs(events[j].timestamp - trigger.timestamp) > 15) break
      if (pattern.responders.includes(events[j].agent)) {
        group.push(events[j])
        used.add(j)
      }
    }

    if (group.length >= 2) {
      chains.push({ chain: pattern.label, events: group })
    }
  }

  return chains.slice(-5).reverse()
}

export function CooperationPanel({ events }: Props) {
  const chains = classifyCooperation(events)

  const uniqueAgents = [...new Set(events.map(e => e.agent))].filter(a => a !== 'orchestrator')

  return (
    <div className="cooperation-panel-wrapper">
      <div className="panel cooperation-panel">
        <div className="panel-header">
          <div
            className="panel-icon"
            style={{ background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.25), rgba(139, 92, 246, 0.15))' }}
          >
            🤝
          </div>
          <div>
            <h2>Agent Cooperation</h2>
            <span className="panel-label">Inter-agent coordination timeline</span>
          </div>
          <div className="cooperation-agent-dots">
            {uniqueAgents.slice(0, 5).map(agent => (
              <span
                key={agent}
                className="cooperation-agent-dot"
                style={{ background: AGENT_COLORS[agent] ?? '#6b7280' }}
                title={agent}
              />
            ))}
          </div>
        </div>

        {chains.length > 0 ? (
          <div className="cooperation-chains">
            {chains.map((chain, ci) => (
              <div key={ci} className="cooperation-chain">
                <div className="cooperation-chain__label">{chain.chain}</div>
                <div className="cooperation-chain__flow">
                  {chain.events.map((evt, ei) => {
                    const color = AGENT_COLORS[evt.agent] ?? '#6b7280'
                    const icon = AGENT_ICONS[evt.agent] ?? '🤖'
                    const msg = (evt.data as Record<string, string>)?.message ?? evt.event_type
                    return (
                      <div key={ei} className="cooperation-node">
                        {ei > 0 && (
                          <div className="cooperation-connector">
                            <div className="cooperation-connector__line" />
                            <span className="cooperation-connector__arrow">→</span>
                          </div>
                        )}
                        <div
                          className="cooperation-node__card"
                          style={{ borderColor: `${color}40` }}
                        >
                          <div className="cooperation-node__header">
                            <span className="cooperation-node__icon">{icon}</span>
                            <span className="cooperation-node__agent" style={{ color }}>
                              {evt.agent}
                            </span>
                            <span className="cooperation-node__time">
                              {new Date(evt.timestamp * 1000).toLocaleTimeString()}
                            </span>
                          </div>
                          <div className="cooperation-node__msg">
                            {msg.length > 80 ? `${msg.slice(0, 80)}…` : msg}
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="cooperation-empty">
            <span className="cooperation-empty__icon">🤝</span>
            <p>Agents are coordinating in the background...</p>
            <p className="cooperation-empty__sub">
              Cooperation events appear when agents detect threats and coordinate responses
            </p>
          </div>
        )}

        {events.length > 0 && (
          <div className="cooperation-summary">
            <div className="cooperation-summary__item">
              <span className="cooperation-summary__value">{events.length}</span>
              <span className="cooperation-summary__label">Total Events</span>
            </div>
            <div className="cooperation-summary__item">
              <span className="cooperation-summary__value">{uniqueAgents.length}</span>
              <span className="cooperation-summary__label">Active Agents</span>
            </div>
            <div className="cooperation-summary__item">
              <span className="cooperation-summary__value">{chains.length}</span>
              <span className="cooperation-summary__label">Cooperation Chains</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
