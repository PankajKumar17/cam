# Intelli-Credit — Dashboard Theme & All Pages
> Complete design system for the Intelli-Credit credit decisioning dashboard.
> Triggered after company name entry + file upload on the landing page.
> Reference: Finexy fintech dashboard — orange + white + near-black

---

## SECTION A — GLOBAL DESIGN SYSTEM

---

### A1. COLOR TOKENS

```css
:root {
  /* ── Backgrounds ── */
  --bg-page:          #F4F5F7;   /* entire app background */
  --bg-card:          #FFFFFF;   /* all card surfaces */
  --bg-row-alt:       #FAFAFA;   /* table alternating rows */
  --bg-sidebar:       #FFFFFF;   /* left icon sidebar */
  --bg-navbar:        #FFFFFF;   /* top navigation bar */

  /* ── Brand Orange ── */
  --orange:           #E8470A;   /* primary accent, CTAs, active nav */
  --orange-light:     #FF6B35;   /* gradient end, highlights */
  --orange-pale:      #FFF7F4;   /* card tint backgrounds */
  --orange-border:    rgba(232, 71, 10, 0.20);
  --orange-glow:      rgba(232, 71, 10, 0.15);
  --orange-hover:     #C73D08;

  /* ── Neutrals ── */
  --text-primary:     #1A1A1A;
  --text-secondary:   #6B7280;
  --text-muted:       #9CA3AF;
  --text-placeholder: #D1D5DB;
  --text-white:       #FFFFFF;
  --border:           #E5E7EB;
  --border-strong:    #D1D5DB;
  --divider:          #F3F4F6;

  /* ── Dark surfaces ── */
  --dark-card:        #1A1A1A;   /* dark metric cards */
  --dark-hover:       #2D2D2D;

  /* ── Semantic ── */
  --success:          #10B981;
  --success-bg:       #ECFDF5;
  --warning:          #F59E0B;
  --warning-bg:       #FFFBEB;
  --danger:           #EF4444;
  --danger-bg:        #FEF2F2;
  --info:             #3B82F6;
  --info-bg:          #EFF6FF;

  /* ── Risk levels ── */
  --risk-high:        #DC2626;
  --risk-high-bg:     #FEF2F2;
  --risk-med:         #EA580C;
  --risk-med-bg:      #FFF7ED;
  --risk-low:         #16A34A;
  --risk-low-bg:      #F0FDF4;
}
```

---

### A2. TYPOGRAPHY

```css
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600;700&display=swap');

--font-display: 'DM Serif Display', serif;   /* greeting H1 only */
--font-ui:      'DM Sans', sans-serif;       /* everything else */

/* Scale */
--type-greeting:   32px / 40px   700   DM Serif Display
--type-h2:         22px / 30px   600   DM Sans
--type-h3:         17px / 24px   600   DM Sans
--type-h4:         14px / 20px   600   DM Sans
--type-body:       14px / 22px   400   DM Sans
--type-small:      13px / 20px   400   DM Sans
--type-label:      11px / 16px   600   DM Sans  uppercase letter-spacing:1.5px
--type-metric:     32px / 40px   700   DM Sans  (big dashboard numbers)
--type-metric-sm:  22px / 28px   700   DM Sans
--type-code:       13px / 20px   500   DM Mono  (file names, IDs, scores)
```

---

### A3. SPACING & RADIUS

```css
--radius-sm:    8px    /* badges, small chips */
--radius-md:    12px   /* buttons, inputs */
--radius-lg:    16px   /* inner cards, feature tiles */
--radius-xl:    20px   /* main cards */
--radius-2xl:   24px   /* modal, large upload card */
--radius-pill:  999px  /* badges, nav pills */

--gap-xs:    8px
--gap-sm:    12px
--gap-md:    16px
--gap-lg:    24px
--gap-xl:    32px
--gap-2xl:   48px

--card-pad:      24px 28px
--section-pad:   24px
--page-pad:      24px
```

---

### A4. SHADOWS

