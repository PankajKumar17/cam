import { Routes, Route } from 'react-router-dom'
import { motion } from 'framer-motion'
import Navbar from '../components/Navbar'
import Overview from './Overview'
import DeepDive from './DeepDive'
import Reports from './Reports'

export default function Dashboard() {
  return (
    <motion.div
      className="min-h-screen bg-surface-page flex flex-col"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <Navbar />
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-[1280px] mx-auto px-3 md:px-6 py-4 md:py-6">
          <Routes>
            <Route index element={<Overview />} />
            <Route path="deep-dive" element={<DeepDive />} />
            <Route path="reports" element={<Reports />} />
          </Routes>
        </div>
      </main>
    </motion.div>
  )
}
