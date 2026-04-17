import React, { useState, useEffect } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend,
  LineChart, Line, AreaChart, Area, ComposedChart
} from 'recharts'
import {
  LayoutDashboard, FileText, Zap, Users,
  Shield, UserCheck, ClipboardList, Banknote,
  CheckCircle, Clock, XCircle, AlertTriangle,
  Activity, ChevronRight, TrendingUp, Percent,
  ShieldAlert, RefreshCw, Search, Eye, Settings,
  ArrowUpRight, ArrowDownRight, Info
} from 'lucide-react'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

// ── Styles ────────────────────────────────────────────────────────────────────

const styles = `
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700;800&display=swap');
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: 'DM Sans', sans-serif; background: #F1F5F9; color: #0F172A; }
  :root {
    --primary: #1A56DB;
    --success: #10B981;
    --warning: #F59E0B;
    --danger: #EF4444;
    --surface: #F1F5F9;
    --card: #FFFFFF;
    --border: #E2E8F0;
    --text: #0F172A;
    --muted: #64748B;
    --hint: #94A3B8;
  }
  .layout { display: flex; min-height: 100vh; }
  .sidebar {
    width: 240px; background: #0F172A; padding: 24px 0;
    display: flex; flex-direction: column; flex-shrink: 0;
    position: fixed; height: 100vh;
  }
  .sidebar-logo {
    padding: 0 20px 24px; display: flex; align-items: center; gap: 10px;
    border-bottom: 1px solid rgba(255,255,255,0.08); margin-bottom: 16px;
  }
  .sidebar-logo span { color: #fff; font-size: 20px; font-weight: 800; letter-spacing: -0.5px; }
  .nav-item {
    padding: 12px 20px; display: flex; align-items: center; gap: 12px;
    color: rgba(255,255,255,0.5); font-size: 14px; font-weight: 500;
    cursor: pointer; transition: all 0.2s;
  }
  .nav-item:hover { color: #fff; background: rgba(255,255,255,0.05); }
  .nav-item.active { color: #fff; background: rgba(26,86,219,0.15); border-right: 3px solid var(--primary); color: #fff; }
  .main { flex: 1; margin-left: 240px; min-width: 0; }
  .topbar {
    background: #fff; padding: 16px 32px; border-bottom: 1px solid var(--border);
    display: flex; align-items: center; justify-content: space-between;
    position: sticky; top: 0; z-index: 10;
  }
  .topbar h1 { font-size: 20px; font-weight: 700; }
  .badge-live {
    background: #ECFDF5; color: var(--success); font-size: 12px; font-weight: 700;
    padding: 6px 12px; border-radius: 20px; display: flex; align-items: center; gap: 8px;
  }
  .live-dot { width: 8px; height: 8px; background: var(--success); border-radius: 50%; animation: pulse 2s infinite; }
  @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.4; } 100% { opacity: 1; } }
  
  .content { padding: 32px; max-width: 1400px; margin: 0 auto; }
  .metrics-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 24px; }
  .metric-card {
    background: var(--card); border: 1px solid var(--border); border-radius: 16px;
    padding: 24px; display: flex; flex-direction: column; gap: 10px;
    transition: transform 0.2s;
  }
  .metric-card:hover { transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05); }
  .metric-header { display: flex; justify-content: space-between; align-items: flex-start; }
  .metric-icon { width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; }
  .metric-val { font-size: 28px; font-weight: 800; letter-spacing: -1px; }
  .metric-label { font-size: 13px; color: var(--muted); font-weight: 500; }
  .metric-trend { font-size: 12px; display: flex; align-items: center; gap: 4px; font-weight: 600; }
  
  .charts-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; margin-bottom: 24px; }
  .card { background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 24px; height: 100%; }
  .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
  .card-title { font-size: 16px; font-weight: 700; color: #1E293B; }
  
  .table-wrap { overflow-x: auto; margin-top: 10px; }
  table { width: 100%; border-collapse: collapse; font-size: 14px; }
  th { text-align: left; padding: 12px 16px; color: var(--muted); font-weight: 600; border-bottom: 1px solid var(--border); font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; }
  td { padding: 14px 16px; border-bottom: 1px solid var(--border); color: #334155; }
  tr:hover { background: #F8FAFC; }
  
  .status-pill {
    display: inline-flex; align-items: center; padding: 4px 12px; border-radius: 20px;
    font-size: 11px; font-weight: 700; text-transform: uppercase;
  }
  .pill-paid { background: #ECFDF5; color: var(--success); }
  .pill-approved { background: #EFF6FF; color: var(--primary); }
  .pill-rejected { background: #FEF2F2; color: var(--danger); }
  .pill-pending { background: #FFFBEB; color: var(--warning); }
  .pill-active { background: #ECFDF5; color: var(--success); }
  .pill-ended { background: #F1F5F9; color: var(--hint); }

  .fraud-tag { font-family: monospace; font-weight: 700; font-size: 13px; }
  .fraud-low { color: var(--success); }
  .fraud-med { color: var(--warning); }
  .fraud-high { color: var(--danger); }

  .modal-overlay {
    position: fixed; top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center;
    z-index: 100; backdrop-filter: blur(4px);
  }
  .modal {
    background: #fff; border-radius: 20px; width: 600px; max-width: 90%;
    max-height: 85vh; overflow-y: auto; padding: 32px; position: relative;
    box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25);
  }
  .modal-close { position: absolute; top: 20px; right: 20px; cursor: pointer; color: var(--muted); }
  
  .worker-protection-card {
    background: linear-gradient(135deg, #1A56DB 0%, #1E40AF 100%);
    color: #fff; border-radius: 16px; padding: 24px; margin-bottom: 24px;
    display: flex; justify-content: space-between; align-items: center;
  }
  .bcr-meter { height: 12px; background: rgba(255,255,255,0.2); border-radius: 6px; overflow: hidden; margin: 10px 0; }
  .bcr-fill { height: 100%; transition: width 1s ease-out; }

  .celery-status {
    padding: 12px 20px; background: rgba(255,255,255,0.03); border-radius: 12px;
    margin: 16px 20px; border: 1px solid rgba(255,255,255,0.08);
  }
  .status-indicator { display: flex; align-items: center; gap: 8px; font-size: 12px; margin-bottom: 8px; }
  .indicator-dot { width: 8px; height: 8px; border-radius: 50%; }

  .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
`