```css
--shadow-card:        0 1px 4px rgba(0,0,0,0.06), 0 2px 12px rgba(0,0,0,0.06);
--shadow-card-hover:  0 4px 16px rgba(0,0,0,0.10), 0 8px 32px rgba(0,0,0,0.08);
--shadow-orange:      0 4px 16px rgba(232, 71, 10, 0.30);
--shadow-orange-lg:   0 8px 32px rgba(232, 71, 10, 0.40);
--shadow-dark:        0 4px 16px rgba(0, 0, 0, 0.25);
--shadow-focus:       0 0 0 3px rgba(232, 71, 10, 0.15);
--shadow-modal:       0 24px 64px rgba(0, 0, 0, 0.18);
```

---

### A5. COMPONENT LIBRARY

#### METRIC CARD (white)
```
border-radius:    var(--radius-xl)
padding:          24px 28px
background:       var(--bg-card)
border:           1px solid var(--border)
shadow:           var(--shadow-card)

label (top):      11px 600 uppercase muted, letter-spacing 1.5px
icon (top-right): 20px, color matches context
value:            32px 700 #1A1A1A, margin-top 8px
trend badge:
  ↑ positive:     background var(--success-bg), color var(--success), 12px 600
  ↓ negative:     background var(--danger-bg),  color var(--danger),  12px 600
  badge radius:   999px, padding 3px 8px
context text:     "This month" — 12px muted, margin-left 6px
```

#### METRIC CARD (orange hero)
```
background: linear-gradient(135deg, #E8470A 0%, #FF6B35 100%)
shadow: var(--shadow-orange-lg)
all text: white
trend badge: rgba(255,255,255,0.25) background, white text
icon: white
```

#### METRIC CARD (dark)
```
background: #1A1A1A
all text: white
trend badge: rgba(255,255,255,0.15) background, white text
border: none
shadow: var(--shadow-dark)
```

#### STATUS BADGE
```
Completed:   bg #ECFDF5   text #059669   dot #10B981
Pending:     bg #FFF7ED   text #C2410C   dot #F59E0B
In Progress: bg #EFF6FF   text #2563EB   dot #3B82F6
Failed:      bg #FEF2F2   text #DC2626   dot #EF4444
Flagged:     bg #FEF9C3   text #854D0E   dot #CA8A04

badge: border-radius 999px, padding 4px 10px, 11px 600
dot: 6px circle, display inline-block, margin-right 5px
```

#### RISK BADGE
```
HIGH:    bg #FEF2F2   text #DC2626   left-border 3px #DC2626
MEDIUM:  bg #FFF7ED   text #EA580C   left-border 3px #EA580C
LOW:     bg #F0FDF4   text #16A34A   left-border 3px #16A34A
border-radius: var(--radius-sm), padding: 4px 10px
```

#### DATA TABLE
```
Header row:
  background: #F9FAFB
  text: 12px 600 uppercase var(--text-muted), letter-spacing 0.5px
  height: 44px, border-bottom: 1px solid var(--border)

Data rows:
  height: 52px
  even rows: white / odd rows: #FAFAFA
  hover: background #FFF7F4 (orange tint), transition 120ms
  border-bottom: 1px solid var(--divider)

Checkbox:
  16px × 16px, border-radius 4px
  checked: background #E8470A, white tick
  hover border: #E8470A

Columns: left-aligned text, right-aligned numbers
ID col: DM Mono 13px #6B7280
```

#### BUTTON — PRIMARY (dark)
```
background: #1A1A1A
color: white
padding: 11px 22px
border-radius: var(--radius-md)
font: DM Sans 600 14px
hover: background #2D2D2D
active: scale(0.98)
transition: all 150ms ease
```

#### BUTTON — PRIMARY (orange)
```
background: linear-gradient(135deg, #E8470A, #FF6B35)
color: white
shadow: var(--shadow-orange)
hover: translateY(-1px), shadow: var(--shadow-orange-lg)
active: translateY(0)
```

#### BUTTON — SECONDARY
```
background: white
border: 1.5px solid var(--border-strong)
color: var(--text-primary)
hover: background #F9FAFB, border-color #E8470A, color #E8470A
```

