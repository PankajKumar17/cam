import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  BarChart, Bar, LineChart, Line, AreaChart, Area, ComposedChart,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Legend,
} from 'recharts'
import { useAnalysis } from '../App'
import { Card, SectionHeader, DataTable, EmptyState, Badge } from '../components/ui'
import { g, fmt, pct, RISK_COLORS } from '../lib/utils'
import { BarChart2, TrendingUp, Zap, MessageSquare } from 'lucide-react'

const TABS = ['Financial', 'Forensics', 'Stress Test', 'Bull vs Bear']

const tooltipStyle = {
  background: '#1A1A1A', border: 'none', borderRadius: 8,
  color: '#fff', fontSize: 12, padding: '8px 12px',
  boxShadow: '0 4px 16px rgba(0,0,0,0.25)',
}

export default function DeepDive() {
  const [activeTab, setActiveTab] = useState(0)
  const { analysis } = useAnalysis()
  const d = analysis?.data || {}
  const fin = g(d, 'financial_data') || {}
  const traj = g(d, 'trajectory') || {}
  const stress = g(d, 'stress_test') || {}
  const company = d.company_name || 'Company'

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <SectionHeader title="Deep Dive Analysis" subtitle={`Visual breakdown for ${company}`} />

      {/* Tab bar */}
      <div className="flex gap-1 mb-6 overflow-x-auto pb-1">
        {TABS.map((tab, i) => (
          <button
            key={tab}
            onClick={() => setActiveTab(i)}
            className={`px-4 py-2 text-sm font-medium transition-all border-b-2 whitespace-nowrap flex-shrink-0
              ${activeTab === i
                ? 'border-orange text-dark font-semibold'
                : 'border-transparent text-text-secondary hover:text-dark'}`}
          >
            {tab}
          </button>
        ))}
      </div>

      {activeTab === 0 && <FinancialTab fin={fin} traj={traj} />}
      {activeTab === 1 && <ForensicsTab fin={fin} d={d} />}
      {activeTab === 2 && <StressTab stress={stress} />}
      {activeTab === 3 && <DebateTab d={d} />}
    </motion.div>
  )
}

