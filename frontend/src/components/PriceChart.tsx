interface PricePoint {
  timestamp: number
  price: string
}

interface Props {
  data: PricePoint[]
  width?: number
  height?: number
  color?: string
}

export function PriceChart({ data, width = 280, height = 60, color = '#3b82f6' }: Props) {
  if (data.length < 2) {
    return (
      <div className="price-chart-empty" style={{
        width, height,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#55556a',
        fontSize: '0.7rem',
        borderRadius: '6px',
        background: 'rgba(255,255,255,0.02)',
      }}>
        Collecting price data...
      </div>
    )
  }

  const prices = data.map(d => parseFloat(d.price))
  const min = Math.min(...prices)
  const max = Math.max(...prices)
  const range = max - min || 1

  const padding = 2
  const chartW = width - padding * 2
  const chartH = height - padding * 2

  const points = prices.map((p, i) => {
    const x = padding + (i / (prices.length - 1)) * chartW
    const y = padding + chartH - ((p - min) / range) * chartH
    return `${x},${y}`
  })

  const polyline = points.join(' ')

  const lastPrice = prices[prices.length - 1]
  const firstPrice = prices[0]
  const trending = lastPrice >= firstPrice
  const lineColor = trending ? '#10b981' : '#ef4444'

  const areaPoints = `${padding},${padding + chartH} ${polyline} ${padding + chartW},${padding + chartH}`

  return (
    <div style={{ position: 'relative' }}>
      <svg width={width} height={height} style={{ display: 'block' }}>
        <defs>
          <linearGradient id="priceGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={lineColor} stopOpacity="0.2" />
            <stop offset="100%" stopColor={lineColor} stopOpacity="0.02" />
          </linearGradient>
        </defs>
        <polygon
          points={areaPoints}
          fill="url(#priceGrad)"
        />
        <polyline
          points={polyline}
          fill="none"
          stroke={lineColor}
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <circle
          cx={padding + chartW}
          cy={padding + chartH - ((lastPrice - min) / range) * chartH}
          r="3"
          fill={lineColor}
          style={{ filter: `drop-shadow(0 0 4px ${lineColor})` }}
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