#### BUTTON — GHOST
```
background: transparent
color: var(--text-secondary)
hover: background var(--divider), color var(--text-primary)
```

#### INPUT FIELD
```
height: 44px
border: 1.5px solid var(--border)
border-radius: var(--radius-md)
padding: 0 14px
font: DM Sans 14px
focus:
  border-color: var(--orange)
  box-shadow: var(--shadow-focus)
  outline: none
placeholder: var(--text-placeholder)
icon-left: padding-left 40px, icon positioned left 12px
```

#### PROGRESS BAR
```
track: background #F3F4F6, border-radius 999px, height 8px
fill:  background linear-gradient(90deg, #E8470A, #FF6B35)
       border-radius 999px, transition: width 800ms ease
label row: flex space-between, 13px muted, margin-bottom 8px
```

#### SIDEBAR ICON
```
container: 40px × 40px, border-radius 10px
active:   background #FFF0EB, icon color #E8470A
hover:    background #F9FAFB, icon color #374151
inactive: background transparent, icon color #9CA3AF
tooltip:  appears right on hover, white card, 12px, shadow
```

#### CHART DEFAULTS
```
library: Plotly (Python) or Recharts (React)
background: white card
plot area bg: white
grid lines: #F3F4F6, opacity 0.8
axis labels: 11px, color #9CA3AF
axis lines: none (just grid)
primary series: #E8470A
secondary series: #1A1A1A
tertiary: #3B82F6
success line: #10B981
danger zone: rgba(239,68,68,0.08) fill
tooltip: dark bg #1A1A1A, white text, border-radius 8px, padding 8px 12px
legend: 12px, color #6B7280
```

---

### A6. APP SHELL

```
┌──────────────────────────────────────────────────────────────┐
│  NAVBAR (64px, sticky, white, border-bottom 1px #F3F4F6)     │
├──────┬───────────────────────────────────────────────────────┤
│      │                                                        │
│ SIDE │   MAIN CONTENT (overflow-y scroll)                    │
│ BAR  │   padding: 24px                                       │
│      │   max inner width: no limit (uses CSS grid)           │
│ 64px │                                                        │
│ white│                                                        │
│      │                                                        │
└──────┴───────────────────────────────────────────────────────┘

NAVBAR contents:
├── Left: Logo (orange circle "IC" + "Intelli-Credit" 600 18px)
│         separator line (1px #E5E7EB)
│         Company name pill: "Sunrise Textile Mills" — #FFF7F4 bg,
│         #E8470A text, border-radius 999px, 13px 500
│
├── Center nav tabs (gap 4px):
│   Overview | Upload | Signals | Deep Dive | Reports | CAM
│   Active tab:   background #1A1A1A, text white,
│                 border-radius 999px, padding 8px 18px
│   Inactive tab: text #6B7280, hover text #1A1A1A
│
└── Right:
    Search icon (20px, #9CA3AF, hover #1A1A1A)
    Bell icon   (badge: orange dot if signals flagged)
    Info icon
    Avatar circle (initials, orange bg) + "Analyst" text + chevron

SIDEBAR icons (top to bottom):
  Overview (grid icon)     ← active on that page
  Upload (upload icon)
  Signals (shield icon)
  Deep Dive (chart icon)
  Reports (document icon)
  ── spacer ──
  Settings (gear icon)
  Help (? icon)
  Logout (exit icon)
```

---

## SECTION B — PAGE-BY-PAGE THEMES

---

### PAGE 1 — OVERVIEW

**Purpose:** Command centre. First thing analyst sees after upload completes.  
**Data shown:** Real data from the uploaded company only. No placeholders.

