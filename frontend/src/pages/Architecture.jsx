import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ChevronRight, ArrowRight } from 'lucide-react'

const container = { hidden: {}, show: { transition: { staggerChildren: 0.08 } } }
const item = { hidden: { opacity: 0, y: 16 }, show: { opacity: 1, y: 0, transition: { duration: 0.38, ease: 'easeOut' } } }

const LAYERS = [
  { id: 'L01', name: 'Excel Parser', owner: 'P1', color: 'bg-orange', desc: 'Screener.in Excel → structured financial dictionary', file: 'pipeline/excel_parser.py' },
  { id: 'L02', name: 'Feature Engineering', owner: 'P1', color: 'bg-orange', desc: '146 features: velocity, Beneish, Z-Score, F-Score, DNA ratios', file: 'modules/person1_ml_core/feature_engineering.py' },
  { id: 'L03', name: 'ML Ensemble Scorer', owner: 'P1', color: 'bg-orange', desc: 'XGBoost + Random Forest + LightGBM → PD score, credit band, SHAP', file: 'modules/person1_ml_core/credit_scorer.py' },
  { id: 'L04', name: 'LSTM Trajectory', owner: 'P1', color: 'bg-orange', desc: 'Multi-year DSCR trajectory modelling + early warning system', file: 'modules/person1_ml_core/temporal_model.py' },
  { id: 'L05', name: 'Promoter Network Graph', owner: 'P2', color: 'bg-blue-500', desc: 'MCA21 director interlock mapping + contagion risk scoring via GNN', file: 'modules/person2_alt_data/network_graph.py' },
  { id: 'L06', name: 'Satellite + GST Intel', owner: 'P2', color: 'bg-blue-500', desc: 'Sentinel-2 factory activity scoring + GST vs bank revenue cross-check', file: 'modules/person2_alt_data/' },
  { id: 'L07', name: 'Monte Carlo Stress Test', owner: 'P2', color: 'bg-blue-500', desc: '1,000-path simulation with named macro scenarios', file: 'modules/person2_alt_data/stress_test.py' },
  { id: 'L08', name: 'Research Agent', owner: 'P3', color: 'bg-success', desc: 'LangGraph + Tavily web research for live industry outlook', file: 'modules/person3_llm_cam/research_agent.py' },
  { id: 'L09', name: 'Adversarial LLM Agents', owner: 'P3', color: 'bg-success', desc: 'Bull + Bear agents debate → coordinator synthesises final recommendation', file: 'modules/person3_llm_cam/' },
  { id: 'L10', name: 'CAM Generator', owner: 'P3', color: 'bg-success', desc: '11-section DOCX Credit Appraisal Memo output', file: 'modules/person3_llm_cam/cam_generator.py' },
]

const OWNER_COLORS = {
  P1: 'bg-orange-pale border-orange-border text-orange',
  P2: 'bg-blue-50 border-blue-200 text-blue-700',
  P3: 'bg-success-bg border-success text-success',
}

