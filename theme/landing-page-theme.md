# Intelli-Credit — Landing Page Theme
> Design specification for the entry point of the Intelli-Credit application.
> Reference aesthetic: Finexy fintech dashboard (orange + white + near-black)

---

## 1. CONCEPT & TONE

**One-line brief:** "A fintech landing page that feels as serious as a Bloomberg terminal but as clean as a Series-A startup."

**Tone:** Professional · Trustworthy · Modern · Minimal  
**NOT:** Startup-flashy, dark/moody, AI-gimmicky, cluttered  
**Audience:** Credit analysts, risk officers, lending institution staff

---

## 2. COLOR PALETTE

```css
:root {
  /* Page */
  --bg-page:        #F4F5F7;   /* warm light grey — entire page background */
  --bg-card:        #FFFFFF;   /* all card surfaces */
  --bg-dark:        #1A1A1A;   /* hero section dark panel, footer */

  /* Brand */
  --orange:         #E8470A;   /* PRIMARY — CTAs, logo, accent, active states */
  --orange-light:   #FF6B35;   /* gradient end point */
  --orange-glow:    rgba(232, 71, 10, 0.15);  /* ambient glow */
  --orange-hover:   #C73D08;   /* button hover */

  /* Text */
  --text-primary:   #1A1A1A;   /* headings, body */
  --text-secondary: #6B7280;   /* subtitles, labels */
  --text-muted:     #9CA3AF;   /* captions, placeholders */
  --text-white:     #FFFFFF;

  /* Borders */
  --border:         #E5E7EB;   /* card borders, input borders */
  --border-focus:   #E8470A;   /* input focused state */

  /* Semantic */
  --success:        #10B981;
  --warning:        #F59E0B;
  --danger:         #EF4444;
  --info:           #3B82F6;
}
```

---

## 3. TYPOGRAPHY

```css
/* Import */
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600;700&display=swap');

/* Usage */
--font-display: 'DM Serif Display', Georgia, serif;  /* Hero headline only */
--font-body:    'DM Sans', sans-serif;               /* All other text */

/* Scale */
--text-hero:    56px / 64px  bold   -- Hero H1
--text-h2:      36px / 44px  600    -- Section titles
--text-h3:      22px / 30px  600    -- Card titles
--text-body-lg: 18px / 28px  400    -- Hero sub, intro paragraphs
--text-body:    15px / 24px  400    -- Regular body
--text-small:   13px / 20px  400    -- Labels, captions
--text-label:   11px / 16px  600    -- Uppercase tags (letter-spacing: 1.5px)
```

---

## 4. LAYOUT & SPACING

```
Page max-width:     1280px (centered with auto margins)
Page padding:       0 40px  (desktop) / 0 20px (mobile)
Section gap:        80px vertical between sections
Card padding:       28px
Card border-radius: 20px
Card shadow:        0 2px 16px rgba(0, 0, 0, 0.07)
Card shadow hover:  0 8px 32px rgba(0, 0, 0, 0.12)

Grid system:        12-column, 24px gap
Sidebar (app):      64px collapsed icon-only
```

---

## 5. NAVBAR

```
Height:           64px
Background:       white (#FFFFFF)
Border-bottom:    1px solid #F3F4F6
Position:         sticky top, z-index 100
Backdrop-filter:  blur(12px) with slight transparency on scroll

Contents (left → right):
├── Logo group
│   ├── Icon: 36px circle, orange gradient bg (#E8470A→#FF6B35),
│   │         white "IC" text inside, font-weight 700, 14px
│   └── Brand: "Intelli-Credit" — DM Sans 600 18px #1A1A1A
│
├── (flex spacer)
│
└── Right group (gap: 24px)
    ├── "Documentation" — text link, 14px #6B7280, hover #1A1A1A
    ├── "About" — text link
    └── "Launch App →" — pill button
            background: #1A1A1A
            color: white
            padding: 10px 20px
            border-radius: 999px
            font: DM Sans 600 14px
            hover: background #E8470A, transition 200ms
```

---

## 6. HERO SECTION

