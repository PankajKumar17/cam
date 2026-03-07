import { NavLink, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { useAnalysis } from '../App'

const tabs = [
  { path: '/dashboard', label: 'Overview', end: true },
  { path: '/dashboard/deep-dive', label: 'Deep Dive' },
  { path: '/dashboard/reports', label: 'Reports' },
]

export default function Navbar() {
  const { analysis, setAnalysis } = useAnalysis()
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)
  const company = analysis?.data?.company_name || ''
  const decision = analysis?.data?.recommendation?.lending_decision || ''

  function handleNewAnalysis() {
    setAnalysis(null)
    setMenuOpen(false)
    navigate('/')
  }

  const decisionClass =
    decision === 'APPROVE' ? 'bg-success-bg text-success' :
    decision === 'CONDITIONAL_APPROVE' ? 'bg-warning-bg text-warning' :
    decision === 'REJECT' ? 'bg-danger-bg text-danger' :
    'bg-surface-row text-text-muted'

  return (
    <>
      <nav className="h-16 bg-white border-b border-border-divider flex items-center px-4 md:px-6 sticky top-0 z-50 gap-2">
        {/* Left: logo + brand + badges (badges desktop-only) */}
        <div className="flex items-center gap-2 flex-shrink-0 min-w-0">
          <img src="/logo.jpeg" alt="Yakṣarāja" className="w-8 h-8 md:w-9 md:h-9 rounded-full object-cover shadow-[0_4px_16px_rgba(232,71,10,0.30)] flex-shrink-0" />
          <span className="font-semibold text-base md:text-lg text-dark whitespace-nowrap">Yakṣarāja</span>
          {company && (
            <>
              <div className="hidden md:block w-px h-5 bg-border mx-1" />
              <span className="hidden md:inline bg-orange-pale border border-orange-border text-orange text-xs font-semibold px-3 py-1 rounded-full truncate max-w-[140px]">
                {company}
              </span>
            </>
          )}
          {decision && (
            <span className={`hidden md:inline text-xs font-semibold px-3 py-1 rounded-full ml-1 flex-shrink-0 ${decisionClass}`}>
              {decision.replace('_', ' ')}
            </span>
          )}
        </div>

        {/* Center tabs — desktop only */}
        <nav className="hidden md:flex flex-1 items-center justify-center gap-1">
          {tabs.map(tab => (
            <NavLink
              key={tab.path}
              to={tab.path}
              end={tab.end}
              className={({ isActive }) =>
                `px-4 py-2 rounded-full text-sm font-medium transition-all whitespace-nowrap ${
                  isActive ? 'bg-dark text-white' : 'text-text-secondary hover:text-dark hover:bg-surface-hover'
                }`
              }
            >
              {tab.label}
            </NavLink>
          ))}
        </nav>

        {/* Right: New Analysis button — desktop only */}
        <button
          onClick={handleNewAnalysis}
          className="hidden md:block flex-shrink-0 px-4 py-2 rounded-full text-sm font-semibold bg-dark text-white hover:bg-orange transition-colors duration-200"
        >
          New Analysis
        </button>

        {/* Right: hamburger — mobile only */}
        <button
          onClick={() => setMenuOpen(o => !o)}
          className="md:hidden ml-auto p-2 rounded-lg text-dark hover:bg-surface-hover transition-colors"
          aria-label="Toggle menu"
          aria-expanded={menuOpen}
        >
          {menuOpen ? (
            <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          ) : (
            <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          )}
        </button>
      </nav>

      {/* Mobile dropdown */}
      {menuOpen && (
        <div className="md:hidden bg-white border-b border-border-divider shadow-md sticky top-16 z-40 px-4 py-3 flex flex-col gap-1">
          {/* Company + decision badge */}
          {company && (
            <div className="flex items-center gap-2 px-3 py-2 mb-1 flex-wrap">
              <span className="bg-orange-pale border border-orange-border text-orange text-xs font-semibold px-3 py-1 rounded-full truncate max-w-[200px]">
                {company}
              </span>
              {decision && (
                <span className={`text-xs font-semibold px-3 py-1 rounded-full flex-shrink-0 ${decisionClass}`}>
                  {decision.replace('_', ' ')}
                </span>
              )}
            </div>
          )}

          {/* Nav links */}
          {tabs.map(tab => (
            <NavLink
              key={tab.path}
              to={tab.path}
              end={tab.end}
              onClick={() => setMenuOpen(false)}
              className={({ isActive }) =>
                `px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                  isActive ? 'bg-dark text-white' : 'text-text-secondary hover:text-dark hover:bg-surface-hover'
                }`
              }
            >
              {tab.label}
            </NavLink>
          ))}

          {/* New Analysis */}
          <button
            onClick={handleNewAnalysis}
            className="mt-2 w-full px-4 py-3 rounded-xl text-sm font-semibold bg-dark text-white hover:bg-orange transition-colors duration-200"
          >
            New Analysis
          </button>
        </div>
      )}
    </>
  )
}
