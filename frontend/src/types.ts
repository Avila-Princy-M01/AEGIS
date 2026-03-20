export interface MemoryEvent {
  event_type: string
  agent: string
  data: Record<string, unknown>
  timestamp: number
}

export interface AgentStatus {
  agent: string
  running: boolean
  [key: string]: unknown
}

export interface PnlData {
  fees_earned: string
  il_loss: string
  gas_cost: string
  net: string
}

export interface GuardStatus extends AgentStatus {
  threat_level: 'safe' | 'warning' | 'critical'
  last_price: string
  position_value: string
  impermanent_loss_pct: string
  live_data?: boolean
  pool_address?: string
  chain?: string
  token_pair?: string
  reasoning?: string
  pnl?: PnlData
  config?: {
    il_threshold: string
    price_drop_alert: string
    auto_exit: boolean
  }
}

export interface GrowStatus extends AgentStatus {
  paused: boolean
  vault_balance: string
  total_fees_collected: string
  total_compounds: number
  live_data?: boolean
  token_pair?: string
  gas_price_gwei?: string
  gas_too_high?: boolean
  reasoning?: string
  config?: {
    compound_frequency_hours: number
    savings_sweep_pct: string
    auto_compound: boolean
  }
}

export interface RebalanceStatus extends AgentStatus {
  paused: boolean
  live_data?: boolean
  chain?: string
  token_pair?: string
  current_tick: number
  tick_lower: number
  tick_upper: number
  in_range: boolean
  range_utilization_pct: string
  suggested_lower: number
  suggested_upper: number
  rebalance_count: number
  reasoning?: string
  config?: {
    range_width_ticks: number
    auto_rebalance: boolean
    threshold_pct: string
  }
}

export interface PricePoint {
  timestamp: number
  price: string
  tick?: number
}

export interface LegacyStatus extends AgentStatus {
  last_check_in: number
  seconds_since_check_in: number
  threshold_days: number
  remaining_seconds: number
  remaining_human: string
  inheritance_triggered: boolean
  reasoning?: string
  beneficiaries: { address: string; share_pct: string; label: string }[]
}

export interface SystemStatus {
  started: boolean
  live_data?: boolean
  chain?: string
  pool_address?: string
  token_pair?: string
  available_pools?: string[]
  block_number?: number
  gas_price_gwei?: string
  eth_price?: string
  agents: {
    guard: GuardStatus | null
    grow: GrowStatus | null
    legacy: LegacyStatus | null
    rebalance: RebalanceStatus | null
  }
  memory_events: number
  config: Record<string, unknown>
}
