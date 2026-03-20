import type { MemoryEvent } from '../types'

interface Props {
  events: MemoryEvent[]
}

const AGENT_COLORS: Record<string, string> = {
  guard: '#ef4444',
  grow: '#10b981',
  legacy: '#8b5cf6',
  rebalance: '#3b82f6',
  orchestrator: '#6366f1',
}

export function ActivityFeed({ events }: Props) {
  const reversed = [...events].reverse()

  return (
    <div className="activity-feed">
      <div className="feed-header">
        <h2>📡 Activity Feed</h2>
        <span className="event-count">{events.length} events</span>
      </div>
      <div className="feed-list">
        {reversed.length === 0 && (
          <div className="feed-empty">Waiting for agent activity...</div>
        )}
        {reversed.map((event, i) => (
          <FeedItem key={`${event.timestamp}-${i}`} event={event} />
        ))}
      </div>
    </div>
  )
}

function FeedItem({ event }: { event: MemoryEvent }) {
  const color = AGENT_COLORS[event.agent] ?? '#6b7280'
  const message = (event.data as Record<string, string>)?.message ?? event.event_type
  const time = new Date(event.timestamp * 1000).toLocaleTimeString()

  return (
    <div className="feed-item">
      <div className="feed-dot" style={{ background: color }} />
      <div className="feed-content">
        <div className="feed-meta">
          <span className="feed-agent" style={{ color }}>{event.agent}</span>
          <span className="feed-type">{event.event_type}</span>
          <span className="feed-time">{time}</span>
        </div>
        <div className="feed-message">{message}</div>
      </div>
    </div>
  )
}
