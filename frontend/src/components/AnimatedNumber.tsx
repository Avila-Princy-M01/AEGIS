import { useEffect, useRef, useState } from 'react'

interface Props {
  value: number
  decimals?: number
  prefix?: string
  suffix?: string
  duration?: number
  locale?: boolean
}

export function AnimatedNumber({
  value,
  decimals = 2,
  prefix = '',
  suffix = '',
  duration = 500,
  locale = true,
}: Props) {
  const [display, setDisplay] = useState(value)
  const [flash, setFlash] = useState(false)
  const prevRef = useRef(value)
  const animRef = useRef(0)
  const startRef = useRef(0)

  useEffect(() => {
    const from = prevRef.current
    const to = value
    prevRef.current = value

    if (isNaN(to) || from === to) return

    setFlash(true)
    const flashTimer = setTimeout(() => setFlash(false), 400)

    startRef.current = performance.now()

    const animate = (now: number) => {
      const elapsed = now - startRef.current
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      setDisplay(from + (to - from) * eased)
      if (progress < 1) {
        animRef.current = requestAnimationFrame(animate)
      }
    }

    cancelAnimationFrame(animRef.current)
    animRef.current = requestAnimationFrame(animate)

    return () => {
      cancelAnimationFrame(animRef.current)
      clearTimeout(flashTimer)
    }
  }, [value, duration])

  const formatted = isNaN(display)
    ? '—'
    : locale
      ? display.toLocaleString('en-US', {
          minimumFractionDigits: decimals,
          maximumFractionDigits: decimals,
        })
      : display.toFixed(decimals)

  return (
    <span className={flash ? 'value-flash' : ''}>
      {prefix}
      {formatted}
      {suffix}
    </span>
  )
}
