import { motion } from 'framer-motion'
import { Shield, Target, DollarSign, Percent, TrendingUp, TrendingDown } from 'lucide-react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts'
import { useAnalysis } from '../App'
import { MetricCard, SignalCard, SectionHeader, Card } from '../components/ui'
import { g, fmt, pct } from '../lib/utils'

const container = { hidden: {}, show: { transition: { staggerChildren: 0.06 } } }
const item = { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0, transition: { duration: 0.4 } } }

export default function Overview() {
  const { analysis } = useAnalysis()
  const d = analysis?.data || {}
  const rec = g(d, 'recommendation') || {}
  const ml = g(d, 'ml_scores') || {}
  const fin = g(d, 'financial_data') || {}
  const traj = g(d, 'trajectory') || {}
  const company = d.company_name || 'Company'

  const now = new Date()
  const hour = now.getHours()
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening'

  const decision = rec.lending_decision || 'REVIEW'
  const ensemblePd = ml.ensemble_pd || 0
  const limit = rec.recommended_limit_cr
  const rate = rec.recommended_rate_pct
  const premium = ml.risk_premium

  // Signals
  const mScore = fin.beneish_m_score ?? -3
  const dscr = fin.dscr ?? 0
  const months = fin.months_to_dscr_danger ?? 120
  const breachProb = g(d, 'stress_test', 'covenant_breach_probability') ?? 0
  const dnaSim = g(d, 'dna_match', 'max_archetype_similarity') ?? 0
  const contagion = fin.contagion_risk_score ?? 0
  const satScore = fin.satellite_activity_score ?? 50
  const satCat = fin.satellite_activity_category || 'N/A'
  const deflection = g(d, 'ceo_interview', 'key_scores', 'ceo_deflection_score') ?? 0
  const mq = g(d, 'ceo_interview', 'management_quality_score') ?? 50

  const signals = [
    { name: 'Forensics: Beneish', detail: `M-Score ${fmt(mScore)} — ${parseFloat(mScore) > -2.22 ? 'SUSPICIOUS' : 'CLEAN'}`, level: parseFloat(mScore) > -2.22 ? 'RED' : 'GREEN' },
    { name: 'DSCR Trajectory', detail: `DSCR ${fmt(dscr)} | Danger in ${Math.round(months)}mo`, level: months < 18 ? 'RED' : months < 36 ? 'AMBER' : 'GREEN' },
    { name: 'ML Ensemble', detail: `PD ${pct(ensemblePd)} | Spread: ${fmt(ml.model_disagreement)}`, level: ensemblePd > 0.4 ? 'RED' : ensemblePd > 0.2 ? 'AMBER' : 'GREEN' },
    { name: 'Bull–Bear Debate', detail: `Decision: ${decision}`, level: decision.includes('APPROVE') && !decision.includes('REJECT') ? 'GREEN' : decision.includes('REJECT') ? 'RED' : 'AMBER' },
    { name: 'Default DNA Match', detail: `Similarity: ${fmt(dnaSim)} — ${g(d, 'dna_match', 'closest_default_archetype') || 'N/A'}`, level: dnaSim > 0.5 ? 'RED' : dnaSim > 0.3 ? 'AMBER' : 'GREEN' },
    { name: 'Network Contagion', detail: `Score: ${fmt(contagion)}`, level: contagion > 0.5 ? 'RED' : contagion > 0.25 ? 'AMBER' : 'GREEN' },
    { name: 'Satellite Verification', detail: `Score: ${fmt(satScore, 0)}/100 — ${satCat}`, level: satScore < 40 ? 'RED' : satScore < 65 ? 'AMBER' : 'GREEN' },
    { name: 'Monte Carlo Stress', detail: `Breach Prob: ${pct(breachProb)} | P10: ${fmt(g(d, 'stress_test', 'dscr_p10'))}`, level: breachProb > 0.3 ? 'RED' : breachProb > 0.1 ? 'AMBER' : 'GREEN' },
    { name: 'Web Research', detail: `Sentiment: ${fmt(g(d, 'research', 'research_sentiment_score'))} | ${g(d, 'research', 'industry_outlook') || 'N/A'}`, level: g(d, 'research', 'industry_outlook') === 'POSITIVE' ? 'GREEN' : 'AMBER' },
    { name: 'CEO Interview', detail: `MQ: ${fmt(mq, 0)}/100 | Deflection: ${fmt(deflection)}`, level: deflection > 0.4 ? 'RED' : deflection > 0.25 ? 'AMBER' : 'GREEN' },
  ]

  // DSCR chart data
  const dscrHistory = traj.dscr_history || []
  const fiscalYears = traj.fiscal_years || []
  const chartData = fiscalYears.map((yr, i) => ({ year: `FY${yr}`, dscr: dscrHistory[i] }))

  // Model gauges
  const models = [
    { name: 'XGBoost', pd: ml.xgb_pd || 0, color: '#E8470A' },
    { name: 'Random Forest', pd: ml.rf_pd || 0, color: '#3B82F6' },
    { name: 'LightGBM', pd: ml.lgb_pd || 0, color: '#6366F1' },
    { name: 'Ensemble', pd: ml.ensemble_pd || 0, color: '#1A1A1A' },
  ]

  return (
    <motion.div variants={container} initial="hidden" animate="show">
      {/* Greeting */}
      <motion.div variants={item} className="mb-3">
        <h1 className="font-[DM_Serif_Display] text-[24px] md:text-[32px] font-bold text-dark">
          {greeting}, Analyst
        </h1>
        <p className="text-[15px] text-text-muted mt-1">
          {company} analysis is ready · {now.toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })}
        </p>
      </motion.div>

      {/* Row 1 — 4 Metric Cards */}
      <motion.div variants={item} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
        <MetricCard label="Lending Decision" value={decision.replace('_', ' ')} subtitle={rec.final_rationale ? rec.final_rationale.slice(0, 60) + '...' : ''} variant="dark" icon={Shield} />
        <MetricCard label="PD Score" value={pct(ensemblePd)} subtitle={`Ensemble of 3 models`} variant="orange" icon={Target} />
        <MetricCard label="Credit Limit" value={limit != null ? `₹${fmt(limit)} Cr` : '—'} subtitle="Recommended exposure" icon={DollarSign} />
        <MetricCard label="Interest Rate" value={rate != null ? `${fmt(rate)}%` : '—'} subtitle={premium != null ? `Risk premium: ${fmt(premium)}%` : ''} icon={Percent} />
      </motion.div>

      {/* Row 2 — Signals */}
      <motion.div variants={item}>
        <SectionHeader title="Risk Signal Overview" subtitle="All AI-computed innovation signals" />
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-2.5">
          {signals.map(s => (
            <SignalCard key={s.name} name={s.name} detail={s.detail} level={s.level} />
          ))}
        </div>
      </motion.div>

      {/* Row 3 — Model Ensemble + DSCR Chart */}
      <motion.div variants={item}>
        <SectionHeader title="Model Consensus" subtitle="Individual PD estimates from ensemble members" />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Model bars */}
          <Card>
            <h3 className="text-sm font-semibold text-dark mb-4">PD Breakdown by Model</h3>
            <div className="space-y-4">
              {models.map(m => (
                <div key={m.name} className="flex items-center gap-3">
                  <span className={`text-[13px] w-28 ${m.name === 'Ensemble' ? 'font-bold' : ''} text-dark`}>{m.name}</span>
                  <div className="flex-1 h-2 bg-border rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-700"
                      style={{ width: `${Math.min(m.pd * 100, 100)}%`, background: m.color }}
                    />
                  </div>
                  <span className={`text-[13px] font-[DM_Mono] w-14 text-right ${m.name === 'Ensemble' ? 'font-bold' : ''}`}>
                    {pct(m.pd)}
                  </span>
                </div>
              ))}
            </div>
            {ml.model_disagreement_flag && (
              <div className="mt-4 bg-warning-bg border border-warning rounded-xl px-4 py-2 text-xs text-warning font-semibold">
                ⚠ High model disagreement detected
              </div>
            )}
          </Card>

          {/* DSCR Chart */}
          <Card>
            <h3 className="text-sm font-semibold text-dark mb-4">DSCR Trajectory</h3>
            {chartData.length > 1 ? (
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" vertical={false} />
                  <XAxis dataKey="year" tick={{ fill: '#9CA3AF', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: '#9CA3AF', fontSize: 11 }} axisLine={false} tickLine={false} domain={['auto', 'auto']} />
                  <Tooltip
                    contentStyle={{
                      background: '#1A1A1A', border: 'none', borderRadius: 8,
                      color: '#fff', fontSize: 12, padding: '8px 12px',
                    }}
                  />
                  <ReferenceLine y={1.25} stroke="#F59E0B" strokeDasharray="4 2" label={{ value: 'Covenant', fill: '#F59E0B', fontSize: 10 }} />
                  <ReferenceLine y={1.0} stroke="#EF4444" strokeDasharray="4 2" label={{ value: 'Danger', fill: '#EF4444', fontSize: 10 }} />
                  <Line type="monotone" dataKey="dscr" stroke="#E8470A" strokeWidth={2.5}
                        dot={{ fill: 'white', stroke: '#E8470A', strokeWidth: 2, r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-[200px] text-sm text-text-muted">
                Insufficient data for trajectory chart
              </div>
            )}
            <div className="flex justify-between mt-3 text-xs">
              <span className="bg-info-bg text-info px-2 py-0.5 rounded-full font-semibold">
                P50: {fmt(g(d, 'stress_test', 'dscr_p50'))}
              </span>
              <span className="bg-danger-bg text-danger px-2 py-0.5 rounded-full font-semibold">
                P10: {fmt(g(d, 'stress_test', 'dscr_p10'))}
              </span>
            </div>
          </Card>
        </div>
      </motion.div>
    </motion.div>
  )
}
