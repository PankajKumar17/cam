import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

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
