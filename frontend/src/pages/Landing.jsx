import { useState, useCallback, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { UploadCloud, CheckCircle, Lock, FileText, X, Brain, FileCheck, ArrowRight, Mic, ChevronDown, ChevronUp, Menu } from 'lucide-react'
import { useAnalysis } from '../App'
import { loadDemo, analyse, warmupServer } from '../api'

const container = { hidden: {}, show: { transition: { staggerChildren: 0.08 } } }
const item = { hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: 'easeOut' } } }

const STAGES = [
  { label: 'Parsing financial statements…', pct: 8 },
  { label: 'Running Beneish forensics (M-Score, Z-Score, F-Score)…', pct: 18 },
  { label: 'Computing ML ensemble — XGBoost · Random Forest · LightGBM…', pct: 30 },
  { label: 'DSCR trajectory modelling & danger horizon…', pct: 40 },
  { label: 'Building promoter network graph…', pct: 50 },
  { label: 'Satellite imagery + GST intelligence…', pct: 60 },
  { label: 'Monte Carlo stress testing (10,000 paths)…', pct: 70 },
  { label: 'Web research & industry outlook…', pct: 78 },
  { label: 'CEO interview NLP simulation…', pct: 85 },
  { label: 'Adversarial LLM agents debating…', pct: 92 },
  { label: 'Generating Credit Appraisal Memo…', pct: 97 },
]

const TRUST_ITEMS = [
  'XGBoost AUC 0.9948',
  '146 ML Features',
  'Full CAM in < 3 min',
  '17 AI Innovations',
]

const STEPS = [
  { num: '01', icon: UploadCloud, title: 'Upload & Name', body: 'Enter the company name and attach annual report Spreadsheets. Multi-year statements unlock trajectory analysis.' },
  { num: '02', icon: Brain, title: 'AI Runs 17 Innovations', body: 'Beneish forensics, network GNN, satellite scoring, Monte Carlo stress testing, and adversarial LLM agents run in parallel.' },
  { num: '03', icon: FileCheck, title: 'Get Your Decision', body: 'Receive PD score, credit limit, risk premium, and a full 10-section Credit Appraisal Memo — ready to present.' },
]

const STATS = [
  { value: '17', label: 'INNOVATIONS' },
  { value: '146', label: 'ML FEATURES' },
  { value: '0.9961', label: 'AUC SCORE' },
  { value: '< 3 min', label: 'PROCESSING' },
]