```
Layout: 2-column (55% left text / 45% right upload card)
Background: #F4F5F7 page colour (NO gradient, NO dark)
Padding: 80px 0

LEFT COLUMN:
├── Tag pill (small):
│   background: #FFF0EB  (orange tint)
│   text: "AI Credit Decisioning Engine"  11px 600 uppercase #E8470A
│   border: 1px solid rgba(232,71,10,0.2)
│   border-radius: 999px, padding: 6px 14px
│
├── H1 (DM Serif Display, 56px, #1A1A1A):
│   "Intelligent Credit"  (line 1 — normal weight)
│   "Decisions in"        (line 2)
│   "Minutes."            (line 3 — italic style if DM Serif Display italic)
│
│   NOTE: "Minutes." in orange (#E8470A)
│
├── Body paragraph (DM Sans 18px, #6B7280, max-width 480px):
│   "Upload financial statements, get a complete Credit Appraisal
│    Memo powered by 17 AI innovations — Beneish forensics, satellite
│    intelligence, and adversarial LLM agents."
│
└── Trust row (flex, gap 24px, margin-top 32px):
    ├── "✓  XGBoost AUC 0.9948"    — 13px #6B7280
    ├── "✓  146 ML Features"        — 13px #6B7280
    └── "✓  Full CAM in < 5 min"   — 13px #6B7280

RIGHT COLUMN — THE UPLOAD CARD:
┌─────────────────────────────────────────────────┐
│  [card: white, border-radius 24px,               │
│   box-shadow: 0 8px 40px rgba(0,0,0,0.10),       │
│   padding: 36px]                                 │
│                                                  │
│  "Start Your Analysis"     ← h3, 20px 600        │
│  "Enter company name and upload financials"      │
│  ← 13px muted                                   │
│                                                  │
│  ─────────────────────────────────────────────  │
│                                                  │
│  Label: "Company Name"  (12px 600 uppercase muted)│
│  ┌────────────────────────────────────────────┐ │
│  │  🏢  Sunrise Textile Mills...              │ │
│  └────────────────────────────────────────────┘ │
│  Input styling:                                  │
│    height: 48px, border-radius: 12px             │
│    border: 1.5px solid #E5E7EB                   │
│    focus border: 1.5px solid #E8470A             │
│    focus box-shadow: 0 0 0 3px rgba(232,71,10,.1)│
│    padding: 0 16px 0 40px (icon left-padded)     │
│    font: DM Sans 15px #1A1A1A                    │
│    placeholder: #9CA3AF                          │
│                                                  │
│  ─── margin-top: 20px ───────────────────────── │
│                                                  │
│  Label: "Financial Statements (PDF)"             │
│  ┌────────────────────────────────────────────┐ │
│  │                                            │ │
│  │      ☁  [upload icon, 32px, #E8470A]       │ │
│  │                                            │ │
│  │   Drag & drop PDF files here               │ │
│  │   or  [Browse Files] ← orange text link    │ │
│  │                                            │ │
│  │   Accepts: PDF, XLSX  ·  Max 50MB          │ │
│  │   ← 12px muted                             │ │
│  └────────────────────────────────────────────┘ │
│  Dropzone styling:                               │
│    background: #FAFAFA                           │
│    border: 2px dashed #E5E7EB                    │
│    border-radius: 16px, padding: 32px            │
│    drag-over state:                              │
│      border-color: #E8470A                       │
│      background: #FFF7F4                         │
│      box-shadow: 0 0 0 4px rgba(232,71,10,0.08) │
│    transition: all 200ms ease                    │
│                                                  │
│  ─── margin-top: 24px ───────────────────────── │
│                                                  │
│  [Analyse with AI  →]  ← PRIMARY CTA BUTTON     │
│    width: 100%                                   │
│    height: 52px                                  │
│    background: linear-gradient(135deg,           │
│                #E8470A 0%, #FF6B35 100%)         │
│    box-shadow: 0 4px 16px rgba(232,71,10,0.35)  │
│    color: white                                  │
│    font: DM Sans 600 16px                        │
│    border-radius: 14px                           │
│    hover: translateY(-1px),                      │
│           box-shadow: 0 8px 24px rgba(232,71,10,.45)│
│    active: translateY(0px)                       │
│    disabled (no file): opacity 0.5, no hover     │
│                                                  │
│  ─── margin-top: 16px ───────────────────────── │
│                                                  │
│  Privacy note (centered, 12px muted):            │
│  "🔒  Files processed locally · never stored"   │
└─────────────────────────────────────────────────┘
```

---

## 7. HOW IT WORKS SECTION

