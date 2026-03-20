import type { MemoryEvent, PricePoint, SystemStatus } from './types'

const API_BASE = '/api'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

export async function deploy(command: string): Promise<{ success: boolean; status: SystemStatus }> {
  return request('/deploy', {
    method: 'POST',
    body: JSON.stringify({ command }),
  })
}

export async function getStatus(): Promise<SystemStatus> {
  return request('/status')
}

export async function getEvents(limit = 50): Promise<MemoryEvent[]> {
  return request(`/events?limit=${limit}`)
}

export async function checkIn(): Promise<Record<string, unknown>> {
  return request('/check-in', { method: 'POST' })
}

export async function simulateThreat(type = 'price_drop'): Promise<Record<string, unknown>> {
  return request('/simulate/threat', {
    method: 'POST',
    body: JSON.stringify({ threat_type: type }),
  })
}

export async function simulateInherit(): Promise<Record<string, unknown>> {
  return request('/simulate/inherit', { method: 'POST' })
}

export async function simulateOutOfRange(): Promise<Record<string, unknown>> {
  return request('/simulate/rebalance', { method: 'POST' })
}

export async function getPriceHistory(): Promise<PricePoint[]> {
  return request('/price-history')
}

export async function setDemoSpeed(multiplier: number): Promise<void> {
  await request('/demo-speed', {
    method: 'POST',
    body: JSON.stringify({ multiplier }),
  })
}

export async function stopAgents(): Promise<void> {
  await request('/stop', { method: 'POST' })
}

export async function switchChain(chain: string): Promise<SystemStatus> {
  return request('/switch-chain', {
    method: 'POST',
    body: JSON.stringify({ chain }),
  })
}

export function connectWebSocket(onEvent: (event: MemoryEvent) => void): WebSocket {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const ws = new WebSocket(`${protocol}//${window.location.host}/ws/feed`)
  ws.onmessage = (e) => {
    try {
      const event = JSON.parse(e.data) as MemoryEvent
      onEvent(event)
    } catch { /* ignore */ }
  }
  return ws
}
