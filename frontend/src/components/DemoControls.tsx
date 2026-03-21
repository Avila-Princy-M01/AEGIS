import * as api from '../api'

export function DemoControls() {
  return (
    <div className="demo-controls">
      <button
        className="demo-btn threat"
        onClick={() => api.simulateThreat('price_drop')}
        title="Simulate a sudden price crash"
      >
        ⚡ Simulate Crash
      </button>
      <button
        className="demo-btn inherit"
        onClick={() => api.simulateInherit()}
        title="Trigger inheritance distribution"
      >
        🏛️ Trigger Inheritance
      </button>
      <button
        className="demo-btn rebalance"
        onClick={() => api.simulateOutOfRange()}
        title="Force position out of range"
      >
        🎯 Out of Range
      </button>
      <button
        className="demo-btn mev"
        onClick={() => api.simulateMev('sandwich')}
        title="Simulate a sandwich attack"
      >
        🥪 Simulate MEV
      </button>
      <button
        className="demo-btn checkin"
        onClick={() => api.checkIn()}
        title="Check in to reset Legacy timer"
      >
        ✅ Check In
      </button>
      <button
        className="demo-btn stop"
        onClick={() => api.stopAgents()}
        title="Stop all agents"
      >
        ⏹ Stop
      </button>
    </div>
  )
}