```
Section title: "How It Works"  (h2, centered)
Subtitle: "From PDF to lending decision in three steps"  (muted, centered)

3-step horizontal flow (desktop) / vertical (mobile):

┌──────────────────┐    →    ┌──────────────────┐    →    ┌──────────────────┐
│  Step 01         │         │  Step 02         │         │  Step 03         │
│  [icon circle    │         │  [icon circle    │         │  [icon circle    │
│   orange, 56px]  │         │   dark, 56px]    │         │   orange, 56px]  │
│                  │         │                  │         │                  │
│  Upload & Name   │         │  AI Analyses     │         │  Get Decision    │
│                  │         │                  │         │                  │
│  Enter company   │         │  17 innovations  │         │  Full CAM doc +  │
│  name and attach │         │  run in parallel │         │  PD score, limit │
│  financial PDFs  │         │  < 5 minutes     │         │  and rate in one │
└──────────────────┘         └──────────────────┘         └──────────────────┘

Card styling:
  background: white
  border: 1px solid #E5E7EB
  border-radius: 20px
  padding: 32px 28px
  text-align: left
  Step number: 11px 700 uppercase #E8470A, letter-spacing 2px
  Title: 18px 600 #1A1A1A
  Body: 14px #6B7280

Connector arrow:
  Simple right-pointing arrow "→" in #E5E7EB, 24px
  Hidden on mobile
```

---

## 8. STATS STRIP

```
Full-width band (no card, just section bg slightly darker: #ECEEF2)
Padding: 48px 0
4 stats in a row:

│  17          │  146         │  0.9961      │  < 5 min     │
│  Innovations │  ML Features │  AUC Score   │  Processing  │

Stat number: DM Serif Display 48px #1A1A1A
Label: DM Sans 13px 500 uppercase #6B7280, letter-spacing 1.5px
Dividers: 1px vertical #D1D5DB between items
```

---

## 9. FEATURES SECTION

```
2-column grid (text left, 3 feature cards right):

Left:
  "Built on Academic-Grade ML"  ← h2
  Long description of Beneish, XGBoost paper citation, etc.
  [Read the technical paper →]  ← text link orange

Right — 3 stacked feature cards:
  Card 1 (orange tinted): Beneish M-Score
  Card 2 (white): Network GNN
  Card 3 (white): Adversarial LLM Agents

Each feature card:
  background: white (card 1: #FFF7F4)
  border: 1px solid #E5E7EB (card 1: 1px solid rgba(232,71,10,0.2))
  border-radius: 16px, padding: 24px
  left accent bar: 3px solid #E8470A (card 1 only)
  icon: 24px, colored per feature
  title: 15px 600 #1A1A1A
  body: 13px #6B7280
```

---

## 10. FOOTER

```
Background: #1A1A1A (dark)
Padding: 48px 0 32px

Contents:
├── Logo row (logo + brand + tagline)
│   "Intelli-Credit — AI Credit Decisioning Engine"
│   Tagline: 13px #9CA3AF
│
├── Links row: Documentation · Architecture · Hackathon
│   13px #9CA3AF, hover #FFFFFF
│
└── Bottom bar (border-top 1px #2D2D2D):
    "© 2025 Intelli-Credit · Vivriti Capital AI Hackathon"
    ← 12px #6B7280
```

---

## 11. STATES & INTERACTIONS

```
UPLOAD FLOW (on the hero card):

STATE 1 — Empty:
  CTA button: disabled (opacity 0.5)
  Dropzone: default dashed border

STATE 2 — Name entered, no file:
  CTA: still disabled
  Name input: border turns orange on focus

STATE 3 — File dropped/selected:
  Dropzone transforms to:
    ┌────────────────────────────────┐
    │  ✓  Sunrise_FY24.pdf          │  ← filename
    │     2.4 MB  ·  Ready          │  ← size + status
    │                          [✕]  │  ← remove button
    └────────────────────────────────┘
    background: #F0FDF4, border: 2px solid #10B981
  CTA: becomes active (full orange)

STATE 4 — Processing (after CTA click):
  CTA transforms to:
    [  ⟳  Analysing...  ]
    background: #1A1A1A (dark)
    spinner rotating animation
  Card dims slightly (pointer-events none)

STATE 5 — Complete:
  Redirect to /dashboard
  OR card expands with tick animation before redirect

MICRO-ANIMATIONS:
  - Hero card: fade-up + scale(0.98→1) on page load (400ms ease-out)
  - Step cards: staggered fade-up (0ms, 100ms, 200ms delay)
  - Stats: count-up when scrolled into view
  - CTA hover: translateY(-2px) + shadow intensifies (150ms)
  - Dropzone drag-over: gentle pulse border animation
```

---

## 12. RESPONSIVE

```
Desktop (1280px+): 2-col hero, 3-col steps
Laptop (1024px):   2-col hero (tighter), 3-col steps
Tablet (768px):    1-col hero (card below text), steps stack
Mobile (< 768px):  Full single column, card full-width

Breakpoints:
  --bp-sm: 640px
  --bp-md: 768px
  --bp-lg: 1024px
  --bp-xl: 1280px
```