// ── Helpers ───────────────────────────────────────────────────────────────────

function fmt(n) {
  if (n === undefined || n === null) return '₹0'
  if (n >= 10000000) return `₹${(n / 10000000).toFixed(2)}Cr`
  if (n >= 100000) return `₹${(n / 100000).toFixed(2)}L`
  if (n >= 1000) return `₹${(n / 1000).toFixed(1)}K`
  return `₹${n.toFixed(0)}`
}

const COLORS = ['#1A56DB', '#10B981', '#F59E0B', '#8B5CF6', '#EF4444', '#06B6D4']

// ── Components ────────────────────────────────────────────────────────────────

function Sidebar({ active, setActive }) {
  const items = [
    { id: 'overview',     label: 'Overview',      Icon: LayoutDashboard },
    { id: 'analytics',    label: 'Predictive HQ',  Icon: TrendingUp },
    { id: 'claims',       label: 'Claims',        Icon: FileText },
    { id: 'disruptions',  label: 'Disruptions',   Icon: Zap },
    { id: 'workers',      label: 'Workers',       Icon: Users },
  ]
  
  return (
    <div className="sidebar">
      <div className="sidebar-logo">
        <Shield size={26} color="#1A56DB" fill="#1A56DB33" />
        <span>Susanoo</span>
      </div>
      
      <div style={{ flex: 1 }}>
        {items.map(({ id, label, Icon }) => (
          <div
            key={id}
            className={`nav-item ${active === id ? 'active' : ''}`}
            onClick={() => setActive(id)}
          >
            <Icon size={18} />
            <span>{label}</span>
          </div>
        ))}
      </div>

      <div className="celery-status">
        <div style={{ color: 'rgba(255,255,255,0.4)', fontSize: 11, marginBottom: 10, fontWeight: 700, textTransform: 'uppercase' }}>Worker Status</div>
        <div className="status-indicator">
          <div className="indicator-dot" style={{ background: '#10B981', boxShadow: '0 0 8px #10B981' }} />
          <span style={{ color: '#fff', fontWeight: 600 }}>Weather Poll Active</span>
        </div>
        <div className="status-indicator">
          <div className="indicator-dot" style={{ background: '#10B981', boxShadow: '0 0 8px #10B981' }} />
          <span style={{ color: '#fff', fontWeight: 600 }}>AQI Monitor Live</span>
        </div>
        <div style={{ marginTop: 12, display: 'flex', alignItems: 'center', gap: 6, color: 'rgba(255,255,255,0.3)', fontSize: 10 }}>
          <RefreshCw size={10} /> Last sync: 2 mins ago
        </div>
      </div>

      <div style={{ padding: '0 20px 24px' }}>
        <div style={{ color: 'rgba(255,255,255,0.3)', fontSize: 11, marginBottom: 4 }}>ENVIRONMENT</div>
        <div style={{ color: '#F59E0B', fontSize: 12, fontWeight: 700, display: 'flex', alignItems: 'center', gap: 6 }}>
          <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#F59E0B' }} /> PROD-SIMULATOR
        </div>
      </div>
    </div>
  )
}

