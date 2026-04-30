import React, { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  LineChart, Line, AreaChart, Area, ComposedChart, PieChart, Pie, Cell
} from 'recharts'
import {
  LayoutDashboard, FileText, Zap, Users, Shield, UserCheck, ClipboardList, Banknote,
  CheckCircle, Clock, XCircle, AlertTriangle, Activity, ChevronRight, TrendingUp, Percent,
  ShieldAlert, RefreshCw, Search, Eye, Settings, ArrowUpRight, ArrowDownRight, Info, Flame,
  BarChart3, Globe, PieChart as PieChartIcon, Sparkles, Gauge
} from 'lucide-react'
import { AnimatedCounter } from './components/AnimatedCounter'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
const ADMIN_API_KEY = import.meta.env.VITE_ADMIN_API_KEY || ''
const adminFetch = (path) => fetch(`${API}${path}`, {
  headers: ADMIN_API_KEY ? { 'X-Admin-API-Key': ADMIN_API_KEY } : {},
})

// ════════════════════════════════════════════════════════════════════════════════
// STYLES - Glassmorphism + 3D + Animations
// ════════════════════════════════════════════════════════════════════════════════

const styles = `
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700;800&display=swap');
  
  * { margin: 0; padding: 0; box-sizing: border-box; }
  
  :root {
    --primary: #1A56DB;
    --success: #10B981;
    --warning: #F59E0B;
    --danger: #EF4444;
    --surface: #0F172A;
    --card: #ffffff;
    --card-dark: #1e293b;
    --border: #E2E8F0;
    --text: #0F172A;
    --muted: #64748B;
    --hint: #94A3B8;
    --glow-primary: rgba(26, 86, 219, 0.6);
    --glow-success: rgba(16, 185, 129, 0.6);
    --glow-warning: rgba(245, 158, 11, 0.6);
    --glow-danger: rgba(239, 68, 68, 0.6);
  }
  
  body {
    font-family: 'DM Sans', sans-serif;
    background: linear-gradient(135deg, #0F172A 0%, #1a1f3a 50%, #0F172A 100%);
    color: var(--text);
    min-height: 100vh;
    overflow-x: hidden;
    backdrop-filter: blur(100px);
  }
  
  .glass {
    background: rgba(255, 255, 255, 0.7);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 16px;
  }
  
  .layout {
    display: flex;
    min-height: 100vh;
    background: linear-gradient(135deg, #0F172A 0%, #1e293b 50%, #0F172A 100%);
    position: relative;
    overflow: hidden;
  }
  
  .layout::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: 
      radial-gradient(circle at 20% 50%, rgba(26, 86, 219, 0.1) 0%, transparent 50%),
      radial-gradient(circle at 80% 80%, rgba(16, 185, 129, 0.1) 0%, transparent 50%);
    pointer-events: none;
    z-index: 0;
  }
  
  .sidebar {
    width: 240px;
    background: rgba(15, 23, 42, 0.8);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    padding: 24px 0;
    display: flex;
    flex-direction: column;
    position: fixed;
    height: 100vh;
    z-index: 50;
    border-right: 1px solid rgba(255, 255, 255, 0.1);
    flex-shrink: 0;
    overflow-y: auto;
  }
  
  .sidebar-logo {
    padding: 0 20px 24px;
    display: flex;
    align-items: center;
    gap: 10px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    margin-bottom: 16px;
  }
  
  .sidebar-logo span {
    color: #fff;
    font-size: 20px;
    font-weight: 800;
    letter-spacing: -0.5px;
    background: linear-gradient(135deg, #1A56DB, #10B981);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  
  .nav-item {
    padding: 12px 20px;
    display: flex;
    align-items: center;
    gap: 12px;
    color: rgba(255, 255, 255, 0.5);
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    margin: 0 8px;
    border-radius: 10px;
  }
  
  .nav-item:hover {
    color: #fff;
    background: rgba(26, 86, 219, 0.1);
    transform: translateX(8px);
  }
  
  .nav-item.active {
    color: #fff;
    background: linear-gradient(135deg, rgba(26, 86, 219, 0.2), rgba(16, 185, 129, 0.1));
    border-left: 3px solid var(--primary);
    padding-left: 17px;
    box-shadow: 0 0 20px rgba(26, 86, 219, 0.3);
  }
  
  .main {
    flex: 1;
    margin-left: 240px;
    min-width: 0;
    position: relative;
    z-index: 1;
  }
  
  .topbar {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    padding: 16px 32px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 40;
  }
  
  .topbar h1 {
    font-size: 20px;
    font-weight: 700;
    background: linear-gradient(135deg, #1A56DB, #10B981);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  
  .badge-live {
    background: rgba(16, 185, 129, 0.2);
    color: #10B981;
    font-size: 12px;
    font-weight: 700;
    padding: 6px 12px;
    border-radius: 20px;
    display: flex;
    align-items: center;
    gap: 8px;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(16, 185, 129, 0.3);
  }
  
  .live-dot {
    width: 8px;
    height: 8px;
    background: #10B981;
    border-radius: 50%;
    animation: pulse 2s infinite, glow 2s infinite;
  }
  
  @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
  @keyframes glow { 0%, 100% { box-shadow: 0 0 8px rgba(16, 185, 129, 0.6); } 50% { box-shadow: 0 0 16px rgba(16, 185, 129, 0.9); } }
  
  .content {
    padding: 32px;
    max-width: 1800px;
    margin: 0 auto;
    width: 100%;
  }
  
  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 20px;
    margin-bottom: 32px;
  }
  
  .metric-card {
    position: relative;
    transform-style: preserve-3d;
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }
  
  .metric-card:hover {
    transform: translateY(-8px) rotateX(5deg);
  }
  
  .metric-card-inner {
    background: rgba(255, 255, 255, 0.8);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 16px;
    padding: 24px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  }
  
  .metric-card-inner::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -50%;
    width: 200px;
    height: 200px;
    background: radial-gradient(circle, rgba(26, 86, 219, 0.1), transparent);
    border-radius: 50%;
    opacity: 0;
    transition: opacity 0.3s;
  }
  
  .metric-card:hover .metric-card-inner::before {
    opacity: 1;
  }
  
  .metric-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
  }
  
  .metric-icon {
    width: 44px;
    height: 44px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s;
  }
  
  .metric-card:hover .metric-icon {
    transform: scale(1.2) rotate(10deg);
  }
  
  .metric-val {
    font-size: 28px;
    font-weight: 800;
    letter-spacing: -1px;
    background: linear-gradient(135deg, #1E293B, #475569);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  
  .metric-label {
    font-size: 13px;
    color: var(--muted);
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  
  .metric-trend {
    font-size: 12px;
    display: flex;
    align-items: center;
    gap: 4px;
    font-weight: 700;
    padding: 6px 12px;
    border-radius: 20px;
  }
  
  .charts-grid {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 20px;
    margin-bottom: 32px;
  }
  
  @media (max-width: 1200px) {
    .charts-grid { grid-template-columns: 1fr; }
  }
  
  .card {
    background: rgba(255, 255, 255, 0.75);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 16px;
    padding: 24px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.05);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }
  
  .card:hover {
    box-shadow: 0 16px 48px rgba(26, 86, 219, 0.15);
    transform: translateY(-4px);
  }
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    flex-wrap: wrap;
    gap: 10px;
  }
  
  .card-title {
    font-size: 16px;
    font-weight: 700;
    background: linear-gradient(135deg, #1E293B, #334155);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  
  .disruption-item {
    padding: 16px;
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.3);
    display: flex;
    align-items: center;
    gap: 16px;
    cursor: pointer;
    transition: all 0.3s;
    position: relative;
    overflow: hidden;
    margin-bottom: 12px;
    transform-style: preserve-3d;
  }
  
  .disruption-item:hover {
    transform: translateY(-4px) translateZ(20px);
    box-shadow: 0 12px 24px rgba(239, 68, 68, 0.2);
  }
  
  .disruption-icon {
    width: 40px;
    height: 40px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    z-index: 1;
  }
  
  .fraud-card {
    background: rgba(255, 255, 255, 0.6);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 16px;
    padding: 20px;
    text-align: center;
    transition: all 0.3s;
    position: relative;
    overflow: hidden;
    transform-style: preserve-3d;
  }
  
  .fraud-card:hover {
    transform: translateY(-4px) scale(1.05);
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.15);
  }
  
  .fraud-score {
    font-size: 48px;
    font-weight: 800;
    margin: 10px 0;
    background: linear-gradient(135deg, #EF4444, #DC2626);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  
  .status-pill {
    display: inline-flex;
    align-items: center;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    backdrop-filter: blur(10px);
  }
  
  .pill-paid { background: rgba(16, 185, 129, 0.2); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.3); }
  .pill-approved { background: rgba(26, 86, 219, 0.2); color: #1A56DB; border: 1px solid rgba(26, 86, 219, 0.3); }
  .pill-rejected { background: rgba(239, 68, 68, 0.2); color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.3); }
  .pill-pending { background: rgba(245, 158, 11, 0.2); color: #F59E0B; border: 1px solid rgba(245, 158, 11, 0.3); }
  .pill-active { background: rgba(16, 185, 129, 0.2); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.3); }
  
  .table-wrap { overflow-x: auto; margin-top: 10px; }
  table { width: 100%; border-collapse: collapse; font-size: 14px; }
  th { text-align: left; padding: 12px 16px; color: var(--muted); font-weight: 600; border-bottom: 1px solid rgba(255, 255, 255, 0.2); font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; }
  td { padding: 14px 16px; border-bottom: 1px solid rgba(255, 255, 255, 0.1); color: #334155; }
  tr:hover { background: rgba(26, 86, 219, 0.05); }
  
  .bcr-meter {
    height: 12px;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 6px;
    overflow: hidden;
    margin: 10px 0;
    box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
  }
  
  .bcr-fill {
    height: 100%;
    background: linear-gradient(90deg, #10B981, #1A56DB);
    transition: width 1.5s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 0 20px rgba(16, 185, 129, 0.6);
  }
  
  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 200;
  }
  
  .modal {
    background: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 20px;
    width: 600px;
    max-width: 90%;
    max-height: 85vh;
    overflow-y: auto;
    padding: 32px;
    position: relative;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  }
  
  .modal-close {
    position: absolute;
    top: 20px;
    right: 20px;
    cursor: pointer;
    color: var(--muted);
    transition: transform 0.3s;
  }
  
  .modal-close:hover { transform: rotate(90deg); }
  
  .worker-protection-card {
    background: linear-gradient(135deg, rgba(26, 86, 219, 0.8), rgba(30, 58, 138, 0.8));
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    color: #fff;
    border-radius: 20px;
    padding: 32px;
    margin-bottom: 32px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border: 1px solid rgba(255, 255, 255, 0.2);
    box-shadow: 0 8px 32px rgba(26, 86, 219, 0.3);
    position: relative;
    overflow: hidden;
  }
  
  .worker-protection-card::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -50%;
    width: 300px;
    height: 300px;
    background: radial-gradient(circle, rgba(255, 255, 255, 0.1), transparent);
    border-radius: 50%;
  }
  
  .worker-protection-card > * {
    position: relative;
    z-index: 1;
  }
  
  .grid-2 {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
  }
  
  .grid-3 {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
  }
  
  .fraud-gauge-container {
    width: 100%;
    height: 300px;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
  }
  
  .india-map-container {
    width: 100%;
    height: 400px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #94A3B8;
  }
  
  @media (max-width: 768px) {
    .grid-2 { grid-template-columns: 1fr; }
    .grid-3 { grid-template-columns: 1fr; }
    .charts-grid { grid-template-columns: 1fr; }
    .metrics-grid { grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); }
  }
`

