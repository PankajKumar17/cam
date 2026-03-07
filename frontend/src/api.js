import axios from 'axios'

// In production (Render+Vercel) VITE_API_BASE_URL is not needed because
// vercel.json rewrites /api/* → Render backend. Setting it overrides that.
const api = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL || '/api' })

export async function loadDemo() {
  const { data } = await api.post('/demo')
  return data
}

/**
 * Pings /health until the server responds (handles Render cold-start spin-up).
 * Calls onWaiting() the first time a failure is detected, then resolves
 * automatically once the server is ready. Rejects after maxWaitMs (default 90s).
 */
export async function warmupServer(onWaiting, { maxWaitMs = 90_000, intervalMs = 3_000 } = {}) {
  const deadline = Date.now() + maxWaitMs
  let notified = false
  while (Date.now() < deadline) {
    try {
      await api.get('/health', { timeout: 5000 })
      return // server is up
    } catch {
      if (!notified) {
        onWaiting()
        notified = true
      }
      await new Promise(r => setTimeout(r, intervalMs))
    }
  }
  throw new Error('Server did not wake up in time. Please try again.')
}

export async function analyse(
  companyName,
  file,
  { ceoAudio = null, ceoTranscript = '', pdfFiles = null, qualitativeNotes = null } = {}
) {
  const form = new FormData()
  form.append('company_name', companyName)
  form.append('file', file)
  if (ceoAudio) form.append('ceo_audio', ceoAudio)
  if (ceoTranscript && ceoTranscript.trim()) form.append('ceo_transcript', ceoTranscript.trim())
  if (pdfFiles && pdfFiles.length > 0) {
    pdfFiles.forEach(pf => form.append('pdf_files', pf))
  }
  if (qualitativeNotes && qualitativeNotes.trim()) {
    form.append('qualitative_notes', qualitativeNotes.trim())
  }

  // Step 1 — submit job (backend returns immediately with job_id, no timeout risk)
  const { data: { job_id } } = await api.post('/analyse', form)

  // Step 2 — poll every 4s until done or error
  // Network errors (ERR_CONNECTION_RESET) are retried up to 5 times before giving up
  let networkRetries = 0
  const MAX_RETRIES = 5
  while (true) {
    await new Promise(r => setTimeout(r, 4000))
    try {
      const { data: job } = await api.get(`/job/${job_id}`, { timeout: 10000 })
      networkRetries = 0 // reset on success
      if (job.status === 'done') {
        return { analysis_id: job.analysis_id, data: job.data }
      }
      if (job.status === 'error') {
        throw new Error(job.error || 'Pipeline failed')
      }
      // status === 'running' → keep polling
    } catch (e) {
      // Re-throw app-level errors (status: error) immediately
      if (e.message && !e.code && !e.response?.status) throw e
      // Transient network errors — retry with back-off
      networkRetries++
      if (networkRetries > MAX_RETRIES) {
        throw new Error('Lost connection to server after multiple retries. Please check and try again.')
      }
      await new Promise(r => setTimeout(r, networkRetries * 3000))
    }
  }
}

export async function getAnalysis(id) {
  const { data } = await api.get(`/analysis/${id}`)
  return data
}

export function camDownloadUrl(id) {
  return `/api/cam/${id}`
}
