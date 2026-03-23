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
  swap_route?: SwapQuote
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

export interface MevStatus extends AgentStatus {
  paused: boolean
  mev_level: 'safe' | 'warning' | 'critical'
  live_data?: boolean
  chain?: string
  token_pair?: string
  sandwich_count: number
  frontrun_count: number
  total_mev_detected: number
  estimated_mev_cost_usd: string
  last_alert: string
  reasoning?: string
  safe_route?: SwapQuote
  config?: {
    sandwich_detection: boolean
    price_impact_threshold: string
    frontrun_window: number
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

export interface LidoYieldData {
  lp_apr_pct: string
  staking_apr_pct: string
  recommendation: 'lp' | 'stake'
  spread_pct: string
  reasoning: string
}

export interface PoolAllocationEntry {
  pool: string
  weight_pct: string
  fee_apr: string
  il_risk: string
  reasoning: string
}

export interface PoolAllocationData {
  allocations: PoolAllocationEntry[]
  strategy_name: string
}

export interface SwapRoutePool {
  type: string
  address: string
  fee: string
  tokenIn: string
  tokenOut: string
}

export interface SwapQuote {
  token_in: string
  token_out: string
  chain_id: number
  amount_in: string
  amount_out: string
  gas_estimate: string
  gas_usd: string
  price_impact: string
  routing: string
  route: SwapRoutePool[]
  slippage: number
  source: string
  error?: string
}

export interface SwapExecution {
  tx_hash: string
  explorer_url: string
  chain_id: number
  from: string
  status: string
  quote?: SwapQuote
  error?: string
}

export interface BacktestResult {
  period_days: number
  total_fees_earned: string
  total_il_loss: string
  gas_costs: string
  net_pnl: string
  max_drawdown_pct: string
  sharpe_ratio: string
  reasoning: string
}

export interface AgentCapability {
  name: string
  icon: string
  agent: string
}

export interface AgentIdentityData {
  agent_name: string
  version: string
  registry_chain: string
  registration_tx: string
  registration_url: string
  agent_wallet: string
  participant_id: string
  status: string
  capabilities: AgentCapability[]
  trust_model: {
    type: string
    private_keys: boolean
    on_chain_logging: boolean
    self_custody: boolean
  }
  autonomy_metrics: {
    uptime_seconds: number
    total_decisions: number
    cooperation_events: number
    human_interventions: number
    autonomy_pct: number
    total_events: number
  }
}

export interface LidoPoolData {
  label: string
  address: string
  fee_bps: number
  liquidity: string
  tick: number
  eth_price_usd: string
  live: boolean
}

export interface LidoMonitorData extends LidoYieldData {
  lido_pools: LidoPoolData[]
  lido_pools_count: number
  monitoring_events: number
  chain: string
  live: boolean
}

export interface UniswapPoolInfo {
  label: string
  address: string
  fee_bps: number
  tick: number
  eth_price_usd: string
  live: boolean
}

export interface UniswapSwapRecord {
  label: string
  chain: string
  tx_hash: string
  url: string
}

export interface UniswapIntegrationItem {
  name: string
  icon: string
  description: string
  status: string
}

export interface UniswapIntegrationData {
  pools: UniswapPoolInfo[]
  pools_count: number
  swap_history: UniswapSwapRecord[]
  total_confirmed_swaps: number
  fee_compounds: number
  trading_api_available: boolean
  chain: string
  live: boolean
  integrations: UniswapIntegrationItem[]
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
  rpc_status?: 'connected' | 'reconnecting' | 'error' | 'disconnected'
  rpc_provider?: string
  agents: {
    guard: GuardStatus | null
    grow: GrowStatus | null
    legacy: LegacyStatus | null
    rebalance: RebalanceStatus | null
    mev: MevStatus | null
  }
  memory_events: number
  config: Record<string, unknown>
}