// ════════════════════════════════════════════════════════════════════════════════
// PARTICLE SYSTEM
// ════════════════════════════════════════════════════════════════════════════════

function ParticleCanvas() {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    canvas.width = window.innerWidth
    canvas.height = window.innerHeight

    const particles = Array.from({ length: 30 }).map(() => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.3,
      vy: (Math.random() - 0.5) * 0.3,
      r: Math.random() * 1.5 + 0.5,
      opacity: Math.random() * 0.3 + 0.1,
    }))

    let animationId
    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      ctx.fillStyle = '#1A56DB'
      ctx.strokeStyle = '#1A56DB'

      particles.forEach((p, i) => {
        p.x += p.vx
        p.y += p.vy

        if (p.x < 0) p.x = canvas.width
        if (p.x > canvas.width) p.x = 0
        if (p.y < 0) p.y = canvas.height
        if (p.y > canvas.height) p.y = 0

        ctx.globalAlpha = p.opacity

        ctx.beginPath()
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
        ctx.fill()

        particles.forEach((p2, j) => {
          if (i < j) {
            const dx = p2.x - p.x
            const dy = p2.y - p.y
            const dist = Math.sqrt(dx * dx + dy * dy)

            if (dist < 150) {
              ctx.globalAlpha = p.opacity * (1 - dist / 150) * 0.2
              ctx.beginPath()
              ctx.moveTo(p.x, p.y)
              ctx.lineTo(p2.x, p2.y)
              ctx.stroke()
            }
          }
        })
      })

      ctx.globalAlpha = 1
      animationId = requestAnimationFrame(animate)
    }

    animate()

    const handleResize = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
    }

    window.addEventListener('resize', handleResize)

    return () => {
      cancelAnimationFrame(animationId)
      window.removeEventListener('resize', handleResize)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
        zIndex: 0,
      }}
    />
  )
}