/* ── Financial Tab ─────────────────────────── */
function FinancialTab({ fin, traj }) {
  const dscrHistory = traj.dscr_history || []
  const years = traj.fiscal_years || []

  const revenueHistory = fin.revenue_history || []
  const revenueData = years.map((yr, i) => ({
    year: `FY${yr}`,
    dscr: dscrHistory[i],
    revenue: revenueHistory[i] != null ? revenueHistory[i] : (fin.revenue ? fin.revenue * (0.7 + i * 0.075) : null),
  }))

  const ratios = [
    { label: 'Revenue', value: fin.revenue, fmt: `₹${fmt(fin.revenue)} Cr` },
    { label: 'EBITDA Margin', value: fin.ebitda_margin, fmt: pct(fin.ebitda_margin) },
    { label: 'Current Ratio', value: fin.current_ratio, fmt: fmt(fin.current_ratio) },
    { label: 'Net Margin', value: fin.net_margin, fmt: pct(fin.net_margin) },
    { label: 'D/E Ratio', value: fin.debt_to_equity, fmt: fmt(fin.debt_to_equity) },
    { label: 'ROE', value: fin.roe, fmt: pct(fin.roe) },
  ]

  return (
    <div className="space-y-4">
      {/* Revenue & DSCR chart */}
      <Card>
        <h3 className="text-sm font-semibold text-dark mb-4">Revenue & DSCR History</h3>
        {revenueData.length > 1 ? (
          <ResponsiveContainer width="100%" height={280}>
            <ComposedChart data={revenueData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" vertical={false} />
              <XAxis dataKey="year" tick={{ fill: '#9CA3AF', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis yAxisId="left" tick={{ fill: '#9CA3AF', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis yAxisId="right" orientation="right" tick={{ fill: '#9CA3AF', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={tooltipStyle} />
              <Legend />
              <Bar yAxisId="left" dataKey="revenue" fill="#E8470A" opacity={0.8} name="Revenue (Cr)" radius={[4,4,0,0]} />
              <Line yAxisId="right" dataKey="dscr" stroke="#1A1A1A" strokeWidth={2.5} name="DSCR"
                    dot={{ fill: 'white', stroke: '#1A1A1A', strokeWidth: 2, r: 4 }} />
              <ReferenceLine yAxisId="right" y={1.25} stroke="#F59E0B" strokeDasharray="4 2" />
              <ReferenceLine yAxisId="right" y={1.0} stroke="#EF4444" strokeDasharray="4 2" />
            </ComposedChart>
          </ResponsiveContainer>
        ) : (
          <EmptyState icon={BarChart2} title="Insufficient data" subtitle="Need at least 2 years for chart" />
        )}
      </Card>

      {/* Key Ratios Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {ratios.map(r => (
          <Card key={r.label} className="p-4">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">{r.label}</p>
            <p className="text-xl font-bold text-dark mt-1">{r.fmt}</p>
          </Card>
        ))}
      </div>
    </div>
  )
}

/* ── Forensics Tab ─────────────────────────── */
function ForensicsTab({ fin, d }) {
  const forensics = g(d, 'forensics') || {}
  const components = [
    { name: 'DSRI', value: fin.beneish_dsri ?? 0.95, threshold: 1.465 },
    { name: 'GMI', value: 1.0, threshold: 1.014 },
    { name: 'AQI', value: 1.0, threshold: 1.254 },
    { name: 'SGI', value: 1.08, threshold: 1.607 },
    { name: 'DEPI', value: 1.0, threshold: 1.077 },
    { name: 'SGAI', value: 1.0, threshold: 1.041 },
    { name: 'TATA', value: fin.beneish_tata ?? 0.03, threshold: 0.031 },
    { name: 'LVGI', value: 1.0, threshold: 1.111 },
  ]

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1.2fr_0.8fr] gap-4">
      <Card>
        <h3 className="text-sm font-semibold text-dark mb-4">Beneish 8-Component Breakdown</h3>
        <div className="space-y-3">
          {components.map(c => {
            const pctVal = Math.min((c.value / (c.threshold * 2)) * 100, 100)
            const isFlag = c.value > c.threshold
            return (
              <div key={c.name} className="flex items-center gap-3">
                <span className="text-xs font-semibold text-text-secondary w-12">{c.name}</span>
                <div className="flex-1 h-2 bg-border rounded-full overflow-hidden relative">
                  <div className="h-full rounded-full" style={{ width: `${pctVal}%`, background: isFlag ? '#EF4444' : '#E8470A' }} />
                  <div className="absolute top-0 h-full w-px bg-text-muted" style={{ left: `${(c.threshold / (c.threshold * 2)) * 100}%` }} />
                </div>
                <span className={`text-xs font-[DM_Mono] w-12 text-right ${isFlag ? 'text-danger font-bold' : ''}`}>
                  {c.value.toFixed(3)}
                </span>
              </div>
            )
          })}
        </div>
      </Card>

      <div className="space-y-4">
        <Card className="text-center p-8">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-text-muted mb-2">Beneish M-Score</p>
          <p className={`text-4xl font-bold ${(fin.beneish_m_score ?? -3) > -2.22 ? 'text-danger' : 'text-success'}`}>
            {fmt(fin.beneish_m_score)}
          </p>
          <Badge
            text={(fin.beneish_m_score ?? -3) > -2.22 ? 'SUSPICIOUS' : 'CLEAN'}
            color={(fin.beneish_m_score ?? -3) > -2.22 ? '#EF4444' : '#10B981'}
            bg={(fin.beneish_m_score ?? -3) > -2.22 ? '#FEF2F2' : '#ECFDF5'}
          />
        </Card>
        <Card className="text-center p-8">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-text-muted mb-2">Altman Z-Score</p>
          <p className="text-4xl font-bold text-warning">{fmt(fin.altman_z_score)}</p>
          <Badge text={forensics.altman_zone || 'GREY'} color="#F59E0B" bg="#FFFBEB" />
        </Card>
        <Card className="text-center p-8">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-text-muted mb-2">Piotroski F-Score</p>
          <p className="text-4xl font-bold text-dark">{fin.piotroski_f_score ?? '—'}</p>
          <Badge text={`${fin.piotroski_f_score ?? 0}/9`} color="#6B7280" bg="#F4F5F7" />
        </Card>
      </div>
    </div>
  )
}

/* ── Stress Tab ────────────────────────────── */
function StressTab({ stress }) {
  const simulated = stress.dscr_simulated || []
  const scenarios = stress.named_scenarios || []

  // Build histogram bins
  const bins = []
  if (simulated.length > 0) {
    const min = Math.floor(Math.min(...simulated) * 10) / 10
    const max = Math.ceil(Math.max(...simulated) * 10) / 10
    const step = 0.1
    for (let v = min; v <= max; v += step) {
      const count = simulated.filter(x => x >= v && x < v + step).length
      bins.push({ range: v.toFixed(1), count })
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1.3fr_0.7fr] gap-4">
      <Card>
        <h3 className="text-sm font-semibold text-dark mb-4">Monte Carlo DSCR Distribution</h3>
        {bins.length > 0 ? (
          <>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={bins}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" vertical={false} />
                <XAxis dataKey="range" tick={{ fill: '#9CA3AF', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#9CA3AF', fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={tooltipStyle} />
                <Bar dataKey="count" fill="#E8470A" radius={[2,2,0,0]} />
                <ReferenceLine x={fmt(stress.dscr_p10, 1)} stroke="#EF4444" strokeDasharray="4 2" label={{ value: 'P10', fill: '#EF4444', fontSize: 10 }} />
                <ReferenceLine x={fmt(stress.dscr_p50, 1)} stroke="#F59E0B" strokeDasharray="4 2" label={{ value: 'P50', fill: '#F59E0B', fontSize: 10 }} />
              </BarChart>
            </ResponsiveContainer>
            <div className="flex gap-3 mt-3">
              <span className="bg-danger-bg text-danger px-2.5 py-1 rounded-full text-xs font-semibold">P10: {fmt(stress.dscr_p10)}</span>
              <span className="bg-warning-bg text-warning px-2.5 py-1 rounded-full text-xs font-semibold">P50: {fmt(stress.dscr_p50)}</span>
              <span className="bg-success-bg text-success px-2.5 py-1 rounded-full text-xs font-semibold">P90: {fmt(stress.dscr_p90)}</span>
            </div>
          </>
        ) : (
          <EmptyState icon={Zap} title="No simulations" subtitle="Run stress test to see distribution" />
        )}
      </Card>

      <Card>
        <h3 className="text-sm font-semibold text-dark mb-4">Scenario Breakdown</h3>
        <div className="space-y-3">
          {scenarios.map(sc => {
            const pass = sc.dscr_impact >= 1.0
            return (
              <div key={sc.name} className="bg-surface-row rounded-xl p-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-dark">{sc.name}</span>
                  <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${pass ? 'bg-success-bg text-success' : 'bg-danger-bg text-danger'}`}>
                    {pass ? 'PASS' : 'FAIL'}
                  </span>
                </div>
                <div className="flex gap-4 mt-1 text-xs text-text-muted">
                  <span>DSCR: {fmt(sc.dscr_impact)}</span>
                  <span>PD Impact: {pct(sc.pd_impact)}</span>
                </div>
              </div>
            )
          })}
          {scenarios.length === 0 && (
            <p className="text-sm text-text-muted italic py-4 text-center">No scenarios available</p>
          )}
        </div>
      </Card>
    </div>
  )
}

/* ── Bull vs Bear Tab ──────────────────────── */
function DebateTab({ d }) {
  const bull = d.bull_case || ''
  const bear = d.bear_case || ''
  const verdict = g(d, 'recommendation', 'final_rationale') || ''

  function inlineBold(text) {
    const parts = text.split(/\*\*(.*?)\*\*/g)
    return parts.map((p, i) => i % 2 === 1 ? <strong key={i} className="font-semibold text-dark">{p}</strong> : p)
  }

  function renderMd(text) {
    if (!text) return null
    return text.split('\n').map((line, i) => {
      if (line.startsWith('#### ')) return <h4 key={i} className="text-xs font-bold uppercase tracking-wide text-dark mt-4 mb-1">{inlineBold(line.replace(/^#{1,4}\s*/, ''))}</h4>
      if (line.startsWith('### ')) return <h3 key={i} className="text-sm font-bold text-dark mt-5 mb-2 border-b border-border pb-1">{inlineBold(line.replace(/^###\s*/, ''))}</h3>
      if (line.startsWith('## ')) return <h3 key={i} className="text-sm font-semibold text-dark mt-4 mb-2">{inlineBold(line.replace(/^##\s*/, ''))}</h3>
      if (line.match(/^[*-] /)) return <li key={i} className="text-sm text-text-secondary ml-4 list-disc leading-relaxed">{inlineBold(line.replace(/^[*-] /, ''))}</li>
      if (line.trim() === '') return <div key={i} className="h-2" />
      return <p key={i} className="text-sm text-text-secondary leading-relaxed">{inlineBold(line)}</p>
    })
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card className="border-l-4 border-l-success bg-success-bg/30 p-5">
          <h3 className="text-success font-semibold mb-3">Bull Case — Approve</h3>
          {bull ? renderMd(bull) : <EmptyState icon={MessageSquare} title="Not available" subtitle="Run LLM agents" />}
        </Card>
        <Card className="border-l-4 border-l-danger bg-danger-bg/30 p-5">
          <h3 className="text-danger font-semibold mb-3">Bear Case — Reject</h3>
          {bear ? renderMd(bear) : <EmptyState icon={MessageSquare} title="Not available" subtitle="Run LLM agents" />}
        </Card>
      </div>

      {verdict && (
        <div className="bg-dark rounded-2xl p-5 text-white">
          <p className="text-xs font-semibold uppercase tracking-wider text-orange mb-2">Coordinator Verdict</p>
          <p className="text-base leading-relaxed">{verdict}</p>
        </div>
      )}
    </div>
  )
}
