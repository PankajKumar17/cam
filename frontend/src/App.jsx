import { useState, createContext, useContext } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import Landing from './pages/Landing'
import Dashboard from './pages/Dashboard'
import Docs from './pages/Docs'
import About from './pages/About'

export const AnalysisContext = createContext(null)

export function useAnalysis() {
  return useContext(AnalysisContext)
}

export default function App() {
  const [analysis, setAnalysis] = useState(null) // { id, data }

  return (
    <AnalysisContext.Provider value={{ analysis, setAnalysis }}>
      <AnimatePresence mode="wait">
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route
            path="/dashboard/*"
            element={analysis ? <Dashboard /> : <Navigate to="/" replace />}
          />
          <Route path="/docs" element={<Docs />} />
          <Route path="/about" element={<About />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AnimatePresence>
    </AnalysisContext.Provider>
  )
}