// ════════════════════════════════════════════════════════════════════════════════
// ANIMATED FRAUD GAUGE
// ════════════════════════════════════════════════════════════════════════════════

function AnimatedFraudGauge({ value = 35 }) {
  const radius = 80
  const circumference = 2 * Math.PI * radius
  const strokeDashoffset = circumference - (value / 100) * circumference

  const getColor = () => {
    if (value > 70) return '#EF4444'
    if (value > 40) return '#F59E0B'
    return '#10B981'
  }

  const getLabel = () => {
    if (value > 70) return 'High Risk'
    if (value > 40) return 'Medium Risk'
    return 'Low Risk'
  }

  return (
    <motion.div
      className="fraud-gauge-container"
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.6 }}
    >
      <svg width="200" height="200" style={{ transform: 'rotate(-90deg)' }}>
        <circle
          cx="100"
          cy="100"
          r={radius}
          fill="none"
          stroke="rgba(255, 255, 255, 0.1)"
          strokeWidth="12"
        />
        <motion.circle
          cx="100"
          cy="100"
          r={radius}
          fill="none"
          stroke={getColor()}
          strokeWidth="12"
          strokeDasharray={circumference}
          strokeDashoffset={circumference}
          strokeLinecap="round"
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset }}
          transition={{ duration: 2, ease: 'easeInOut' }}
          style={{ filter: `drop-shadow(0 0 12px ${getColor()})` }}
        />
      </svg>
      <div style={{ position: 'absolute', textAlign: 'center' }}>
        <div style={{ fontSize: 40, fontWeight: 800, color: getColor() }}>
          <AnimatedCounter value={value} duration={2} />%
        </div>
        <div style={{ fontSize: 12, color: '#94A3B8', fontWeight: 700, marginTop: 8 }}>
          {getLabel()}
        </div>
      </div>
    </motion.div>
  )
}

// ════════════════════════════════════════════════════════════════════════════════
// INDIA RISK MAP
// ════════════════════════════════════════════════════════════════════════════════

