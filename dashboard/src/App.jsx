import React, { useState, useEffect } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend
} from 'recharts'
import {
  LayoutDashboard, FileText, Zap, Users,
  Shield, UserCheck, ClipboardList, Banknote,
  CheckCircle, Clock, XCircle, AlertTriangle,
  Activity, ChevronRight
} from 'lucide-react'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

// ── Styles ────────────────────────────────────────────────────────────────────

const styles = `
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: 'DM Sans', sans-serif; background: #F8FAFC; color: #0F172A; }
  :root {
    --primary: #1A56DB;
    --success: #10B981;
    --warning: #F59E0B;
    --danger: #EF4444;
    --surface: #F8FAFC;
    --card: #FFFFFF;
    --border: #E2E8F0;
    --text: #0F172A;
    --muted: #64748B;
    --hint: #94A3B8;
  }
  .layout { display: flex; min-height: 100vh; }
  .sidebar {
    width: 220px; background: #0F172A; padding: 24px 0;
    display: flex; flex-direction: column; flex-shrink: 0;
  }
  .sidebar-logo {
    padding: 0 20px 24px; display: flex; align-items: center; gap: 10px;
    border-bottom: 1px solid rgba(255,255,255,0.08); margin-bottom: 16px;
  }
  .sidebar-logo span { color: #fff; font-size: 18px; font-weight: 800; }
  .nav-item {
    padding: 10px 20px; display: flex; align-items: center; gap: 10px;
    color: rgba(255,255,255,0.5); font-size: 14px; font-weight: 500;
    cursor: pointer; transition: all 0.15s;
  }
  .nav-item:hover { color: #fff; background: rgba(255,255,255,0.05); }
  .nav-item.active { color: #fff; background: rgba(26,86,219,0.3); border-right: 2px solid var(--primary); }
  .main { flex: 1; overflow: auto; }
  .topbar {
    background: #fff; padding: 16px 28px; border-bottom: 1px solid var(--border);
    display: flex; align-items: center; justify-content: space-between;
    position: sticky; top: 0; z-index: 10;
  }
  .topbar h1 { font-size: 18px; font-weight: 700; }
  .badge-live {
    background: #ECFDF5; color: var(--success); font-size: 11px; font-weight: 700;
    padding: 4px 10px; border-radius: 20px; display: flex; align-items: center; gap: 6px;
  }
  .live-dot { width: 6px; height: 6px; background: var(--success); border-radius: 50%; }
  .content { padding: 24px 28px; }
  .metrics-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
  .metric-card {
    background: var(--card); border: 1px solid var(--border); border-radius: 14px;
    padding: 20px; display: flex; flex-direction: column; gap: 8px;
  }
  .metric-icon { width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; }
  .metric-val { font-size: 26px; font-weight: 800; }
  .metric-label { font-size: 12px; color: var(--muted); }
  .charts-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 16px; margin-bottom: 24px; }
  .card { background: var(--card); border: 1px solid var(--border); border-radius: 14px; padding: 20px; }
  .card-title { font-size: 14px; font-weight: 700; margin-bottom: 16px; }
  .table-wrap { overflow-x: auto; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th { text-align: left; padding: 10px 12px; color: var(--muted); font-weight: 600; border-bottom: 1px solid var(--border); font-size: 11px; text-transform: uppercase; }
  td { padding: 12px 12px; border-bottom: 1px solid var(--border); }
  tr:last-child td { border-bottom: none; }
  .status-pill {
    display: inline-block; padding: 3px 10px; border-radius: 20px;
    font-size: 11px; font-weight: 700; text-transform: uppercase;
  }
  .pill-paid { background: #ECFDF5; color: var(--success); }
  .pill-approved { background: #EFF6FF; color: var(--primary); }
  .pill-rejected { background: #FEF2F2; color: var(--danger); }
  .pill-pending { background: #FFFBEB; color: var(--warning); }
  .pill-active { background: #ECFDF5; color: var(--success); }
  .pill-ended { background: #F1F5F9; color: var(--hint); }
  .disruption-row { display: flex; align-items: center; gap: 12px; padding: 10px 0; border-bottom: 1px solid var(--border); }
  .disruption-row:last-child { border-bottom: none; }
  .sev-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
  .sev-extreme { background: #991B1B; }
  .sev-severe { background: var(--danger); }
  .sev-moderate { background: var(--warning); }
  .dss-bar { flex: 1; height: 6px; background: var(--border); border-radius: 3px; overflow: hidden; }
  .dss-fill { height: 100%; border-radius: 3px; background: var(--primary); }
  .empty { color: var(--muted); font-size: 13px; padding: 24px 0; text-align: center; }
  .loading { color: var(--hint); font-size: 13px; padding: 40px 0; text-align: center; }
  .verified-badge { display: inline-flex; align-items: center; gap: 4px; font-size: 11px; font-weight: 600; }
`

