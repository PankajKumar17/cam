import axios from 'axios'

// In production (Render+Vercel) VITE_API_BASE_URL is not needed because
// vercel.json rewrites /api/* → Render backend. Setting it overrides that.
const api = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL || '/api' })

export async function loadDemo() {
  const { data } = await api.post('/demo')
  return data
}

export async function analyse(companyName, file, { ceoAudio = null, ceoTranscript = '' } = {}) {
  const form = new FormData()
  form.append('company_name', companyName)
  form.append('file', file)
  if (ceoAudio) form.append('ceo_audio', ceoAudio)
  if (ceoTranscript && ceoTranscript.trim()) form.append('ceo_transcript', ceoTranscript.trim())
  const { data } = await api.post('/analyse', form)
  return data
}

export async function getAnalysis(id) {
  const { data } = await api.get(`/analysis/${id}`)
  return data
}

export function camDownloadUrl(id) {
  return `/api/cam/${id}`
}
