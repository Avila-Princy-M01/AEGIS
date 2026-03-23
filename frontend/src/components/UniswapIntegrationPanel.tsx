import type { UniswapIntegrationData } from '../types'

interface Props {
  data: UniswapIntegrationData | null
}

function shortenAddress(addr: string): string {
  if (!addr || addr.length < 12) return addr
  return `${addr.slice(0, 6)}…${addr.slice(-4)}`
}

function shortenHash(hash: string): string {
  return `${hash.slice(0, 10)}…${hash.slice(-6)}`
}

const STATUS_COLORS: Record<string, string> = {
  active: '#10b981',
  connected: '#10b981',
  monitoring: '#f59e0b',
  inactive: '#6b7280',
  key_required: '#f59e0b',
}

export function UniswapIntegrationPanel({ data }: Props) {
  if (!data) return <UniswapSkeleton />

  return (
    <div className="uniswap-integration-wrapper">
      <div className="panel uniswap-integration-panel">
        <div className="panel-header">
          <div
            className="panel-icon"
            style={{ background: 'linear-gradient(135deg, rgba(255, 0, 122, 0.25), rgba(168, 85, 247, 0.15))' }}
          >
            🦄
          </div>
          <div>
            <h2>Uniswap Integration</h2>
            <span className="panel-label">Agentic Finance · Full Protocol Integration</span>
          </div>
          <div className="uniswap-track-badge">
            <span className="uniswap-track-dot" />
            Uniswap Track
          </div>
        </div>

        <div className={`data-source-badge ${data.live ? 'live' : 'simulated'}`}>
          <span className="badge-dot" />
          {data.live ? `LIVE · ${data.chain?.toUpperCase() ?? 'ETH'}` : 'SIMULATED'}
          <span style={{ color: '#8888a0', marginLeft: '0.25rem' }}>
            · {data.pools_count} pools · {data.total_confirmed_swaps} swaps
          </span>
        </div>

        {/* Integration Cards */}
        <div className="uniswap-integrations-grid">
          {data.integrations.map((item) => {
            const statusColor = STATUS_COLORS[item.status] ?? '#6b7280'
            return (
              <div key={item.name} className="uniswap-int-card">
                <div className="uniswap-int-card__header">
                  <span className="uniswap-int-card__icon">{item.icon}</span>
                  <span className="uniswap-int-card__name">{item.name}</span>
                  <span
                    className="uniswap-int-card__status"
                    style={{ color: statusColor }}
                  >
                    ● {item.status}
                  </span>
                </div>
                <div className="uniswap-int-card__desc">{item.description}</div>
              </div>
            )
          })}
        </div>

        {/* Pool Table */}
        {data.pools.length > 0 && (
          <div className="uniswap-pools-section">
            <span className="uniswap-section-label">Live Pool Monitoring</span>
            <div className="uniswap-pools-table">
              {data.pools.map((pool) => (
                <a
                  key={pool.address}
                  href={`https://etherscan.io/address/${pool.address}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="uniswap-pool-row"
                >
                  <span className="uniswap-pool-row__label">{pool.label}</span>
                  <span className="uniswap-pool-row__addr">{shortenAddress(pool.address)}</span>
                  <span className="uniswap-pool-row__fee">{(pool.fee_bps / 10000).toFixed(2)}%</span>
                  <span className="uniswap-pool-row__status">🟢</span>
                </a>
              ))}
            </div>
          </div>
        )}

        {/* Swap History */}
        <div className="uniswap-swaps-section">
          <span className="uniswap-section-label">Confirmed Swap Transactions</span>
          <div className="uniswap-swaps-list">
            {data.swap_history.map((swap) => (
              <a
                key={swap.tx_hash}
                href={swap.url}
                target="_blank"
                rel="noopener noreferrer"
                className="uniswap-swap-card"
              >
                <div className="uniswap-swap-card__icon">⚡</div>
                <div className="uniswap-swap-card__info">
                  <span className="uniswap-swap-card__label">{swap.label}</span>
                  <span className="uniswap-swap-card__chain">{swap.chain}</span>
                  <span className="uniswap-swap-card__hash">{shortenHash(swap.tx_hash)}</span>
                </div>
                <span className="uniswap-swap-card__arrow">↗</span>
              </a>
            ))}
          </div>
        </div>

        {/* Stats */}
        <div className="uniswap-stats">
          <div className="uniswap-stat">
            <span className="uniswap-stat__value">{data.pools_count}</span>
            <span className="uniswap-stat__label">Live Pools</span>
          </div>
          <div className="uniswap-stat">
            <span className="uniswap-stat__value">{data.total_confirmed_swaps}</span>
            <span className="uniswap-stat__label">Confirmed Swaps</span>
          </div>
          <div className="uniswap-stat">
            <span className="uniswap-stat__value">{data.fee_compounds}</span>
            <span className="uniswap-stat__label">Fee Compounds</span>
          </div>
          <div className="uniswap-stat">
            <span className="uniswap-stat__value">{data.trading_api_available ? '✅' : '🔑'}</span>
            <span className="uniswap-stat__label">Trading API</span>
          </div>
        </div>
      </div>
    </div>
  )
}

function UniswapSkeleton() {
  return (
    <div className="uniswap-integration-wrapper">
      <div className="panel uniswap-integration-panel skeleton" style={{ minHeight: 200 }}>
        <div className="panel-header">
          <div className="panel-icon">🦄</div>
          <div>
            <h2>Uniswap Integration</h2>
            <span className="panel-label">Loading...</span>
          </div>
        </div>
      </div>
    </div>
  )
}