// ── Helpers ───────────────────────────────────────────────────────────────────

function fmt(n) {
  if (n >= 100000) return `₹${(n / 100000).toFixed(2)}L`
  if (n >= 1000) return `₹${(n / 1000).toFixed(1)}K`
  return `₹${n}`
}

const TIER_COLORS = { Basic: '#10B981', Smart: '#1A56DB', Pro: '#F59E0B' }

// ── Sidebar ───────────────────────────────────────────────────────────────────

function Sidebar({ active, setActive }) {
  const items = [
    { id: 'overview',     label: 'Overview',    Icon: LayoutDashboard },
    { id: 'claims',       label: 'Claims',       Icon: FileText },
    { id: 'disruptions',  label: 'Disruptions',  Icon: Zap },
    { id: 'workers',      label: 'Workers',      Icon: Users },
  ]
  return (
    <div className="sidebar">
      <div className="sidebar-logo">
        <Shield size={22} color="#1A56DB" />
        <span>Susanoo</span>
      </div>
      {items.map(({ id, label, Icon }) => (
        <div
          key={id}
          className={`nav-item ${active === id ? 'active' : ''}`}
          onClick={() => setActive(id)}
        >
          <Icon size={16} />
          <span>{label}</span>
        </div>
      ))}
      <div style={{ marginTop: 'auto', padding: '0 20px' }}>
        <div style={{ color: 'rgba(255,255,255,0.3)', fontSize: 11, marginBottom: 4 }}>Environment</div>
        <div style={{ color: '#F59E0B', fontSize: 12, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6 }}>
          <Activity size={12} /> Development
        </div>
      </div>
    </div>
  )
}

// ── MetricCard ────────────────────────────────────────────────────────────────

function MetricCard({ Icon, label, value, color }) {
  return (
    <div className="metric-card">
      <div className="metric-icon" style={{ background: color + '18' }}>
        <Icon size={20} color={color} />
      </div>
      <div className="metric-val">{value}</div>
      <div className="metric-label">{label}</div>
    </div>
  )
}

// ── Overview ──────────────────────────────────────────────────────────────────

