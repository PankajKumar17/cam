/* Shared helper – safe nested access */
export function g(data, ...keys) {
  let current = data
  for (const key of keys) {
    if (current && typeof current === 'object') {
      current = current[key]
    } else {
      return undefined
    }
  }
  return current ?? undefined
}

export function fmt(value, decimals = 2, prefix = '', suffix = '') {
  if (value == null || value === 'N/A') return 'N/A'
  const n = parseFloat(value)
  if (isNaN(n)) return String(value)
  return `${prefix}${n.toFixed(decimals)}${suffix}`
}

export function pct(value, decimals = 1) {
  if (value == null || value === 'N/A') return 'N/A'
  const n = parseFloat(value)
  if (isNaN(n)) return String(value)
  return `${(n * 100).toFixed(decimals)}%`
}

export function riskLevel(value, good, warn, higherIsBetter = true) {
  const v = parseFloat(value)
  if (isNaN(v)) return 'GREY'
  if (higherIsBetter) return v >= good ? 'GREEN' : v >= warn ? 'AMBER' : 'RED'
  return v <= good ? 'GREEN' : v <= warn ? 'AMBER' : 'RED'
}

export const RISK_COLORS = {
  GREEN: '#10B981', AMBER: '#F59E0B', RED: '#EF4444', LOW: '#10B981',
  MEDIUM: '#F59E0B', HIGH: '#EF4444', GREY: '#9CA3AF',
}

export const RISK_BG = {
  GREEN: '#ECFDF5', AMBER: '#FFFBEB', RED: '#FEF2F2',
  LOW: '#ECFDF5', MEDIUM: '#FFFBEB', HIGH: '#FEF2F2', GREY: '#F9FAFB',
}

export const DECISION_COLORS = {
  APPROVE: '#10B981', CONDITIONAL_APPROVE: '#F59E0B',
  REJECT: '#EF4444', REVIEW: '#9CA3AF',
}
