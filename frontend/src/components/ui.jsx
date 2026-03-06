export function Card({ children, className = '', ...props }) {
  return (
    <div
      className={`bg-white rounded-2xl border border-border shadow-[0_1px_4px_rgba(0,0,0,0.06),0_2px_12px_rgba(0,0,0,0.06)]
                  hover:shadow-[0_4px_16px_rgba(0,0,0,0.10),0_8px_32px_rgba(0,0,0,0.08)]
                  transition-shadow duration-200 p-6 ${className}`}
      {...props}
    >
      {children}
    </div>
  )
}

export function MetricCard({ label, value, subtitle, icon: Icon, variant = 'white' }) {
  const styles = {
    white: {
      bg: 'bg-white border border-border shadow-[0_1px_4px_rgba(0,0,0,0.06),0_2px_12px_rgba(0,0,0,0.06)]',
      label: 'text-text-muted', value: 'text-dark', sub: 'text-text-muted', icon: 'text-text-muted',
    },
    orange: {
      bg: 'bg-gradient-to-br from-orange to-orange-light shadow-[0_8px_32px_rgba(232,71,10,0.40)]',
      label: 'text-white/70', value: 'text-white', sub: 'text-white/60', icon: 'text-white/50',
    },
    dark: {
      bg: 'bg-dark shadow-[0_4px_16px_rgba(0,0,0,0.25)]',
      label: 'text-white/50', value: 'text-white', sub: 'text-white/40', icon: 'text-white/30',
    },
  }
  const s = styles[variant] || styles.white

  return (
    <div className={`${s.bg} rounded-2xl p-6 relative font-[DM_Sans]`}>
      {Icon && (
        <span className={`absolute top-6 right-6 ${s.icon}`}>
          <Icon size={20} />
        </span>
      )}
      <p className={`text-[11px] font-semibold uppercase tracking-[1.5px] ${s.label} mb-2`}>
        {label}
      </p>
      <p className={`text-[32px] font-bold ${s.value} leading-tight`}>{value}</p>
      {subtitle && <p className={`text-xs ${s.sub} mt-1.5`}>{subtitle}</p>}
    </div>
  )
}

export function SignalCard({ name, detail, level = 'GREEN' }) {
  const colorMap = { GREEN: '#10B981', AMBER: '#F59E0B', RED: '#EF4444' }
  const bgMap = { GREEN: 'bg-success-bg', AMBER: 'bg-warning-bg', RED: 'bg-danger-bg' }
  const textMap = { GREEN: 'text-success', AMBER: 'text-warning', RED: 'text-danger' }
  const color = colorMap[level] || '#9CA3AF'

  return (
    <div
      className="bg-white border border-border rounded-[14px] p-4 mb-2.5
                 hover:-translate-y-0.5 hover:shadow-[0_4px_16px_rgba(0,0,0,0.08)]
                 transition-all duration-150"
      style={{ borderLeft: `4px solid ${color}` }}
    >
      <div className="flex justify-between items-center mb-1.5">
        <span className="text-xs font-semibold text-text-secondary">{name}</span>
        <span className={`text-[11px] font-semibold px-2.5 py-0.5 rounded-full ${bgMap[level] || 'bg-surface-row'} ${textMap[level] || 'text-text-muted'}`}>
          {level}
        </span>
      </div>
      <p className="text-[13px] font-medium text-dark">{detail}</p>
    </div>
  )
}

export function Badge({ text, color, bg }) {
  return (
    <span
      className="inline-block px-2.5 py-1 rounded-full text-[11px] font-semibold"
      style={{ background: bg, color }}
    >
      {text}
    </span>
  )
}

export function SectionHeader({ title, subtitle }) {
  return (
    <div className="mt-8 mb-4">
      <h2 className="text-[22px] font-semibold text-dark">{title}</h2>
      {subtitle && <p className="text-sm text-text-secondary mt-1">{subtitle}</p>}
    </div>
  )
}

export function EmptyState({ icon: Icon, title, subtitle }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-3">
      <div className="w-12 h-12 rounded-full bg-surface-row flex items-center justify-center">
        <Icon className="w-6 h-6 text-text-placeholder" />
      </div>
      <p className="text-sm font-semibold text-text-secondary">{title}</p>
      {subtitle && <p className="text-xs text-text-muted max-w-xs text-center">{subtitle}</p>}
    </div>
  )
}

export function DataTable({ headers, rows, colAlign }) {
  const align = colAlign || headers.map(() => 'left')
  return (
    <div className="bg-white rounded-2xl border border-border shadow-[0_1px_4px_rgba(0,0,0,0.06)] overflow-hidden">
      <table className="w-full border-collapse">
        <thead>
          <tr className="bg-surface-row border-b border-border">
            {headers.map((h, i) => (
              <th key={i} className="px-5 py-3 text-xs font-semibold uppercase tracking-wider text-text-muted"
                  style={{ textAlign: align[i] }}>
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, ri) => (
            <tr key={ri} className="border-b border-border-divider last:border-0 hover:bg-orange-pale/30 transition-colors duration-100">
              {row.map((cell, ci) => (
                <td key={ci} className="px-5 py-3.5 text-sm text-dark" style={{ textAlign: align[ci] }}>
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
