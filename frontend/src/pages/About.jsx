import { useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ChevronRight, Brain, BarChart2, Globe, FileText, Users, ArrowRight, Menu, X } from 'lucide-react'

const container = { hidden: {}, show: { transition: { staggerChildren: 0.09 } } }
const item = { hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: 'easeOut' } } }

const TEAM = [
  {
    id: 'P1',
    role: 'Person 1',
    focus: 'ML Core',
    color: 'from-orange to-orange-light',
    icon: Brain,
    modules: 'modules/person1_ml_core/',
    deliverables: [
      'Synthetic data generator — 30 companies, FY2009–2024',
      '146-feature engineering pipeline (velocity, Beneish, DNA)',
      '3-model ensemble credit scorer (XGBoost · RF · LightGBM)',
      'LSTM trajectory model + early warning system',
      'Beneish M-Score · Altman Z-Score · Piotroski F-Score forensics',
    ],
  },
  {
    id: 'P2',
    role: 'Person 2',
    focus: 'Alternative Data',
    color: 'from-blue-500 to-blue-400',
    icon: Globe,
    modules: 'modules/person2_alt_data/',
    deliverables: [
      'Promoter network contagion analysis via GNN',
      'Monte Carlo stress testing — 1,000 simulation paths',
      'Sentinel-2 satellite factory activity scoring',
      'GST filing vs bank revenue cross-check engine',
      'Default DNA fingerprinting — 6 historical archetypes',
    ],
  },
  {
    id: 'P3',
    role: 'Person 3',
    focus: 'LLM Agents + CAM',
    color: 'from-success to-green-400',
    icon: FileText,
    modules: 'modules/person3_llm_cam/ + api/ + frontend/',
    deliverables: [
      'Tavily-powered research agent (LangGraph)',
      'Adversarial Bull/Bear LLM agents with coordinator',
      'CEO interview — Whisper transcription + VADER sentiment',
      '11-section CAM DOCX generator',
      'FastAPI backend + React 19 dashboard',
    ],
  },
]

const INNOVATIONS = [
  'Beneish M-Score Forensics',
  'Altman Z-Score',
  'Piotroski F-Score',
  'XGBoost Ensemble',
  'Random Forest Ensemble',
  'LightGBM Ensemble',
  'LSTM Trajectory',
  'SHAP Explainability',
  'Promoter Network GNN',
  'Monte Carlo Stress Test',
  'Sentinel-2 Satellite',
  'GST Intelligence',
  'Default DNA Matching',
  'Tavily Research Agent',
  'Bull LLM Agent',
  'Bear LLM Agent',
  'CEO Interview NLP',
]