export default function Landing() {
  const [companyName, setCompanyName] = useState('')
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [loadingDemo, setLoadingDemo] = useState(false)
  const [error, setError] = useState('')
  const [dragOver, setDragOver] = useState(false)
  const [progress, setProgress] = useState(0)
  const [stageLabel, setStageLabel] = useState('')
  const timersRef = useRef([])
  const [menuOpen, setMenuOpen] = useState(false)
  // CEO Interview optional section
  const [ceoExpanded, setCeoExpanded] = useState(false)
  const [ceoMode, setCeoMode] = useState('skip') // 'skip' | 'audio' | 'transcript'
  const [ceoAudio, setCeoAudio] = useState(null)
  const [ceoTranscript, setCeoTranscript] = useState('')
  // PDF documents optional
  const [pdfExpanded, setPdfExpanded] = useState(false)
  const [pdfFiles, setPdfFiles] = useState([])
  // Credit officer qualitative notes
  const [notesExpanded, setNotesExpanded] = useState(false)
  const [qualitativeNotes, setQualitativeNotes] = useState('')
  const [warmingUp, setWarmingUp] = useState(false)
  const { setAnalysis } = useAnalysis()
  const navigate = useNavigate()

  const canSubmit = companyName.trim() && file && !loading

  function clearTimers() {
    timersRef.current.forEach(clearTimeout)
    timersRef.current = []
  }

  function startFakeProgress() {
    setProgress(0)
    let i = 0
    function tick() {
      if (i >= STAGES.length) return
      setProgress(STAGES[i].pct)
      setStageLabel(STAGES[i].label)
      i++
      if (i < STAGES.length) {
        timersRef.current.push(setTimeout(tick, 5000 + Math.random() * 4000))
      }
    }
    tick()
  }

  async function handleAnalyse() {
    if (!canSubmit) return
    setLoading(true)
    setError('')
    setWarmingUp(false)
    // Wake up Render if it has spun down, before starting the progress animation
    try {
      await warmupServer(() => {
        setWarmingUp(true)
        setProgress(2)
        setStageLabel('Server is waking up after idle… this takes ~30s, hang tight!')
      })
    } catch (e) {
      setLoading(false)
      setProgress(0)
      setWarmingUp(false)
      setError(e.message)
      return
    }
    setWarmingUp(false)
    startFakeProgress()
    try {
      const result = await analyse(
        companyName.trim(),
        file,
        {
          ceoAudio: ceoMode === 'audio' ? ceoAudio : null,
          ceoTranscript: ceoMode === 'transcript' ? ceoTranscript : '',
          pdfFiles: pdfFiles.length > 0 ? pdfFiles : null,
          qualitativeNotes: qualitativeNotes.trim() || null,
        }
      )
      clearTimers()
      setProgress(100)
      setStageLabel('Analysis complete!')
      await new Promise(r => setTimeout(r, 500))
      setAnalysis({ id: result.analysis_id, data: result.data })
      navigate('/dashboard')
    } catch (e) {
      clearTimers()
      setLoading(false)
      setProgress(0)
      setError(e.response?.data?.detail || 'Analysis failed. Please try again.')
    }
  }

  async function handleDemo() {
    setLoadingDemo(true)
    setError('')
    // Wake up Render if it has spun down
    try {
      await warmupServer(() =>
        setError('⏳ Server is waking up after idle (~30s)… retrying automatically, please wait.')
      )
    } catch (e) {
      setError(e.message)
      setLoadingDemo(false)
      return
    }
    setError('')
    try {
      const result = await loadDemo()
      setAnalysis({ id: result.analysis_id, data: result.data })
      navigate('/dashboard')
    } catch (e) {
      setError('Failed to load demo data.')
    } finally {
      setLoadingDemo(false)
    }
  }

  const onDrop = useCallback((e) => {
    e.preventDefault()
    setDragOver(false)
    const f = e.dataTransfer?.files?.[0]
    if (f) setFile(f)
  }, [])

  return (
    <motion.div
      className="min-h-screen bg-surface-page"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, y: -20 }}
    >
      {/* Navbar */}
      <nav className="h-16 bg-white/90 backdrop-blur-md border-b border-border-divider sticky top-0 z-50">
        <div className="max-w-[1280px] mx-auto px-4 md:px-10 h-full flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img src="/logo.jpeg" alt="Yakṣarāja" className="w-9 h-9 rounded-full object-cover shadow-[0_4px_16px_rgba(232,71,10,0.30)]" />
            <span className="font-[DM_Serif_Display] text-xl text-dark">Yakṣarāja</span>
          </div>
          <div className="hidden sm:flex items-center gap-4 md:gap-6">
            <Link to="/docs" className="text-sm text-text-secondary hover:text-dark transition-colors">Docs</Link>
            <Link to="/about" className="text-sm text-text-secondary hover:text-dark transition-colors">About</Link>
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
          <Link to="/docs" onClick={() => setMenuOpen(false)} className="block py-2 text-sm text-text-secondary hover:text-dark">Docs</Link>
          <Link to="/about" onClick={() => setMenuOpen(false)} className="block py-2 text-sm text-text-secondary hover:text-dark">About</Link>
        </div>
      )}

      {/* Hero Section */}
      <section className="max-w-[1280px] mx-auto px-4 md:px-10 py-10 md:py-12">
        <motion.div
          className="grid grid-cols-1 lg:grid-cols-[1fr_480px] gap-10 lg:gap-16 items-center"
          variants={container}
          initial="hidden"
          animate="show"
        >
          {/* Left Column */}
          <motion.div variants={item}>
            <span className="bg-orange-pale border border-orange-border text-orange
                             text-xs font-semibold uppercase tracking-widest
                             px-3.5 py-1.5 rounded-full inline-flex">
              AI Credit Decisioning Engine
            </span>

            <h1 className="font-[DM_Serif_Display] text-[56px] leading-tight text-dark mt-6">
              Intelligent Credit<br />Decisions in<br />
              <span className="text-orange italic">Minutes.</span>
            </h1>

            <p className="text-lg text-text-secondary leading-relaxed max-w-lg mt-6">
              Upload financial statements, get a complete Credit Appraisal
              Memo powered by 17 AI innovations — Beneish forensics, satellite
              intelligence, and adversarial LLM agents.
            </p>

            <div className="flex gap-6 mt-8 flex-wrap">
              {TRUST_ITEMS.map(t => (
                <div key={t} className="flex items-center gap-2 text-sm text-text-muted">
                  <CheckCircle size={14} className="text-success" />
                  {t}
                </div>
              ))}
            </div>
          </motion.div>

          {/* Right Column — Upload Card */}
          <motion.div
            variants={item}
            initial={{ opacity: 0, scale: 0.97, y: 16 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ duration: 0.45, ease: 'easeOut', delay: 0.15 }}
          >
            <div className="bg-white rounded-3xl shadow-[0_24px_64px_rgba(0,0,0,0.18)] p-9 border border-border">
              <h2 className="text-xl font-semibold text-dark">Start Your Analysis</h2>
              <p className="text-sm text-text-muted mt-1">Enter company name and upload statements</p>

              <div className="border-t border-border-divider mt-5 mb-5" />

              {loading ? (
                /* ── Progress View ── */
                <div className="py-4 space-y-5">
                  <div className="text-center">
                    <div className="w-14 h-14 rounded-full bg-orange-pale flex items-center justify-center mx-auto mb-4">
                      <Brain className="text-orange w-7 h-7 animate-pulse" />
                    </div>
                    <p className="text-base font-semibold text-dark">Analysing {companyName}</p>
                    <p className="text-sm text-text-muted mt-1 min-h-[20px] leading-snug">{stageLabel}</p>
                  </div>
                  <div>
                    <div className="flex justify-between mb-2">
                      <span className="text-xs font-medium text-text-muted">Progress</span>
                      <span className="text-xs font-bold text-orange font-[DM_Mono]">{progress}%</span>
                    </div>
                    <div className="h-3 bg-surface-page rounded-full overflow-hidden border border-border">
                      <div
                        className="h-full bg-gradient-to-r from-orange to-orange-light rounded-full transition-[width] duration-700 ease-out"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                    <div className="flex gap-1 mt-2">
                      {STAGES.map((s, i) => (
                        <div key={i} className={`h-1 flex-1 rounded-full transition-all duration-500 ${progress >= s.pct ? 'bg-orange' : 'bg-border'}`} />
                      ))}
                    </div>
                  </div>
                  <p className="text-xs text-text-muted text-center">Full analysis takes 2-3 minutes</p>
                </div>
              ) : (
                /* ── Normal Form ── */
                <>
                  {/* Company Name */}
                  <label className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-2 block">
                    Company Name
                  </label>
                  <input
                    type="text"
                    value={companyName}
                    onChange={e => setCompanyName(
                      e.target.value.replace(/\b\w/g, c => c.toUpperCase())
                    )}
                    placeholder="e.g. Sunrise Textile Mills"
                    className="w-full h-12 px-4 rounded-xl border border-border text-sm text-dark bg-white
                               placeholder:text-text-placeholder focus:outline-none focus:border-orange
                               focus:shadow-[0_0_0_3px_rgba(232,71,10,0.15)] transition-all duration-150"
                  />

                  {/* File Dropzone */}
                  <label className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-2 block mt-5">
                    Financial Statements
                  </label>

                  {!file ? (
                    <div
                      onDragOver={e => { e.preventDefault(); setDragOver(true) }}
                      onDragLeave={() => setDragOver(false)}
                      onDrop={onDrop}
                      onClick={() => document.getElementById('file-input').click()}
                      className={`border-2 border-dashed rounded-2xl p-8 flex flex-col items-center gap-2 cursor-pointer
                        transition-all duration-200
                        ${dragOver
                          ? 'border-orange bg-orange-pale shadow-[0_0_0_3px_rgba(232,71,10,0.15)]'
                          : 'border-border hover:border-orange hover:bg-orange-pale/40'}`}
                    >
                      <UploadCloud className="w-8 h-8 text-orange" />
                      <span className="text-sm font-medium text-dark">Drag &amp; drop files here</span>
                      <span className="text-xs text-text-muted">or</span>
                      <span className="text-orange text-sm font-semibold underline">Browse files</span>
                      <span className="text-xs text-text-muted mt-1">Accepts XLSX, XLS, CSV · Max 200MB</span>
                      <input
                        id="file-input"
                        type="file"
                        accept=".xlsx,.xls,.csv"
                        className="hidden"
                        onChange={e => setFile(e.target.files?.[0] || null)}
                      />
                    </div>
                  ) : (
                    <div className="bg-success-bg border-2 border-success rounded-2xl p-4 flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <FileText className="text-success" size={20} />
                        <div>
                          <p className="text-sm font-medium text-dark font-[DM_Mono]">{file.name}</p>
                          <p className="text-xs text-text-muted">{(file.size / 1024).toFixed(0)} KB</p>
                        </div>
                      </div>
                      <button onClick={() => setFile(null)} className="text-text-muted hover:text-danger transition-colors">
                        <X size={18} />
                      </button>
                    </div>
                  )}

                  {/* CEO Interview — Optional */}
                  <div className="mt-5">
                    <button
                      type="button"
                      onClick={() => setCeoExpanded(v => !v)}
                      className="w-full flex items-center justify-between px-4 py-3 rounded-xl
                                 border border-dashed border-border hover:border-orange hover:bg-orange-pale/30
                                 transition-all duration-150 group"
                    >
                      <div className="flex items-center gap-2 text-sm">
                        <Mic size={15} className="text-orange" />
                        <span className="font-medium text-dark">CEO Interview Analysis</span>
                        <span className="text-xs text-text-muted bg-surface-page px-2 py-0.5 rounded-full">Optional</span>
                      </div>
                      {ceoExpanded
                        ? <ChevronUp size={15} className="text-text-muted group-hover:text-orange transition-colors" />
                        : <ChevronDown size={15} className="text-text-muted group-hover:text-orange transition-colors" />}
                    </button>

                    <AnimatePresence>
                      {ceoExpanded && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.22, ease: 'easeInOut' }}
                          className="overflow-hidden"
                        >
                          <div className="pt-4 space-y-3">
                            <p className="text-xs text-text-muted leading-relaxed">
                              Upload an audio recording or paste the transcript to enable NLP
                              sentiment & deception analysis. Skip to use AI-simulated scores.
                            </p>

                            {/* Mode selector */}
                            <div className="flex gap-2">
                              {[['skip', 'Skip (AI Simulates)'], ['audio', 'Audio File'], ['transcript', 'Transcript Text']].map(([val, label]) => (
                                <button
                                  key={val}
                                  type="button"
                                  onClick={() => { setCeoMode(val); setCeoAudio(null); setCeoTranscript('') }}
                                  className={`flex-1 text-xs font-medium py-2 px-3 rounded-lg border transition-all duration-150
                                    ${ ceoMode === val
                                      ? 'border-orange bg-orange-pale text-orange'
                                      : 'border-border text-text-muted hover:border-orange hover:text-orange hover:bg-orange-pale/30'}`}
                                >
                                  {label}
                                </button>
                              ))}
                            </div>

                            {/* Audio upload */}
                            {ceoMode === 'audio' && (
                              !ceoAudio ? (
                                <div
                                  onClick={() => document.getElementById('ceo-audio-input').click()}
                                  className="border-2 border-dashed border-border rounded-xl p-5 flex flex-col items-center
                                             gap-1.5 cursor-pointer hover:border-orange hover:bg-orange-pale/30 transition-all"
                                >
                                  <Mic className="w-6 h-6 text-orange" />
                                  <span className="text-sm font-medium text-dark">Upload Audio</span>
                                  <span className="text-xs text-text-muted">MP3, WAV, MP4, M4A · Max 500MB</span>
                                  <input id="ceo-audio-input" type="file" accept=".mp3,.wav,.mp4,.m4a,.ogg,.flac" className="hidden"
                                    onChange={e => setCeoAudio(e.target.files?.[0] || null)} />
                                </div>
                              ) : (
                                <div className="bg-success-bg border border-success rounded-xl p-3 flex items-center justify-between">
                                  <div className="flex items-center gap-2.5">
                                    <Mic className="text-success" size={16} />
                                    <div>
                                      <p className="text-xs font-medium text-dark font-[DM_Mono]">{ceoAudio.name}</p>
                                      <p className="text-xs text-text-muted">{(ceoAudio.size / 1024 / 1024).toFixed(1)} MB</p>
                                    </div>
                                  </div>
                                  <button onClick={() => setCeoAudio(null)} className="text-text-muted hover:text-danger transition-colors">
                                    <X size={15} />
                                  </button>
                                </div>
                              )
                            )}

                            {/* Transcript paste */}
                            {ceoMode === 'transcript' && (
                              <textarea
                                value={ceoTranscript}
                                onChange={e => setCeoTranscript(e.target.value)}
                                placeholder="Paste the CEO/promoter interview transcript here…"
                                rows={5}
                                className="w-full px-4 py-3 rounded-xl border border-border text-xs text-dark
                                           bg-white placeholder:text-text-placeholder focus:outline-none
                                           focus:border-orange focus:shadow-[0_0_0_3px_rgba(232,71,10,0.15)]
                                           resize-y transition-all duration-150 font-[DM_Mono] leading-relaxed"
                              />
                            )}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>

                  {/* ─── PDF Document Upload — Optional ──────────────────── */}
                  <div className="mt-3">
                    <button
                      type="button"
                      onClick={() => setPdfExpanded(v => !v)}
                      className="w-full flex items-center justify-between px-4 py-3 rounded-xl
                                 border border-dashed border-border hover:border-orange hover:bg-orange-pale/30
                                 transition-all duration-150 group"
                    >
                      <div className="flex items-center gap-2 text-sm">
                        <FileText size={15} className="text-orange" />
                        <span className="font-medium text-dark">Supporting Documents</span>
                        <span className="text-xs text-text-muted bg-surface-page px-2 py-0.5 rounded-full">Optional — PDF</span>
                      </div>
                      {pdfExpanded
                        ? <ChevronUp size={15} className="text-text-muted group-hover:text-orange transition-colors" />
                        : <ChevronDown size={15} className="text-text-muted group-hover:text-orange transition-colors" />}
                    </button>

                    <AnimatePresence>
                      {pdfExpanded && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.22, ease: 'easeInOut' }}
                          className="overflow-hidden"
                        >
                          <div className="pt-3 space-y-2">
                            <p className="text-xs text-text-muted leading-relaxed">
                              Upload Annual Reports, Legal Notices, or Sanction Letters. The AI will extract
                              DINs, CINs, legal risks, and financial data automatically.
                            </p>
                            <div
                              onClick={() => document.getElementById('pdf-upload-input').click()}
                              className="border-2 border-dashed border-border rounded-xl p-4 flex flex-col items-center
                                         gap-1.5 cursor-pointer hover:border-orange hover:bg-orange-pale/30 transition-all"
                            >
                              <FileText className="w-6 h-6 text-orange" />
                              <span className="text-sm font-medium text-dark">Add PDF Documents</span>
                              <span className="text-xs text-text-muted">Annual Report · Legal Notice · Sanction Letter · Max 100MB each</span>
                              <input
                                id="pdf-upload-input"
                                type="file"
                                accept=".pdf"
                                multiple
                                className="hidden"
                                onChange={e => {
                                  const selected = Array.from(e.target.files || [])
                                  setPdfFiles(prev => {
                                    const names = new Set(prev.map(f => f.name))
                                    return [...prev, ...selected.filter(f => !names.has(f.name))]
                                  })
                                  e.target.value = ''
                                }}
                              />
                            </div>
                            {pdfFiles.length > 0 && (
                              <div className="space-y-1.5">
                                {pdfFiles.map((pf, i) => (
                                  <div key={i} className="bg-surface-card border border-border rounded-xl px-3 py-2 flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                      <FileText size={14} className="text-text-muted shrink-0" />
                                      <span className="text-xs font-medium text-dark font-[DM_Mono] truncate max-w-[200px]">{pf.name}</span>
                                      <span className="text-xs text-text-muted">{(pf.size / 1024).toFixed(0)} KB</span>
                                    </div>
                                    <button onClick={() => setPdfFiles(prev => prev.filter((_, j) => j !== i))} className="text-text-muted hover:text-danger transition-colors">
                                      <X size={14} />
                                    </button>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>

                  {/* ─── Credit Officer Qualitative Notes — Optional ─────── */}
                  <div className="mt-3">
                    <button
                      type="button"
                      onClick={() => setNotesExpanded(v => !v)}
                      className="w-full flex items-center justify-between px-4 py-3 rounded-xl
                                 border border-dashed border-border hover:border-navy hover:bg-navy/5
                                 transition-all duration-150 group"
                    >
                      <div className="flex items-center gap-2 text-sm">
                        <span className="text-navy text-base leading-none">✎</span>
                        <span className="font-medium text-dark">Credit Officer Field Notes</span>
                        <span className="text-xs text-text-muted bg-surface-page px-2 py-0.5 rounded-full">Optional</span>
                      </div>
                      {notesExpanded
                        ? <ChevronUp size={15} className="text-text-muted group-hover:text-navy transition-colors" />
                        : <ChevronDown size={15} className="text-text-muted group-hover:text-navy transition-colors" />}
                    </button>

                    <AnimatePresence>
                      {notesExpanded && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.22, ease: 'easeInOut' }}
                          className="overflow-hidden"
                        >
                          <div className="pt-3">
                            <p className="text-xs text-text-muted mb-2 leading-relaxed">
                              Site visit observations, mgmt behaviour, capacity utilisation, collateral quality
                              — anything not captured in the financials. The AI will factor these into its risk assessment.
                            </p>
                            <textarea
                              value={qualitativeNotes}
                              onChange={e => setQualitativeNotes(e.target.value)}
                              placeholder={`e.g.\n• Factory operating at ~40% capacity\n• Management evasive on working capital cycle\n• Promoter recently reduced pledge stake by 12%\n• Site visit: machinery visibly idle in Unit 2`}
                              rows={5}
                              className="w-full px-4 py-3 rounded-xl border border-border text-xs text-dark
                                         bg-white placeholder:text-text-placeholder focus:outline-none
                                         focus:border-navy focus:shadow-[0_0_0_3px_rgba(10,35,80,0.12)]
                                         resize-y transition-all duration-150 font-[DM_Mono] leading-relaxed"
                            />
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>

                  {/* CTA Buttons */}
                  <button
                    onClick={handleAnalyse}
                    disabled={!canSubmit}
                    className={`w-full h-[52px] rounded-2xl text-base font-semibold mt-6 transition-all duration-150
                      ${canSubmit
                        ? 'bg-gradient-to-br from-orange to-orange-light text-white shadow-[0_4px_16px_rgba(232,71,10,0.30)] hover:shadow-[0_8px_32px_rgba(232,71,10,0.40)] hover:-translate-y-0.5 active:translate-y-0'
                        : 'bg-dark/30 text-white/50 cursor-not-allowed'}`}
                  >
                    Analyse with AI <ArrowRight className="inline ml-1" size={16} />
                  </button>

                  <button
                    onClick={handleDemo}
                    disabled={loadingDemo}
                    className="w-full h-[44px] rounded-2xl text-sm font-semibold mt-3 bg-white text-dark
                               border-[1.5px] border-border-strong hover:border-orange hover:text-orange
                               hover:bg-orange-pale transition-all duration-150"
                  >
                    {loadingDemo ? (
                      <span className="flex items-center justify-center gap-2">
                        <span className="w-4 h-4 border-2 border-dark/30 border-t-dark rounded-full animate-spin" />
                        Loading Demo…
                      </span>
                    ) : 'Load Demo — Sunrise Textile Mills'}
                  </button>

                  {error && (
                    <p className="text-sm text-danger mt-3 text-center">{error}</p>
                  )}

                  <div className="flex items-center justify-center gap-1.5 mt-4 text-xs text-text-muted">
                    <Lock size={12} />
                    Files processed locally · never stored externally
                  </div>
                </>
              )}
            </div>
          </motion.div>
        </motion.div>
      </section>

      {/* How It Works */}
      <section id="how" className="max-w-[1280px] mx-auto px-4 md:px-10 py-12 md:py-20">
        <div className="text-center">
          <h2 className="font-[DM_Serif_Display] text-4xl text-dark">How It Works</h2>
          <p className="text-base text-text-muted mt-2">Three steps from Spreadsheets to lending decision</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
          {STEPS.map(step => (
            <motion.div
              key={step.num}
              className="bg-white rounded-2xl border border-border shadow-[0_1px_4px_rgba(0,0,0,0.06),0_2px_12px_rgba(0,0,0,0.06)]
                         p-7 hover:shadow-[0_4px_16px_rgba(0,0,0,0.10),0_8px_32px_rgba(0,0,0,0.08)]
                         hover:-translate-y-0.5 transition-all duration-200"
              whileHover={{ y: -2 }}
            >
              <span className="text-xs font-bold uppercase tracking-widest text-orange">
                STEP {step.num}
              </span>
              <div className="w-[52px] h-[52px] bg-orange-pale rounded-full flex items-center justify-center mt-3 mb-4">
                <step.icon className="w-6 h-6 text-orange" />
              </div>
              <h3 className="font-[DM_Serif_Display] text-xl text-dark">{step.title}</h3>
              <p className="text-sm text-text-secondary leading-relaxed mt-2">{step.body}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Stats Strip */}
      <section className="bg-[#ECEEF2] py-12">
        <div className="max-w-[1280px] mx-auto px-4 md:px-10 grid grid-cols-2 md:grid-cols-4 divide-x divide-border-strong">
          {STATS.map(s => (
            <div key={s.label} className="text-center px-2 md:px-8">
              <p className="font-[DM_Serif_Display] text-3xl md:text-5xl text-dark">{s.value}</p>
              <p className="text-xs font-semibold uppercase tracking-widest text-text-muted mt-2">{s.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section id="features" className="max-w-[1280px] mx-auto px-4 md:px-10 py-12 md:py-20">
        <div className="text-center mb-12">
          <h2 className="font-[DM_Serif_Display] text-4xl text-dark">Built on Academic-Grade ML</h2>
          <p className="text-sm text-text-secondary leading-relaxed mt-3 max-w-2xl mx-auto">
            Our credit decisioning engine combines Beneish M-Score forensic analysis with an
            XGBoost / LightGBM / Random Forest ensemble trained on 146 engineered features.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            { title: 'Beneish M-Score Forensics', body: '8-factor earnings manipulation detection based on Prof. Beneish\'s academic model. Flags accounting anomalies before they become crises.' },
            { title: 'Network Graph GNN', body: 'Promoter network analysis mapping director interlocks, group company contagion risk, and NPA exposure across corporate relationships.' },
            { title: 'Adversarial LLM Agents', body: 'Bull and bear agents independently argue for and against lending, with a coordinator synthesising the final recommendation — removing single-model bias.' },
          ].map(f => (
            <div key={f.title} className="bg-white rounded-2xl border border-border shadow-[0_1px_4px_rgba(0,0,0,0.06),0_2px_12px_rgba(0,0,0,0.06)] p-7">
              <h4 className="font-[DM_Serif_Display] text-lg text-dark">{f.title}</h4>
              <p className="text-sm text-text-secondary leading-relaxed mt-2">{f.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-dark py-12">
        <div className="max-w-[1280px] mx-auto px-4 md:px-10">
          <div className="flex items-center gap-3">
            <img src="/logo.jpeg" alt="Yakṣarāja" className="w-9 h-9 rounded-full object-cover shadow-[0_4px_16px_rgba(232,71,10,0.30)]" />

            <div>
              <span className="font-[DM_Serif_Display] text-xl text-white">Yakṣarāja</span>
              <p className="text-sm text-text-muted mt-0.5">AI-Powered Credit Decisioning Engine</p>
            </div>
          </div>
          <div className="flex gap-6 mt-8">
            <Link to="/docs" className="text-sm text-text-muted hover:text-white transition-colors">Documentation</Link>
            <Link to="/about" className="text-sm text-text-muted hover:text-white transition-colors">About</Link>
          </div>
          <div className="mt-8 pt-6 border-t border-white/10 text-xs text-text-muted">
            © 2025 Yakṣarāja · Vivriti Capital AI Hackathon
          </div>
        </div>
      </footer>
    </motion.div>
  )
}