```
GREETING HEADER (no card, bare page):
  "Good morning, [Analyst Name]"  ← DM Serif Display 32px
  "[Company Name] analysis is ready · [date]"  ← 15px muted

ROW 1 — 4 METRIC CARDS (equal columns):
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ LENDING      │  │ PD SCORE     │  │ CREDIT LIMIT │  │ RISK PREMIUM │
│ DECISION     │  │  (ORANGE     │  │              │  │              │
│              │  │   CARD)      │  │              │  │              │
│ CONDITIONAL  │  │  42%         │  │  ₹10.5 Cr    │  │  12.75%      │
│ APPROVE      │  │  ↑ High Risk │  │  Recommended │  │  +160bps     │
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘

Card 1: dark card (#1A1A1A) — decision is most important
Card 2: orange card (hero gradient) — PD score highlighted
Card 3: white card, success-tinted value
Card 4: white card, warning-tinted value

ROW 2 — 3-COLUMN LAYOUT:
LEFT (35%): Borrower Profile card
  Shows REAL company data only:
  - Company name, sector, location (from input)
  - Loan amount requested
  - 3 sub-boxes: [DSCR] [D/E Ratio] [Interest Coverage]
    Each: small card, value + label, colored by risk level

CENTER (32%): Key Ratios card (2×2 grid)
  ┌─────────────┐ ┌─────────────┐
  │ DSCR        │ │ D/E Ratio   │
  │ 1.38        │ │ 3.4x        │
  │ ⬇ Declining │ │ ⬆ High      │
  └─────────────┘ └─────────────┘
  ┌─────────────┐ ┌─────────────┐
  │ Revenue     │ │ EBITDA Mrgn │
  │ ₹[actual]Cr │ │ [actual]%   │
  │ YoY change  │ │ YoY change  │
  └─────────────┘ └─────────────┘
  Values come ONLY from uploaded file. If not computable → show "—"

RIGHT (33%): Total Income equivalent → DSCR Trajectory mini-chart
  Title: "DSCR Trend"
  Subtitle: "Movement over available years"
  Chart: small line chart (Plotly/Recharts), orange line
  Below chart: "P50 Stress: 1.39 | P10 Worst: 0.72" badges

ROW 3 — 2-COLUMN:
LEFT (42%):
  "Model Ensemble" card (Monthly Spending Limit equivalent)
  4 horizontal fill bars:
  XGBoost:    [████████░░] 44%
  LightGBM:   [████████░░] 43%
  Rand Forest:[███████░░░] 38%
  Ensemble:   [████████░░] 42%  ← bold, orange label
  Each bar: label left, % right, orange fill bar

RIGHT (58%):
  "Signal Dashboard" (Recent Activities equivalent)
  Search bar + Filter button (same as reference)
  Table columns: Signal | Value | Status | Risk | Date Run
  Rows — REAL computed values only:
    Beneish M-Score | [value] | Flagged/Clear | HIGH/MED/LOW
    DSCR Velocity   | [value] | Declining/Stable
    GST Divergence  | [value] | Inflation/Clear
    Default DNA     | [value] | Match/No match
    Covenant Breach | [value] | Likely/Unlikely
    Satellite Score | [value] | Active/Moderate/Dormant
  If a module didn't run: show "—" NOT fake data
```

---

### PAGE 2 — UPLOAD

**Purpose:** Re-upload or upload additional documents. Accessible from sidebar.

```
HEADER:
  "Upload Financial Statements"  ← h2
  "Attach company documents for processing"  ← muted subtitle

2-COLUMN LAYOUT:
LEFT (55%): Upload card (same as landing page upload card, same styling)
  - Company name input (pre-filled from landing, editable)
  - PDF dropzone
  - "Re-Analyse" orange button

RIGHT (45%): Upload history card
  Title: "Previous Uploads"
  Table: File | Size | Uploaded | Status | Action
  Only show real files uploaded this session
  Empty state: "No files uploaded yet"
    [icon centered, muted text, no fake rows]

BELOW: Processing Steps card
  3 step pills:
  [✓ Uploaded] → [✓ Processed] → [✓ Decision Ready]
  Completed steps: orange filled circle + tick
  Pending: grey dashed circle
  Active: orange spinning ring
```

---

### PAGE 3 — SIGNALS

**Purpose:** Deep-dive into all 17 innovation signals.

