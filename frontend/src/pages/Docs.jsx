import { useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { BookOpen, Terminal, Upload, Server, Code2, FlaskConical, ChevronRight, FileText, ExternalLink, Copy, Check, Menu, X } from 'lucide-react'

const NAV_SECTIONS = [
  { id: 'overview', label: 'Overview' },
  { id: 'quickstart', label: 'Quick Start' },
  { id: 'api-reference', label: 'API Reference' },
  { id: 'modules', label: 'Modules' },
  { id: 'pipeline', label: 'Pipeline' },
  { id: 'configuration', label: 'Configuration' },
]

const CODE_BLOCK = ({ children, language = 'bash' }) => {
  const [copied, setCopied] = useState(false)
  function copy() {
    navigator.clipboard.writeText(children).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }
  return (
    <div className="relative group">
      <pre className="bg-[#1a1a2e] text-[#e2e8f0] text-xs font-[DM_Mono] rounded-xl p-5 overflow-x-auto border border-white/10 leading-relaxed">
        <code>{children}</code>
      </pre>
      <button
        onClick={copy}
        className="absolute top-3 right-3 flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg
                   bg-white/10 hover:bg-white/20 text-[#e2e8f0] text-[11px] font-medium
                   opacity-0 group-hover:opacity-100 transition-all duration-150"
      >
        {copied ? <><Check size={11} /> Copied</> : <><Copy size={11} /> Copy</>}
      </button>
    </div>
  )
}

const Section = ({ id, title, icon: Icon, children }) => (
  <section id={id} className="scroll-mt-24 mb-16">
    <div className="flex items-center gap-3 mb-6">
      <div className="w-9 h-9 rounded-xl bg-orange-pale flex items-center justify-center">
        <Icon size={18} className="text-orange" />
      </div>
      <h2 className="text-2xl font-semibold text-dark">{title}</h2>
    </div>
    {children}
  </section>
)

const Badge = ({ children, color = 'orange' }) => {
  const colors = {
    orange: 'bg-orange-pale border-orange-border text-orange',
    green: 'bg-success-bg border-success text-success',
    blue: 'bg-blue-50 border-blue-200 text-blue-700',
    gray: 'bg-surface-row border-border text-text-muted',
  }
  return (
    <span className={`inline-block text-xs font-semibold px-2.5 py-0.5 rounded-full border ${colors[color]}`}>
      {children}
    </span>
  )
}

const EndpointCard = ({ method, path, description, body }) => {
  const methodColors = {
    GET: 'bg-success-bg text-success border-success',
    POST: 'bg-blue-50 text-blue-700 border-blue-200',
    DELETE: 'bg-danger-bg text-danger border-danger',
  }
  return (
    <div className="bg-white rounded-2xl border border-border shadow-[0_1px_4px_rgba(0,0,0,0.06)] p-5 mb-4">
      <div className="flex items-center gap-3 mb-3">
        <span className={`text-xs font-bold px-2.5 py-1 rounded-lg border font-[DM_Mono] ${methodColors[method] || methodColors.GET}`}>
          {method}
        </span>
        <code className="text-sm font-[DM_Mono] text-dark">{path}</code>
      </div>
      <p className="text-sm text-text-secondary">{description}</p>
      {body && <div className="mt-3"><CODE_BLOCK language="json">{body}</CODE_BLOCK></div>}
    </div>
  )
}

export default function Docs() {
  const [activeSection, setActiveSection] = useState('overview')
  const [menuOpen, setMenuOpen] = useState(false)

  function scrollTo(id) {
    setActiveSection(id)
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  return (
    <div className="min-h-screen bg-surface-page">
      {/* Top Navbar */}
      <nav className="h-16 bg-white/90 backdrop-blur-md border-b border-border-divider sticky top-0 z-50">
        <div className="max-w-[1280px] mx-auto px-4 md:px-10 h-full flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link to="/" className="flex items-center gap-3">
              <img src="/logo.jpeg" alt="Yakṣarāja" className="w-9 h-9 rounded-full object-cover shadow-[0_4px_16px_rgba(232,71,10,0.30)]" />
              <span className="font-semibold text-lg text-dark">Yakṣarāja</span>
            </Link>
            <ChevronRight size={14} className="text-text-muted" />
            <span className="text-sm text-text-muted font-medium">Documentation</span>
          </div>
          <div className="hidden sm:flex items-center gap-4">
            <Link to="/about" className="text-sm text-text-secondary hover:text-dark transition-colors">About</Link>
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
        <div className="sm:hidden bg-white border-b border-border-divider px-4 py-3 space-y-1 sticky top-16 z-40">
          <Link to="/about" onClick={() => setMenuOpen(false)} className="block py-2 text-sm text-text-secondary hover:text-dark">About</Link>
          <Link to="/" onClick={() => setMenuOpen(false)} className="block py-2 text-sm font-semibold text-orange">Try It →</Link>
        </div>
      )}

      <div className="max-w-[1280px] mx-auto px-4 md:px-10 py-12 flex gap-10">
        {/* Sidebar */}
        <aside className="hidden lg:block w-56 flex-shrink-0">
          <div className="sticky top-28">
            <p className="text-xs font-semibold uppercase tracking-widest text-text-muted mb-4">Contents</p>
            <nav className="space-y-1">
              {NAV_SECTIONS.map(s => (
                <button
                  key={s.id}
                  onClick={() => scrollTo(s.id)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-all duration-150 ${
                    activeSection === s.id
                      ? 'bg-orange-pale text-orange font-semibold'
                      : 'text-text-secondary hover:text-dark hover:bg-surface-row'
                  }`}
                >
                  {s.label}
                </button>
              ))}
            </nav>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 min-w-0">
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
            {/* Hero */}
            <div className="bg-white rounded-3xl border border-border shadow-[0_1px_4px_rgba(0,0,0,0.06),0_2px_12px_rgba(0,0,0,0.06)] p-10 mb-12">
              <div className="flex items-center gap-2 mb-4">
                <Badge>Documentation</Badge>
                <Badge color="green">v1.0</Badge>
              </div>
              <h1 className="font-[DM_Serif_Display] text-3xl md:text-4xl text-dark mb-3">
                Yakṣarāja Developer Guide
              </h1>
              <p className="text-base text-text-secondary leading-relaxed max-w-2xl">
                Complete reference for the Yakṣarāja AI-Powered Credit Decisioning Engine.
                Learn how to set up the environment, run the pipeline, call the API, and
                integrate the 17 AI innovations into your workflow.
              </p>
              <div className="flex gap-3 mt-6 flex-wrap">
                <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer"
                   className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold bg-dark text-white hover:bg-orange transition-colors">
                  <ExternalLink size={14} />
                  Live API Docs
                </a>

              </div>
            </div>

            {/* Overview */}
            <Section id="overview" title="Overview" icon={BookOpen}>
              <p className="text-sm text-text-secondary leading-relaxed mb-4">
                Yakṣarāja automates end-to-end preparation of Comprehensive Credit Appraisal Memos (CAMs)
                using <strong className="text-dark">17 innovations</strong> in ML, alternative data, and adversarial LLM agents —
                from raw financials to a print-ready DOCX in one pipeline call.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
                {[
                  { title: 'Person 1 — ML Core', desc: 'Synthetic data generator (30 companies, 146+ features), 3-model ensemble credit scorer, LSTM trajectory model, Beneish/Altman/Piotroski forensics.', badge: 'ML Core' },
                  { title: 'Person 2 — Alt Data', desc: 'Promoter network contagion (GNN), Monte Carlo stress test (1,000 sims), Sentinel-2 satellite scoring, GST truth layer, Default DNA fingerprinting.', badge: 'Alt Data' },
                  { title: 'Person 3 — LLM + CAM', desc: 'Tavily research agent, adversarial Bull/Bear LLM agents (LangGraph), CEO interview (Whisper + VADER), 11-section CAM DOCX generator.', badge: 'LLM + CAM' },
                ].map(card => (
                  <div key={card.title} className="bg-white rounded-2xl border border-border p-5 shadow-[0_1px_4px_rgba(0,0,0,0.06)]">
                    <Badge>{card.badge}</Badge>
                    <h3 className="text-sm font-semibold text-dark mt-3 mb-2">{card.title}</h3>
                    <p className="text-xs text-text-secondary leading-relaxed">{card.desc}</p>
                  </div>
                ))}
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
                {[
                  { value: '17', label: 'AI Innovations' },
                  { value: '146', label: 'ML Features' },
                  { value: '0.9961', label: 'AUC Score' },
                  { value: '< 5 min', label: 'Full CAM' },
                ].map(s => (
                  <div key={s.label} className="bg-orange-pale rounded-xl border border-orange-border p-4 text-center">
                    <p className="font-[DM_Serif_Display] text-3xl text-dark">{s.value}</p>
                    <p className="text-xs font-semibold uppercase tracking-wider text-text-muted mt-1">{s.label}</p>
                  </div>
                ))}
              </div>
            </Section>

            {/* Quick Start */}
            <Section id="quickstart" title="Quick Start" icon={Terminal}>
              <div className="space-y-6">
                <div>
                  <h3 className="text-base font-semibold text-dark mb-2 flex items-center gap-2">
                    <span className="w-6 h-6 rounded-full bg-dark text-white text-xs flex items-center justify-center font-bold">1</span>
                    Clone & Setup Python Environment
                  </h3>
                  <CODE_BLOCK>{`git clone https://github.com/PankajKumar17/yaksaraja.git
cd yaksaraja

# Create and activate virtual environment
python -m venv .venv
.venv\\Scripts\\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Copy env template and add API keys
cp .env.example .env`}</CODE_BLOCK>
                </div>

                <div>
                  <h3 className="text-base font-semibold text-dark mb-2 flex items-center gap-2">
                    <span className="w-6 h-6 rounded-full bg-dark text-white text-xs flex items-center justify-center font-bold">2</span>
                    Start the FastAPI Backend
                  </h3>
                  <CODE_BLOCK>{`uvicorn api.server:app --reload --port 8000
# API docs available at http://localhost:8000/docs`}</CODE_BLOCK>
                </div>

                <div>
                  <h3 className="text-base font-semibold text-dark mb-2 flex items-center gap-2">
                    <span className="w-6 h-6 rounded-full bg-dark text-white text-xs flex items-center justify-center font-bold">3</span>
                    Start the React Frontend
                  </h3>
                  <CODE_BLOCK>{`cd frontend
npm install
npm run dev
# UI available at http://localhost:5173`}</CODE_BLOCK>
                </div>

                <div>
                  <h3 className="text-base font-semibold text-dark mb-2 flex items-center gap-2">
                    <span className="w-6 h-6 rounded-full bg-dark text-white text-xs flex items-center justify-center font-bold">4</span>
                    Run the Pipeline (CLI)
                  </h3>
                  <CODE_BLOCK>{`# Generate synthetic training dataset
python modules/person1_ml_core/data_generator.py

# Run full end-to-end pipeline on a company
python pipeline/main_pipeline.py
# Output → data/processed/CAM_<company>_<date>.docx
# Output → data/processed/scores_<company>.json`}</CODE_BLOCK>
                </div>

                <div className="bg-surface-row rounded-xl border border-border p-4">
                  <p className="text-xs font-semibold text-dark mb-1">Required API Keys</p>
                  <p className="text-xs text-text-secondary mb-3">Add these to your <code className="font-[DM_Mono] bg-white px-1 rounded border border-border">.env</code> file:</p>
                  <CODE_BLOCK>{`GOOGLE_API_KEY=your_gemini_api_key
TAVILY_API_KEY=your_tavily_key

# Optional — falls back to synthetic score if absent
SENTINEL_CLIENT_ID=sh-xxxx-xxxx-xxxx
SENTINEL_CLIENT_SECRET=your_sentinel_secret`}</CODE_BLOCK>
                </div>
              </div>
            </Section>

            {/* API Reference */}
            <Section id="api-reference" title="API Reference" icon={Server}>
              <p className="text-sm text-text-secondary leading-relaxed mb-6">
                The FastAPI backend exposes the following endpoints at <code className="font-[DM_Mono] text-orange">http://localhost:8000</code>.
                Full interactive docs are available at <code className="font-[DM_Mono] text-orange">/docs</code>.
              </p>

              <EndpointCard
                method="GET"
                path="/health"
                description="Health check endpoint. Returns service status and version."
              />
              <EndpointCard
                method="POST"
                path="/analyse"
                description="Run the full AI pipeline on a company. Accepts company name and financial statement file (XLSX/CSV). Returns analysis ID and full credit decisioning data."
                body={`{
  "company_name": "Sunrise Textile Mills",
  "file": "<multipart/form-data>",
  "ceo_transcript": "optional transcript text"
}`}
              />
              <EndpointCard
                method="GET"
                path="/demo"
                description="Load the pre-computed demo analysis for Sunrise Textile Mills. No file upload required."
              />
              <EndpointCard
                method="GET"
                path="/results/{analysis_id}"
                description="Retrieve a stored analysis result by ID. Returns full scores, recommendation, and CAM sections."
              />
              <EndpointCard
                method="GET"
                path="/download/{analysis_id}/cam"
                description="Download the generated Credit Appraisal Memo (DOCX) for an analysis."
              />
            </Section>

            {/* Modules */}
            <Section id="modules" title="Modules" icon={Code2}>
              <div className="space-y-4">
                {[
                  {
                    path: 'modules/person1_ml_core/',
                    files: [
                      { name: 'data_generator.py', desc: 'Generates synthetic dataset — 30 companies, FY2009–2024, 146+ features including velocity metrics, Beneish ratios, and DNA fingerprints.' },
                      { name: 'feature_engineering.py', desc: 'Computes 146 engineered features: revenue velocity, DSRI, GMI, AQI, SGI, DEPI, SGAI, TATA, LVGI, and more.' },
                      { name: 'forensics.py', desc: 'Orchestrates Beneish M-Score, Altman Z-Score, and Piotroski F-Score computations.' },
                      { name: 'credit_scorer.py', desc: 'XGBoost + Random Forest + LightGBM ensemble with SHAP explainability.' },
                      { name: 'temporal_model.py', desc: 'LSTM trajectory model for multi-year DSCR trend & early warning system.' },
                      { name: 'validate_dataset.py', desc: 'Dataset validation, distribution plots, and quality reports.' },
                    ],
                  },
                  {
                    path: 'modules/person2_alt_data/',
                    files: [
                      { name: 'network_graph.py', desc: 'MCA21 promoter network — director interlocks, group contagion risk, NPA exposure mapping via GNN.' },
                      { name: 'stress_test.py', desc: 'Monte Carlo stress testing with 1,000 simulations and named macro scenarios (COVID shock, rate hike, etc.).' },
                      { name: 'satellite_module.py', desc: 'Sentinel-2 satellite imagery scoring for factory operational activity.' },
                      { name: 'gst_intelligence.py', desc: 'Cross-checks GST filing consistency against reported bank revenues to detect mismatches.' },
                      { name: 'dna_matching.py', desc: 'Default DNA fingerprinting — classifies companies against 6 historical default archetypes.' },
                    ],
                  },
                  {
                    path: 'modules/person3_llm_cam/',
                    files: [
                      { name: 'research_agent.py', desc: 'LangGraph + Tavily web research agent that fetches live industry outlook and news.' },
                      { name: 'approval_agent.py', desc: 'Bull-case LLM agent that constructs the strongest possible approval argument.' },
                      { name: 'dissent_agent.py', desc: 'Bear-case LLM agent that challenges the approval — plus a coordinator for final synthesis.' },
                      { name: 'ceo_interview.py', desc: 'Whisper transcription + VADER sentiment analysis for CEO/promoter interview scoring.' },
                      { name: 'cam_generator.py', desc: 'Generates a full 11-section Credit Appraisal Memo in DOCX format.' },
                    ],
                  },
                ].map(mod => (
                  <div key={mod.path} className="bg-white rounded-2xl border border-border shadow-[0_1px_4px_rgba(0,0,0,0.06)] overflow-hidden">
                    <div className="px-5 py-3 bg-surface-row border-b border-border">
                      <code className="text-sm font-[DM_Mono] text-dark font-semibold">{mod.path}</code>
                    </div>
                    <div className="divide-y divide-border-divider">
                      {mod.files.map(f => (
                        <div key={f.name} className="px-5 py-3 flex gap-4">
                          <code className="text-xs font-[DM_Mono] text-orange w-48 flex-shrink-0 mt-0.5">{f.name}</code>
                          <p className="text-xs text-text-secondary leading-relaxed">{f.desc}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </Section>

            {/* Pipeline */}
            <Section id="pipeline" title="Pipeline" icon={FlaskConical}>
              <p className="text-sm text-text-secondary leading-relaxed mb-6">
                <code className="font-[DM_Mono] text-orange">pipeline/main_pipeline.py</code> orchestrates all 10 layers sequentially.
              </p>
              <div className="bg-white rounded-2xl border border-border shadow-[0_1px_4px_rgba(0,0,0,0.06)] overflow-hidden">
                <div className="divide-y divide-border-divider">
                  {[
                    { step: '01', name: 'Excel Parser', desc: 'Parses Screener.in Excel → structured financial dictionary.' },
                    { step: '02', name: 'Feature Engineering', desc: 'Computes 146 features: velocity metrics, Beneish ratios, Z/F-Scores.' },
                    { step: '03', name: 'ML Ensemble Scoring', desc: 'XGBoost + RF + LightGBM → PD score, credit band, SHAP explanations.' },
                    { step: '04', name: 'LSTM Trajectory', desc: 'Multi-year DSCR trajectory modelling and danger horizon prediction.' },
                    { step: '05', name: 'Network Graph', desc: 'Promoter contagion risk mapping via MCA21 director interlock analysis.' },
                    { step: '06', name: 'Satellite + GST', desc: 'Sentinel-2 factory activity scoring and GST revenue cross-check.' },
                    { step: '07', name: 'Monte Carlo Stress', desc: '1,000-path stress simulation with named macro scenarios.' },
                    { step: '08', name: 'Research Agent', desc: 'Tavily-powered live web research for industry outlook and news.' },
                    { step: '09', name: 'Adversarial LLM Agents', desc: 'Bull agent + Bear agent debate, coordinated by a synthesis agent.' },
                    { step: '10', name: 'CAM Generator', desc: 'Compiles all outputs into an 11-section DOCX Credit Appraisal Memo.' },
                  ].map(layer => (
                    <div key={layer.step} className="px-5 py-3.5 flex items-center gap-4">
                      <span className="text-xs font-bold text-orange font-[DM_Mono] w-8 flex-shrink-0">L{layer.step}</span>
                      <span className="text-sm font-semibold text-dark w-44 flex-shrink-0">{layer.name}</span>
                      <p className="text-xs text-text-secondary leading-relaxed">{layer.desc}</p>
                    </div>
                  ))}
                </div>
              </div>
            </Section>

            {/* Configuration */}
            <Section id="configuration" title="Configuration" icon={FileText}>
              <div className="space-y-5">
                <div className="bg-white rounded-2xl border border-border p-5 shadow-[0_1px_4px_rgba(0,0,0,0.06)]">
                  <h3 className="text-sm font-semibold text-dark mb-3">Environment Variables</h3>
                  <div className="space-y-2">
                    {[
                      { key: 'GOOGLE_API_KEY', desc: 'Google Gemini API key for LLM agent tasks. Required.' },
                      { key: 'TAVILY_API_KEY', desc: 'Tavily API key for the research agent web search. Required.' },
                      { key: 'SENTINEL_CLIENT_ID', desc: 'Sentinel Hub OAuth client ID for Sentinel-2 satellite imagery scoring. Optional — falls back to synthetic score if absent.' },
                      { key: 'SENTINEL_CLIENT_SECRET', desc: 'Sentinel Hub OAuth client secret paired with SENTINEL_CLIENT_ID. Optional.' },
                    ].map(env => (
                      <div key={env.key} className="flex items-start gap-3 py-2 border-b border-border-divider last:border-0">
                        <code className="text-xs font-[DM_Mono] text-orange w-44 flex-shrink-0 mt-0.5 font-semibold">{env.key}</code>
                        <p className="text-xs text-text-secondary">{env.desc}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-white rounded-2xl border border-border p-5 shadow-[0_1px_4px_rgba(0,0,0,0.06)]">
                  <h3 className="text-sm font-semibold text-dark mb-3">Data Directories</h3>
                  <div className="space-y-0">
                    {[
                      { path: 'data/raw/', desc: 'Place uploaded Excel files here at runtime.' },
                      { path: 'data/processed/', desc: 'Pipeline writes CAM DOCX, score JSON, and charts here.' },
                      { path: 'data/synthetic/', desc: 'Pre-generated synthetic dataset (352 rows × 149 cols).' },
                      { path: 'models/', desc: 'Pre-trained LSTM, XGBoost, LightGBM, RF, and scaler artefacts.' },
                    ].map(d => (
                      <div key={d.path} className="flex items-start gap-3 py-2 border-b border-border-divider last:border-0">
                        <code className="text-xs font-[DM_Mono] text-orange w-44 flex-shrink-0 mt-0.5">{d.path}</code>
                        <p className="text-xs text-text-secondary">{d.desc}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-white rounded-2xl border border-border p-5 shadow-[0_1px_4px_rgba(0,0,0,0.06)]">
                  <h3 className="text-sm font-semibold text-dark mb-3">Running Tests</h3>
                  <CODE_BLOCK>{`# All tests
pytest tests/

# Module-specific
pytest tests/test_person1.py   # ML core tests
pytest tests/test_person2.py   # Alt data tests (49 tests)
pytest tests/test_person3.py   # LLM agent tests (mocked APIs)`}</CODE_BLOCK>
                </div>
              </div>
            </Section>
          </motion.div>
        </main>
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
            <Link to="/docs" className="text-sm text-orange font-semibold hover:text-white transition-colors">Documentation</Link>
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
