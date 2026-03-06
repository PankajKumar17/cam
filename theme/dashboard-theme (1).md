# dashboard-theme.md
# Intelli-Credit — Full Dashboard Design Theme
# Stack: Vite + React + Tailwind CSS + Framer Motion + Recharts/Plotly.js
# 6 Pages: Overview · Upload · Signals · Deep Dive · Reports · CAM

---

## SECTION A — GLOBAL DESIGN SYSTEM

### A1. TAILWIND THEME EXTENSION

```js
// tailwind.config.js
module.exports = {
  content: ['./src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    fontFamily: {
      dm:    ['DM Sans', 'sans-serif'],
      serif: ['DM Serif Display', 'serif'],
      mono:  ['DM Mono', 'monospace'],
    },
    extend: {
      colors: {
        orange: {
          DEFAULT: '#E8470A', light: '#FF6B35',
          pale: '#FFF7F4', border: '#F5C4B0', hover: '#C73D08',
        },
        surface: { page: '#F4F5F7', card: '#FFFFFF',
                   hover: '#F9FAFB', row: '#FAFAFA' },
        dark:    { DEFAULT: '#1A1A1A', hover: '#2D2D2D' },
        border:  { DEFAULT: '#E5E7EB', strong: '#D1D5DB',
                   divider: '#F3F4F6' },
        text:    { primary: '#1A1A1A', secondary: '#6B7280',
                   muted: '#9CA3AF', placeholder: '#D1D5DB' },
        success: { DEFAULT: '#10B981', bg: '#ECFDF5' },
        warning: { DEFAULT: '#F59E0B', bg: '#FFFBEB' },
        danger:  { DEFAULT: '#EF4444', bg: '#FEF2F2' },
        info:    { DEFAULT: '#3B82F6', bg: '#EFF6FF' },
      },
      boxShadow: {
        card:         '0 1px 4px rgba(0,0,0,0.06), 0 2px 12px rgba(0,0,0,0.06)',
        'card-hover': '0 4px 16px rgba(0,0,0,0.10), 0 8px 32px rgba(0,0,0,0.08)',
        orange:       '0 4px 16px rgba(232,71,10,0.30)',
        'orange-lg':  '0 8px 32px rgba(232,71,10,0.40)',
        focus:        '0 0 0 3px rgba(232,71,10,0.15)',
        dark:         '0 4px 16px rgba(0,0,0,0.25)',
        modal:        '0 24px 64px rgba(0,0,0,0.18)',
      },
      borderRadius: { '2xl': '20px', '3xl': '24px' },
      animation: {
        'spin-slow':  'spin 1.4s linear infinite',
        'shimmer':    'shimmer 1.4s ease-in-out infinite',
        'count-up':   'countUp 1.2s ease-out forwards',
      },
      keyframes: {
        shimmer: {
          '0%':   { backgroundPosition: '-400px 0' },
          '100%': { backgroundPosition: '400px 0' },
        },
      },
    },
  },
}
```

---

### A2. APP SHELL LAYOUT