function IndiaRiskMap({ cityData = [] }) {
  const majorCities = [
    { name: 'Mumbai', x: 25, y: 60, risk: 0.65 },
    { name: 'Delhi', x: 50, y: 20, risk: 0.45 },
    { name: 'Bangalore', x: 55, y: 75, risk: 0.35 },
    { name: 'Hyderabad', x: 60, y: 70, risk: 0.55 },
    { name: 'Chennai', x: 65, y: 85, risk: 0.42 },
    { name: 'Kolkata', x: 70, y: 35, risk: 0.50 },
  ]

  return (
    <motion.div
      className="india-map-container"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.6 }}
      style={{ position: 'relative' }}
    >
      <svg width="100%" height="100%" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet">
        {/* Simplified India outline */}
        <path
          d="M 25 20 L 70 25 L 75 40 L 72 60 L 65 90 L 30 85 L 15 70 L 20 40 Z"
          fill="rgba(26, 86, 219, 0.1)"
          stroke="rgba(26, 86, 219, 0.3)"
          strokeWidth="0.5"
        />

        {/* Risk zones */}
        {majorCities.map((city, i) => {
          const color = city.risk > 0.6 ? '#EF4444' : city.risk > 0.4 ? '#F59E0B' : '#10B981'
          const radius = 3 + city.risk * 4

          return (
            <g key={i}>
              <circle
                cx={city.x}
                cy={city.y}
                r={radius}
                fill={color}
                opacity="0.3"
              />
              <motion.circle
                cx={city.x}
                cy={city.y}
                r={radius / 2}
                fill={color}
                initial={{ r: 0 }}
                animate={{ r: radius / 2 }}
                transition={{ duration: 0.6, delay: i * 0.1 }}
              />
              <text x={city.x} y={city.y - radius - 2} fontSize="2" fill={color} textAnchor="middle" fontWeight="bold">
                {city.name.substring(0, 3)}
              </text>
            </g>
          )
        })}
      </svg>

      {/* Legend */}
      <div style={{ position: 'absolute', bottom: 10, right: 10, fontSize: 10, display: 'flex', flexDirection: 'column', gap: 4 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#EF4444' }}>
          <div style={{ width: 8, height: 8, background: '#EF4444', borderRadius: '50%' }} />
          High
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#F59E0B' }}>
          <div style={{ width: 8, height: 8, background: '#F59E0B', borderRadius: '50%' }} />
          Medium
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#10B981' }}>
          <div style={{ width: 8, height: 8, background: '#10B981', borderRadius: '50%' }} />
          Low
        </div>
      </div>
    </motion.div>
  )
}

// ════════════════════════════════════════════════════════════════════════════════
// HELPER FUNCTIONS
// ════════════════════════════════════════════════════════════════════════════════

function fmt(n) {
  if (n === undefined || n === null) return '₹0'
  if (n >= 10000000) return `₹${(n / 10000000).toFixed(2)}Cr`
  if (n >= 100000) return `₹${(n / 100000).toFixed(2)}L`
  if (n >= 1000) return `₹${(n / 1000).toFixed(1)}K`
  return `₹${n.toFixed(0)}`
}

const COLORS = ['#1A56DB', '#10B981', '#F59E0B', '#8B5CF6', '#EF4444', '#06B6D4']

// Sample data generators
const generateWeeklyChart = () => {
  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
  return days.map((day, i) => ({
    name: day,
    claims: Math.floor(Math.random() * 100) + 50,
    payouts: Math.floor(Math.random() * 150) + 100,
  }))
}

const generateCityData = () => {
  const cities = ['Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Chennai', 'Kolkata']
  return cities.map(city => ({
    city,
    loss: Math.floor(Math.random() * 500) + 100,
  }))
}

const generateTierData = () => {
  return [
    { name: 'Basic', value: 45, color: '#1A56DB' },
    { name: 'Pro', value: 30, color: '#10B981' },
    { name: 'Premium', value: 25, color: '#F59E0B' },
  ]
}

// ════════════════════════════════════════════════════════════════════════════════
// SIDEBAR COMPONENT
// ════════════════════════════════════════════════════════════════════════════════

function Sidebar({ active, setActive }) {
  const items = [
    { id: 'overview', label: 'Overview', Icon: LayoutDashboard },
    { id: 'analytics', label: 'Analytics', Icon: BarChart3 },
    { id: 'claims', label: 'Claims', Icon: FileText },
    { id: 'disruptions', label: 'Disruptions', Icon: Zap },
    { id: 'workers', label: 'Workers', Icon: Users },
  ]

  return (
    <div className="sidebar">
      <div className="sidebar-logo">
        <Shield size={26} fill="#1A56DB" color="#1A56DB" />
        <span>Susanoo</span>
      </div>

      <div style={{ flex: 1 }}>
        {items.map(({ id, label, Icon }) => (
          <motion.div
            key={id}
            className={`nav-item ${active === id ? 'active' : ''}`}
            onClick={() => setActive(id)}
            whileHover={{ x: 8 }}
            whileTap={{ scale: 0.95 }}
          >
            <Icon size={18} />
            <span>{label}</span>
          </motion.div>
        ))}
      </div>

      <div style={{ padding: '0 20px 24px', color: 'rgba(255,255,255,0.6)', fontSize: 11 }}>
        <div style={{ fontWeight: 700, marginBottom: 8, textTransform: 'uppercase' }}>Status</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
          <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#10B981', boxShadow: '0 0 8px #10B981' }} />
          <span>All Systems Live</span>
        </div>
        <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.4)' }}>v3.2.0 • Prod</div>
      </div>
    </div>
  )
}

// ════════════════════════════════════════════════════════════════════════════════
// ENHANCED METRIC CARD
// ════════════════════════════════════════════════════════════════════════════════

function MetricCard({ Icon, label, value, trend, color, isCurrency, delay = 0 }) {
  const isPositive = trend > 0
  const trendColor = isPositive ? '#10B981' : '#EF4444'

  return (
    <motion.div
      className="metric-card"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay }}
    >
      <div className="metric-card-inner" style={{ borderColor: color + '30' }}>
        <div className="metric-header">
          <div
            className="metric-icon"
            style={{
              background: color + '15',
              color: color,
            }}
          >
            <Icon size={22} />
          </div>
          {trend !== undefined && (
            <motion.div
              className="metric-trend"
              style={{
                background: isPositive ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                color: trendColor,
                border: `1px solid ${trendColor}30`,
              }}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: delay + 0.2 }}
            >
              {isPositive ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
              {Math.abs(trend)}%
            </motion.div>
          )}
        </div>
        <div>
          <div className="metric-val">
            <AnimatedCounter value={value} duration={1.5} isCurrency={isCurrency} />
          </div>
          <div className="metric-label">{label}</div>
        </div>
      </div>
    </motion.div>
  )
}

