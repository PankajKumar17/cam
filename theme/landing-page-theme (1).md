# landing-page-theme.md
# Intelli-Credit — Landing Page Design Theme
# Stack: Vite + React + Tailwind CSS + Framer Motion
# Reference aesthetic: Finexy (orange + white + near-black fintech)

---

## CONCEPT

Single-page entry point. User enters a company name, uploads financial PDFs,
clicks "Analyse". On completion → React Router pushes to /dashboard.

Tone: Serious fintech. Premium. Trustworthy. NOT startup-flashy.
Light theme throughout. Orange is the ONLY accent color.

---

## FONTS

```
Primary display:  'DM Serif Display'  — hero H1 only
UI font:          'DM Sans'           — everything else
Code/mono:        'DM Mono'           — file names, scores, IDs

Google Fonts import:
  https://fonts.googleapis.com/css2?
    family=DM+Serif+Display:ital@0;1
    &family=DM+Sans:opsz,wght@9..40,300;400;500;600;700
    &family=DM+Mono:wght@400;500
    &display=swap
```

---

## COLOR TOKENS  (tailwind.config.js extend.colors)

```js
colors: {
  orange:       { DEFAULT: '#E8470A', light: '#FF6B35', pale: '#FFF7F4',
                  border: '#F5C4B0', hover: '#C73D08',
                  glow:  'rgba(232,71,10,0.15)' },
  surface:      { page: '#F4F5F7', card: '#FFFFFF',
                  hover: '#F9FAFB', row: '#FAFAFA' },
  dark:         { DEFAULT: '#1A1A1A', hover: '#2D2D2D', muted: '#374151' },
  border:       { DEFAULT: '#E5E7EB', strong: '#D1D5DB', divider: '#F3F4F6' },
  text:         { primary: '#1A1A1A', secondary: '#6B7280',
                  muted: '#9CA3AF', placeholder: '#D1D5DB' },
  success:      { DEFAULT: '#10B981', bg: '#ECFDF5' },
  warning:      { DEFAULT: '#F59E0B', bg: '#FFFBEB' },
  danger:       { DEFAULT: '#EF4444', bg: '#FEF2F2' },
  info:         { DEFAULT: '#3B82F6', bg: '#EFF6FF' },
}
```

---

## SHADOWS  (tailwind.config.js extend.boxShadow)

```js
boxShadow: {
  card:         '0 1px 4px rgba(0,0,0,0.06), 0 2px 12px rgba(0,0,0,0.06)',
  'card-hover': '0 4px 16px rgba(0,0,0,0.10), 0 8px 32px rgba(0,0,0,0.08)',
  orange:       '0 4px 16px rgba(232,71,10,0.30)',
  'orange-lg':  '0 8px 32px rgba(232,71,10,0.40)',
  focus:        '0 0 0 3px rgba(232,71,10,0.15)',
  dark:         '0 4px 16px rgba(0,0,0,0.25)',
  modal:        '0 24px 64px rgba(0,0,0,0.18)',
}
```

---

## LAYOUT

```
<body bg>       bg-surface-page (#F4F5F7)
max-w:          1280px, mx-auto, px-10 (desktop) px-5 (mobile)
section gap:    80px vertical
card radius:    rounded-2xl (20px)   — main cards
                rounded-xl  (16px)   — inner tiles
                rounded-full         — pills, badges
```

---

## NAVBAR

```
height:         64px
bg:             white
border-bottom:  1px solid #F3F4F6
position:       sticky top-0 z-50
backdrop:       backdrop-blur-md bg-white/90 on scroll

LEFT:
  Logo circle: 36px, bg gradient orange→light-orange, "IC" white 700 14px
  "Intelli-Credit"  DM Sans 600 18px #1A1A1A

RIGHT (gap-6):
  "Docs"        — text link 14px text-secondary hover:text-primary
  "About"       — text link
  "Launch App →"— pill button
                   bg-dark text-white px-5 py-2.5 rounded-full text-sm font-semibold
                   hover:bg-orange transition-colors duration-200
```

---

## HERO SECTION