```
Root layout: flex flex-col h-screen overflow-hidden bg-surface-page

┌──────────────────────────────────────────────────────────────┐
│  NAVBAR  h-16  sticky top-0 z-50  bg-white                   │
│          border-b border-border shadow-sm                     │
├─────────┬────────────────────────────────────────────────────┤
│         │                                                     │
│ SIDEBAR │  MAIN CONTENT                                       │
│  w-16   │  flex-1 overflow-y-auto                            │
│  bg-    │  padding: p-6                                      │
│  white  │                                                     │
│  border-│                                                     │
│  r      │                                                     │
└─────────┴────────────────────────────────────────────────────┘

NAVBAR JSX structure:
<nav className="h-16 bg-white border-b border-border flex items-center
                justify-between px-6 sticky top-0 z-50">

  {/* LEFT */}
  <div className="flex items-center gap-3">
    <div className="w-9 h-9 rounded-full bg-gradient-to-br from-orange
                    to-orange-light flex items-center justify-center
                    shadow-orange text-white font-bold text-sm">IC</div>
    <span className="font-dm font-semibold text-lg text-dark">
      Intelli-Credit
    </span>
    <div className="w-px h-5 bg-border mx-1" />
    {/* Company name pill — from app state */}
    <span className="bg-orange-pale border border-orange-border text-orange
                     text-xs font-semibold px-3 py-1 rounded-full">
      {companyName}
    </span>
  </div>

  {/* CENTER TABS */}
  <nav className="flex items-center gap-1">
    {tabs.map(tab => (
      <Link key={tab.path} to={tab.path}
        className={`px-4 py-2 rounded-full text-sm font-medium transition-all
          ${isActive ? 'bg-dark text-white' : 'text-text-secondary
            hover:text-dark hover:bg-surface-hover'}`}>
        {tab.label}
      </Link>
    ))}
  </nav>

  {/* RIGHT */}
  <div className="flex items-center gap-4">
    <button><Search className="w-5 h-5 text-text-muted hover:text-dark" /></button>
    <button className="relative">
      <Bell className="w-5 h-5 text-text-muted" />
      {hasAlerts && <span className="absolute -top-1 -right-1 w-2 h-2
                                     bg-orange rounded-full" />}
    </button>
    <div className="w-9 h-9 rounded-full bg-orange flex items-center
                    justify-center text-white text-sm font-semibold">
      {analystInitials}
    </div>
  </div>
</nav>

SIDEBAR icon list (top-to-bottom):
  /overview     — LayoutDashboard
  /upload       — Upload
  /signals      — Shield
  /deep-dive    — TrendingUp
  /reports      — FileText
  /cam          — BookOpen
  ── divider ──
  /settings     — Settings  (bottom)
  /logout       — LogOut    (bottom)

Each icon button:
  w-10 h-10 rounded-xl flex items-center justify-center mx-auto
  active:   bg-orange-pale text-orange
  hover:    bg-surface-hover text-dark
  inactive: text-text-muted
  Tooltip: on hover, right-side, bg-dark text-white text-xs px-2.5 py-1
           rounded-lg shadow-dark
```

---

### A3. CARD COMPONENT

```jsx
// Base card — use everywhere
<div className="bg-white rounded-2xl border border-border shadow-card
                hover:shadow-card-hover transition-shadow duration-200 p-6">
```

---

### A4. METRIC CARD VARIANTS

```jsx
// WHITE metric card
<div className="bg-white rounded-2xl border border-border shadow-card p-6">
  <div className="flex items-center justify-between">
    <span className="text-xs font-semibold uppercase tracking-wider
                     text-text-muted">{label}</span>
    <Icon className="w-5 h-5 text-text-muted" />
  </div>
  <p className="text-3xl font-bold text-dark mt-3 font-dm">{value}</p>
  <div className="flex items-center gap-2 mt-2">
    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full
      ${positive ? 'bg-success-bg text-success' : 'bg-danger-bg text-danger'}`}>
      {trend}
    </span>
    <span className="text-xs text-text-muted">{context}</span>
  </div>
</div>

// ORANGE hero card
<div className="bg-gradient-to-br from-orange to-orange-light rounded-2xl
                shadow-orange-lg p-6 text-white">
  ...same structure, all text white, badge: bg-white/20 text-white...
</div>

// DARK card
<div className="bg-dark rounded-2xl shadow-dark p-6 text-white">
  ...same structure, badge: bg-white/15 text-white...
</div>
```

---

### A5. STATUS & RISK BADGES

```jsx
// Status badge
const statusMap = {
  completed:   'bg-success-bg text-success',
  pending:     'bg-warning-bg text-warning',
  'in-progress':'bg-info-bg text-info',
  failed:      'bg-danger-bg text-danger',
  flagged:     'bg-[#FEF9C3] text-[#854D0E]',
}
<span className={`text-xs font-semibold px-2.5 py-1 rounded-full
                  flex items-center gap-1.5 ${statusMap[status]}`}>
  <span className="w-1.5 h-1.5 rounded-full bg-current" />
  {label}
</span>

// Risk badge (with left border)
const riskMap = {
  HIGH:   'bg-danger-bg  text-[#DC2626] border-l-[3px] border-[#DC2626]',
  MEDIUM: 'bg-warning-bg text-[#EA580C] border-l-[3px] border-[#EA580C]',
  LOW:    'bg-success-bg text-[#16A34A] border-l-[3px] border-[#16A34A]',
}
<span className={`text-xs font-semibold px-2.5 py-1 rounded-r-lg
                  ${riskMap[level]}`}>{level}</span>
```

---

### A6. DATA TABLE

```jsx
<div className="bg-white rounded-2xl border border-border shadow-card overflow-hidden">
  {/* Search + Filter header */}
  <div className="flex items-center justify-between px-5 py-4
                  border-b border-divider">
    <div className="relative">
      <Search className="absolute left-3 top-1/2 -translate-y-1/2
                         w-4 h-4 text-text-muted" />
      <input placeholder="Search..." className="pl-9 pr-4 h-9 rounded-xl
               border border-border text-sm focus:border-orange
               focus:shadow-focus outline-none w-60" />
    </div>
    <button className="flex items-center gap-2 px-3 py-2 rounded-xl
                        border border-border text-sm text-text-secondary
                        hover:bg-surface-hover">
      <Filter className="w-4 h-4" /> Filter
    </button>
  </div>
  <table className="w-full">
    <thead>
      <tr className="bg-surface-row border-b border-border">
        <th className="text-left px-5 py-3 text-xs font-semibold uppercase
                       tracking-wider text-text-muted">{col}</th>
      </tr>
    </thead>
    <tbody>
      {rows.map((row, i) => (
        <tr key={i} className="border-b border-divider last:border-0
                                hover:bg-orange-pale/30 transition-colors
                                duration-100 cursor-pointer">
          <td className="px-5 py-3.5 text-sm text-dark">{cell}</td>
        </tr>
      ))}
    </tbody>
  </table>
</div>
```

---

### A7. CHART DEFAULTS (Recharts)

```jsx
// All charts share these defaults
const chartDefaults = {
  fontFamily: 'DM Sans',
  fontSize: 11,
  colors: {
    primary:   '#E8470A',
    secondary: '#1A1A1A',
    success:   '#10B981',
    danger:    '#EF4444',
    muted:     '#9CA3AF',
    grid:      '#F3F4F6',
  },
}

// CartesianGrid
<CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" vertical={false} />

// Axes
<XAxis tick={{ fill: '#9CA3AF', fontSize: 11, fontFamily: 'DM Sans' }}
       axisLine={false} tickLine={false} />
<YAxis tick={{ fill: '#9CA3AF', fontSize: 11 }} axisLine={false}
       tickLine={false} />

// Tooltip
<Tooltip
  contentStyle={{
    background: '#1A1A1A', border: 'none', borderRadius: 8,
    color: '#fff', fontSize: 12, fontFamily: 'DM Sans',
    padding: '8px 12px', boxShadow: '0 4px 16px rgba(0,0,0,0.25)'
  }}
  cursor={{ stroke: '#E8470A', strokeWidth: 1, strokeDasharray: '3 3' }}
/>
```

---

### A8. SKELETON LOADER

```jsx
// Shimmer skeleton — replace any loading card
const Skeleton = ({ className }) => (
  <div className={`animate-shimmer bg-gradient-to-r
    from-border via-surface-hover to-border
    bg-[length:800px_100%] rounded-xl ${className}`} />
)

// Usage
{isLoading ? <Skeleton className="h-8 w-32 mt-3" /> : <p>{value}</p>}
```

---

### A9. EMPTY STATE

```jsx
const EmptyState = ({ icon: Icon, title, subtitle, action }) => (
  <div className="flex flex-col items-center justify-center py-16 gap-3">
    <div className="w-12 h-12 rounded-full bg-surface-row flex items-center
                    justify-center">
      <Icon className="w-6 h-6 text-text-placeholder" />
    </div>
    <p className="text-sm font-semibold text-text-secondary">{title}</p>
    <p className="text-xs text-text-muted max-w-xs text-center">{subtitle}</p>
    {action && (
      <button className="mt-2 text-sm font-semibold text-orange
                          hover:underline">{action.label}</button>
    )}
  </div>
)
```

---

## SECTION B — PAGE THEMES

---

### PAGE 1 — /overview

```
GREETING (no card, bare page top):
  "Good morning, Analyst"      font-serif text-3xl text-dark
  "[Company Name] · Analysis ready · [date]"  text-sm text-muted mt-1
  Framer: fade-up 0.4s on mount

ROW 1 — 4 metric cards  (grid grid-cols-4 gap-4 mt-6)
  Card 1: DARK    — "LENDING DECISION"   value: CONDITIONAL / APPROVE / REJECT
  Card 2: ORANGE  — "PD SCORE"           value: [%] from ensemble
  Card 3: WHITE   — "CREDIT LIMIT"       value: ₹[X] Cr   (success tint)
  Card 4: WHITE   — "RISK PREMIUM"       value: [X]% p.a. (warning tint)

  Real data only. If not computed: show "—" with muted style.
  Framer: staggerChildren 0.06s, each card: opacity 0→1 + y 12→0

ROW 2 — grid grid-cols-[1.1fr_1fr_1fr] gap-4 mt-4

  LEFT CARD: "Borrower Profile"
    Company name: text-lg font-semibold text-dark
    2-col detail rows: (label: muted 11px uppercase | value: 13px dark)
      Sector | Location | Loan Ask | Tenor | Years of Data
    Bottom: 3 KPI tiles (grid grid-cols-3 gap-2 mt-4 border-t pt-4)
      Each tile: bg-surface-row rounded-xl p-3 text-center
        value: text-lg font-bold [risk-colored]
        label: text-xs text-muted mt-0.5
      KPIs: DSCR | D/E Ratio | ICR
    Empty if field missing: show "—"

  CENTER CARD: "Key Ratios"  (2×2 grid gap-2)
    Each cell: bg-surface-row rounded-xl p-3
      label: 11px uppercase muted
      value: 20px bold, colored by risk
      trend arrow + delta: 12px
    Cells: Revenue | EBITDA Margin | Current Ratio | Net Profit Margin
    Computed from uploaded data only

  RIGHT CARD: "DSCR Trajectory"
    Subtitle: "Trend across available years"
    Recharts LineChart (responsive, height 160px)
      Line: stroke #E8470A strokeWidth 2.5
      Dot: fill white stroke #E8470A strokeWidth 2 r 4
      Reference line at y=1.25: stroke #F59E0B strokeDasharray "4 2"
      Reference line at y=1.0: stroke #EF4444 strokeDasharray "4 2"
      No X-axis line, no Y-axis line, subtle grid
    Bottom stat row (flex justify-between mt-3):
      "P50 Stress: [val]" badge-blue | "P10 Worst: [val]" badge-red

ROW 3 — grid grid-cols-[0.9fr_1.1fr] gap-4 mt-4

  LEFT CARD: "Model Ensemble"  (Monthly Spending Limit equivalent)
    Title + "PD breakdown" subtitle
    4 rows:
      Each row: label (13px) | bar track (flex-1 mx-3 h-2 bg-border
                rounded-full) | fill (bg-orange) | % value (font-mono 13px)
      XGBoost:    44%  |  LightGBM: 43%  |  RF: 38%  |  Ensemble: 42% (bold)
      Ensemble row: label bold + value bold + bar slightly taller (h-2.5)
    Animated: bar fills left-to-right on mount (CSS width transition 800ms)

  RIGHT CARD: "Signal Dashboard"  (Recent Activities equivalent)
    Title + Search + Filter row
    Table: Signal | Value | Status | Risk | —
    Columns widths: auto | font-mono 13px | badge | badge | —
    6 signals (only show if computed):
      Beneish M-Score | DSCR Velocity | GST Divergence
      Default DNA | Covenant Breach | Satellite Score
    Empty rows if signal not run: "—" in muted italic, no fake data
    "View all signals →" orange text link at bottom right
```

---

### PAGE 2 — /upload

```
HEADER (no card):
  "Upload Financial Statements"   text-2xl font-semibold
  "Submit documents for AI processing"  text-sm text-muted mt-1

GRID grid-cols-[1.1fr_0.9fr] gap-6 mt-6

  LEFT: UPLOAD CARD (same as landing page upload card)
    bg-white rounded-2xl border shadow-card p-8
    Company name input (pre-filled from state, editable)
    PDF dropzone (same styling as landing)
    "Re-Analyse" button (orange gradient)

  RIGHT: UPLOAD HISTORY CARD
    Title: "Session Uploads"
    Table: File Name | Size | Time | Status | —
    Only real files. If none: EmptyState component
      icon: FolderOpen
      title: "No files yet"
      subtitle: "Uploaded files appear here"

BELOW: PROCESSING TIMELINE CARD (full width, mt-4)
  3 step pills in a row:
  [✓ Uploaded] ──── [✓ Processing] ──── [○ Decision Ready]
  
  Completed: bg-success-bg border border-success text-success
             CheckCircle icon 16px
  Active:    bg-info-bg border border-info text-info
             Loader2 icon animate-spin 16px
  Pending:   bg-surface-row border border-border text-text-muted
             Circle icon 16px
  Connector: flex-1 h-px bg-border mx-2 (line between pills)
```

---

### PAGE 3 — /signals

```
HEADER:
  "Credit Signals"
  "All AI-computed risk indicators for [Company Name]"

TOP STRIP: grid grid-cols-3 gap-4 mt-4
  HIGH RISK count:    bg-danger-bg  border-l-4 border-danger  rounded-2xl p-5
  MEDIUM RISK count:  bg-warning-bg border-l-4 border-warning rounded-2xl p-5
  LOW RISK count:     bg-success-bg border-l-4 border-success rounded-2xl p-5
  Each: count (28px bold risk-colored) + "signals" label (12px muted)
  Counts computed from actual results, not hardcoded

SIGNAL GRID: grid grid-cols-2 gap-4 mt-4
  (3 columns on 1440px+:  xl:grid-cols-3)

  Each signal card:
    bg-white rounded-2xl shadow-card border-l-4 [risk-border-color] p-5
    hover:shadow-card-hover transition-all duration-200

    Row 1 (flex justify-between):
      Left:  signal name  text-sm font-semibold text-dark
             category pill  bg-surface-row text-muted text-xs px-2 py-0.5
      Right: <RiskBadge level="HIGH|MEDIUM|LOW" />

    Value:  text-2xl font-bold font-mono [risk-colored] mt-3
    Unit:   inline text-sm text-muted ml-1 (e.g. "/yr", "%", "/100")

    Interpretation: text-xs text-text-secondary mt-1.5 leading-relaxed
                    max 2 lines, line-clamp-2

    Footer: "Computed [datetime]"  text-xs text-text-muted mt-3

    NOT COMPUTED STATE:
      Border-color: #E5E7EB (default border, not risk)
      Value: "—"  text-text-muted
      Interpretation: "Requires [data source]"  italic text-text-muted
      Footer: "Not run"

  17 SIGNALS (in order):
  01 Beneish M-Score         category: FORENSICS
  02 DSCR Velocity           category: TRAJECTORY
  03 Promoter Pledge %       category: STRUCTURE
  04 GST Divergence          category: ALT DATA
  05 Default DNA             category: SIMILARITY
  06 Satellite Activity      category: ALT DATA
  07 Network Contagion       category: NETWORK
  08 Altman Z-Score          category: FORENSICS
  09 Piotroski F-Score       category: FORENSICS
  10 Interest Coverage Ratio category: RATIOS
  11 Auditor Signal          category: QUALITATIVE
  12 CEO Sentiment           category: QUALITATIVE
  13 Model Disagreement      category: ML
  14 ESG Score               category: SUSTAINABILITY
  15 Covenant Breach Prob    category: RISK
  16 CFaR-95%                category: STRESS
  17 Counterfactual Gaps     category: ADVISORY
```

---

### PAGE 4 — /deep-dive

```
HEADER:
  "Deep Dive Analysis"
  "Visual breakdown for [Company Name]"

TABS row (below header, mt-4):
  [Financial] [Forensics] [Alt Data] [Stress Test] [Agents]
  Tab style: underline variant — not pills
  Active: border-b-2 border-orange text-dark font-semibold
  Inactive: text-text-secondary hover:text-dark
  Each tab reveals different chart set below

── TAB: FINANCIAL ───────────────────────────────────────────

  LARGE CHART CARD (full width): "Revenue & DSCR History"
    ResponsiveContainer height 280px
    ComposedChart:
      Bar: Revenue each year  fill #E8470A opacity 0.8  (left Y-axis)
      Line: DSCR each year    stroke #1A1A1A strokeWidth 2.5  (right Y-axis)
      ReferenceLine y=1.25 stroke #F59E0B label "Covenant"
      ReferenceLine y=1.0  stroke #EF4444 label "Danger"
    Empty state if < 2 years data: EmptyState with BarChart2 icon

  GRID grid-cols-3 gap-4 mt-4:
    Card: EBITDA Margin trend  — AreaChart, fill orange, low opacity
    Card: D/E Ratio progression— LineChart, stroke dark
    Card: Current Ratio        — BarChart horizontal, single series

── TAB: FORENSICS ───────────────────────────────────────────

  GRID grid-cols-[1.2fr_0.8fr] gap-4:
    LEFT: Beneish 8-Component breakdown
      8 component bars (horizontal):
        DSRI | GMI | AQI | SGI | DEPI | SGAI | TATA | LVGI
        Each bar: label | fill bar (#E8470A) | value (mono)
        Threshold line: vertical dashed at expected value
    RIGHT: Z-Score + F-Score gauges
      Each: circular arc gauge (SVG or Recharts RadialBar)
      Z-Score: colored by zone (green/yellow/red)
      F-Score: 0-9 bar with orange fill

── TAB: ALT DATA ────────────────────────────────────────────

  GRID grid-cols-2 gap-4:
    Card: Default DNA Similarity
      6 horizontal bars (one per known default)
      Highlighted bar (highest match): orange + bold
      Warning strip if any > 65%: amber border + text

    Card: Revenue vs GST (Grouped Bar)
      GroupedBar per year: declared revenue (orange) vs GSTN (dark)
      Divergence % annotated above each group pair
      Empty if no GST data

  GRID grid-cols-2 gap-4 mt-4:
    Card: Satellite Activity Score
      Single large gauge: 0-100 arc
      Color zones: 0-40 red | 41-70 amber | 71-100 green
      Current value large in center
    Card: Auditor & CEO Signals
      2 rows with icon + label + value pill each
      Auditor Opinion | CEO Sentiment Score
      Plain card, no chart needed

── TAB: STRESS TEST ─────────────────────────────────────────

  GRID grid-cols-[1.3fr_0.7fr] gap-4:
    LEFT: Monte Carlo Distribution
      ResponsiveContainer height 260px
      BarChart (histogram bins)
        fill #E8470A
        ReferenceLine P10: stroke #EF4444 strokeDasharray "4 2"
        ReferenceLine P50: stroke #F59E0B strokeDasharray "4 2"
        ReferenceLine P90: stroke #10B981 strokeDasharray "4 2"
        ReferenceArea x=min to x=1.0: fill #FEF2F2 (danger zone)
      Below chart: 3 stat pills (P10 | P50 | P90) colored red/amber/green

    RIGHT: Scenario Breakdown
      4 named scenario cards stacked:
        Base Case | Rate +200bps | Revenue -20% | Combined Adverse
        Each: name + DSCR outcome + "PASS/FAIL" badge
        bg-surface-row rounded-xl p-3

── TAB: AGENTS ──────────────────────────────────────────────

  2-column card:
    LEFT PANEL: "Bull Case"
      border-l-4 border-success bg-success-bg/30 p-5
      title: "Approve" text-success font-semibold
      Bullet points from LLM bull agent (real output)
      Empty: EmptyState (MessageSquare icon, "Run LLM agents")

    RIGHT PANEL: "Bear Case"
      border-l-4 border-danger bg-danger-bg/30 p-5
      title: "Reject" text-danger font-semibold
      Counter-points from bear agent (real output)

  Coordinator verdict card (below, full width):
    bg-dark text-white rounded-2xl p-5
    "Coordinator Verdict"  text-xs uppercase orange tracking-wider
    Verdict text: text-base leading-relaxed
    Empty: show "—"
```

---

### PAGE 5 — /reports

```
HEADER:
  "Reports & Downloads"
  "Export credit decision documents for [Company Name]"

DECISION BANNER (full width):
  bg-dark rounded-2xl p-8 flex items-center justify-between
  LEFT:
    "FINAL LENDING DECISION"  text-xs uppercase orange tracking-wider
    Decision value: text-4xl font-bold text-white mt-2
                    APPROVE → text-success | CONDITIONAL → text-warning
                    REJECT  → text-danger
    Summary: "₹[X] Cr at [Y]% with [Z] conditions"  text-base text-muted mt-2

  RIGHT: button stack (flex flex-col gap-3)
    [↓ Download CAM (DOCX)]   orange gradient button w-52
    [↓ Export Signals (PDF)]  white outline button w-52
    [↓ Raw Data (JSON)]       ghost button w-52

GRID grid-cols-2 gap-4 mt-4:
  LEFT: "Lending Conditions"
    List of real conditions from coordinator output
    Each condition: flex items-start gap-3
      CheckCircle icon (orange 16px) + condition text (14px dark)
    border-l-3 orange on each item
    Empty: "No conditions — clean approval" success state

  RIGHT: "Path to Improvement" (Counterfactual)
    Table: Step | Action | Current | Target | ΔPD
    Rows from counterfactual engine output
    ΔPD column: text-success font-semibold
    Footer badge: feasibility level
    Empty: "Already strong profile" or "Data not available"

TIMELINE CARD (full width, mt-4):
  "Monitoring Milestones"
  Horizontal scroll timeline (or vertical list on mobile)
  Each milestone: dot + vertical line + date + action text
  dot colors: orange (< 30 days) | info (30-90) | muted (> 90)
  Empty: EmptyState (Calendar icon)
```

---

### PAGE 6 — /cam

```
HEADER:
  "Credit Appraisal Memo"
  Left: "[Company Name]  ·  Generated [datetime]"  text-sm text-muted
  Right: [Download DOCX] orange button

DOCUMENT VIEWER:
  max-w-3xl mx-auto mt-6
  bg-white rounded-2xl border shadow-card
  padding: p-12  (document feel)

  Sticky section navigator (right side, fixed at 1280px+):
    Thin vertical list of section names, 12px
    Active: text-orange font-semibold
    Inactive: text-text-muted hover:text-dark

  10 SECTIONS (rendered as HTML, scroll-based):
  Each section:
    Section header: text-xl font-semibold text-dark pb-3
                    border-b-2 border-divider mb-5
    Content: text-sm text-dark leading-7

    Tables within sections:
      table-fixed w-full text-sm
      th: bg-surface-row font-semibold text-text-muted uppercase text-xs
          tracking-wider px-4 py-3
      td: px-4 py-3 border-b border-divider

  Sections:
  1. Executive Summary
  2. Company Background
  3. Financial Analysis
  4. Forensics Summary
  5. Network Risk
  6. Stress Testing
  7. Alternative Data
  8. Management Quality
  9. Bull vs Bear Analysis
  10. Final Recommendation

  If section has no data:
    <p className="text-sm italic text-text-muted py-4">
      Data not available for this section.
    </p>
```

---

## SECTION C — PROCESSING STATES

```
GLOBAL ANALYSIS BANNER (shows while backend is running):
  Fixed top-[64px] (below navbar) w-full z-40
  bg-orange-pale border-b border-orange-border
  flex items-center gap-3 px-6 py-2.5

  Loader2 (animate-spin text-orange w-4 h-4)
  "Analysing [Company Name]..."  text-sm font-medium text-dark
  Current stage: "Running Beneish forensics..."  text-xs text-text-muted ml-1
  Thin progress bar (3px) at very bottom: orange fill, animates 0→100%

COMPLETION TOAST (bottom-right, Framer slide-in):
  bg-dark text-white rounded-xl shadow-dark p-4
  border-l-4 border-success
  "✓ Analysis complete"  text-sm font-semibold
  "[Company Name] · 17 signals computed"  text-xs text-muted
  auto-dismiss 4s

ERROR TOAST:
  same position
  border-l-4 border-danger
  "Analysis failed — [error reason]"  text-danger
  Retry button: text-orange text-xs font-semibold
```

---

## SECTION D — DO NOT / NEVER

```
❌ NEVER show hardcoded or fake numbers in any component
❌ NEVER render a chart with random/sample data — show EmptyState instead
❌ NEVER use dark-bg pages — the app is strictly light-themed
❌ NEVER use purple anywhere — orange (#E8470A) is the only brand accent
❌ NEVER use Inter, Roboto, or system fonts — use DM Sans only
❌ NEVER skip the loading skeleton on any async data fetch
❌ NEVER use pie charts — bar, line, area, donut only
❌ NEVER use table borders on every cell — horizontal row dividers only
❌ NEVER center body/paragraph text — left-align all content
❌ NEVER put underlines under section headings
❌ NEVER make buttons less than 44px tall (accessibility minimum)
❌ NEVER show partial states — if data partially loaded, show full skeleton
❌ NEVER hardcode company name — always read from app state / route params
❌ NEVER show signals that were not computed — show "not run" state instead
```