function MetricCard({ Icon, label, value, trend, color, isCurrency }) {
  const isPositive = trend > 0
  return (
    <div className="metric-card">
      <div className="metric-header">
        <div className="metric-icon" style={{ background: color + '15' }}>
          <Icon size={22} color={color} />
        </div>
        {trend && (
          <div className="metric-trend" style={{ color: isPositive ? 'var(--success)' : 'var(--danger)' }}>
            {isPositive ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
            {Math.abs(trend)}%
          </div>
        )}
      </div>
      <div>
        <div className="metric-val">{isCurrency ? fmt(value) : value.toLocaleString()}</div>
        <div className="metric-label">{label}</div>
      </div>
    </div>
  )
}

// ── Fraud Detail Modal ────────────────────────────────────────────────────────

function FraudModal({ claim, onClose }) {
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`${API}/admin/claims/${claim.id}/fraud`)
      .then(r => r.json())
      .then(d => { setDetail(d); setLoading(false); })
  }, [claim.id])

  if (loading) return (
    <div className="modal-overlay">
      <div className="modal" style={{ textAlign: 'center' }}>Loading Fraud Analysis...</div>
    </div>
  )

  const score = detail.fraud_score * 100
  const color = score > 70 ? 'var(--danger)' : score > 30 ? 'var(--warning)' : 'var(--success)'

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <XCircle className="modal-close" onClick={onClose} />
        <h2 style={{ marginBottom: 24, fontSize: 22, fontWeight: 800 }}>Fraud Deep-Dive</h2>
        
        <div style={{ display: 'flex', gap: 24, marginBottom: 32 }}>
          <div style={{ flex: 1, padding: 24, borderRadius: 16, background: color + '10', border: `1px solid ${color}33`, textAlign: 'center' }}>
            <div style={{ fontSize: 12, color: 'var(--muted)', fontWeight: 700, textTransform: 'uppercase', marginBottom: 8 }}>AI Fraud Score</div>
            <div style={{ fontSize: 48, fontWeight: 800, color }}>{score.toFixed(0)}</div>
            <div style={{ fontSize: 14, fontWeight: 700, color }}>{detail.verdict}</div>
          </div>
          
          <div style={{ flex: 1.5 }}>
            <div style={{ marginBottom: 12 }}>
              <div style={{ fontSize: 12, color: 'var(--muted)', fontWeight: 600 }}>Worker Name</div>
              <div style={{ fontSize: 16, fontWeight: 700 }}>{detail.worker}</div>
            </div>
            <div style={{ marginBottom: 12 }}>
              <div style={{ fontSize: 12, color: 'var(--muted)', fontWeight: 600 }}>Claim ID</div>
              <div style={{ fontSize: 14, fontFamily: 'monospace', fontWeight: 700, color: 'var(--primary)' }}>{detail.claim_id}</div>
            </div>
            <div>
              <div style={{ fontSize: 12, color: 'var(--muted)', fontWeight: 600 }}>Decision Type</div>
              <div style={{ fontSize: 14, fontWeight: 700 }}>{detail.auto_approved ? '🤖 AI Auto-Approved' : '👨‍💻 Manual Review'}</div>
            </div>
          </div>
        </div>

        <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
          <ShieldAlert size={18} color="var(--danger)" /> Detected Anomalies
        </h3>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {detail.flags.length === 0 ? (
            <div style={{ padding: 16, background: '#F8FAFC', borderRadius: 12, color: 'var(--success)', fontWeight: 600, fontSize: 14 }}>
              No fraud flags detected. Behavioral pattern consistent with historical data.
            </div>
          ) : detail.flags.map((flag, i) => (
            <div key={i} style={{ padding: 16, background: '#FEF2F2', borderRadius: 12, borderLeft: '4px solid var(--danger)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: 14, fontWeight: 600, color: '#991B1B' }}>{flag}</span>
              <AlertTriangle size={16} color="var(--danger)" />
            </div>
          ))}
        </div>

        <div style={{ marginTop: 32, padding: 20, background: '#F8FAFC', borderRadius: 16, border: '1px solid var(--border)' }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--muted)', marginBottom: 12 }}>ISOLATION FOREST RECOMMENDATION</div>
          <p style={{ fontSize: 13, lineHeight: 1.6, color: '#475569' }}>
            The claim exhibits <strong>{detail.flags.length}</strong> suspicious characteristics. 
            The cross-city behavioral analysis suggests {score > 70 ? 'high probability of systematic abuse' : 'possible edge-case disruption effect'}. 
            {score > 70 ? ' Recommended action: REJECT and Flag Account.' : ' Recommended action: APPROVE with adjusted payout.'}
          </p>
        </div>
      </div>
    </div>
  )
}

