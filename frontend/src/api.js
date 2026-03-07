import axios from 'axios'

// In production (Render+Vercel) VITE_API_BASE_URL is not needed because
// vercel.json rewrites /api/* → Render backend. Setting it overrides that.
const api = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL || '/api' })

export async function loadDemo() {
  const { data } = await api.post('/demo')
  return data
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

  // Step 2 — poll every 3s until done or error
  while (true) {
    await new Promise(r => setTimeout(r, 3000))
    const { data: job } = await api.get(`/job/${job_id}`)
    if (job.status === 'done') {
      return { analysis_id: job.analysis_id, data: job.data }
    }
    if (job.status === 'error') {
      throw new Error(job.error || 'Pipeline failed')
    }
    // status === 'running' → keep polling
  }
}

export async function getAnalysis(id) {
  const { data } = await api.get(`/analysis/${id}`)
  return data
}

export function camDownloadUrl(id) {
  return `/api/cam/${id}`
}
