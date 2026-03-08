import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  BarChart, Bar, LineChart, Line, AreaChart, Area, ComposedChart,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Legend,
} from 'recharts'
import { useAnalysis } from '../App'
import { Card, SectionHeader, DataTable, EmptyState, Badge } from '../components/ui'
import { g, fmt, pct, RISK_COLORS } from '../lib/utils'
import { BarChart2, TrendingUp, Zap, MessageSquare, Satellite, Shield } from 'lucide-react'

const TABS = ['Financial', 'Forensics', 'Stress Test', 'Bull vs Bear', 'Satellite', 'Compliance']

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
  const sat = g(d, 'satellite') || {}
  const mca = g(d, 'mca_legal') || {}
  const bank = g(d, 'bank_analysis') || {}
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
      {activeTab === 4 && <SatelliteTab sat={sat} />}
      {activeTab === 5 && <ComplianceTab mca={mca} bank={bank} />}
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

  // Prefer live values from forensics module; fall back to financial_data fields
  const components = [
    { name: 'DSRI',  value: forensics.beneish_dsri  ?? fin.beneish_dsri  ?? 0.95, threshold: 1.465, desc: 'Days Sales Receivables Index' },
    { name: 'GMI',   value: forensics.beneish_gmi   ?? 1.0, threshold: 1.014, desc: 'Gross Margin Index' },
    { name: 'AQI',   value: forensics.beneish_aqi   ?? 1.0, threshold: 1.254, desc: 'Asset Quality Index' },
    { name: 'SGI',   value: forensics.beneish_sgi   ?? 1.08, threshold: 1.607, desc: 'Sales Growth Index' },
    { name: 'DEPI',  value: forensics.beneish_depi  ?? 1.0, threshold: 1.077, desc: 'Depreciation Index' },
    { name: 'SGAI',  value: forensics.beneish_sgai  ?? 1.0, threshold: 1.041, desc: 'SG&A Index' },
    { name: 'TATA',  value: forensics.beneish_tata  ?? fin.beneish_tata  ?? 0.03, threshold: 0.031, desc: 'Total Accruals to Total Assets' },
    { name: 'LVGI',  value: forensics.beneish_lvgi  ?? 1.0, threshold: 1.111, desc: 'Leverage Index' },
  ]

  // Piotroski 9-signal breakdown
  const psignals = forensics.piotroski_signals || []

  return (
    <div className="space-y-4">
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
                  <span className={`text-xs font-[DM_Mono] w-14 text-right ${isFlag ? 'text-danger font-bold' : ''}`}>
                    {typeof c.value === 'number' ? c.value.toFixed(3) : c.value}
                  </span>
                </div>
              )
            })}
          </div>
          {forensics.beneish_red_flags?.length > 0 && (
            <div className="mt-3 pt-3 border-t border-border space-y-1">
              {forensics.beneish_red_flags.map((f, i) => (
                <p key={i} className="text-xs text-danger">⚠ {f}</p>
              ))}
            </div>
          )}
        </Card>

        <div className="space-y-4">
          <Card className="text-center p-6">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-text-muted mb-2">Beneish M-Score</p>
            <p className={`text-4xl font-bold ${
              (forensics.beneish_m_score ?? fin.beneish_m_score ?? -3) > -2.22 ? 'text-danger' : 'text-success'
            }`}>
              {fmt(forensics.beneish_m_score ?? fin.beneish_m_score)}
            </p>
            <Badge
              text={forensics.beneish_flag ?? ((forensics.beneish_m_score ?? fin.beneish_m_score ?? -3) > -2.22 ? 'MANIPULATOR' : 'CLEAN')}
              color={(forensics.beneish_m_score ?? fin.beneish_m_score ?? -3) > -2.22 ? '#EF4444' : '#10B981'}
              bg={(forensics.beneish_m_score ?? fin.beneish_m_score ?? -3) > -2.22 ? '#FEF2F2' : '#ECFDF5'}
            />
          </Card>
          <Card className="text-center p-6">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-text-muted mb-2">Altman Z-Score</p>
            <p className="text-4xl font-bold text-warning">{fmt(forensics.altman_z_score ?? fin.altman_z_score)}</p>
            <Badge
              text={forensics.altman_zone || 'GREY'}
              color={forensics.altman_zone === 'SAFE' ? '#10B981' : forensics.altman_zone === 'DISTRESS' ? '#EF4444' : '#F59E0B'}
              bg={forensics.altman_zone === 'SAFE' ? '#ECFDF5' : forensics.altman_zone === 'DISTRESS' ? '#FEF2F2' : '#FFFBEB'}
            />
          </Card>
          <Card className="text-center p-6">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-text-muted mb-2">Piotroski F-Score</p>
            <p className="text-4xl font-bold text-dark">{forensics.piotroski_f_score ?? fin.piotroski_f_score ?? '—'}</p>
            <Badge
              text={`${forensics.piotroski_f_score ?? fin.piotroski_f_score ?? 0}/9 · ${forensics.piotroski_strength || 'N/A'}`}
              color={forensics.piotroski_strength === 'STRONG' ? '#10B981' : forensics.piotroski_strength === 'WEAK' ? '#EF4444' : '#6B7280'}
              bg={forensics.piotroski_strength === 'STRONG' ? '#ECFDF5' : forensics.piotroski_strength === 'WEAK' ? '#FEF2F2' : '#F4F5F7'}
            />
          </Card>
        </div>
      </div>

      {/* Piotroski 9-signal breakdown */}
      {psignals.length > 0 && (
        <Card>
          <h3 className="text-sm font-semibold text-dark mb-4">Piotroski F-Score — 9 Signal Breakdown</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
            {psignals.map((sig, i) => (
              <div key={i} className={`flex items-center gap-2 rounded-xl px-3 py-2 ${
                sig.passed ? 'bg-success-bg' : 'bg-surface-row'
              }`}>
                <span className={`text-base ${sig.passed ? 'text-success' : 'text-text-muted'}`}>
                  {sig.passed ? '✓' : '✗'}
                </span>
                <div className="min-w-0">
                  <p className={`text-xs font-medium truncate ${sig.passed ? 'text-success' : 'text-text-muted'}`}>{sig.signal}</p>
                  <p className="text-[10px] text-text-muted">{sig.group}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
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

/* ── Satellite Tab ──────────────────────────── */
function SatelliteTab({ sat }) {
  const score = sat.activity_score ?? 0
  const classification = sat.activity_category ?? sat.classification ?? 'N/A'
  const ndviScore = sat.ndvi_score ?? 0
  const brightnessScore = sat.brightness_score ?? 0
  const deltaScore = sat.delta_score ?? 50
  const flag = sat.satellite_vs_revenue_flag ?? sat.vs_revenue_flag ?? 0
  const source = sat.data_source ?? 'synthetic_fallback'
  const imageCurrent = sat.image_b64
  const imageBaseline = sat.baseline_image_b64

  const scoreColor = score >= 70 ? '#10B981' : score >= 50 ? '#F59E0B' : score >= 30 ? '#F97316' : '#EF4444'

  const subScores = [
    { label: 'NDVI Score', value: ndviScore, weight: '35%', color: '#1565C0', desc: 'Low NDVI = industrial activity (good for factory)' },
    { label: 'Brightness Score', value: brightnessScore, weight: '40%', color: '#E8470A', desc: 'Higher pixel brightness = more surface activity' },
    { label: 'Temporal Delta', value: deltaScore, weight: '25%', color: '#10B981', desc: 'Year-over-year brightness change (monsoon-safe baseline)' },
  ]

  return (
    <div className="space-y-4">
      {/* Source badge */}
      <div className="flex items-center gap-2">
        <Satellite size={15} className="text-text-muted" />
        <span className="text-xs text-text-muted">Data source:</span>
        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${source === 'sentinel_api' ? 'bg-success-bg text-success' : 'bg-surface-row text-text-secondary'}`}>
          {source === 'sentinel_api' ? 'Sentinel-2 Live Imagery (ESA Copernicus)' : 'Synthetic Model (Sentinel Hub credentials not active)'}
        </span>
      </div>

      {/* Images */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <h3 className="text-sm font-semibold text-dark mb-3">Current Imagery</h3>
          {imageCurrent ? (
            <img
              src={`data:image/png;base64,${imageCurrent}`}
              alt="Current satellite view"
              className="w-full rounded-xl border border-border"
              style={{ imageRendering: 'pixelated' }}
            />
          ) : (
            <EmptyState icon={Satellite} title="Image unavailable" subtitle="No image data returned" />
          )}
          <p className="text-xs text-text-muted mt-2">{sat.current_date || 'Latest available'} · RGB composite (B04/B03/B02)</p>
        </Card>

        <Card>
          <h3 className="text-sm font-semibold text-dark mb-3">6-Month Baseline</h3>
          {imageBaseline ? (
            <img
              src={`data:image/png;base64,${imageBaseline}`}
              alt="Baseline satellite view"
              className="w-full rounded-xl border border-border"
              style={{ imageRendering: 'pixelated' }}
            />
          ) : (
            <EmptyState icon={Satellite} title="Baseline unavailable" subtitle="No historical image found" />
          )}
          <p className="text-xs text-text-muted mt-2">{sat.baseline_date || '~1 year ago'} · RGB composite (B04/B03/B02)</p>
          {sat.baseline_date_reason && (
            <div className="mt-2 flex items-start gap-1.5 bg-amber-50 border border-amber-200 rounded-lg px-2.5 py-1.5">
              <span className="text-amber-500 mt-px text-[11px]">☁</span>
              <p className="text-[10px] text-amber-700 leading-tight">{sat.baseline_date_reason}</p>
            </div>
          )}
        </Card>
      </div>

      {/* Score + breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-[200px_1fr] gap-4">
        <Card className="flex flex-col items-center justify-center p-8 text-center">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-text-muted mb-2">Activity Score</p>
          <p className="text-5xl font-bold" style={{ color: scoreColor }}>{fmt(score, 1)}</p>
          <p className="text-xs text-text-muted mt-1">/ 100</p>
          <span className="mt-3 px-3 py-1 rounded-full text-xs font-bold border" style={{ borderColor: scoreColor, color: scoreColor }}>
            {classification}
          </span>
          {flag ? (
            <div className="mt-3 bg-danger-bg text-danger text-xs px-3 py-1.5 rounded-lg font-semibold">⚠ Revenue Mismatch</div>
          ) : (
            <div className="mt-3 bg-success-bg text-success text-xs px-3 py-1.5 rounded-lg font-semibold">✓ Revenue Consistent</div>
          )}
        </Card>

        <Card>
          <h3 className="text-sm font-semibold text-dark mb-4">Score Breakdown</h3>
          <div className="space-y-4">
            {subScores.map(s => (
              <div key={s.label}>
                <div className="flex justify-between items-baseline mb-1">
                  <span className="text-xs font-medium text-text-secondary">{s.label}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-text-muted">weight {s.weight}</span>
                    <span className="text-sm font-bold text-dark">{fmt(s.value, 1)}</span>
                  </div>
                </div>
                <div className="h-2.5 bg-border rounded-full overflow-hidden">
                  <div className="h-full rounded-full" style={{ width: `${Math.min(s.value, 100)}%`, background: s.color }} />
                </div>
                <p className="text-[10px] text-text-muted mt-0.5">{s.desc}</p>
              </div>
            ))}
          </div>

          <div className="mt-4 pt-3 border-t border-border grid grid-cols-3 gap-2">
            {[
              { label: 'NDVI (mean)', value: (sat.mean_ndvi ?? 0).toFixed(4) },
              { label: 'Brightness', value: (sat.mean_brightness ?? 0).toFixed(4) },
              { label: 'Δ Brightness', value: sat.brightness_delta != null ? `${sat.brightness_delta >= 0 ? '+' : ''}${sat.brightness_delta.toFixed(4)}` : 'N/A' },
            ].map(m => (
              <div key={m.label} className="bg-surface-row rounded-lg p-2 text-center">
                <p className="text-[10px] text-text-muted">{m.label}</p>
                <p className="text-xs font-mono font-semibold text-dark mt-0.5">{m.value}</p>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  )
}

/* ── Compliance Tab (MCA + Bank / Circular Trading) ─────── */
function ComplianceTab({ mca, bank }) {
  const legalScore = mca.legal_risk_score ?? 0
  const legalLevel = mca.legal_risk_level ?? 'LOW'
  const riskFactors = mca.risk_factors ?? []
  const legalCases = mca.legal_cases ?? []
  const charges = mca.charges ?? []
  const dinDisqualified = mca.din_disqualified_count ?? 0

  const bankScore = bank.overall_bank_risk_score ?? 0
  const bankLevel = bank.overall_bank_risk_level ?? 'LOW'
  const circularScore = bank.circular_trading_score ?? 0
  const circularDetected = bank.circular_detected ?? false
  const gstRisk = bank.gst_2a_3b_risk_level ?? 'LOW'
  const itcMatch = bank.itc_match_pct ?? 100
  const revDiv = bank.revenue_divergence_pct ?? 0
  const bounceCount = bank.bounce_count_12m ?? 0
  const bankFlags = bank.all_risk_flags ?? []

  const scoreColor = (level) =>
    level === 'HIGH' ? '#EF4444' : level === 'MEDIUM' ? '#F59E0B' : '#10B981'
  const scoreBg = (level) =>
    level === 'HIGH' ? '#FEF2F2' : level === 'MEDIUM' ? '#FFFBEB' : '#ECFDF5'

  return (
    <div className="space-y-4">
      {/* Summary cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="text-center p-6">
          <Shield size={20} className="mx-auto mb-2 text-text-muted" />
          <p className="text-[11px] font-semibold uppercase tracking-wider text-text-muted mb-1">MCA / Legal Risk Score</p>
          <p className="text-4xl font-bold" style={{ color: scoreColor(legalLevel) }}>{legalScore}</p>
          <p className="text-xs text-text-muted mt-0.5">/ 100</p>
          <Badge text={legalLevel} color={scoreColor(legalLevel)} bg={scoreBg(legalLevel)} />
          {dinDisqualified > 0 && (
            <div className="mt-3 bg-danger-bg text-danger text-xs px-3 py-1.5 rounded-lg font-semibold">
              ⚠ {dinDisqualified} Director DIN Disqualified
            </div>
          )}
        </Card>

        <Card className="text-center p-6">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-text-muted mb-1">Bank / Circular Trading Risk</p>
          <p className="text-4xl font-bold" style={{ color: scoreColor(bankLevel) }}>{bankScore}</p>
          <p className="text-xs text-text-muted mt-0.5">/ 100</p>
          <Badge text={bankLevel} color={scoreColor(bankLevel)} bg={scoreBg(bankLevel)} />
          {circularDetected && (
            <div className="mt-3 bg-danger-bg text-danger text-xs px-3 py-1.5 rounded-lg font-semibold">
              ⚠ Circular Trading Pattern Detected
            </div>
          )}
        </Card>
      </div>

      {/* MCA details grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <h3 className="text-sm font-semibold text-dark mb-4">MCA / Legal Intelligence</h3>
          <div className="space-y-2 text-sm">
            {[
              { label: 'Legal Risk Score', value: `${legalScore} / 100` },
              { label: 'DIN Disqualified Count', value: dinDisqualified },
              { label: 'NCLT Case', value: mca.nclt_case ? '⚠ YES' : '✓ None found' },
              { label: 'Summary', value: mca.summary || '—' },
            ].map(row => (
              <div key={row.label} className="flex justify-between py-1.5 border-b border-border last:border-0">
                <span className="text-text-muted text-xs">{row.label}</span>
                <span className="font-medium text-dark text-xs text-right max-w-[60%]">{String(row.value)}</span>
              </div>
            ))}
          </div>

          {riskFactors.length > 0 && (
            <div className="mt-3 pt-3 border-t border-border">
              <p className="text-xs font-semibold text-text-muted mb-2 uppercase tracking-wide">Risk Factors</p>
              <ul className="space-y-1">
                {riskFactors.slice(0, 6).map((f, i) => (
                  <li key={i} className="text-xs text-danger flex gap-1.5">
                    <span>⚠</span><span>{f}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {charges.length > 0 && (
            <div className="mt-3 pt-3 border-t border-border">
              <p className="text-xs font-semibold text-text-muted mb-2 uppercase tracking-wide">Charges / Liens</p>
              <div className="space-y-1">
                {charges.slice(0, 5).map((ch, i) => (
                  <div key={i} className="bg-surface-row rounded-lg px-3 py-2 flex justify-between text-xs">
                    <span className="text-dark font-medium">{ch.lender || ch.holder || 'Unknown'}</span>
                    <span className="text-text-muted">{ch.amount_cr ? `₹${ch.amount_cr} Cr` : ch.type || ''}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </Card>

        <Card>
          <h3 className="text-sm font-semibold text-dark mb-4">Bank Statement & GST Analysis</h3>
          <div className="space-y-2 text-sm">
            {[
              { label: 'Circular Trading Score', value: `${(circularScore * 100).toFixed(0)}%`, flag: circularDetected },
              { label: 'GSTR-2A vs 3B Risk', value: gstRisk, flag: gstRisk !== 'LOW' },
              { label: 'ITC Match %', value: `${itcMatch.toFixed(1)}%`, flag: itcMatch < 90 },
              { label: 'Revenue Divergence', value: `${revDiv.toFixed(1)}%`, flag: revDiv > 15 },
              { label: 'Cheque Bounce Count (12m)', value: bounceCount, flag: bounceCount > 2 },
            ].map(row => (
              <div key={row.label} className="flex justify-between py-1.5 border-b border-border last:border-0">
                <span className="text-text-muted text-xs">{row.label}</span>
                <span className={`font-medium text-xs ${row.flag ? 'text-danger font-bold' : 'text-dark'}`}>
                  {String(row.value)}
                </span>
              </div>
            ))}
          </div>

          {bankFlags.length > 0 && (
            <div className="mt-3 pt-3 border-t border-border">
              <p className="text-xs font-semibold text-text-muted mb-2 uppercase tracking-wide">Risk Flags</p>
              <ul className="space-y-1">
                {bankFlags.slice(0, 6).map((f, i) => (
                  <li key={i} className="text-xs text-danger flex gap-1.5">
                    <span>⚠</span><span>{f}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}
