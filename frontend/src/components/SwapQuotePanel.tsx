import { useState } from 'react'
import type { SwapQuote, SwapExecution } from '../types'
import * as api from '../api'

interface Props {
  chain: string
}

const TOKEN_LABELS: Record<string, string> = {
  WETH: 'Wrapped ETH',
  USDC: 'USD Coin',
  USDT: 'Tether',
  wstETH: 'Wrapped stETH',
}

const AMOUNT_PRESETS = [
  { label: '0.01 ETH', wei: '10000000000000000' },
  { label: '0.1 ETH', wei: '100000000000000000' },
  { label: '1 ETH', wei: '1000000000000000000' },
]

function formatAmount(raw: string, decimals: number): string {
  const num = parseFloat(raw) / 10 ** decimals
  if (num >= 1000) return num.toLocaleString(undefined, { maximumFractionDigits: 2 })
  if (num >= 1) return num.toFixed(4)
  return num.toFixed(6)
}

function shortenAddress(addr: string): string {
  if (!addr || addr.length < 12) return addr
  return `${addr.slice(0, 6)}…${addr.slice(-4)}`
}

export function SwapQuotePanel({ chain }: Props) {
  const [quote, setQuote] = useState<SwapQuote | null>(null)
  const [loading, setLoading] = useState(false)
  const [executing, setExecuting] = useState(false)
  const [execution, setExecution] = useState<SwapExecution | null>(null)
  const [selectedAmount, setSelectedAmount] = useState(2)
  const [tokenOut, setTokenOut] = useState('USDC')

  const fetchQuote = async () => {
    setLoading(true)
    try {
      const q = await api.getSwapQuote('WETH', tokenOut, AMOUNT_PRESETS[selectedAmount].wei, chain)
      setQuote(q)
    } catch {
      setQuote(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="swap-quote-panel-wrapper">
      <div className="panel swap-quote-panel">
        <div className="panel-header">
          <div
            className="panel-icon"
            style={{ background: 'linear-gradient(135deg, rgba(255, 0, 122, 0.2), rgba(168, 85, 247, 0.1))' }}
          >
            🦄
          </div>
          <div>
            <h2>Uniswap Trading API</h2>
            <span className="panel-label">Real swap quotes from Uniswap Developer Platform</span>
          </div>
          <div className="swap-api-badge">
            <span className="swap-api-dot" />
            API Connected
          </div>
        </div>

        <div className="swap-controls">
          <div className="swap-amount-presets">
            {AMOUNT_PRESETS.map((preset, i) => (
              <button
                key={preset.label}
                className={`swap-preset-btn ${selectedAmount === i ? 'active' : ''}`}
                onClick={() => setSelectedAmount(i)}
              >
                {preset.label}
              </button>
            ))}
          </div>
          <div className="swap-token-select">
            {['USDC', 'USDT', 'wstETH'].map(t => (
              <button
                key={t}
                className={`swap-preset-btn ${tokenOut === t ? 'active' : ''}`}
                onClick={() => setTokenOut(t)}
              >
                → {t}
              </button>
            ))}
          </div>
          <button
            className="swap-fetch-btn"
            onClick={fetchQuote}
            disabled={loading}
          >
            {loading ? <span className="spinner" /> : '🔄 Get Live Quote'}
          </button>
        </div>

        {quote && !quote.error && (
          <div className="swap-result">
            <div className="swap-pair">
              <div className="swap-token-card swap-token-in">
                <span className="swap-token-icon">⟠</span>
                <div className="swap-token-info">
                  <span className="swap-token-amount">{formatAmount(quote.amount_in, 18)}</span>
                  <span className="swap-token-name">WETH</span>
                </div>
              </div>
              <div className="swap-arrow">
                <span className="swap-arrow-icon">→</span>
              </div>
              <div className="swap-token-card swap-token-out">
                <span className="swap-token-icon">💲</span>
                <div className="swap-token-info">
                  <span className="swap-token-amount">{formatAmount(quote.amount_out, tokenOut === 'wstETH' ? 18 : 6)}</span>
                  <span className="swap-token-name">{tokenOut}</span>
                </div>
              </div>
            </div>

            <div className="swap-details">
              <div className="swap-detail-row">
                <span className="swap-detail-label">Routing</span>
                <span className="swap-detail-value swap-routing-badge">{quote.routing}</span>
              </div>
              <div className="swap-detail-row">
                <span className="swap-detail-label">Gas Estimate</span>
                <span className="swap-detail-value">
                  {parseFloat(quote.gas_usd) > 0 ? `$${parseFloat(quote.gas_usd).toFixed(2)}` : quote.gas_estimate}
                </span>
              </div>
              <div className="swap-detail-row">
                <span className="swap-detail-label">Price Impact</span>
                <span className={`swap-detail-value ${parseFloat(quote.price_impact) > 1 ? 'warn' : ''}`}>
                  {parseFloat(quote.price_impact).toFixed(4)}%
                </span>
              </div>
              <div className="swap-detail-row">
                <span className="swap-detail-label">Slippage Tolerance</span>
                <span className="swap-detail-value">{quote.slippage}%</span>
              </div>
              <div className="swap-detail-row">
                <span className="swap-detail-label">Chain</span>
                <span className="swap-detail-value">{quote.chain_id === 1 ? 'Ethereum' : 'Base'} (ID: {quote.chain_id})</span>
              </div>
            </div>

            {quote.route.length > 0 && (
              <div className="swap-route-section">
                <div className="swap-route-label">Route Path</div>
                <div className="swap-route-path">
                  {quote.route.map((pool, i) => (
                    <div key={i} className="swap-route-hop">
                      <span className="swap-route-pool-type">{pool.type}</span>
                      <span className="swap-route-pool-addr">{shortenAddress(pool.address)}</span>
                      {pool.fee && <span className="swap-route-fee">{(parseInt(pool.fee) / 10000).toFixed(2)}%</span>}
                      <span className="swap-route-tokens">
                        {pool.tokenIn} → {pool.tokenOut}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="swap-execute-section">
              <button
                className="swap-execute-btn"
                onClick={async () => {
                  setExecuting(true)
                  try {
                    const result = await api.executeSwap('WETH', tokenOut, AMOUNT_PRESETS[selectedAmount].wei)
                    setExecution(result)
                  } catch {
                    setExecution({ error: 'Execution failed', tx_hash: '', explorer_url: '', chain_id: 0, from: '', status: 'failed' })
                  } finally {
                    setExecuting(false)
                  }
                }}
                disabled={executing}
              >
                {executing ? <span className="spinner" /> : '⚡ Execute Swap (Sepolia Testnet)'}
              </button>
              {execution && !execution.error && (
                <div className="swap-execution-result">
                  <span className="swap-execution-status">✅ Transaction Broadcast</span>
                  <a
                    href={execution.explorer_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="swap-tx-link"
                  >
                    {execution.tx_hash ? `${execution.tx_hash.slice(0, 10)}…${execution.tx_hash.slice(-6)}` : 'View on Etherscan'}
                  </a>
                </div>
              )}
              {execution && execution.error && (
                <div className="swap-execution-error">
                  ⚠️ {execution.error}
                </div>
              )}
            </div>

            <div className="swap-source">
              🔗 Source: {quote.source} · Uniswap Developer Platform
            </div>
          </div>
        )}

        {quote && quote.error && (
          <div className="swap-error">
            ⚠️ {quote.error}
          </div>
        )}

        {!quote && !loading && (
          <div className="swap-placeholder">
            <span className="swap-placeholder-icon">🦄</span>
            <p>Click "Get Live Quote" to fetch a real-time swap quote from the Uniswap Trading API</p>
            <p className="swap-placeholder-sub">Powered by your Uniswap Developer Platform API key</p>
          </div>
        )}
      </div>
    </div>
  )
}