function OverviewPage({ data }) {
  if (!data) return <div className="loading">Loading stats…</div>

  const metrics = data.metrics || {}
  const weekly_chart = data.weekly_chart || []
  const tier_distribution = data.tier_distribution || []
  const fraud_summary = data.fraud_summary || {}
  const active_disruptions = data.active_disruptions || []

  const tierData = tier_distribution.map(t => ({
    ...t,
    color: TIER_COLORS[t.name] || '#94A3B8'
  }))

  return (
    <>
      <div className="metrics-grid">
        <MetricCard Icon={Users}         label="Active Workers"     value={(metrics.active_workers ?? 0).toLocaleString()}  color="#1A56DB" />
        <MetricCard Icon={Shield}        label="Active Policies"    value={(metrics.active_policies ?? 0).toLocaleString()} color="#10B981" />
        <MetricCard Icon={ClipboardList} label="Claims This Week"   value={(metrics.claims_this_week ?? 0).toLocaleString()} color="#F59E0B" />
        <MetricCard Icon={Banknote}      label="Payouts This Week"  value={fmt(metrics.payouts_this_week ?? 0)}            color="#8B5CF6" />
      </div>

      <div className="charts-grid">
        <div className="card">
          <div className="card-title">Claims & Payouts — Last 7 Days</div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={weekly_chart} barSize={18}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
              <XAxis dataKey="day" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="claims"  fill="#1A56DB" radius={[4,4,0,0]} name="Claims" />
              <Bar dataKey="payouts" fill="#10B981" radius={[4,4,0,0]} name="Payout (₹)" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="card-title">Policy Tier Distribution</div>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={tierData} cx="50%" cy="50%" innerRadius={55} outerRadius={85} dataKey="value">
                {tierData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <div className="card">
          <div className="card-title">Active Disruptions</div>
          {active_disruptions.length === 0
            ? <div className="empty">No active disruptions</div>
            : active_disruptions.map((d, i) => (
              <div key={i} className="disruption-row">
                <div className={`sev-dot sev-${d.severity}`} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13, fontWeight: 600 }}>{d.city} — {d.type}</div>
                  <div style={{ fontSize: 11, color: 'var(--muted)' }}>{d.severity.toUpperCase()} • DSS {(d.dss * 100).toFixed(0)}%</div>
                </div>
                <div className="dss-bar">
                  <div className="dss-fill" style={{ width: `${d.dss * 100}%` }} />
                </div>
                <span style={{ fontSize: 11, color: d.active ? 'var(--success)' : 'var(--hint)', fontWeight: 600 }}>
                  {d.active ? 'LIVE' : 'ENDED'}
                </span>
              </div>
            ))
          }
        </div>

        <div className="card">
          <div className="card-title">Fraud Summary</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {[
              { label: 'Auto-approved (score < 30)', val: fraud_summary.auto_approved ?? 0, Icon: CheckCircle, color: 'var(--success)' },
              { label: 'Under review (30–70)',        val: fraud_summary.under_review ?? 0,  Icon: Clock,        color: 'var(--warning)' },
              { label: 'Auto-rejected (score > 70)', val: fraud_summary.auto_rejected ?? 0, Icon: XCircle,      color: 'var(--danger)' },
            ].map(({ label, val, Icon, color }, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 13, color: 'var(--muted)', display: 'flex', alignItems: 'center', gap: 6 }}>
                  <Icon size={14} color={color} /> {label}
                </span>
                <span style={{ fontWeight: 700, color, fontSize: 16 }}>{val}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  )
}

// ── Claims ────────────────────────────────────────────────────────────────────

