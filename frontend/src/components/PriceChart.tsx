interface PricePoint {
  timestamp: number
  price: string
}

interface Props {
  data: PricePoint[]
  width?: number
  height?: number
}

export function PriceChart({ data, width = 320, height = 60 }: Props) {
  if (data.length < 2) {
    return (
      <div style={{
        width: '100%', height,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#55556a',
        fontSize: '0.7rem',
        borderRadius: '8px',
        background: 'rgba(255,255,255,0.02)',
        border: '1px solid rgba(255,255,255,0.04)',
      }}>
        Collecting price data...
      </div>
    )
  }

  const prices = data.map(d => parseFloat(d.price))
  const min = Math.min(...prices)
  const max = Math.max(...prices)
  const isFlat = max - min === 0
  const range = isFlat ? 1 : max - min

  const padding = 2
  const chartW = width - padding * 2
  const chartH = height - padding * 2

  const points = prices.map((p, i) => {
    const x = padding + (i / (prices.length - 1)) * chartW
    const y = isFlat
      ? padding + chartH / 2
      : padding + chartH - ((p - min) / range) * chartH
    return `${x},${y}`
  })

  const polyline = points.join(' ')

  const lastPrice = prices[prices.length - 1]
  const firstPrice = prices[0]
  const trending = lastPrice >= firstPrice
  const lineColor = trending ? '#10b981' : '#ef4444'
  const glowColor = trending ? 'rgba(16, 185, 129, 0.4)' : 'rgba(239, 68, 68, 0.4)'

  const areaPoints = `${padding},${padding + chartH} ${polyline} ${padding + chartW},${padding + chartH}`

  const lastX = padding + chartW
  const lastY = isFlat
    ? padding + chartH / 2
    : padding + chartH - ((lastPrice - min) / range) * chartH

  return (
    <div className="price-chart-container" style={{ width: '100%' }}>
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{ display: 'block', width: '100%', height: 'auto' }}>
        <defs>
          <linearGradient id="priceAreaGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={lineColor} stopOpacity="0.2" />
            <stop offset="100%" stopColor={lineColor} stopOpacity="0.01" />
          </linearGradient>
          <filter id="chartGlow">
            <feGaussianBlur stdDeviation="2" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        <polygon
          points={areaPoints}
          fill="url(#priceAreaGrad)"
        />
        <polyline
          points={polyline}
          fill="none"
          stroke={lineColor}
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          filter="url(#chartGlow)"
        />
        {/* Pulsing last-price dot */}
        <circle
          cx={lastX}
          cy={lastY}
          r="4"
          fill={lineColor}
          opacity="0.25"
        >
          <animate
            attributeName="r"
            values="4;7;4"
            dur="2s"
            repeatCount="indefinite"
          />
          <animate
            attributeName="opacity"
            values="0.25;0.08;0.25"
            dur="2s"
            repeatCount="indefinite"
          />
        </circle>
        <circle
          cx={lastX}
          cy={lastY}
          r="2.5"
          fill={lineColor}
          style={{ filter: `drop-shadow(0 0 4px ${glowColor})` }}
        />
      </svg>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        fontSize: '0.6rem',
        color: '#55556a',
        marginTop: '2px',
        fontFamily: 'var(--font-mono)',
      }}>
        <span>${min.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}</span>
        <span style={{ color: lineColor, fontWeight: 600 }}>
          {trending ? '▲' : '▼'} ${lastPrice.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </span>
        <span>${max.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}</span>
      </div>
    </div>
  )
}