export default function About() {
  const [menuOpen, setMenuOpen] = useState(false)
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
            <span className="text-sm text-text-muted font-medium">About</span>
          </div>
          <div className="hidden sm:flex items-center gap-4">
            <Link to="/docs" className="text-sm text-text-secondary hover:text-dark transition-colors">Docs</Link>
            <Link to="/" className="px-4 py-2 rounded-full text-sm font-semibold bg-dark text-white hover:bg-orange transition-colors duration-200">
              Try It
            </Link>
          </div>
          <button
            className="sm:hidden p-2 rounded-lg hover:bg-surface-row transition-colors"
            onClick={() => setMenuOpen(v => !v)}
          >
            {menuOpen ? <X size={20} className="text-dark" /> : <Menu size={20} className="text-dark" />}
          </button>
        </div>
      </nav>
      {/* Mobile menu */}
      {menuOpen && (
        <div className="sm:hidden bg-white border-b border-border-divider px-4 py-3 space-y-1">
          <Link to="/docs" onClick={() => setMenuOpen(false)} className="block py-2 text-sm text-text-secondary hover:text-dark">Docs</Link>
          <Link to="/" onClick={() => setMenuOpen(false)} className="block py-2 text-sm font-semibold text-orange">Try It →</Link>
        </div>
      )}

      <div className="max-w-[1280px] mx-auto px-4 md:px-10 py-12 md:py-20">
        <motion.div variants={container} initial="hidden" animate="show" className="space-y-20">

          {/* Hero */}
          <motion.div variants={item} className="text-center max-w-3xl mx-auto">
            <span className="bg-orange-pale border border-orange-border text-orange text-xs font-semibold uppercase tracking-widest px-3.5 py-1.5 rounded-full inline-flex">
              About Yakṣarāja
            </span>
            <h1 className="font-[DM_Serif_Display] text-3xl sm:text-4xl md:text-5xl text-dark mt-6 leading-tight">
              Reimagining Credit<br />Decisions with AI
            </h1>
            <p className="text-lg text-text-secondary leading-relaxed mt-6">
              Yakṣarāja — named after the divine treasurer of Hindu mythology — is an AI-powered
              Credit Decisioning Engine that compresses weeks of manual credit analysis into
              minutes. It combines rigorous academic-grade ML with alternative data intelligence
              and adversarial LLM agents to eliminate bias and blind spots in lending decisions.
            </p>
          </motion.div>

          {/* Mission */}
          <motion.div variants={item}>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-10 items-center">
              <div>
                <h2 className="text-3xl font-semibold text-dark mb-5">The Problem We Solve</h2>
                <div className="space-y-4">
                  {[
                    { title: 'Weeks, Not Minutes', body: 'Traditional Credit Appraisal Memos take 2–4 weeks of analyst time. Yakṣarāja reduces this to under 5 minutes.' },
                    { title: 'Single-Model Bias', body: 'Most systems rely on one model — one narrative, one blind spot. We deploy adversarial Bull and Bear LLM agents to argue both sides before synthesising a recommendation.' },
                    { title: 'Missing Context', body: 'Traditional analysis misses satellite imagery of factory activity, promoter network contagion, and GST filing anomalies — all of which Yakṣarāja incorporates automatically.' },
                  ].map(p => (
                    <div key={p.title} className="flex gap-4">
                      <div className="w-1.5 rounded-full bg-gradient-to-b from-orange to-orange-light flex-shrink-0 mt-1" style={{ minHeight: 40 }} />
                      <div>
                        <p className="text-base font-semibold text-dark">{p.title}</p>
                        <p className="text-sm text-text-secondary leading-relaxed mt-1">{p.body}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                {[
                  { value: '17', label: 'AI Innovations' },
                  { value: '146', label: 'ML Features' },
                  { value: '0.9961', label: 'AUC Score' },
                  { value: '< 5 min', label: 'Full CAM Output' },
                  { value: '30', label: 'Synthetic Companies' },
                  { value: '1,000', label: 'Monte Carlo Paths' },
                ].map(s => (
                  <div key={s.label} className="bg-white rounded-2xl border border-border p-4 text-center shadow-[0_1px_4px_rgba(0,0,0,0.06)]">
                    <p className="font-[DM_Serif_Display] text-3xl md:text-4xl text-dark">{s.value}</p>
                    <p className="text-xs font-semibold uppercase tracking-wider text-text-muted mt-2">{s.label}</p>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>

          {/* 17 Innovations */}
          <motion.div variants={item}>
            <div className="text-center mb-10">
              <h2 className="text-3xl font-semibold text-dark">17 AI Innovations</h2>
              <p className="text-base text-text-muted mt-2">Each layer independently validated and ensemble-combined</p>
            </div>
            <div className="flex flex-wrap gap-3 justify-center">
              {INNOVATIONS.map((inn, i) => (
                <span key={inn} className="bg-white border border-border text-sm text-dark font-medium px-4 py-2 rounded-full shadow-[0_1px_4px_rgba(0,0,0,0.06)] hover:-translate-y-0.5 transition-transform duration-200">
                  <span className="text-orange font-[DM_Mono] text-xs mr-1.5">{String(i + 1).padStart(2, '0')}</span>
                  {inn}
                </span>
              ))}
            </div>
          </motion.div>

          {/* Team */}
          <motion.div variants={item}>
            <div className="text-center mb-10">
              <h2 className="text-3xl font-semibold text-dark">Team Structure</h2>
              <p className="text-base text-text-muted mt-2">Three engineers, one unified pipeline</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {TEAM.map(member => (
                <div key={member.id} className="bg-white rounded-3xl border border-border shadow-[0_1px_4px_rgba(0,0,0,0.06),0_2px_12px_rgba(0,0,0,0.06)] overflow-hidden">
                  <div className={`h-2 bg-gradient-to-r ${member.color}`} />
                  <div className="p-7">
                    <div className={`w-12 h-12 rounded-2xl bg-gradient-to-br ${member.color} flex items-center justify-center mb-4`}>
                      <member.icon size={22} className="text-white" />
                    </div>
                    <p className="text-xs font-semibold uppercase tracking-widest text-text-muted">{member.role}</p>
                    <h3 className="text-xl font-semibold text-dark mt-1 mb-1">{member.focus}</h3>
                    <code className="text-xs font-[DM_Mono] text-orange">{member.modules}</code>
                    <ul className="mt-5 space-y-2">
                      {member.deliverables.map(d => (
                        <li key={d} className="flex items-start gap-2 text-xs text-text-secondary leading-relaxed">
                          <span className="w-1 h-1 rounded-full bg-orange mt-1.5 flex-shrink-0" />
                          {d}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Tech Stack */}
          <motion.div variants={item}>
            <div className="text-center mb-10">
              <h2 className="text-3xl font-semibold text-dark">Technology Stack</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {[
                {
                  layer: 'ML & Data Science',
                  items: ['XGBoost · LightGBM · RandomForest', 'PyTorch LSTM', 'SHAP', 'NetworkX (GNN)', 'Pandas · NumPy · Scikit-learn'],
                },
                {
                  layer: 'Alternative Data',
                  items: ['Sentinel-2 Satellite API', 'MCA21 Director Data', 'GST API', 'Tavily Web Search', 'Monte Carlo (NumPy)'],
                },
                {
                  layer: 'LLM & Agents',
                  items: ['Google Gemini Flash', 'LangGraph (Agent Orchestration)', 'Whisper (Audio Transcription)', 'VADER (Sentiment Analysis)', 'python-docx (CAM Generation)'],
                },
                {
                  layer: 'Infrastructure',
                  items: ['FastAPI + Uvicorn', 'React 19 + Vite', 'Tailwind CSS', 'Framer Motion', 'Axios'],
                },
              ].map(cat => (
                <div key={cat.layer} className="bg-white rounded-2xl border border-border p-6 shadow-[0_1px_4px_rgba(0,0,0,0.06)]">
                  <h3 className="text-base font-semibold text-dark mb-4">{cat.layer}</h3>
                  <div className="flex flex-wrap gap-2">
                    {cat.items.map(t => (
                      <span key={t} className="text-xs bg-surface-row text-dark px-3 py-1.5 rounded-lg border border-border font-medium">
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </motion.div>

          {/* CTA */}
          <motion.div variants={item} className="text-center">
            <div className="bg-dark rounded-3xl p-12">
              <h2 className="font-[DM_Serif_Display] text-3xl md:text-4xl text-white mb-4">Ready to see it in action?</h2>
              <p className="text-base text-text-muted mb-8 max-w-lg mx-auto">
                Upload financial statements or load the Sunrise Textile Mills demo to experience the full AI pipeline.
              </p>
              <div className="flex items-center justify-center gap-4 flex-wrap">
                <Link to="/" className="inline-flex items-center gap-2 px-6 py-3 rounded-full text-sm font-semibold bg-gradient-to-br from-orange to-orange-light text-white shadow-[0_4px_16px_rgba(232,71,10,0.35)] hover:-translate-y-0.5 transition-transform duration-200">
                  Try Yakṣarāja <ArrowRight size={15} />
                </Link>
                <Link to="/docs" className="inline-flex items-center gap-2 px-6 py-3 rounded-full text-sm font-semibold border border-white/20 text-white hover:bg-white/10 transition-colors">
                  Read the Docs
                </Link>
              </div>
            </div>
          </motion.div>

        </motion.div>
      </div>

      {/* Footer */}
      <footer className="bg-dark border-t border-white/10 py-12">
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
            <Link to="/about" className="text-sm text-orange font-semibold hover:text-white transition-colors">About</Link>
          </div>
          <div className="mt-8 pt-6 border-t border-white/10 text-xs text-text-muted">
            © 2025 Yakṣarāja · Vivriti Capital AI Hackathon
          </div>
        </div>
      </footer>
    </div>
  )
}