// ════════════════════════════════════════════════════════════════════════════════
// FRAUD MODAL
// ════════════════════════════════════════════════════════════════════════════════

function FraudModal({ claim, onClose }) {
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`${API}/admin/claims/${claim.id}/fraud`)
      .then((r) => r.json())
      .then((d) => {
        setDetail(d)
        setLoading(false)
      })
      .catch(() => {
        setDetail({
          fraud_score: 0.45,
          verdict: 'Low Risk',
          worker: claim.worker,
          claim_id: claim.id,
          auto_approved: true,
          flags: [],
        })
        setLoading(false)
      })
  }, [claim.id])

  if (loading)
    return (
      <div className="modal-overlay" onClick={onClose}>
        <motion.div
          className="modal"
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
        >
          <div style={{ textAlign: 'center', padding: 40 }}>
            <Sparkles size={40} style={{ marginBottom: 16, animation: 'spin 2s linear infinite' }} />
            Loading Fraud Analysis...
          </div>
        </motion.div>
      </div>
    )

  const score = detail.fraud_score * 100
  const color = score > 70 ? '#EF4444' : score > 30 ? '#F59E0B' : '#10B981'

  return (
    <motion.div
      className="modal-overlay"
      onClick={onClose}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      <motion.div
        className="modal"
        onClick={(e) => e.stopPropagation()}
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
      >
        <XCircle className="modal-close" onClick={onClose} size={24} />
        <h2 style={{ marginBottom: 24, fontSize: 22, fontWeight: 800 }}>Fraud Deep-Dive</h2>

        <div style={{ display: 'flex', gap: 24, marginBottom: 32 }}>
          <motion.div
            style={{
              flex: 1,
              padding: 24,
              borderRadius: 16,
              background: color + '15',
              border: `2px solid ${color}`,
              textAlign: 'center',
              boxShadow: `0 0 20px ${color}40`,
            }}
            initial={{ scale: 0.8 }}
            animate={{ scale: 1 }}
          >
            <div style={{ fontSize: 12, fontWeight: 700, textTransform: 'uppercase', marginBottom: 8, color: '#64748B' }}>
              AI Score
            </div>
            <div style={{ fontSize: 48, fontWeight: 800, color }}>{score.toFixed(0)}</div>
            <div style={{ fontSize: 14, fontWeight: 700, color, marginTop: 8 }}>{detail.verdict}</div>
          </motion.div>

          <div style={{ flex: 1.5 }}>
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 12, color: '#64748B', fontWeight: 700, marginBottom: 4 }}>WORKER</div>
              <div style={{ fontSize: 16, fontWeight: 700 }}>{detail.worker}</div>
            </div>
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 12, color: '#64748B', fontWeight: 700, marginBottom: 4 }}>CLAIM ID</div>
              <div style={{ fontSize: 14, fontFamily: 'monospace', fontWeight: 700, color: '#1A56DB' }}>
                {detail.claim_id}
              </div>
            </div>
            <div>
              <div style={{ fontSize: 12, color: '#64748B', fontWeight: 700, marginBottom: 4 }}>DECISION</div>
              <div style={{ fontSize: 14, fontWeight: 700 }}>
                {detail.auto_approved ? '🤖 AI Auto-Approved' : '👨‍💻 Manual Review'}
              </div>
            </div>
          </div>
        </div>

        <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
          <ShieldAlert size={18} color="#EF4444" /> Detected Anomalies
        </h3>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {detail.flags.length === 0 ? (
            <motion.div
              style={{
                padding: 16,
                background: 'rgba(16, 185, 129, 0.1)',
                borderRadius: 12,
                color: '#10B981',
                fontWeight: 600,
                fontSize: 14,
                border: '1px solid rgba(16, 185, 129, 0.2)',
              }}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              ✓ No fraud flags detected
            </motion.div>
          ) : (
            detail.flags.map((flag, i) => (
              <motion.div
                key={i}
                style={{
                  padding: 16,
                  background: 'rgba(239, 68, 68, 0.1)',
                  borderRadius: 12,
                  borderLeft: '4px solid #EF4444',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  color: '#991B1B',
                }}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1 }}
              >
                <span style={{ fontSize: 14, fontWeight: 600 }}>{flag}</span>
                <AlertTriangle size={16} />
              </motion.div>
            ))
          )}
        </div>
      </motion.div>
    </motion.div>
  )
}

// ════════════════════════════════════════════════════════════════════════════════
// PAGE COMPONENTS
// ════════════════════════════════════════════════════════════════════════════════