```
HEADER:
  "Credit Signals"  ← h2
  "All AI-computed risk indicators for [Company Name]"

TOP SUMMARY STRIP — 3 risk-level count cards:
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ HIGH RISK    │  │ MEDIUM RISK  │  │ LOW RISK     │
│ 3 signals    │  │ 2 signals    │  │ 1 signal     │
│ (red card)   │  │ (amber card) │  │ (green card) │
└──────────────┘  └──────────────┘  └──────────────┘
Card backgrounds: risk-high-bg / risk-med-bg / risk-low-bg
Card borders: 1.5px solid matching risk color

SIGNALS GRID — 2-column card grid:

Each signal card:
  border-radius: var(--radius-xl)
  border-left: 4px solid [risk color]  ← THE key visual
  padding: 24px
  header row:
    left: signal name (15px 600), category badge (11px pill)
    right: risk badge (HIGH/MED/LOW)
  value: 28px 700, color matches risk level
  interpretation: 13px muted, max 2 lines
  "Last computed: [date/time]" — 11px muted bottom

SIGNAL CARDS (17 total, 2 columns):
01 Beneish M-Score      — Value: -1.85     — HIGH (if > -2.22)
02 DSCR Velocity        — Value: -0.18/yr  — HIGH
03 Promoter Pledge      — Value: [%]       — VARIES
04 GST Divergence       — Value: [%]       — HIGH (if >20%)
05 Default DNA          — Value: [%] [name]— MED/HIGH
06 Satellite Activity   — Value: [0-100]   — MED
07 Network Contagion    — Value: [0-1]     — MED/HIGH
08 Altman Z-Score       — Value: [score]   — VARIES
09 Piotroski F-Score    — Value: [0-9]     — VARIES
10 ICR                  — Value: [ratio]   — VARIES
11 Auditor Signal       — Value: Clean/Flag— VARIES
12 CEO Sentiment        — Value: [0-100]   — VARIES
13 Model Disagreement   — Value: [spread]  — VARIES
14 ESG Score            — Value: [0-1]     — VARIES
15 Covenant Breach Prob — Value: [%]       — HIGH (if >70%)
16 CFaR-95%             — Value: ₹[Cr]     — VARIES
17 Counterfactual       — Value: [n] changes— VARIES

If a signal has NO data (module not run): card shows grey,
  "Not computed — requires [data source]" in muted text
  NO fake values ever
```

---

### PAGE 4 — DEEP DIVE

**Purpose:** Charts and visualisations. Equivalent to the "Total Income" section of the reference.

```
HEADER:
  "Deep Dive Analysis"
  "Visual breakdown of financial trajectory and stress scenarios"

ROW 1 — LARGE CHART (full width):
  Card: DSCR Trajectory  (Total Income equivalent)
  Chart: Line chart, full width, height 280px
    X-axis: actual years from uploaded data
    Y-axis: DSCR values
    Orange line: actual DSCR
    Dashed dark line: linear trend
    Dotted amber line: DSCR = 1.25 (covenant threshold)
    Red shaded zone: DSCR < 1.0 (danger)
    Annotation: "Danger in X months" if applicable
  Legend: Actual | Trend | Min Threshold (1.25) | Danger Zone
  Empty state if no multi-year data: "Upload multi-year PDFs to see trajectory"

ROW 2 — 3-COLUMN:
LEFT: Default DNA Similarity
  6 horizontal bars — each company a row:
    IL&FS      [██░░░░░░░░] 12%
    DHFL       [███░░░░░░░] 18%
    Jet Airways[██████░░░░] 62%  ← orange highlight if highest
    Videocon   [████░░░░░░] 21%
    Satyam     [██░░░░░░░░] 14%
    Kingfisher [█████░░░░░] 55%
  Warning banner below if any > 65%: amber strip

CENTER: Monte Carlo Distribution
  Histogram chart (Plotly)
  X: DSCR at maturity
  Y: scenario frequency
  Orange bars
  3 vertical dashed lines: P10 (red), P50 (amber), P90 (green)
  Red shaded zone: DSCR < 1.0
  Below chart: P10 / P50 / P90 stat pills

RIGHT: Model Confidence
  Doughnut chart (Recharts/Plotly)
  3 segments: XGBoost | LightGBM | RF
  Center text: "Ensemble\n42% PD"
  Legend below: 3 items with weights (50% / 30% / 20%)

ROW 3 — 2-COLUMN:
LEFT: Revenue vs GST
  Grouped bar chart (2 series per year)
    Series 1: Bank-declared revenue — orange bars
    Series 2: GSTN-declared revenue — dark bars
  Divergence % shown as annotation per year
  Empty state if no GST data available

RIGHT: Bull vs Bear Summary
  2 panels side by side inside one card:
    LEFT PANEL: BULL CASE
      Border-left 3px solid #10B981
      Title: 14px 600 green
      3-4 bullet points from LLM agent output
    RIGHT PANEL: BEAR CASE  
      Border-left 3px solid #EF4444
      Title: 14px 600 red
      3-4 counter-points from bear agent
  Divider: 1px #E5E7EB vertical
  Footer: "Coordinator verdict: [text]" — 13px #6B7280
  Empty state: "Run LLM agents to see analysis"
```

