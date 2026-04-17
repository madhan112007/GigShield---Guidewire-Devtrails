import React, { useRef, useEffect, useState } from 'react'

const CITIES = [
  { name: 'Mumbai',    x: 0.18, y: 0.52, loss: 0.65 },
  { name: 'Delhi',     x: 0.38, y: 0.22, loss: 0.52 },
  { name: 'Bangalore', x: 0.32, y: 0.72, loss: 0.48 },
  { name: 'Hyderabad', x: 0.38, y: 0.60, loss: 0.58 },
  { name: 'Chennai',   x: 0.42, y: 0.75, loss: 0.71 },
  { name: 'Kolkata',   x: 0.65, y: 0.38, loss: 0.62 },
  { name: 'Pune',      x: 0.22, y: 0.56, loss: 0.55 },
]

function lossColor(loss) {
  if (loss > 0.65) return '#EF4444'
  if (loss > 0.50) return '#F59E0B'
  return '#10B981'
}

export function Globe3D({ data = [], onCitySelect }) {
  const canvasRef = useRef(null)
  const [hovered, setHovered] = useState(null)
  const animRef = useRef(0)
  const tickRef = useRef(0)

  const cities = CITIES.map(c => {
    const live = data.find(d => d.city === c.name)
    return { ...c, loss: live ? live.loss_ratio : c.loss }
  })

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')

    const draw = (ts) => {
      tickRef.current = ts
      const W = canvas.width
      const H = canvas.height
      ctx.clearRect(0, 0, W, H)

      // Background gradient
      const bg = ctx.createRadialGradient(W / 2, H / 2, 0, W / 2, H / 2, W * 0.7)
      bg.addColorStop(0, '#0f172a')
      bg.addColorStop(1, '#020617')
      ctx.fillStyle = bg
      ctx.fillRect(0, 0, W, H)

      // Grid lines
      ctx.strokeStyle = 'rgba(26,86,219,0.08)'
      ctx.lineWidth = 1
      for (let i = 0; i < W; i += 40) {
        ctx.beginPath(); ctx.moveTo(i, 0); ctx.lineTo(i, H); ctx.stroke()
      }
      for (let i = 0; i < H; i += 40) {
        ctx.beginPath(); ctx.moveTo(0, i); ctx.lineTo(W, i); ctx.stroke()
      }

      // Arcs between high-risk cities
      const highRisk = cities.filter(c => c.loss > 0.55)
      for (let i = 0; i < highRisk.length; i++) {
        for (let j = i + 1; j < highRisk.length; j++) {
          const a = highRisk[i], b = highRisk[j]
          const ax = a.x * W, ay = a.y * H
          const bx = b.x * W, by = b.y * H
          const mx = (ax + bx) / 2, my = (ay + by) / 2 - 40
          const phase = (ts / 2000 + i * 0.3 + j * 0.2) % 1
          const grad = ctx.createLinearGradient(ax, ay, bx, by)
          grad.addColorStop(0, 'rgba(239,68,68,0)')
          grad.addColorStop(phase, 'rgba(239,68,68,0.6)')
          grad.addColorStop(Math.min(phase + 0.1, 1), 'rgba(239,68,68,0)')
          grad.addColorStop(1, 'rgba(239,68,68,0)')
          ctx.beginPath()
          ctx.moveTo(ax, ay)
          ctx.quadraticCurveTo(mx, my, bx, by)
          ctx.strokeStyle = grad
          ctx.lineWidth = 1.5
          ctx.stroke()
        }
      }

      // City dots with pulse rings
      cities.forEach((city) => {
        const cx = city.x * W
        const cy = city.y * H
        const color = lossColor(city.loss)
        const isHov = hovered === city.name
        const pulse = Math.sin(ts / 600 + city.x * 10) * 0.5 + 0.5

        // Outer pulse ring
        const ringR = (isHov ? 28 : 18) + pulse * 8
        ctx.beginPath()
        ctx.arc(cx, cy, ringR, 0, Math.PI * 2)
        ctx.strokeStyle = color + '33'
        ctx.lineWidth = 1
        ctx.stroke()

        // Mid ring
        ctx.beginPath()
        ctx.arc(cx, cy, (isHov ? 18 : 12) + pulse * 4, 0, Math.PI * 2)
        ctx.strokeStyle = color + '66'
        ctx.lineWidth = 1.5
        ctx.stroke()

        // Core dot
        const r = isHov ? 10 : 7
        const grd = ctx.createRadialGradient(cx, cy, 0, cx, cy, r)
        grd.addColorStop(0, '#fff')
        grd.addColorStop(0.4, color)
        grd.addColorStop(1, color + '88')
        ctx.beginPath()
        ctx.arc(cx, cy, r, 0, Math.PI * 2)
        ctx.fillStyle = grd
        ctx.fill()

        // Glow
        ctx.shadowColor = color
        ctx.shadowBlur = isHov ? 24 : 12
        ctx.beginPath()
        ctx.arc(cx, cy, r, 0, Math.PI * 2)
        ctx.fillStyle = color
        ctx.fill()
        ctx.shadowBlur = 0

        // Label
        if (isHov) {
          ctx.fillStyle = 'rgba(0,0,0,0.85)'
          ctx.beginPath()
          ctx.roundRect(cx + 14, cy - 22, 130, 44, 8)
          ctx.fill()
          ctx.fillStyle = '#fff'
          ctx.font = 'bold 13px DM Sans, sans-serif'
          ctx.fillText(city.name, cx + 22, cy - 5)
          ctx.fillStyle = color
          ctx.font = 'bold 11px DM Sans, sans-serif'
          ctx.fillText(`Loss Ratio: ${(city.loss * 100).toFixed(1)}%`, cx + 22, cy + 12)
        } else {
          ctx.fillStyle = 'rgba(255,255,255,0.7)'
          ctx.font = '11px DM Sans, sans-serif'
          ctx.fillText(city.name, cx + 12, cy + 4)
        }
      })

      // Title
      ctx.fillStyle = 'rgba(255,255,255,0.3)'
      ctx.font = '11px DM Sans, sans-serif'
      ctx.fillText('INDIA RISK MAP — LIVE', 16, 20)

      animRef.current = requestAnimationFrame(draw)
    }

    animRef.current = requestAnimationFrame(draw)
    return () => cancelAnimationFrame(animRef.current)
  }, [hovered, cities])

  const handleMouseMove = (e) => {
    const canvas = canvasRef.current
    const rect = canvas.getBoundingClientRect()
    const mx = (e.clientX - rect.left) * (canvas.width / rect.width)
    const my = (e.clientY - rect.top) * (canvas.height / rect.height)
    const hit = cities.find(c => {
      const dx = c.x * canvas.width - mx
      const dy = c.y * canvas.height - my
      return Math.sqrt(dx * dx + dy * dy) < 20
    })
    setHovered(hit ? hit.name : null)
    if (hit && onCitySelect) onCitySelect(hit.name)
  }

  return (
    <canvas
      ref={canvasRef}
      width={520}
      height={340}
      onMouseMove={handleMouseMove}
      onMouseLeave={() => setHovered(null)}
      style={{ width: '100%', height: '100%', borderRadius: 16, cursor: hovered ? 'pointer' : 'default' }}
    />
  )
}