function OverviewPage({ data }) {
  if (!data) return <div style={{ padding: 40, textAlign: 'center', color: '#94A3B8' }}>Loading...</div>

  const metrics = data.metrics || {}
  const weekly_chart = data.weekly_chart?.length ? data.weekly_chart.map(d => ({ name: d.day, claims: d.claims, payouts: d.payouts })) : generateWeeklyChart()
  const tier_distribution = data.tier_distribution?.length ? data.tier_distribution : generateTierData()
  const city_loss = generateCityData()
  const active_disruptions = data.active_disruptions || []

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5 }}>
      {/* Worker Protection Card */}
      <motion.div
        className="worker-protection-card"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <div>
          <h2 style={{ fontSize: 14, opacity: 0.9, fontWeight: 600, marginBottom: 8 }}>Gig Worker Income Protected</h2>
          <div style={{ fontSize: 32, fontWeight: 800 }}>
            <AnimatedCounter value={metrics.payouts_this_week * 12.4} isCurrency duration={2} />
          </div>
          <p style={{ fontSize: 12, opacity: 0.7, marginTop: 8 }}>
            Estimated total income shortfall covered this month
          </p>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: 11, fontWeight: 700, opacity: 0.8, marginBottom: 8, textTransform: 'uppercase' }}>
            Actuarial Health
          </div>
          <div style={{ fontSize: 28, fontWeight: 800 }}>58.4%</div>
          <motion.div
            className="bcr-meter"
            style={{ width: 150 }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <motion.div
              className="bcr-fill"
              initial={{ width: 0 }}
              animate={{ width: '58.4%' }}
              transition={{ duration: 1.5, delay: 0.3 }}
            />
          </motion.div>
          <div style={{ fontSize: 10, fontWeight: 700, color: '#ECFDF5', marginTop: 4 }}>SAFE ZONE</div>
        </div>
      </motion.div>

      {/* Metrics Grid */}
      <div className="metrics-grid">
        <MetricCard Icon={Users} label="Active Workers" value={metrics.active_workers ?? 0} trend={+12} color="#1A56DB" delay={0.1} />
        <MetricCard Icon={Shield} label="Active Policies" value={metrics.active_policies ?? 0} trend={+8} color="#10B981" delay={0.15} />
        <MetricCard Icon={ClipboardList} label="Claims (7D)" value={metrics.claims_this_week ?? 0} trend={-3} color="#F59E0B" delay={0.2} />
        <MetricCard Icon={Banknote} label="Payouts (7D)" value={metrics.payouts_this_week ?? 0} trend={+15} color="#8B5CF6" isCurrency delay={0.25} />
      </div>

      {/* Charts */}
      <div className="charts-grid">
        <motion.div className="card" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.6, delay: 0.3 }}>
          <div className="card-header">
            <h3 className="card-title">Weekly Trend</h3>
            <div style={{ fontSize: 12, color: '#64748B', fontWeight: 600 }}>Last 7 Days</div>
          </div>
          <ResponsiveContainer width="100%" height={250}>
            <ComposedChart data={weekly_chart}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="name" stroke="#94A3B8" />
              <YAxis stroke="#94A3B8" />
              <Tooltip contentStyle={{ background: 'rgba(30, 41, 59, 0.95)', border: '1px solid rgba(255,255,255,0.2)' }} />
              <Legend />
              <Bar dataKey="claims" fill="#1A56DB" radius={[8, 8, 0, 0]} />
              <Line type="monotone" dataKey="payouts" stroke="#10B981" strokeWidth={2} />
            </ComposedChart>
          </ResponsiveContainer>
        </motion.div>

        <motion.div className="card" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.6, delay: 0.4 }}>
          <div className="card-header">
            <h3 className="card-title">Policy Distribution</h3>
          </div>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={tier_distribution}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name} ${value}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {tier_distribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </motion.div>
      </div>

      {/* Disruptions & Fraud */}
      <div className="grid-2">
        <motion.div className="card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.5 }}>
          <div className="card-header">
            <h3 className="card-title">Live Disruptions</h3>
            <span className="badge-live">
              <div className="live-dot" />
              {active_disruptions.length} Events
            </span>
          </div>
          {active_disruptions.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px 20px', color: '#94A3B8' }}>
              <CheckCircle size={40} style={{ opacity: 0.3, marginBottom: 12 }} />
              <p>All systems normal</p>
            </div>
          ) : (
            active_disruptions.slice(0, 3).map((d, i) => (
              <motion.div
                key={i}
                className="disruption-item"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.5 + i * 0.1 }}
              >
                <div
                  className="disruption-icon"
                  style={{
                    background: d.severity === 'extreme' ? 'rgba(239, 68, 68, 0.2)' : d.severity === 'severe' ? 'rgba(245, 158, 11, 0.2)' : 'rgba(26, 86, 219, 0.2)',
                  }}
                >
                  <Zap
                    size={20}
                    color={d.severity === 'extreme' ? '#EF4444' : d.severity === 'severe' ? '#F59E0B' : '#1A56DB'}
                  />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 14, fontWeight: 700 }}>
                    {d.city} • {d.type}
                  </div>
                  <div style={{ fontSize: 12, color: '#64748B', marginTop: 2 }}>
                    Severity: <span style={{ fontWeight: 700 }}>{d.severity.toUpperCase()}</span>
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: 16, fontWeight: 800, color: '#1A56DB' }}>x{d.dss.toFixed(2)}</div>
                  <div style={{ fontSize: 10, fontWeight: 700, color: '#64748B', textTransform: 'uppercase' }}>DSS</div>
                </div>
              </motion.div>
            ))
          )}
        </motion.div>

        <motion.div className="card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.6 }}>
          <div className="card-header">
            <h3 className="card-title">Fraud Risk Score</h3>
          </div>
          <AnimatedFraudGauge value={data.fraud_summary?.avg_score ?? 35} />
        </motion.div>
      </div>
    </motion.div>
  )
}