// ── Overview Page ─────────────────────────────────────────────────────────────

function OverviewPage({ data }) {
  if (!data) return <div style={{ padding: 40, textAlign: 'center', color: 'var(--hint)' }}>Loading Real-time Metrics...</div>

  const metrics = data.metrics || {}
  const weekly_chart = data.weekly_chart || []
  const tier_distribution = data.tier_distribution || []
  const active_disruptions = data.active_disruptions || []

  return (
    <>
      <div className="worker-protection-card">
        <div>
          <h2 style={{ fontSize: 14, opacity: 0.8, fontWeight: 600, marginBottom: 4 }}>Gig Worker Income Protected</h2>
          <div style={{ fontSize: 32, fontWeight: 800 }}>{fmt(metrics.payouts_this_week * 12.4)}</div>
          <p style={{ fontSize: 12, opacity: 0.7, marginTop: 4 }}>Estimated total income shortfall covered across all cities this month</p>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: 11, fontWeight: 700, opacity: 0.8, marginBottom: 8 }}>ACTUARIAL HEALTH (BCR)</div>
          <div style={{ fontSize: 24, fontWeight: 800 }}>58.4%</div>
          <div className="bcr-meter" style={{ width: 140 }}>
            <div className="bcr-fill" style={{ width: '58.4%', background: '#fff' }} />
          </div>
          <div style={{ fontSize: 10, fontWeight: 700, color: '#ECFDF5' }}>SAFE ZONE (TARGET: 55-70%)</div>
        </div>
      </div>

      <div className="metrics-grid">
        <MetricCard Icon={Users} label="Active Workers" value={metrics.active_workers ?? 0} trend={+12} color="#1A56DB" />
        <MetricCard Icon={Shield} label="Active Policies" value={metrics.active_policies ?? 0} trend={+8} color="#10B981" />
        <MetricCard Icon={ClipboardList} label="Claims (7D)" value={metrics.claims_this_week ?? 0} trend={-3} color="#F59E0B" />
        <MetricCard Icon={Banknote} label="Payouts (7D)" value={metrics.payouts_this_week ?? 0} trend={+15} color="#8B5CF6" isCurrency />
      </div>

      <div className="charts-grid">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Claims vs. Payouts Efficiency</h3>
            <div style={{ fontSize: 12, color: 'var(--muted)', fontWeight: 600 }}>Last 7 Days</div>
          </div>
          <ResponsiveContainer width="100%" height={280}>
            <ComposedChart data={weekly_chart}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F1F5F9" />
              <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748B' }} dy={10} />
              <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748B' }} />
              <Tooltip 
                contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)' }}
              />
              <Bar dataKey="claims" fill="#1A56DB" radius={[4, 4, 0, 0]} name="Claims Filed" barSize={32} />
              <Line type="monotone" dataKey="payouts" stroke="#10B981" strokeWidth={3} dot={{ r: 4, fill: '#10B981', strokeWidth: 2, stroke: '#fff' }} name="Payout Amt" />
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Risk Exposure</h3>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={tier_distribution}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={80}
                paddingAngle={5}
                dataKey="value"
              >
                {tier_distribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <div style={{ marginTop: 20 }}>
            {tier_distribution.map((t, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8, fontSize: 13 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{ width: 10, height: 10, borderRadius: 2, background: COLORS[i % COLORS.length] }} />
                  <span style={{ fontWeight: 600, color: '#475569' }}>{t.name}</span>
                </div>
                <span style={{ fontWeight: 700 }}>{t.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Live Disruption Monitor</h3>
            <span className="badge-live"><div className="live-dot" /> Tracking {active_disruptions.length} events</span>
          </div>
          {active_disruptions.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--hint)' }}>
              <CheckCircle size={40} color="var(--success)" style={{ opacity: 0.2, marginBottom: 12 }} />
              <p>All cities operating within normal parameters</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {active_disruptions.map((d, i) => (
                <div key={i} style={{ padding: 16, borderRadius: 12, background: '#F8FAFC', border: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 16 }}>
                  <div style={{ 
                    width: 40, height: 40, borderRadius: 10, 
                    background: d.severity === 'extreme' ? '#FEF2F2' : d.severity === 'severe' ? '#FFFBEB' : '#EFF6FF',
                    display: 'flex', alignItems: 'center', justifyCenter: 'center'
                  }}>
                    <Zap size={20} color={d.severity === 'extreme' ? 'var(--danger)' : d.severity === 'severe' ? 'var(--warning)' : 'var(--primary)'} />
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 14, fontWeight: 700 }}>{d.city} • {d.type}</div>
                    <div style={{ fontSize: 12, color: 'var(--muted)' }}>Severity: {d.severity.toUpperCase()} • Infra DSS: {(d.dss * 100).toFixed(0)}%</div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: 14, fontWeight: 800, color: 'var(--primary)' }}>x{d.dss.toFixed(2)}</div>
                    <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--muted)' }}>MULTIPLIER</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Fraud Operations</h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <div style={{ display: 'flex', gap: 16 }}>
              <div style={{ flex: 1, padding: 20, borderRadius: 16, background: '#ECFDF5', textAlign: 'center' }}>
                <div style={{ fontSize: 24, fontWeight: 800, color: 'var(--success)' }}>{data.fraud_summary?.auto_approved ?? 0}</div>
                <div style={{ fontSize: 11, fontWeight: 700, color: '#065F46', marginTop: 4 }}>AUTO-APPROVED</div>
              </div>
              <div style={{ flex: 1, padding: 20, borderRadius: 16, background: '#FEF2F2', textAlign: 'center' }}>
                <div style={{ fontSize: 24, fontWeight: 800, color: 'var(--danger)' }}>{data.fraud_summary?.auto_rejected ?? 0}</div>
                <div style={{ fontSize: 11, fontWeight: 700, color: '#991B1B', marginTop: 4 }}>AUTO-REJECTED</div>
              </div>
            </div>
            
            <div style={{ padding: 20, borderRadius: 16, background: '#F8FAFC', border: '1px solid var(--border)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <div style={{ fontSize: 13, fontWeight: 700 }}>Manual Queue</div>
                <span className="status-pill pill-pending" style={{ padding: '2px 8px' }}>{data.fraud_summary?.under_review ?? 0} Pending</span>
              </div>
              <p style={{ fontSize: 12, color: 'var(--muted)', lineHeight: 1.5 }}>
                AI confidence for these claims is between 30-70%. Requires human verification of platform activity logs.
              </p>
              <button style={{ marginTop: 12, width: '100%', padding: '8px', borderRadius: 8, border: '1px solid var(--primary)', background: 'transparent', color: 'var(--primary)', fontSize: 12, fontWeight: 700, cursor: 'pointer' }}>
                Review Queue
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}

// ── Analytics Page ────────────────────────────────────────────────────────────

function AnalyticsPage({ data }) {
  if (!data) return <div style={{ padding: 40, textAlign: 'center', color: 'var(--hint)' }}>Crunching Predictive Models...</div>

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Benefit-Cost Ratio (BCR) Trend</h3>
            <div style={{ display: 'flex', gap: 8 }}>
               <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--success)' }}>Safe Zone (55-70%)</span>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={240}>
            <AreaChart data={[
              { week: 'W1', bcr: 48 }, { week: 'W2', bcr: 52 }, { week: 'W3', bcr: 61 }, 
              { week: 'W4', bcr: 58 }, { week: 'W5', bcr: 64 }, { week: 'W6', bcr: 58.4 }
            ]}>
              <defs>
                <linearGradient id="colorBcr" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#1A56DB" stopOpacity={0.2}/>
                  <stop offset="95%" stopColor="#1A56DB" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F1F5F9" />
              <XAxis dataKey="week" axisLine={false} tickLine={false} tick={{ fontSize: 12 }} />
              <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12 }} />
              <Tooltip />
              <Area type="monotone" dataKey="bcr" stroke="#1A56DB" strokeWidth={3} fillOpacity={1} fill="url(#colorBcr)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">City-wise Loss Ratios</h3>
            <Info size={16} color="var(--hint)" />
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>City</th><th>Loss Ratio</th><th>Status</th></tr>
              </thead>
              <tbody>
                {data.city_loss_ratios?.map((city, i) => (
                  <tr key={i}>
                    <td style={{ fontWeight: 700 }}>{city.city}</td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <div style={{ flex: 1, height: 6, background: '#F1F5F9', borderRadius: 3, overflow: 'hidden', minWidth: 60 }}>
                          <div style={{ height: '100%', background: city.loss_ratio > 0.8 ? 'var(--danger)' : 'var(--primary)', width: `${Math.min(100, city.loss_ratio * 100)}%` }} />
                        </div>
                        <span style={{ fontWeight: 800 }}>{(city.loss_ratio * 100).toFixed(1)}%</span>
                      </div>
                    </td>
                    <td>
                      <span className={`status-pill ${city.loss_ratio > 0.7 ? 'pill-rejected' : 'pill-active'}`}>
                        {city.loss_ratio > 0.7 ? 'CRITICAL' : 'STABLE'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Next-Week Forecast (Predictive AI)</h3>
          <div style={{ fontSize: 12, padding: '4px 10px', background: '#F1F5F9', borderRadius: 6, fontWeight: 700 }}>XGBoost Engine V4.2</div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 16 }}>
          {data.next_week_forecast?.map((f, i) => (
            <div key={i} style={{ padding: 20, borderRadius: 16, border: '1px solid var(--border)', background: '#F8FAFC' }}>
              <div style={{ fontSize: 14, fontWeight: 800, marginBottom: 12 }}>{f.city}</div>
              <div style={{ fontSize: 11, color: 'var(--muted)', fontWeight: 600, marginBottom: 4 }}>WORKERS AT RISK</div>
              <div style={{ fontSize: 20, fontWeight: 800, color: 'var(--primary)', marginBottom: 16 }}>{f.workers_at_risk}</div>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {f.top_risks.map((risk, j) => (
                  <div key={j} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11 }}>
                    <span style={{ fontWeight: 600 }}>{risk.peril.replace('_', ' ')}</span>
                    <span style={{ fontWeight: 700, color: risk.probability > 30 ? 'var(--danger)' : 'var(--muted)' }}>{risk.probability}%</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="card" style={{ background: '#0F172A', color: '#fff' }}>
        <div className="card-header">
          <h3 className="card-title" style={{ color: '#fff' }}>Actuarial Stress Test: Monsoon Season</h3>
          <span style={{ fontSize: 11, fontWeight: 700, background: 'rgba(255,255,255,0.1)', padding: '4px 12px', borderRadius: 20 }}>SIMULATION MODE</span>
        </div>
        <div style={{ display: 'flex', gap: 40, alignItems: 'center' }}>
          <div style={{ flex: 1 }}>
            <p style={{ fontSize: 14, color: 'rgba(255,255,255,0.6)', lineHeight: 1.6 }}>
              Simulating 14 days of sustained "Severe" rainfall (75mm/day) in <strong>Mumbai</strong> for <strong>{data.stress_test?.workers}</strong> workers.
              This stress test calculates the insolvency risk and capital requirements for extreme climate events.
            </p>
          </div>
          <div style={{ display: 'flex', gap: 24 }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', marginBottom: 4 }}>EST. CLAIMS</div>
              <div style={{ fontSize: 24, fontWeight: 800 }}>{data.stress_test?.est_claims}</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', marginBottom: 4 }}>EST. PAYOUT</div>
              <div style={{ fontSize: 24, fontWeight: 800, color: '#F59E0B' }}>{fmt(data.stress_test?.est_payout)}</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', marginBottom: 4 }}>SOLVENCY RATIO</div>
              <div style={{ fontSize: 24, fontWeight: 800, color: '#10B981' }}>{data.stress_test?.solvency_ratio}x</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Claims Page ───────────────────────────────────────────────────────────────

function ClaimsPage({ data }) {
  const [selectedClaim, setSelectedClaim] = useState(null)
  
  if (!data) return <div style={{ padding: 40, textAlign: 'center', color: 'var(--hint)' }}>Loading Claim Register...</div>

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">Claims Management ({data.length})</h3>
        <div style={{ display: 'flex', gap: 8 }}>
          <div style={{ position: 'relative' }}>
            <Search size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--hint)' }} />
            <input type="text" placeholder="Search Claim ID..." style={{ padding: '8px 12px 8px 36px', borderRadius: 8, border: '1px solid var(--border)', fontSize: 13, width: 220 }} />
          </div>
        </div>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Claim ID</th><th>Worker</th><th>Event</th>
              <th>Payout</th><th>Fraud Score</th><th>Status</th><th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {data.map(c => (
              <tr key={c.id}>
                <td style={{ fontFamily: 'monospace', color: 'var(--primary)', fontWeight: 700 }}>{c.id}</td>
                <td style={{ fontWeight: 700 }}>{c.worker} <div style={{ fontSize: 11, color: 'var(--muted)', fontWeight: 500 }}>{c.city}</div></td>
                <td><span style={{ fontSize: 13, fontWeight: 600 }}>{c.event}</span></td>
                <td style={{ fontWeight: 800 }}>{c.amount}</td>
                <td>
                  <span className={`fraud-tag ${c.fraud > 70 ? 'fraud-high' : c.fraud > 30 ? 'fraud-med' : 'fraud-low'}`}>
                    {c.fraud}%
                  </span>
                </td>
                <td><span className={`status-pill pill-${c.status}`}>{c.status}</span></td>
                <td>
                  <button 
                    onClick={() => setSelectedClaim(c)}
                    style={{ padding: '6px 12px', borderRadius: 6, border: '1px solid var(--border)', background: '#fff', fontSize: 11, fontWeight: 700, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6 }}
                  >
                    <Eye size={12} /> Analyze
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {selectedClaim && <FraudModal claim={selectedClaim} onClose={() => setSelectedClaim(null)} />}
    </div>
  )
}

// ── Disruptions Page ──────────────────────────────────────────────────────────

function DisruptionsPage({ data }) {
  if (!data) return <div style={{ padding: 40, textAlign: 'center', color: 'var(--hint)' }}>Loading Event Logs...</div>
  return (
    <div className="card">
      <div className="card-title">Disruption Event History ({data.length})</div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr><th>City</th><th>Trigger Type</th><th>Severity</th><th>DSS Impact</th><th>Time</th><th>Status</th></tr>
          </thead>
          <tbody>
            {data.map((d, i) => (
              <tr key={i}>
                <td style={{ fontWeight: 700 }}>{d.city}</td>
                <td style={{ fontWeight: 600 }}>{d.type}</td>
                <td>
                  <span className={`status-pill ${d.severity === 'extreme' ? 'pill-rejected' : d.severity === 'severe' ? 'pill-pending' : 'pill-approved'}`}>
                    {d.severity}
                  </span>
                </td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <div style={{ flex: 1, height: 6, background: '#F1F5F9', borderRadius: 3, width: 80, overflow: 'hidden' }}>
                      <div style={{ height: '100%', background: 'var(--primary)', width: `${d.dss * 100}%` }} />
                    </div>
                    <span style={{ fontWeight: 800 }}>{(d.dss * 100).toFixed(0)}%</span>
                  </div>
                </td>
                <td style={{ color: 'var(--muted)', fontSize: 12, fontWeight: 500 }}>
                  {d.started_at ? new Date(d.started_at).toLocaleString('en-IN', { dateStyle: 'short', timeStyle: 'short' }) : '—'}
                </td>
                <td><span className={`status-pill ${d.active ? 'pill-active' : 'pill-ended'}`}>{d.active ? 'LIVE' : 'ARCHIVED'}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ── Workers Page ──────────────────────────────────────────────────────────────

function WorkersPage({ data }) {
  if (!data) return <div style={{ padding: 40, textAlign: 'center', color: 'var(--hint)' }}>Loading Worker Registry...</div>
  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">Active Risk Profiles ({data.length})</h3>
        <button style={{ padding: '8px 16px', borderRadius: 8, background: 'var(--primary)', color: '#fff', border: 'none', fontSize: 12, fontWeight: 700, cursor: 'pointer' }}>
          Export CRM
        </button>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr><th>Worker Name</th><th>Platform</th><th>City</th><th>Risk Level</th><th>Verification</th><th>Status</th></tr>
          </thead>
          <tbody>
            {data.map(w => (
              <tr key={w.id}>
                <td style={{ fontWeight: 700 }}>{w.name} <div style={{ fontSize: 11, color: 'var(--muted)', fontWeight: 500 }}>{w.phone}</div></td>
                <td style={{ textTransform: 'capitalize', fontWeight: 600 }}>{w.platform.replace('_', ' ')}</td>
                <td>{w.city}</td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <div style={{ width: 8, height: 8, borderRadius: '50%', background: w.risk_score > 0.7 ? 'var(--danger)' : w.risk_score > 0.4 ? 'var(--warning)' : 'var(--success)' }} />
                    <span style={{ fontWeight: 700 }}>{(w.risk_score * 100).toFixed(0)}%</span>
                  </div>
                </td>
                <td>
                  {w.is_verified
                    ? <span style={{ color: 'var(--success)', display: 'flex', alignItems: 'center', gap: 4, fontSize: 12, fontWeight: 700 }}><UserCheck size={14} /> KYC OK</span>
                    : <span style={{ color: 'var(--hint)', display: 'flex', alignItems: 'center', gap: 4, fontSize: 12, fontWeight: 700 }}><AlertTriangle size={14} /> UNVERIFIED</span>
                  }
                </td>
                <td><span className={`status-pill ${w.is_active ? 'pill-active' : 'pill-ended'}`}>{w.is_active ? 'ACTIVE' : 'OFFLINE'}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ── Main App ──────────────────────────────────────────────────────────────────

export default function App() {
  const [active, setActive] = useState('overview')
  const [stats, setStats]           = useState(null)
  const [analytics, setAnalytics]   = useState(null)
  const [claims, setClaims]         = useState(null)
  const [disruptions, setDisruptions] = useState(null)
  const [workers, setWorkers]       = useState(null)

  useEffect(() => {
    fetch(`${API}/admin/stats`).then(r => r.json()).then(setStats).catch(() => setStats({}))
    fetch(`${API}/admin/analytics`).then(r => r.json()).then(setAnalytics).catch(() => setAnalytics({}))
  }, [])

  useEffect(() => {
    if (active === 'claims' && !claims)
      fetch(`${API}/admin/claims`).then(r => r.json()).then(setClaims).catch(() => setClaims([]))
    if (active === 'disruptions' && !disruptions)
      fetch(`${API}/admin/disruptions`).then(r => r.json()).then(setDisruptions).catch(() => setDisruptions([]))
    if (active === 'workers' && !workers)
      fetch(`${API}/admin/workers`).then(r => r.json()).then(setWorkers).catch(() => setWorkers([]))
  }, [active])

  const renderContent = () => {
    switch (active) {
      case 'overview':    return <OverviewPage    data={stats} />
      case 'analytics':   return <AnalyticsPage   data={analytics} />
      case 'claims':      return <ClaimsPage      data={claims} />
      case 'disruptions': return <DisruptionsPage data={disruptions} />
      case 'workers':     return <WorkersPage     data={workers} />
      default:            return <OverviewPage    data={stats} />
    }
  }

  const titles = {
    overview: 'InsurOps Command Center',
    analytics: 'Actuarial Predictive HQ',
    claims: 'Claims & Fraud Operations',
    disruptions: 'Climate Disruption Registry',
    workers: 'Worker Risk Profiles'
  }

  return (
    <>
      <style>{styles}</style>
      <div className="layout">
        <Sidebar active={active} setActive={setActive} />
        <div className="main">
          <div className="topbar">
            <h1>{titles[active]}</h1>
            <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
              <div style={{ textAlign: 'right', display: 'none' /* mobile hide */ }}>
                <div style={{ fontSize: 12, fontWeight: 700 }}>Admin Session</div>
                <div style={{ fontSize: 10, color: 'var(--muted)' }}>v3.0.4 - Secure Access</div>
              </div>
              <div className="badge-live">
                <div className="live-dot" />
                Live Network Data
              </div>
              <div style={{ width: 36, height: 36, borderRadius: '50%', background: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 800, fontSize: 14 }}>
                AD
              </div>
            </div>
          </div>
          <div className="content">
            {renderContent()}
          </div>
        </div>
      </div>
    </>
  )
}
