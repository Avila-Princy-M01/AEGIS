import type { LidoYieldData, PoolAllocationData } from '../types'
import { AnimatedNumber } from './AnimatedNumber'

interface Props {
  lidoYield: LidoYieldData | null
  poolAllocation: PoolAllocationData | null
}

export function AnalyticsPanel({ lidoYield, poolAllocation }: Props) {
  if (!lidoYield && !poolAllocation) return <AnalyticsSkeleton />

  return (
    <div className="analytics-panel-wrapper">
      <div className="analytics-grid">
        {/* ── Lido Yield Comparison ── */}
        {lidoYield && (
          <div className="panel analytics-card analytics-lido">
            <div className="panel-header">
              <div
                className="panel-icon"
                style={{ background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(6, 182, 212, 0.1))' }}
              >
                💧
              </div>
              <div>
                <h2>Lido Yield Comparison</h2>
                <span className="panel-label">LP vs Staking</span>
              </div>
              <span
                className="threat-badge"
                style={{
                  background: lidoYield.recommendation === 'lp'
                    ? 'linear-gradient(135deg, #10b981, #059669)'
                    : 'linear-gradient(135deg, #3b82f6, #2563eb)',
                }}
              >
                {lidoYield.recommendation === 'lp' ? '📈 LP WINS' : '🔵 STAKE WINS'}
              </span>
            </div>

            <div className="yield-comparison">
              <div className="yield-card">
                <span className="yield-label">🦄 Uniswap LP APR</span>
                <span className="yield-value yield-lp">
                  <AnimatedNumber value={parseFloat(lidoYield.lp_apr_pct)} decimals={2} />%
                </span>
              </div>
              <div className="yield-vs">vs</div>
              <div className="yield-card">
                <span className="yield-label">💧 Lido Staking APR</span>
                <span className="yield-value yield-staking">
                  <AnimatedNumber value={parseFloat(lidoYield.staking_apr_pct)} decimals={2} />%
                </span>
              </div>
            </div>

            <div className="yield-spread">
              <span className="yield-spread-label">Spread</span>
              <span className={`yield-spread-value ${parseFloat(lidoYield.spread_pct) >= 0 ? 'positive' : 'negative'}`}>
                {parseFloat(lidoYield.spread_pct) >= 0 ? '+' : ''}
                <AnimatedNumber value={Math.abs(parseFloat(lidoYield.spread_pct))} decimals={2} />%
              </span>
            </div>

            <div className="reasoning-line">🧠 {lidoYield.reasoning}</div>
          </div>
        )}

        {/* ── Cross-Pool Allocation ── */}
        {poolAllocation && poolAllocation.allocations.length > 0 && (
          <div className="panel analytics-card analytics-pools">
            <div className="panel-header">
              <div
                className="panel-icon"
                style={{ background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(99, 102, 241, 0.1))' }}
              >
                🏊
              </div>
              <div>
                <h2>Cross-Pool Allocation</h2>
                <span className="panel-label">{poolAllocation.strategy_name} strategy</span>
              </div>
              <span
                className="threat-badge"
                style={{ background: 'linear-gradient(135deg, #8b5cf6, #6d28d9)' }}
              >
                {poolAllocation.allocations.length} POOLS
              </span>
            </div>

            <div className="pool-alloc-list">
              {poolAllocation.allocations.map((a) => {
                const weight = parseFloat(a.weight_pct)
                return (
                  <div key={a.pool} className="pool-alloc-row">
                    <div className="pool-alloc-info">
                      <span className="pool-alloc-name">{a.pool}</span>
                      <span className="pool-alloc-meta">
                        APR {a.fee_apr}% · IL risk {a.il_risk}%
                      </span>
                    </div>
                    <div className="pool-alloc-bar-wrap">
                      <div className="pool-alloc-bar">
                        <div
                          className="pool-alloc-fill"
                          style={{ width: `${Math.min(weight, 100)}%` }}
                        />
                      </div>
                      <span className="pool-alloc-weight">{a.weight_pct}%</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function AnalyticsSkeleton() {
  return (
    <div className="analytics-panel-wrapper">
      <div className="analytics-grid">
        <div className="panel skeleton" style={{ minHeight: 180 }} />
        <div className="panel skeleton" style={{ minHeight: 180 }} />
      </div>
    </div>
  )
}