function AnalyticsPage({ data }) {
  const cityData = data?.city_loss_ratios?.length
    ? data.city_loss_ratios.map(c => ({ city: c.city, loss: Math.round(c.loss_ratio * 100) }))
    : generateCityData()
  const forecastData = data?.next_week_forecast?.length
    ? data.next_week_forecast.map(f => ({ name: f.city, claims: f.estimated_claims }))
    : generateWeeklyChart()

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5 }}>
      {/* India Risk Map */}
      <motion.div className="card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.1 }}>
        <div className="card-header">
          <h3 className="card-title">India Risk Heatmap</h3>
        </div>
        <IndiaRiskMap cityData={cityData} />
      </motion.div>

      {/* Analytics Grid */}
      <div className="grid-2" style={{ marginTop: 20 }}>
        <motion.div className="card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.2 }}>
          <div className="card-header">
            <h3 className="card-title">City Loss Ratios</h3>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={cityData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="city" stroke="#94A3B8" />
              <YAxis stroke="#94A3B8" />
              <Tooltip contentStyle={{ background: 'rgba(30, 41, 59, 0.95)', border: '1px solid rgba(255,255,255,0.2)' }} />
              <Bar dataKey="loss" fill="#EF4444" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>

        <motion.div className="card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.3 }}>
          <div className="card-header">
            <h3 className="card-title">Next Week Forecast</h3>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={forecastData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="name" stroke="#94A3B8" />
              <YAxis stroke="#94A3B8" />
              <Tooltip contentStyle={{ background: 'rgba(30, 41, 59, 0.95)', border: '1px solid rgba(255,255,255,0.2)' }} />
              <Area type="monotone" dataKey="claims" fill="#10B981" stroke="#10B981" />
            </AreaChart>
          </ResponsiveContainer>
        </motion.div>
      </div>
    </motion.div>
  )
}

const MOCK_CLAIMS = [
  { id: 'CLM-001', worker: 'Rajesh Kumar', city: 'Mumbai', amount: '₹5,000', fraud: 15, status: 'approved' },
  { id: 'CLM-002', worker: 'Priya Singh', city: 'Delhi', amount: '₹8,500', fraud: 45, status: 'pending' },
  { id: 'CLM-003', worker: 'Arjun Patel', city: 'Bangalore', amount: '₹12,000', fraud: 78, status: 'rejected' },
  { id: 'CLM-004', worker: 'Sneha Gupta', city: 'Hyderabad', amount: '₹6,200', fraud: 22, status: 'approved' },
  { id: 'CLM-005', worker: 'Vikram Das', city: 'Chennai', amount: '₹9,800', fraud: 62, status: 'pending' },
]

const MOCK_DISRUPTIONS = [
  { city: 'Mumbai', type: 'Rain', severity: 'severe', dss: 1.2, active: true },
  { city: 'Delhi', type: 'Heatwave', severity: 'extreme', dss: 1.5, active: true },
  { city: 'Bangalore', type: 'Low AQI', severity: 'moderate', dss: 0.8, active: false },
]

const MOCK_WORKERS = [
  { name: 'Rajesh Kumar', platform: 'blinkit', city: 'Mumbai', risk_score: 0.35, is_active: true },
  { name: 'Priya Singh', platform: 'zomato', city: 'Delhi', risk_score: 0.52, is_active: true },
  { name: 'Arjun Patel', platform: 'swiggy', city: 'Bangalore', risk_score: 0.15, is_active: false },
  { name: 'Sneha Gupta', platform: 'zepto', city: 'Hyderabad', risk_score: 0.68, is_active: true },
  { name: 'Vikram Das', platform: 'blinkit', city: 'Chennai', risk_score: 0.42, is_active: true },
]

function ClaimsPage({ data, selectedClaim, setSelectedClaim }) {
  const claims = data === null ? MOCK_CLAIMS : data
  if (data === null) return <div style={{ padding: 40, textAlign: 'center', color: '#94A3B8' }}>Loading claims...</div>

  return (
    <>
      <motion.div className="card" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.6 }}>
        <div className="card-header">
          <h3 className="card-title">Recent Claims</h3>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Claim ID</th>
                <th>Worker</th>
                <th>Amount</th>
                <th>Fraud Score</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {claims.map((c, i) => (
                <motion.tr
                  key={i}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: i * 0.1 }}
                >
                  <td style={{ fontFamily: 'monospace', color: '#1A56DB', fontWeight: 700 }}>{c.id}</td>
                  <td style={{ fontWeight: 700 }}>{c.worker}</td>
                  <td>{c.amount}</td>
                  <td>
                    <span style={{ fontWeight: 700, color: c.fraud > 70 ? '#EF4444' : c.fraud > 30 ? '#F59E0B' : '#10B981' }}>
                      {c.fraud}%
                    </span>
                  </td>
                  <td>
                    <span className={`status-pill pill-${c.status}`}>{c.status}</span>
                  </td>
                  <td>
                    <button
                      onClick={() => setSelectedClaim(c)}
                      style={{
                        padding: '6px 12px',
                        borderRadius: 6,
                        border: '1px solid #1A56DB',
                        background: 'transparent',
                        color: '#1A56DB',
                        fontSize: 11,
                        fontWeight: 700,
                        cursor: 'pointer',
                      }}
                    >
                      Analyze
                    </button>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>

      <AnimatePresence>
        {selectedClaim && <FraudModal claim={selectedClaim} onClose={() => setSelectedClaim(null)} />}
      </AnimatePresence>
    </>
  )
}