export default function Architecture() {
  return (
    <div className="min-h-screen bg-surface-page">
      {/* Navbar */}
      <nav className="h-16 bg-white/90 backdrop-blur-md border-b border-border-divider sticky top-0 z-50">
        <div className="max-w-[1280px] mx-auto px-4 md:px-10 h-full flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link to="/" className="flex items-center gap-3">
              <img src="/logo.jpeg" alt="Yakṣarāja" className="w-9 h-9 rounded-full object-cover shadow-[0_4px_16px_rgba(232,71,10,0.30)]" />
              <span className="font-semibold text-lg text-dark">Yakṣarāja</span>
            </Link>
            <ChevronRight size={14} className="text-text-muted" />
            <span className="text-sm text-text-muted font-medium">Architecture</span>
          </div>
          <div className="flex items-center gap-6">
            <Link to="/docs" className="text-sm text-text-secondary hover:text-dark transition-colors">Docs</Link>
            <Link to="/about" className="text-sm text-text-secondary hover:text-dark transition-colors">About</Link>
            <Link to="/" className="px-4 py-2 rounded-full text-sm font-semibold bg-dark text-white hover:bg-orange transition-colors duration-200">
              Try It
            </Link>
          </div>
        </div>
      </nav>

      <div className="max-w-[1280px] mx-auto px-4 md:px-10 py-10 md:py-16">
        <motion.div variants={container} initial="hidden" animate="show" className="space-y-16">

          {/* Header */}
          <motion.div variants={item} className="text-center max-w-3xl mx-auto">
            <span className="bg-orange-pale border border-orange-border text-orange text-xs font-semibold uppercase tracking-widest px-3.5 py-1.5 rounded-full inline-flex mb-5">
              System Architecture
            </span>
            <h1 className="font-[DM_Serif_Display] text-3xl sm:text-4xl md:text-5xl text-dark leading-tight">
              How Yakṣarāja Works
            </h1>
            <p className="text-lg text-text-secondary leading-relaxed mt-5">
              A 10-layer AI pipeline connecting raw financial statements to a complete
              Credit Appraisal Memo — orchestrated by a single pipeline call.
            </p>
          </motion.div>

          {/* High-Level Diagram */}
          <motion.div variants={item}>
            <div className="bg-dark rounded-3xl p-10 font-[DM_Mono] text-sm overflow-x-auto">
              <p className="text-orange font-bold text-base mb-6 text-center tracking-wide">YAKṢARĀJA ENGINE</p>
              <div className="flex flex-col items-center gap-0">
                {/* Input */}
                <div className="bg-white/10 border border-white/20 rounded-xl px-8 py-3 text-white text-center">
                  <p className="text-xs text-text-muted mb-1">INPUT</p>
                  <p className="font-semibold">Financial Statements (XLSX / CSV)</p>
                  <p className="text-xs text-text-muted mt-0.5">+ Optional: CEO Audio / Transcript</p>
                </div>
                <div className="flex flex-col items-center gap-0.5 my-3">
                  <div className="w-px h-6 bg-white/30" />
                  <div className="w-2 h-2 rotate-45 border-b-2 border-r-2 border-white/40 -mt-1" />
                </div>

                {/* Three Persons in parallel */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 w-full max-w-2xl">
                  {[
                    { label: 'PERSON 1 — ML CORE', color: 'border-orange text-orange', items: ['Data Gen', 'Feature Eng', 'Credit Scorer', 'LSTM Traj', 'Forensics'] },
                    { label: 'PERSON 2 — ALT DATA', color: 'border-blue-400 text-blue-400', items: ['Network Graph', 'Stress Test', 'Satellite', 'GST Intel', 'DNA Match'] },
                    { label: 'PERSON 3 — LLM + CAM', color: 'border-green-400 text-green-400', items: ['Research Agt', 'Bull Agent', 'Bear Agent', 'CEO Interview', 'CAM Gen'] },
                  ].map(col => (
                    <div key={col.label} className={`border ${col.color} rounded-xl p-4`}>
                      <p className={`text-[10px] font-bold uppercase tracking-wider ${col.color} mb-3`}>{col.label}</p>
                      {col.items.map(i => (
                        <p key={i} className="text-xs text-white/70 py-0.5">{i}</p>
                      ))}
                    </div>
                  ))}
                </div>

                <div className="flex flex-col items-center gap-0.5 my-3">
                  <div className="w-px h-6 bg-white/30" />
                  <div className="w-2 h-2 rotate-45 border-b-2 border-r-2 border-white/40 -mt-1" />
                </div>

                {/* Pipeline */}
                <div className="bg-white/10 border border-white/20 rounded-xl px-8 py-3 text-white text-center">
                  <p className="text-xs text-text-muted mb-1">INTEGRATION</p>
                  <p className="font-semibold">pipeline/main_pipeline.py</p>
                  <p className="text-xs text-text-muted mt-0.5">10-Layer Engine</p>
                </div>

                <div className="flex flex-col items-center gap-0.5 my-3">
                  <div className="w-px h-6 bg-white/30" />
                  <div className="w-2 h-2 rotate-45 border-b-2 border-r-2 border-white/40 -mt-1" />
                </div>

                {/* API */}
                <div className="bg-orange/20 border border-orange/40 rounded-xl px-8 py-3 text-white text-center">
                  <p className="text-xs text-orange mb-1">API LAYER</p>
                  <p className="font-semibold">api/server.py (FastAPI)</p>
                </div>

                <div className="flex flex-col items-center gap-0.5 my-3">
                  <div className="w-px h-6 bg-white/30" />
                  <div className="w-2 h-2 rotate-45 border-b-2 border-r-2 border-white/40 -mt-1" />
                </div>

                {/* Frontend */}
                <div className="bg-white/10 border border-white/20 rounded-xl px-8 py-3 text-white text-center">
                  <p className="text-xs text-text-muted mb-1">FRONTEND</p>
                  <p className="font-semibold">frontend/ (Vite + React 19)</p>
                  <p className="text-xs text-text-muted mt-0.5">Landing · Dashboard · DeepDive · Reports</p>
                </div>
              </div>
            </div>
          </motion.div>

          {/* 10-Layer Pipeline */}
          <motion.div variants={item}>
            <h2 className="text-2xl font-semibold text-dark mb-6">10-Layer Pipeline</h2>
            <div className="relative">
              {/* Vertical connector */}
              <div className="absolute left-[27px] top-8 bottom-8 w-px bg-gradient-to-b from-orange via-blue-400 to-success opacity-30" />
              <div className="space-y-3">
                {LAYERS.map((layer, i) => (
                  <motion.div
                    key={layer.id}
                    initial={{ opacity: 0, x: -16 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.3, delay: i * 0.05 }}
                    className="relative flex gap-4 items-start"
                  >
                    {/* Layer dot */}
                    <div className={`w-7 h-7 rounded-full ${layer.color} flex items-center justify-center flex-shrink-0 z-10 mt-3`}>
                      <span className="text-[9px] font-bold text-white">{layer.id.replace('L0', '').replace('L', '')}</span>
                    </div>
                    {/* Card */}
                    <div className="flex-1 bg-white rounded-2xl border border-border shadow-[0_1px_4px_rgba(0,0,0,0.06)] p-4 hover:shadow-[0_4px_12px_rgba(0,0,0,0.10)] hover:-translate-y-0.5 transition-all duration-200">
                      <div className="flex items-center gap-3 flex-wrap">
                        <span className="text-xs font-bold text-text-muted font-[DM_Mono]">{layer.id}</span>
                        <span className="text-base font-semibold text-dark">{layer.name}</span>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${OWNER_COLORS[layer.owner]}`}>
                          {layer.owner}
                        </span>
                        <code className="text-[10px] font-[DM_Mono] text-text-muted ml-auto">{layer.file}</code>
                      </div>
                      <p className="text-sm text-text-secondary mt-1.5 leading-relaxed">{layer.desc}</p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>

          {/* Data Flow */}
          <motion.div variants={item}>
            <h2 className="text-2xl font-semibold text-dark mb-6">Data Flow</h2>
            <div className="flex flex-col sm:flex-row flex-wrap items-center gap-2">
              {[
                { label: 'XLSX / CSV', sub: 'Financial statements' },
                { label: 'Features', sub: '146 engineered' },
                { label: 'Scores', sub: 'PD + credit band' },
                { label: 'Alt Data', sub: 'Network · Satellite · GST' },
                { label: 'CAM DOCX', sub: '11-section memo' },
              ].map((step, i) => (
                <div key={step.label} className="flex sm:flex-row flex-col items-center gap-2">
                  <div className="bg-white rounded-xl border border-border p-4 text-center shadow-[0_1px_4px_rgba(0,0,0,0.06)] w-36">
                    <p className="text-sm font-bold text-dark">{step.label}</p>
                    <p className="text-xs text-text-muted mt-1">{step.sub}</p>
                  </div>
                  {i < 4 && <ArrowRight size={16} className="text-text-muted flex-shrink-0 rotate-90 sm:rotate-0" />}
                </div>
              ))}
            </div>
          </motion.div>

          {/* Storage */}
          <motion.div variants={item}>
            <h2 className="text-2xl font-semibold text-dark mb-6">Storage & Artefacts</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {[
                {
                  title: 'Pipeline Outputs',
                  path: 'data/processed/',
                  items: ['CAM_<company>_<date>.docx', 'scores_<company>.json', 'network_graph_<company>.html', 'stress_charts/'],
                },
                {
                  title: 'Pre-trained Models',
                  path: 'models/',
                  items: ['lstm_trajectory_model.pt', 'xgb_model.pkl', 'lgb_model.pkl', 'rf_model.pkl', 'scaler.pkl'],
                },
                {
                  title: 'Synthetic Dataset',
                  path: 'data/synthetic/',
                  items: ['intelli_credit_dataset.csv (352 × 149)', 'demo_sunrise_textile.csv', 'schema.json'],
                },
                {
                  title: 'Raw Inputs',
                  path: 'data/raw/',
                  items: ['Uploaded XLSX / XLS / CSV files', 'Runtime only — not committed'],
                },
              ].map(s => (
                <div key={s.title} className="bg-white rounded-2xl border border-border p-5 shadow-[0_1px_4px_rgba(0,0,0,0.06)]">
                  <p className="text-xs font-semibold uppercase tracking-widest text-text-muted mb-1">{s.title}</p>
                  <code className="text-sm font-[DM_Mono] text-orange font-semibold">{s.path}</code>
                  <ul className="mt-4 space-y-1.5">
                    {s.items.map(it => (
                      <li key={it} className="flex items-start gap-2 text-xs text-text-secondary">
                        <span className="w-1 h-1 rounded-full bg-border mt-1.5 flex-shrink-0" />
                        <code className="font-[DM_Mono]">{it}</code>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </motion.div>

          {/* CTA */}
          <motion.div variants={item} className="text-center">
            <div className="flex items-center justify-center gap-4 flex-wrap">
              <Link to="/docs" className="inline-flex items-center gap-2 px-6 py-3 rounded-full text-sm font-semibold bg-dark text-white hover:bg-orange transition-colors">
                Read the Docs
              </Link>
              <Link to="/" className="inline-flex items-center gap-2 px-6 py-3 rounded-full text-sm font-semibold border border-border-strong text-dark hover:border-orange hover:text-orange transition-colors">
                Try the Engine <ArrowRight size={14} />
              </Link>
            </div>
          </motion.div>

        </motion.div>
      </div>

      {/* Footer */}
      <footer className="bg-dark py-12 mt-8">
        <div className="max-w-[1280px] mx-auto px-4 md:px-10">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-orange to-orange-light flex items-center justify-center text-white font-bold text-sm">YR</div>
            <div>
              <span className="font-semibold text-white">Yakṣarāja</span>
              <p className="text-sm text-text-muted mt-0.5">AI-Powered Credit Decisioning Engine</p>
            </div>
          </div>
          <div className="flex gap-6 mt-8">
            <Link to="/docs" className="text-sm text-text-muted hover:text-white transition-colors">Documentation</Link>
            <Link to="/architecture" className="text-sm text-orange font-semibold hover:text-white transition-colors">Architecture</Link>
            <Link to="/about" className="text-sm text-text-muted hover:text-white transition-colors">About</Link>
          </div>
          <div className="mt-8 pt-6 border-t border-white/10 text-xs text-text-muted">
            © 2025 Yakṣarāja · Vivriti Capital AI Hackathon
          </div>
        </div>
      </footer>
    </div>
  )
}
