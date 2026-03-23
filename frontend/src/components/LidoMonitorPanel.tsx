import type { LidoMonitorData } from '../types'
import { AnimatedNumber } from './AnimatedNumber'

interface Props {
  data: LidoMonitorData | null
}

function shortenAddress(addr: string): string {
  if (!addr || addr.length < 12) return addr
  return `${addr.slice(0, 6)}…${addr.slice(-4)}`
}

export function LidoMonitorPanel({ data }: Props) {
  if (!data) return <LidoSkeleton />

  const lpApr = parseFloat(data.lp_apr_pct)
  const stakingApr = parseFloat(data.staking_apr_pct)
  const spread = parseFloat(data.spread_pct)
  const maxApr = Math.max(lpApr, stakingApr, 1)

  return (
    <div className="lido-monitor-wrapper">
      <div className="panel lido-monitor-panel">
        <div className="panel-header">
          <div
            className="panel-icon"
            style={{ background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.25), rgba(6, 182, 212, 0.15))' }}
          >
            🔵
          </div>
          <div>
            <h2>Vault Position Monitor</h2>
            <span className="panel-label">Lido Labs · LP vs Staking Yield</span>
          </div>
          <div className="lido-track-badge">
            <span className="lido-track-dot" />
            Lido Labs Track
          </div>
        </div>

        <div className={`data-source-badge ${data.live ? 'live' : 'simulated'}`}>
          <span className="badge-dot" />
          {data.live ? `LIVE · ${data.chain?.toUpperCase() ?? 'ETH'} Mainnet` : 'SIMULATED'}
          <span style={{ color: '#8888a0', marginLeft: '0.25rem' }}>
            · wstETH/ETH + stETH/ETH
          </span>
        </div>

        {/* APR Visual Comparison */}
        <div className="lido-apr-comparison">
          <div className="lido-apr-row">
            <div className="lido-apr-label">
              <span className="lido-apr-icon">🦄</span>
              <span>Uniswap LP APR</span>
            </div>
            <div className="lido-apr-bar-wrap">
              <div className="lido-apr-bar">
                <div
                  className="lido-apr-bar__fill lido-apr-bar__fill--lp"
                  style={{ width: `${Math.min(100, (lpApr / maxApr) * 100)}%` }}
                />
              </div>
              <span className="lido-apr-value lido-apr-value--lp">
                <AnimatedNumber value={lpApr} decimals={2} />%
              </span>
            </div>
          </div>
          <div className="lido-apr-row">
            <div className="lido-apr-label">
              <span className="lido-apr-icon">💧</span>
              <span>Lido Staking APR</span>
            </div>
            <div className="lido-apr-bar-wrap">
              <div className="lido-apr-bar">
                <div
                  className="lido-apr-bar__fill lido-apr-bar__fill--staking"
                  style={{ width: `${Math.min(100, (stakingApr / maxApr) * 100)}%` }}
                />
              </div>
              <span className="lido-apr-value lido-apr-value--staking">
                <AnimatedNumber value={stakingApr} decimals={2} />%
              </span>
            </div>
          </div>
        </div>

        {/* Verdict */}
        <div className={`lido-verdict lido-verdict--${data.recommendation}`}>
          <span className="lido-verdict__icon">
            {data.recommendation === 'lp' ? '📈' : '🔵'}
          </span>
          <div className="lido-verdict__text">
            <span className="lido-verdict__title">
              {data.recommendation === 'lp' ? 'LP Outperforms Staking' : 'Staking Outperforms LP'}
            </span>
            <span className="lido-verdict__spread">
              Spread: {spread >= 0 ? '+' : ''}<AnimatedNumber value={Math.abs(spread)} decimals={2} />%
            </span>
          </div>
        </div>

        {/* Lido Pool Cards */}
        {data.lido_pools.length > 0 && (
          <div className="lido-pools">
            <span className="lido-section-label">Monitored Lido Pools</span>
            <div className="lido-pools-grid">
              {data.lido_pools.map((pool) => (
                <a
                  key={pool.address}
                  href={`https://etherscan.io/address/${pool.address}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="lido-pool-card"
                >
                  <div className="lido-pool-card__header">
                    <span className="lido-pool-card__label">{pool.label}</span>
                    <span className="lido-pool-card__live">🟢 LIVE</span>
                  </div>
                  <div className="lido-pool-card__details">
                    <span>{shortenAddress(pool.address)}</span>
                    <span>Fee: {(pool.fee_bps / 10000).toFixed(2)}%</span>
                    <span>Tick: {pool.tick}</span>
                  </div>
                </a>
              ))}
            </div>
          </div>
        )}

        {/* Stats */}
        <div className="lido-stats">
          <div className="lido-stat">
            <span className="lido-stat__value">{data.lido_pools_count}</span>
            <span className="lido-stat__label">Lido Pools</span>
          </div>
          <div className="lido-stat">
            <span className="lido-stat__value">{data.monitoring_events}</span>
            <span className="lido-stat__label">Yield Events</span>
          </div>
          <div className="lido-stat">
            <span className="lido-stat__value">{data.chain?.toUpperCase() || 'ETH'}</span>
            <span className="lido-stat__label">Network</span>
          </div>
        </div>

        {data.reasoning && (
          <div className="reasoning-line">🧠 {data.reasoning}</div>
        )}

        <div className="lido-footer">
          Monitoring Lido pools live on Ethereum Mainnet · wstETH/ETH 0.01% + stETH/ETH 1%
        </div>
      </div>
    </div>
  )
}

function LidoSkeleton() {
  return (
    <div className="lido-monitor-wrapper">
      <div className="panel lido-monitor-panel skeleton" style={{ minHeight: 200 }}>
        <div className="panel-header">
          <div className="panel-icon">🔵</div>
          <div>
            <h2>Vault Position Monitor</h2>
            <span className="panel-label">Loading Lido data...</span>
          </div>
        </div>
      </div>
    </div>
  )
}
