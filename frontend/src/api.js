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

  const { data } = await api.post('/analyse', form, { timeout: 120_000 })
  return { analysis_id: data.analysis_id, data: data.data }
}

export async function getAnalysis(id) {
  const { data } = await api.get(`/analysis/${id}`)
  return data
}

export function camDownloadUrl(id) {
  return `/api/cam/${id}`
}
