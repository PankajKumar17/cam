import { motion } from 'framer-motion'
import { Download, CheckCircle, FileText, Database } from 'lucide-react'
import { useAnalysis } from '../App'
import { Card, SectionHeader, DataTable, Badge } from '../components/ui'
import { g, fmt, pct, DECISION_COLORS } from '../lib/utils'
import { camDownloadUrl } from '../api'

export default function Reports() {
  const { analysis } = useAnalysis()
  const d = analysis?.data || {}
  const rec = g(d, 'recommendation') || {}
  const ml = g(d, 'ml_scores') || {}
  const fin = g(d, 'financial_data') || {}
  const ceo = g(d, 'ceo_interview') || {}
  const company = d.company_name || 'Company'

  const decision = rec.lending_decision || 'REVIEW'
  const dc = DECISION_COLORS[decision] || '#9CA3AF'
  const limit = rec.recommended_limit_cr
  const rate = rec.recommended_rate_pct
  const conditions = rec.key_conditions || []

  function downloadJSON() {
    const blob = new Blob([JSON.stringify(d, null, 2)], { type: 'application/json' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `${company.replace(/\s+/g, '_')}_analysis.json`
    a.click()
    URL.revokeObjectURL(a.href)
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      {/* Decision Banner */}
      <div className="bg-white border border-border rounded-2xl p-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-6 mb-6 shadow-sm">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[1.5px] text-orange mb-3">Final Lending Decision</p>
          <p className="text-4xl font-bold" style={{ color: dc }}>
            {decision.replace('_', ' ')}
          </p>
          <p className="text-base text-text-secondary mt-2">
            ₹{fmt(limit)} Cr at {fmt(rate)}% with {conditions.length} conditions
          </p>
        </div>
        <div className="flex flex-col gap-3">
          {analysis?.id && d.cam_path && (
            <a
              href={camDownloadUrl(analysis.id)}
              className="flex items-center justify-center gap-2 w-full sm:w-52 h-11 rounded-xl
                         bg-gradient-to-br from-orange to-orange-light text-white font-semibold text-sm
                         shadow-[0_4px_16px_rgba(232,71,10,0.30)] hover:shadow-[0_8px_32px_rgba(232,71,10,0.40)]
                         transition-all duration-150"
            >
              <Download size={16} /> Download CAM
            </a>
          )}
          <button
            onClick={downloadJSON}
            className="flex items-center justify-center gap-2 w-full sm:w-52 h-11 rounded-xl
                       bg-transparent text-dark border border-border font-semibold text-sm
                       hover:bg-surface-page transition-all duration-150"
          >
            <Database size={16} /> Raw Data (JSON)
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Lending Conditions */}
        <Card>
          <h3 className="text-sm font-semibold text-dark mb-4">Lending Conditions</h3>
          {conditions.length > 0 ? (
            <div className="space-y-3">
              {conditions.map((c, i) => (
                <div key={i} className="flex items-start gap-3 bg-orange/5 border-l-[3px] border-orange rounded-r-xl pl-3 pr-3 py-2.5">
                  <CheckCircle size={16} className="text-orange mt-0.5 flex-shrink-0" />
                  <span className="text-sm text-dark">{c}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-success italic">No conditions — clean approval</p>
          )}
        </Card>

        {/* Score Summary */}
        <Card>
          <h3 className="text-sm font-semibold text-dark mb-4">Score Summary</h3>
          <DataTable
            headers={['Metric', 'Value']}
            rows={[
              ['Ensemble PD', pct(ml.ensemble_pd)],
              ['DSCR', fmt(fin.dscr)],
              ['Beneish M-Score', fmt(fin.beneish_m_score)],
              ['Altman Z-Score', fmt(fin.altman_z_score)],
              ['Piotroski F-Score', String(fin.piotroski_f_score ?? '—')],
              ['D/E Ratio', fmt(fin.debt_to_equity)],
              ['Interest Coverage', fmt(fin.interest_coverage)],
              ['Management Quality', fmt(g(ceo, 'management_quality_score'), 0) + '/100'],
              ['Satellite Score', fmt(fin.satellite_activity_score, 0) + '/100'],
              ['Research Sentiment', fmt(g(d, 'research', 'research_sentiment_score'))],
            ]}
          />
        </Card>
      </div>

      {/* Bull / Bear Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-4">
        <Card>
          <h3 className="text-sm font-semibold text-success mb-2">Bull Summary</h3>
          <p className="text-sm text-text-secondary leading-relaxed">{rec.bull_summary || '—'}</p>
        </Card>
        <Card>
          <h3 className="text-sm font-semibold text-danger mb-2">Bear Summary</h3>
          <p className="text-sm text-text-secondary leading-relaxed">{rec.bear_summary || '—'}</p>
        </Card>
      </div>

      {/* Final Rationale */}
      {rec.final_rationale && (
        <Card className="mt-4">
          <h3 className="text-sm font-semibold text-dark mb-2">Final Rationale</h3>
          <p className="text-sm text-text-secondary leading-relaxed">{rec.final_rationale}</p>
        </Card>
      )}
    </motion.div>
  )
}