function ClaimsPage({ data }) {
  if (!data) return <div className="loading">Loading claims…</div>
  return (
    <div className="card">
      <div className="card-title">All Claims ({data.length})</div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Claim ID</th><th>Worker</th><th>City</th>
              <th>Event</th><th>Amount</th><th>Fraud Score</th><th>Status</th>
            </tr>
          </thead>
          <tbody>
            {data.length === 0
              ? <tr><td colSpan={7} className="empty">No claims found</td></tr>
              : data.map(c => (
                <tr key={c.id}>
                  <td style={{ fontFamily: 'monospace', color: 'var(--primary)' }}>{c.id}</td>
                  <td style={{ fontWeight: 600 }}>{c.worker}</td>
                  <td>{c.city}</td>
                  <td>{c.event}</td>
                  <td style={{ fontWeight: 700 }}>{c.amount}</td>
                  <td>
                    <span style={{
                      color: c.fraud > 70 ? 'var(--danger)' : c.fraud > 30 ? 'var(--warning)' : 'var(--success)',
                      fontWeight: 700
                    }}>{c.fraud}/100</span>
                  </td>
                  <td><span className={`status-pill pill-${c.status}`}>{c.status}</span></td>
                </tr>
              ))
            }
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ── Disruptions ───────────────────────────────────────────────────────────────

function DisruptionsPage({ data }) {
  if (!data) return <div className="loading">Loading disruptions…</div>
  return (
    <div className="card">
      <div className="card-title">Disruption Events ({data.length})</div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr><th>City</th><th>Type</th><th>Severity</th><th>DSS Multiplier</th><th>Started</th><th>Status</th></tr>
          </thead>
          <tbody>
            {data.length === 0
              ? <tr><td colSpan={6} className="empty">No disruptions found</td></tr>
              : data.map((d, i) => (
                <tr key={i}>
                  <td style={{ fontWeight: 600 }}>{d.city}</td>
                  <td>{d.type}</td>
                  <td>
                    <span className={`status-pill ${d.severity === 'extreme' ? 'pill-rejected' : d.severity === 'severe' ? 'pill-pending' : 'pill-approved'}`}>
                      {d.severity}
                    </span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div className="dss-bar" style={{ width: 80 }}>
                        <div className="dss-fill" style={{ width: `${d.dss * 100}%` }} />
                      </div>
                      <span style={{ fontWeight: 600 }}>{(d.dss * 100).toFixed(0)}%</span>
                    </div>
                  </td>
                  <td style={{ color: 'var(--muted)', fontSize: 12 }}>
                    {d.started_at ? new Date(d.started_at).toLocaleString('en-IN', { dateStyle: 'short', timeStyle: 'short' }) : '—'}
                  </td>
                  <td><span className={`status-pill ${d.active ? 'pill-active' : 'pill-ended'}`}>{d.active ? 'ACTIVE' : 'ENDED'}</span></td>
                </tr>
              ))
            }
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ── Workers ───────────────────────────────────────────────────────────────────

function WorkersPage({ data }) {
  if (!data) return <div className="loading">Loading workers…</div>
  return (
    <div className="card">
      <div className="card-title">All Workers ({data.length})</div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr><th>Name</th><th>Phone</th><th>Platform</th><th>City</th><th>Risk Score</th><th>Verified</th><th>Status</th></tr>
          </thead>
          <tbody>
            {data.length === 0
              ? <tr><td colSpan={7} className="empty">No workers found</td></tr>
              : data.map(w => (
                <tr key={w.id}>
                  <td style={{ fontWeight: 600 }}>{w.name}</td>
                  <td style={{ fontFamily: 'monospace', color: 'var(--muted)' }}>{w.phone}</td>
                  <td style={{ textTransform: 'capitalize' }}>{w.platform.replace('_', ' ')}</td>
                  <td>{w.city}</td>
                  <td>
                    <span style={{
                      color: w.risk_score > 0.7 ? 'var(--danger)' : w.risk_score > 0.4 ? 'var(--warning)' : 'var(--success)',
                      fontWeight: 700
                    }}>{(w.risk_score * 100).toFixed(0)}%</span>
                  </td>
                  <td>
                    {w.is_verified
                      ? <span className="verified-badge" style={{ color: 'var(--success)' }}><UserCheck size={13} /> Yes</span>
                      : <span className="verified-badge" style={{ color: 'var(--hint)' }}><AlertTriangle size={13} /> No</span>
                    }
                  </td>
                  <td><span className={`status-pill ${w.is_active ? 'pill-active' : 'pill-ended'}`}>{w.is_active ? 'ACTIVE' : 'INACTIVE'}</span></td>
                </tr>
              ))
            }
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ── App ───────────────────────────────────────────────────────────────────────

export default function App() {
  const [active, setActive] = useState('overview')
  const [stats, setStats]           = useState(null)
  const [claims, setClaims]         = useState(null)
  const [disruptions, setDisruptions] = useState(null)
  const [workers, setWorkers]       = useState(null)

  useEffect(() => {
    fetch(`${API}/admin/stats`).then(r => r.json()).then(d => setStats(d && typeof d === 'object' ? d : {})).catch(() => setStats({}))
  }, [])

  useEffect(() => {
    if (active === 'claims' && !claims)
      fetch(`${API}/admin/claims`).then(r => r.json()).then(setClaims).catch(() => setClaims([]))
    if (active === 'disruptions' && !disruptions)
      fetch(`${API}/admin/disruptions`).then(r => r.json()).then(setDisruptions).catch(() => setDisruptions([]))
    if (active === 'workers' && !workers)
      fetch(`${API}/admin/workers`).then(r => r.json()).then(setWorkers).catch(() => setWorkers([]))
  }, [active])

  const pages = {
    overview:    { title: 'Overview',             component: <OverviewPage    data={stats} /> },
    claims:      { title: 'Claims Management',    component: <ClaimsPage      data={claims} /> },
    disruptions: { title: 'Disruption Monitor',   component: <DisruptionsPage data={disruptions} /> },
    workers:     { title: 'Workers',              component: <WorkersPage     data={workers} /> },
  }
  const page = pages[active]

  return (
    <>
      <style>{styles}</style>
      <div className="layout">
        <Sidebar active={active} setActive={setActive} />
        <div className="main">
          <div className="topbar">
            <h1>{page.title}</h1>
            <div className="badge-live">
              <div className="live-dot" />
              Live Data
            </div>
          </div>
          <div className="content">{page.component}</div>
        </div>
      </div>
    </>
  )
}