```
Layout:         grid grid-cols-[1fr_480px] gap-16 items-center py-20
Mobile:         grid-cols-1, upload card below text

LEFT COLUMN:
  1. Tag pill
     bg-orange-pale border border-orange-border text-orange
     text-xs font-semibold uppercase tracking-widest
     px-3.5 py-1.5 rounded-full inline-flex
     text: "AI Credit Decisioning Engine"

  2. H1  (DM Serif Display, 56px, leading-tight, text-dark)
     Line 1: "Intelligent Credit"
     Line 2: "Decisions in"
     Line 3: <span class="text-orange italic">Minutes.</span>

  3. Subtitle  (DM Sans 18px text-secondary leading-relaxed max-w-lg mt-6)
     "Upload financial statements and get a complete Credit Appraisal
      Memo — Beneish forensics, satellite intelligence, XGBoost ensemble,
      and adversarial LLM agents — in under five minutes."

  4. Trust row  (flex gap-6 mt-8 flex-wrap)
     Each item: flex items-center gap-2 text-sm text-muted
     Icon: 14px CheckCircle (green)
     "XGBoost AUC 0.9948"
     "146 ML Features"
     "Full CAM in < 5 min"
     "17 AI Innovations"

RIGHT COLUMN — UPLOAD CARD:
  bg-white rounded-3xl shadow-modal p-9
  border border-border

  Header:
    "Start Your Analysis"   text-xl font-semibold text-dark
    "Enter company name and upload statements"  text-sm text-muted mt-1

  Divider: border-t border-divider mt-5 mb-5

  ── Company Name Input ──────────────────────────────
  Label: "COMPANY NAME"  text-xs font-semibold uppercase tracking-wider
         text-muted mb-2

  Input wrapper: relative
    Icon: Building2 (Lucide) — absolute left-3.5 top-1/2 -translate-y-1/2
          text-muted w-4 h-4
    Input:
      w-full h-12 pl-10 pr-4 rounded-xl border border-border
      font-dm text-sm text-dark bg-white
      placeholder:text-placeholder
      focus:outline-none focus:border-orange
      focus:shadow-focus transition-all duration-150
      placeholder="e.g. Sunrise Textile Mills"

  ── File Dropzone ────────────────────────────────────  mt-5
  Label: "FINANCIAL STATEMENTS"  (same label style)

  EMPTY STATE (no file):
    border-2 border-dashed border-border rounded-2xl p-8
    flex flex-col items-center gap-2 cursor-pointer
    hover: border-orange bg-orange-pale/40 transition-all duration-200
    drag-over: border-orange bg-orange-pale shadow-focus

    Icon: UploadCloud  — w-8 h-8 text-orange
    Text: "Drag & drop PDF files here"  text-sm font-medium text-dark
    Sub:  "or"  text-xs text-muted
    Browse button: text-orange text-sm font-semibold underline
    Footer: "Accepts PDF, XLSX  ·  Max 50MB per file"  text-xs text-muted

  FILE SELECTED STATE:
    bg-success-bg border-2 border-success rounded-2xl p-4
    flex items-center justify-between
    Left: FileText icon (green) + filename (DM Mono 13px) + size (text-muted 12px)
    Right: X button (ghost, hover:text-danger)

  ── CTA Button ───────────────────────────────────────  mt-6
  DISABLED (no file or no name):
    w-full h-13 rounded-2xl bg-dark/30 text-white/50 cursor-not-allowed
    text-base font-semibold

  ACTIVE:
    w-full h-13 rounded-2xl
    bg-gradient-to-br from-orange to-orange-light
    text-white font-semibold text-base
    shadow-orange hover:shadow-orange-lg
    hover:-translate-y-0.5 active:translate-y-0
    transition-all duration-150
    text: "Analyse with AI  →"

  LOADING:
    bg-dark text-white cursor-wait
    Left spinner (animate-spin) + "Analysing..."

  ── Privacy note ─────────────────────────────────────  mt-4
  text-center text-xs text-muted flex items-center justify-center gap-1.5
  Lock icon (12px) + "Files processed locally · never stored externally"
```

---

## HOW IT WORKS SECTION

```
Container: py-20
Header (centered):
  "How It Works"  text-3xl font-semibold text-dark
  "Three steps from PDF to lending decision"  text-base text-muted mt-2

Cards: grid grid-cols-3 gap-6 mt-12
Mobile: grid-cols-1

Each step card:
  bg-white rounded-2xl border border-border shadow-card p-7
  hover:shadow-card-hover hover:-translate-y-0.5 transition-all duration-200

  Step label:  "STEP 01"  text-xs font-bold uppercase tracking-widest text-orange
  Icon circle: 52px, bg-orange-pale, icon text-orange  (rounded-full flex center)
               mt-3 mb-4
  Title:       text-lg font-semibold text-dark
  Body:        text-sm text-secondary leading-relaxed mt-2

  Steps:
  01: UploadCloud icon — "Upload & Name"
      "Enter the company name and attach annual report PDFs.
       Multi-year statements unlock trajectory analysis."

  02: Brain icon — "AI Runs 17 Innovations"
      "Beneish forensics, network GNN, satellite scoring, Monte Carlo
       stress testing, and adversarial LLM agents run in parallel."

  03: FileCheck icon — "Get Your Decision"
      "Receive PD score, credit limit, risk premium, and a full
       10-section Credit Appraisal Memo — ready to present."

Connector arrows between cards (desktop only):
  absolute positioned "→" text-2xl text-border between cards
```

---

## STATS STRIP

```
bg-[#ECEEF2] py-12
Grid: grid-cols-4 divide-x divide-border-strong
Each stat: text-center px-8

Value:  DM Serif Display 48px text-dark
Label:  text-xs font-semibold uppercase tracking-widest text-muted mt-2

Stats:
  17         INNOVATIONS
  146        ML FEATURES
  0.9961     AUC SCORE
  < 5 min    PROCESSING TIME
```

---

## FOOTER

```
bg-dark py-12
Logo + "Intelli-Credit"  text-white
Tagline: "AI-Powered Credit Decisioning Engine"  text-sm text-muted mt-1

Links row (mt-8 gap-6): Docs · Architecture · Hackathon
  text-sm text-muted hover:text-white transition-colors

Bottom bar (mt-8 pt-6 border-t border-white/10):
  "© 2025 Intelli-Credit · Vivriti Capital AI Hackathon"
  text-xs text-muted
```

---

## ANIMATIONS (Framer Motion)

```js
// Page load — stagger children
const container = { hidden: {}, show: { transition: { staggerChildren: 0.08 } } }
const item = { hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0,
               transition: { duration: 0.4, ease: 'easeOut' } } }

// Upload card entrance
initial={{ opacity: 0, scale: 0.97, y: 16 }}
animate={{ opacity: 1, scale: 1, y: 0 }}
transition={{ duration: 0.45, ease: 'easeOut', delay: 0.15 }}

// CTA button hover (use whileHover / whileTap)
whileHover={{ y: -2 }}
whileTap={{ scale: 0.98 }}

// Stats count-up: use useInView + react-countup on enter viewport

// Page transition to dashboard:
exit={{ opacity: 0, y: -20 }}  + AnimatePresence wrapping routes
```