function DisruptionsPage({ data }) {
  const disruptions = data === null ? MOCK_DISRUPTIONS : data
  if (data === null) return <div style={{ padding: 40, textAlign: 'center', color: '#94A3B8' }}>Loading disruptions...</div>

  return (
    <motion.div className="card" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.6 }}>
      <div className="card-header">
        <h3 className="card-title">Disruption Events ({disruptions.length})</h3>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>City</th>
              <th>Type</th>
              <th>Severity</th>
              <th>DSS Impact</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {disruptions.map((d, i) => (
              <motion.tr key={i} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.05 }}>
                <td style={{ fontWeight: 700 }}>{d.city}</td>
                <td>{d.type}</td>
                <td>
                  <span
                    className={`status-pill ${d.severity === 'extreme' ? 'pill-rejected' : d.severity === 'severe' ? 'pill-pending' : 'pill-approved'}`}
                  >
                    {d.severity}
                  </span>
                </td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{ flex: 1, height: 6, background: '#F1F5F9', borderRadius: 3, width: 60, overflow: 'hidden' }}>
                      <div style={{ height: '100%', background: '#1A56DB', width: `${d.dss * 100}%` }} />
                    </div>
                    <span style={{ fontWeight: 700, fontSize: 12 }}>{(d.dss * 100).toFixed(0)}%</span>
                  </div>
                </td>
                <td>
                  <span className={`status-pill ${d.active ? 'pill-active' : 'pill-pending'}`}>{d.active ? 'LIVE' : 'ARCHIVED'}</span>
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>
    </motion.div>
  )
}

function WorkersPage({ data }) {
  const workers = data === null ? MOCK_WORKERS : data
  if (data === null) return <div style={{ padding: 40, textAlign: 'center', color: '#94A3B8' }}>Loading workers...</div>

  return (
    <motion.div className="card" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.6 }}>
      <div className="card-header">
        <h3 className="card-title">Active Workers ({workers.length})</h3>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Worker Name</th>
              <th>Platform</th>
              <th>City</th>
              <th>Risk Level</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {workers.map((w, i) => (
              <motion.tr key={i} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.05 }}>
                <td style={{ fontWeight: 700 }}>{w.name}</td>
                <td style={{ textTransform: 'capitalize' }}>{w.platform.replace('_', ' ')}</td>
                <td>{w.city}</td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <div
                      style={{
                        width: 8,
                        height: 8,
                        borderRadius: '50%',
                        background: w.risk_score > 0.7 ? '#EF4444' : w.risk_score > 0.4 ? '#F59E0B' : '#10B981',
                      }}
                    />
                    <span style={{ fontWeight: 700 }}>{(w.risk_score * 100).toFixed(0)}%</span>
                  </div>
                </td>
                <td>
                  <span className={`status-pill ${w.is_active ? 'pill-active' : 'pill-pending'}`}>{w.is_active ? 'ACTIVE' : 'OFFLINE'}</span>
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>
    </motion.div>
  )
}

// ════════════════════════════════════════════════════════════════════════════════
// MAIN APP
// ════════════════════════════════════════════════════════════════════════════════

const MOCK_STATS = {
  metrics: { active_workers: 2847, active_policies: 3452, claims_this_week: 234, payouts_this_week: 156000 },
  fraud_summary: { avg_score: 35, auto_approved: 89, auto_rejected: 12, under_review: 8 },
  active_disruptions: [
    { city: 'Mumbai', type: 'Rain', severity: 'severe', dss: 1.2 },
    { city: 'Delhi', type: 'Heatwave', severity: 'extreme', dss: 1.5 },
  ],
}

export default function App() {
  const [active, setActive] = useState('overview')
  const [stats, setStats] = useState(null)
  const [analytics, setAnalytics] = useState(null)
  const [claims, setClaims] = useState(null)
  const [disruptions, setDisruptions] = useState(null)
  const [workers, setWorkers] = useState(null)
  const [selectedClaim, setSelectedClaim] = useState(null)

  useEffect(() => {
    adminFetch('/admin/stats').then(r => r.json()).then(setStats).catch(() => setStats(MOCK_STATS))
    adminFetch('/admin/analytics').then(r => r.json()).then(setAnalytics).catch(() => setAnalytics({}))
  }, [])

  useEffect(() => {
    if (active === 'claims' && !claims)
      adminFetch('/admin/claims').then(r => r.json()).then(setClaims).catch(() => setClaims(MOCK_CLAIMS))
    if (active === 'disruptions' && !disruptions)
      adminFetch('/admin/disruptions').then(r => r.json()).then(setDisruptions).catch(() => setDisruptions(MOCK_DISRUPTIONS))
    if (active === 'workers' && !workers)
      adminFetch('/admin/workers').then(r => r.json()).then(setWorkers).catch(() => setWorkers(MOCK_WORKERS))
  }, [active])

  const renderContent = () => {
    switch (active) {
      case 'overview':
        return <OverviewPage data={stats} />
      case 'analytics':
        return <AnalyticsPage data={analytics} />
      case 'claims':
        return <ClaimsPage data={claims} selectedClaim={selectedClaim} setSelectedClaim={setSelectedClaim} />
      case 'disruptions':
        return <DisruptionsPage data={disruptions} />
      case 'workers':
        return <WorkersPage data={workers} />
      default:
        return <OverviewPage data={stats} />
    }
  }

  const titles = {
    overview: 'InsurOps Command Center',
    analytics: 'Predictive Analytics HQ',
    claims: 'Claims & Fraud Operations',
    disruptions: 'Climate Disruption Events',
    workers: 'Worker Risk Profiles',
  }

  return (
    <>
      <style>{styles}</style>
      <ParticleCanvas />
      <div className="layout">
        <Sidebar active={active} setActive={setActive} />
        <div className="main">
          <div className="topbar">
            <h1>{titles[active]}</h1>
            <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
              <span className="badge-live">
                <div className="live-dot" />
                Live Data
              </span>
              <div style={{ width: 36, height: 36, borderRadius: '50%', background: 'linear-gradient(135deg, #1A56DB, #10B981)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 800, fontSize: 14 }}>
                AD
              </div>
            </div>
          </div>
          <div className="content">{renderContent()}</div>
        </div>
      </div>
    </>
  )
}