---

### PAGE 5 — REPORTS

**Purpose:** Download outputs and see final recommendation.

```
HEADER:
  "Reports & Downloads"
  "Export credit decision documents for [Company Name]"

ROW 1 — DECISION SUMMARY CARD (full width, dark bg):
  background: #1A1A1A
  border-radius: var(--radius-xl)
  padding: 32px
  Layout: LEFT text | RIGHT buttons

  LEFT:
    Label: "FINAL LENDING DECISION"  ← 11px 600 uppercase orange
    Decision: [APPROVE / CONDITIONAL / REJECT]  ← 36px 700 white
    Summary line: "₹[limit] at [rate]% with [n] conditions"  ← 16px #9CA3AF

  RIGHT (vertical stack of buttons):
    [↓ Download CAM (DOCX)]  ← orange button
    [↓ Export Signals (PDF)] ← dark outline button
    [↓ Raw Data (JSON)]      ← ghost button

ROW 2 — 2-COLUMN:
LEFT: Conditions & Covenants card
  Title: "Lending Conditions"
  List of conditions (from coordinator output):
  Each condition: checkbox-style row with condition text
  Style: border-left 3px solid orange, 14px, #374151
  If no conditions: "No conditions — clean approval" (green)

RIGHT: Counterfactual Card
  Title: "Path to Approval" (or "Already Approved" if PD<35%)
  Subtitle: "Changes needed to improve PD from [current] to [target]"
  Table:
    Col 1: Step number
    Col 2: Action description (e.g., "Reduce promoter pledge")
    Col 3: Current value
    Col 4: Target value
    Col 5: Estimated PD reduction
  Footer: "Feasibility: [FEASIBLE / CHALLENGING / DIFFICULT]"
           badge colored by feasibility

ROW 3 — TIMELINE CARD (full width):
  Title: "Next Monitoring Milestones"
  Horizontal timeline (or vertical list):
    Each milestone: date + action + responsible
  Style: dot + line connector
  Dot colors: orange (upcoming) / green (past) / grey (future)
  Examples:
    "30 days: Covenant check — DSCR review"
    "90 days: GST filing verification"
    "180 days: Satellite activity re-scan"
  Empty state: "No monitoring schedule set"
```

---

### PAGE 6 — CAM (CREDIT APPRAISAL MEMO)

**Purpose:** View and download the auto-generated professional memo.

