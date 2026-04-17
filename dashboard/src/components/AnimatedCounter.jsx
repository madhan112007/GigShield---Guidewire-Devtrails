import React, { useEffect, useState, useRef } from 'react'

export function AnimatedCounter({ value, duration = 1.8, prefix = '', suffix = '', isCurrency = false }) {
  const [display, setDisplay] = useState(0)
  const startRef = useRef(null)
  const rafRef = useRef(null)

  useEffect(() => {
    startRef.current = null
    const animate = (ts) => {
      if (!startRef.current) startRef.current = ts
      const progress = Math.min((ts - startRef.current) / (duration * 1000), 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      setDisplay(Math.floor(eased * value))
      if (progress < 1) rafRef.current = requestAnimationFrame(animate)
      else setDisplay(value)
    }
    rafRef.current = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(rafRef.current)
  }, [value, duration])

  const fmt = (v) => {
    if (isCurrency) {
      if (v >= 10000000) return `₹${(v / 10000000).toFixed(2)}Cr`
      if (v >= 100000)   return `₹${(v / 100000).toFixed(1)}L`
      if (v >= 1000)     return `₹${(v / 1000).toFixed(1)}K`
      return `₹${v.toFixed(0)}`
    }
    return v.toLocaleString()
  }

  return <span>{prefix}{fmt(display)}{suffix}</span>
}
