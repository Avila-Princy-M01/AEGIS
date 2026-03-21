import type { ReactNode } from 'react'
import type { BacktestResult } from '../types'
import { AnimatedNumber } from './AnimatedNumber'

interface Props {
  results: BacktestResult | null
}

const THEME_COLOR = '#06b6d4'

export function BacktestPanel({ results }: Props) {
  if (!results) return <PanelSkeleton />

  const netPnl = parseFloat(results.net_pnl)
  const pnlColor = netPnl >= 0 ? '#10b981' : '#ef4444'
  const sharpe = parseFloat(results.sharpe_ratio)

  return (
    <div className="backtest-panel-wrapper">
      <div className="panel backtest-panel anim-backtest-fadein">
        <div className="panel-header">
          <div className="panel-icon" style={{ background: THEME_COLOR }}>📊</div>
          <div>
            <h2>Backtest Engine</h2>
            <span className="panel-label">Historical Simulation</span>
          </div>
        </div>

        <div className="panel-stats backtest-stats">
          <StatItem label="Period (days)">
            <span>{results.period_days}</span>
          </StatItem>
          <StatItem label="Total Fees Earned">
            <AnimatedNumber value={parseFloat(results.total_fees_earned)} prefix="$" decimals={2} />
          </StatItem>
          <StatItem label="Total IL Loss">
            <AnimatedNumber value={parseFloat(results.total_il_loss)} prefix="$" decimals={2} />
          </StatItem>
          <StatItem label="Gas Costs">
            <AnimatedNumber value={parseFloat(results.gas_costs)} prefix="$" decimals={2} />
          </StatItem>
          <StatItem label="Net P&L">
            <span style={{ color: pnlColor, fontWeight: 700 }}>
              <AnimatedNumber value={netPnl} prefix="$" decimals={2} />
            </span>
          </StatItem>
          <StatItem label="Max Drawdown">
            <span style={{ color: '#f59e0b' }}>{results.max_drawdown_pct}%</span>
          </StatItem>
          <StatItem label="Sharpe Ratio">
            <span style={{ color: sharpe >= 1 ? '#10b981' : sharpe >= 0 ? '#f59e0b' : '#ef4444' }}>
              {results.sharpe_ratio}
            </span>
          </StatItem>
        </div>

        {results.reasoning && (
          <div className="reasoning-line">🧠 {results.reasoning}</div>
        )}
      </div>
    </div>
  )
}

function StatItem({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="stat-item">
      <span className="stat-label">{label}</span>
      <span className="stat-value">{children}</span>
    </div>
  )
}

function PanelSkeleton() {
  return (
    <div className="backtest-panel-wrapper">
      <div className="panel backtest-panel skeleton">
        <div className="panel-header">
          <div className="panel-icon" style={{ background: THEME_COLOR }}>📊</div>
          <div>
            <h2>Backtest Engine</h2>
            <span className="panel-label">Initializing...</span>
          </div>
        </div>
      </div>
    </div>
  )
}