```
HEADER:
  "Credit Appraisal Memo"
  "[Company Name]  ·  Generated [date]  ·  [analyst name]"

  Right side: [Download DOCX] orange button

DOCUMENT VIEWER CARD:
  background: white
  border: 1px solid var(--border)
  border-radius: var(--radius-xl)
  padding: 48px  (to simulate document feel)
  max-width: 860px, centered within the card

  Document sections rendered as HTML (accordion or scroll):
  Each section has:
    Section number + title: 18px 600, border-bottom 2px solid #F3F4F6
    Content: 14px #374151, line-height 1.7
    Tables: styled with var(--border) borders, header row #F9FAFB

  Sections:
  1. Executive Summary
  2. Company Background
  3. Financial Analysis  (table from uploaded data)
  4. Forensics Summary   (Beneish, Altman, Piotroski values)
  5. Network Risk        (contagion score, promoter map)
  6. Stress Testing      (P10/P50/P90 DSCR)
  7. Alternative Data    (satellite, GST)
  8. Management Quality  (CEO interview if available)
  9. Bull vs Bear        (LLM agent outputs)
  10. Final Recommendation + Conditions

  If a section has no data: grey italic "Data not available for this section"
  Section jumps: sticky mini TOC on right side (visible at 1440px+)
```

---

## SECTION C — EMPTY STATES

```
Rule: NEVER show placeholder/fake data. Always show a proper empty state.

Empty state pattern:
  centered in card
  icon: 48px, color #D1D5DB (grey)
  title: 15px 600 #6B7280
  subtitle: 13px #9CA3AF
  optional: [action button] if something can be done

Examples:
  No signals computed:
    icon: shield-off
    "Signals not computed yet"
    "Upload financial statements to run analysis"
    [Go to Upload →]

  No chart data:
    icon: bar-chart
    "Not enough data to plot"
    "Multi-year statements required for this chart"

  No LLM output:
    icon: message-square
    "LLM agents not run"
    "Add an Anthropic API key to enable agent analysis"
```

---

## SECTION D — LOADING STATES

```
Skeleton loader:
  Use animated shimmer gradient sweeping left-to-right
  Color: #F3F4F6 → #E5E7EB → #F3F4F6
  Duration: 1.4s, ease-in-out, infinite
  Border-radius: match the element being loaded
  Never show fake content — shimmer blocks only

Processing banner (full-width, below navbar):
  background: #FFF7F4  (orange pale)
  border-bottom: 1px solid var(--orange-border)
  text: "⟳  Analysing [Company Name]... Beneish forensics in progress"
  rotating spinner icon: orange, 16px
  progress bar: thin (3px) at very bottom of banner, orange fill

Completion toast:
  bottom-right corner
  background: #1A1A1A
  text: "✓  Analysis complete — [Company Name]"  ← white
  sub: "17 signals computed"  ← #9CA3AF
  auto-dismiss: 4 seconds
  border-left: 3px solid #10B981
```

---

## SECTION E — TRANSITION FROM LANDING → DASHBOARD

```
After CTA click on landing page:
1. CTA button text changes to "⟳  Analysing..."
   background darkens to #1A1A1A
   spinner animation

2. Card dims (opacity 0.7, pointer-events none)

3. After processing:
   Full-page transition:
     current page: fade out + slide up (-20px) — 300ms
     dashboard: fade in + slide up from below (+20px) — 300ms
     timing: overlap by 100ms (feels smooth not jarring)

4. Dashboard loads directly on Overview page
   Greeting uses the company name entered on landing
   "Good morning, Analyst · [Company Name] analysis ready"
```

---

## SECTION F — DO NOT / NEVER

```
❌ NEVER show hardcoded numbers not from actual computation
❌ NEVER use placeholder text like "Lorem ipsum" or "Sample Co"
❌ NEVER show charts with random data — empty state instead
❌ NEVER use dark background pages (the app is light-themed)
❌ NEVER use purple as accent — orange (#E8470A) is the only brand color
❌ NEVER use Inter or Roboto — use DM Sans only
❌ NEVER show more than 4 top metric cards in a single row
❌ NEVER skip loading states on data-fetching operations
❌ NEVER use pie charts — use bar charts, line charts, or donuts
❌ NEVER center body text — left-align all paragraphs and table content
❌ NEVER underline section headings (hallmark of amateur AI design)
❌ NEVER use table borders on every cell — only use horizontal row dividers
❌ NEVER make buttons smaller than 44px height (accessibility)
❌ NEVER use more than 2 font families on any page
```
