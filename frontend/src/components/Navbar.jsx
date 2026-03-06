import { NavLink, useNavigate } from 'react-router-dom'
import { useAnalysis } from '../App'

const tabs = [
  { path: '/dashboard', label: 'Overview', end: true },
  { path: '/dashboard/deep-dive', label: 'Deep Dive' },
  { path: '/dashboard/reports', label: 'Reports' },
]

export default function Navbar() {
  const { analysis, setAnalysis } = useAnalysis()
  const navigate = useNavigate()
  const company = analysis?.data?.company_name || ''
  const decision = analysis?.data?.recommendation?.lending_decision || ''

  function handleNewAnalysis() {
    setAnalysis(null)
    navigate('/')
  }

  return (
    <nav className="h-16 bg-white border-b border-border-divider flex items-center px-4 md:px-6 sticky top-0 z-50 gap-2">
      {/* Left */}
      <div className="flex items-center gap-2 flex-shrink-0 min-w-0">
        <img src="/logo.jpeg" alt="Yakṣarāja" className="w-8 h-8 md:w-9 md:h-9 rounded-full object-cover shadow-[0_4px_16px_rgba(232,71,10,0.30)] flex-shrink-0" />
        <span className="font-semibold text-base md:text-lg text-dark whitespace-nowrap">Yakṣarāja</span>
        {company && (
          <>
            <div className="hidden md:block w-px h-5 bg-border mx-1" />
            <span className="hidden md:inline bg-orange-pale border border-orange-border text-orange
                             text-xs font-semibold px-3 py-1 rounded-full truncate max-w-[140px]">
              {company}
            </span>
          </>
        )}
        {decision && (
          <span className={`hidden md:inline text-xs font-semibold px-3 py-1 rounded-full ml-1 flex-shrink-0
            ${decision === 'APPROVE' ? 'bg-success-bg text-success' :
              decision === 'CONDITIONAL_APPROVE' ? 'bg-warning-bg text-warning' :
              decision === 'REJECT' ? 'bg-danger-bg text-danger' :
              'bg-surface-row text-text-muted'}`}>
            {decision.replace('_', ' ')}
          </span>
        )}
      </div>

      {/* Center tabs */}
      <nav className="flex-1 flex items-center justify-center gap-1 overflow-x-auto">
        {tabs.map(tab => (
          <NavLink
            key={tab.path}
            to={tab.path}
            end={tab.end}
            className={({ isActive }) =>
              `px-3 md:px-4 py-2 rounded-full text-sm font-medium transition-all whitespace-nowrap flex-shrink-0 ${
                isActive
                  ? 'bg-dark text-white'
                  : 'text-text-secondary hover:text-dark hover:bg-surface-hover'
              }`
            }
          >
            {tab.label}
          </NavLink>
        ))}
      </nav>

      {/* Right */}
      <button
        onClick={handleNewAnalysis}
        className="flex-shrink-0 px-3 md:px-4 py-2 rounded-full text-xs md:text-sm font-semibold bg-dark text-white
                   hover:bg-orange transition-colors duration-200"
      >
        <span className="hidden sm:inline">New Analysis</span>
        <span className="sm:hidden">New</span>
      </button>
    </nav>
  )
}
