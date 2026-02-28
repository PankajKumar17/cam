# 🏦 Intelli-Credit — AI-Powered Credit Decisioning Engine

### Vivriti Capital AI/ML Hackathon

> *Automates end-to-end preparation of Comprehensive Credit Appraisal Memos (CAMs) using **11 innovations** in ML, alternative data, and adversarial LLM agents — from raw financials to a print-ready DOCX in one pipeline call.*

---

## 🏗️ Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                     INTELLI-CREDIT ENGINE                       │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │  PERSON 1        │  │  PERSON 2        │  │  PERSON 3        │  │
│  │  ML Core         │  │  Alt Data        │  │  LLM + CAM       │  │
│  │                   │  │                   │  │                   │  │
│  │  • Data Gen      │  │  • Network Graph  │  │  • Research Agent │  │
│  │  • Feature Eng   │  │  • Stress Test    │  │  • Bull Agent     │  │
│  │  • Credit Scorer │  │  • Satellite      │  │  • Bear Agent     │  │
│  │  • LSTM Traj     │  │  • GST Intel      │  │  • CEO Interview  │  │
│  │  • Forensics     │  │  • DNA Matching   │  │  • CAM Generator  │  │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘  │
│           │                      │                      │            │
│           └──────────────────────┼──────────────────────┘            │
│                                  ▼                                   │
│                     ┌──────────────────────┐                         │
│                     │  pipeline/            │                         │
│                     │  main_pipeline.py     │                         │
│                     │  (10-Layer Engine)    │                         │
│                     └──────────┬───────────┘                         │
│                                ▼                                     │
│              ┌─────────────────────────────────┐                     │
│              │  Output: CAM DOCX + Scores JSON │                     │
│              │  + Network Graph + Stress Chart  │                     │
│              └─────────────────────────────────┘                     │
│                                                                      │
│  ┌──────────────────────┐  ┌──────────────────────────────┐          │
│  │  dashboard/app.py    │  │  notebooks/demo_sunrise.ipynb │          │
│  │  Streamlit 4-Page UI │  │  27-Cell Demo Walkthrough     │          │
│  └──────────────────────┘  └──────────────────────────────┘          │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 👥 Team Structure

| Member | Module Ownership | Key Deliverables |
|---|---|---|
| **Person 1** | `modules/person1_ml_core/` — Data Pipeline + ML Core | Synthetic data generator (30 companies, 160+ features), 3-model ensemble credit scorer, LSTM trajectory model, Beneish/Altman/Piotroski forensics |
| **Person 2** | `modules/person2_alt_data/` — Alternative Data + Graph Intelligence | Promoter network contagion (GNN), Monte Carlo stress test (1000 sims), Sentinel-2 satellite scoring, GST truth layer, Default DNA fingerprinting |
| **Person 3** | `modules/person3_llm_cam/` — LLM Agents + Dashboard + CAM | Tavily research agent, adversarial Bull/Bear LLM agents (LangGraph), CEO interview analysis (Whisper + VADER), 11-section CAM DOCX generator, Streamlit dashboard |

---

## 📁 Project Structure

```
cam/
├── data/
│   ├── raw/                              # Raw uploaded files
│   ├── processed/                        # Feature matrix, CAM DOCX, scores JSON
│   └── synthetic/                        # Generated dataset (30 companies × 12 yrs)
│       ├── intelli_credit_dataset.csv    # 352 rows × 149 columns
│       ├── demo_sunrise_textile.csv      # Single-company demo data
│       └── schema.json                   # Full dataset schema (747 lines)
│
├── modules/
│   ├── person1_ml_core/                  # Person 1 — ML Core
│   │   ├── __init__.py
│   │   ├── data_generator.py             # Synthetic dataset (30 companies, FY2009–2024)
│   │   ├── feature_engineering.py        # 160 features: velocity, Beneish, DNA, ratios
│   │   ├── forensics.py                  # Forensic analysis coordination
│   │   ├── credit_scorer.py              # XGBoost + RF + LightGBM ensemble + SHAP
│   │   ├── temporal_model.py             # LSTM trajectory + early warning system
│   │   └── validate_dataset.py           # Dataset validation + distribution plots
│   │
│   ├── person2_alt_data/                 # Person 2 — Alternative Data
│   │   ├── __init__.py                   # Exports all public functions
│   │   ├── network_graph.py              # MCA21 promoter network + contagion risk
│   │   ├── stress_test.py                # Monte Carlo (1000 sims) + named scenarios
│   │   ├── satellite_module.py           # Sentinel-2 factory activity scoring
│   │   ├── gst_intelligence.py           # GST filing intelligence vs bank revenue
│   │   └── dna_matching.py               # Default DNA fingerprints (6 archetypes)
│   │
│   └── person3_llm_cam/                  # Person 3 — LLM Agents + CAM
│       ├── __init__.py                   # Exports all agent functions
│       ├── research_agent.py             # LangGraph Tavily + Claude research agent
│       ├── approval_agent.py             # Bull case agent (structured approval)
│       ├── dissent_agent.py              # Bear case + coordinator (final recommendation)
│       ├── ceo_interview.py              # Whisper transcription + VADER sentiment
│       └── cam_generator.py              # 11-section DOCX CAM generator
│
├── pipeline/
│   └── main_pipeline.py                  # 10-layer integration pipeline
│
├── dashboard/
│   └── app.py                            # 4-page Streamlit dashboard
│
├── notebooks/
│   └── demo_sunrise_textile.ipynb        # 27-cell interactive demo
│
├── tests/
│   ├── test_person1.py                   # ML core tests (dataset, Beneish, scorer)
│   ├── test_person2.py                   # Alt data tests (49 tests, all 5 modules)
│   └── test_person3.py                   # LLM agent tests (mocked APIs)
│
├── .env.example                          # API keys template
├── .gitignore
├── requirements.txt
├── COPILOT_PROMPTS.md                    # Agent prompts used during development
├── QUICKSTART_PERSON1.md                 # Person 1 quickstart guide
├── QUICKSTART_PERSON2.md                 # Person 2 quickstart guide
├── QUICKSTART_PERSON3.md                 # Person 3 quickstart guide
└── README.md
```

---

## 🚀 Quick Start (3 Steps)

### Step 1 — Install

```bash
# Clone repo
git clone https://github.com/PankajKumar17/intelli-credit.git
cd intelli-credit

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Mac/Linux
# venv\Scripts\activate         # Windows

# Install all dependencies
pip install -r requirements.txt

# Copy env template and fill in your API keys
cp .env.example .env
# Edit .env with: ANTHROPIC_API_KEY, TAVILY_API_KEY, etc.
```

### Step 2 — Generate Data & Run Pipeline

```bash
# Generate synthetic dataset (352 rows × 149 columns, 30 companies)
python modules/person1_ml_core/data_generator.py

# Run feature engineering (expands to 160 columns)
python modules/person1_ml_core/feature_engineering.py

# Run full pipeline for demo company
python pipeline/main_pipeline.py
# → Outputs: CAM DOCX, scores JSON, network graph, stress chart
```

### Step 3 — Explore

```bash
# Option A: Launch Streamlit dashboard
streamlit run dashboard/app.py

# Option B: Open Jupyter notebook
jupyter notebook notebooks/demo_sunrise_textile.ipynb

# Option C: Run tests
python -m pytest tests/ -v
# → 75 passed, 15 skipped, 1 xfailed
```

---

## 🧠 11 Innovations — All Implemented ✅

| # | Innovation | Module | Owner | Status |
|---|---|---|---|---|
| 1 | **Beneish M-Score Forensics** — Detects earnings manipulation using 8 financial ratios. Satyam Computer validated as fraudulent. | `feature_engineering.py` | Person 1 | ✅ |
| 2 | **3-Model Ensemble Credit Scorer** — XGBoost + Random Forest + LightGBM with SMOTE balancing, temporal train/test split, SHAP explanations. | `credit_scorer.py` | Person 1 | ✅ |
| 3 | **LSTM Trajectory Model** — Predicts 3-year financial trajectory with early warning system. Plots trajectory curves. | `temporal_model.py` | Person 1 | ✅ |
| 4 | **Model Disagreement Signal** — Flags cases where ensemble sub-models disagree, indicating high-uncertainty credits. | `credit_scorer.py` | Person 1 | ✅ |
| 5 | **Promoter Network Contagion** — Builds MCA21 director network graph. Computes contagion risk from connected NPA-tainted entities. | `network_graph.py` | Person 2 | ✅ |
| 6 | **Monte Carlo Stress Test** — 1000 simulations across interest rate, revenue, and margin shocks. 4 named scenarios (rate hike, revenue decline, margin squeeze, perfect storm). | `stress_test.py` | Person 2 | ✅ |
| 7 | **Sentinel-2 Satellite Activity** — Scores factory operational activity using satellite imagery analysis. Cross-validates against reported utilization. | `satellite_module.py` | Person 2 | ✅ |
| 8 | **GST Truth Layer** — Compares GST filing patterns with bank-reported revenue to detect mismatches and revenue inflation. | `gst_intelligence.py` | Person 2 | ✅ |
| 9 | **Default DNA Fingerprinting** — Matches borrower against 6 historical default archetypes (IL&FS, Kingfisher, DHFL, Café Coffee Day, Bhushan Steel, Jet Airways). | `dna_matching.py` | Person 2 | ✅ |
| 10 | **Adversarial Bull/Bear LLM Agents** — LangGraph-powered approval vs. dissent agents debate the credit case. Coordinator synthesizes final recommendation. | `approval_agent.py` + `dissent_agent.py` | Person 3 | ✅ |
| 11 | **CEO Interview Sentiment** — Whisper transcription + VADER sentiment + deflection detection on CEO management interviews. | `ceo_interview.py` | Person 3 | ✅ |

### Bonus Innovations

| Innovation | Module | Owner |
|---|---|---|
| **Tavily Web Research Agent** — Automated industry research with LangGraph state machine | `research_agent.py` | Person 3 |
| **11-Section CAM DOCX Generator** — Professional credit memo with executive summary, financial analysis, all scores | `cam_generator.py` | Person 3 |
| **4-Page Streamlit Dashboard** — Interactive demo with company selector, score visualizations, CAM download | `app.py` | Person 3 |
| **Altman Z-Score + Piotroski F-Score** — Additional forensic scoring integrated into feature engineering | `feature_engineering.py` | Person 1 |
| **Default DNA Velocity Features** — Rate-of-change features capturing deterioration patterns | `feature_engineering.py` | Person 1 |

---

## 📊 Dataset Details

| Property | Value |
|---|---|
| **Rows** | 352 (30 companies × ~12 fiscal years) |
| **Raw Columns** | 149 |
| **Engineered Columns** | 160 (after feature_engineering.py) |
| **Companies** | 30 (15 defaulted + 15 healthy) |
| **Fiscal Years** | FY2009 – FY2024 |
| **Notable Companies** | Satyam, IL&FS, Kingfisher, DHFL, Jet Airways, Bhushan Steel, Café Coffee Day, TCS, HDFC Bank, Infosys, Reliance, etc. |
| **Schema** | `data/synthetic/schema.json` (747 lines, all column definitions) |

---

## 🔧 Pipeline — 10-Layer Engine

The `pipeline/main_pipeline.py` orchestrates all modules in sequence:

```
Layer  1 → Forensic Analysis (Beneish M-Score, Altman Z-Score, Piotroski F-Score)
Layer  2 → Feature Engineering (160 engineered features)
Layer  3 → ML Credit Scoring (3-model ensemble + SHAP)
Layer  4 → LSTM Trajectory Prediction (3-year financial trajectory)
Layer  5 → Promoter Network Analysis (contagion risk scoring)
Layer  6 → Satellite Activity Verification (Sentinel-2 imagery)
Layer  7 → GST Intelligence (filing vs revenue cross-validation)
Layer  8 → Monte Carlo Stress Testing (1000 simulations)
Layer  9 → Default DNA Matching (6 archetype fingerprints)
Layer 10 → LLM Agents + CAM Generation (research → bull → bear → DOCX)
```

**Demo output** (Sunrise Textile Mills):
- Decision: `CONDITIONAL_APPROVE`
- Probability of Default: `25.35%`
- Credit Rating: `BB+`
- CAM: `data/processed/CAM_Sunrise_Textile_Mills_YYYYMMDD.docx`

---

## 🧪 Test Suite

```
75 passed, 15 skipped, 1 xfailed — ALL GREEN ✅
```

| Test File | Coverage | Notes |
|---|---|---|
| `test_person1.py` | Dataset generation, Beneish validation, Altman zones, credit scorer, temporal model, data leakage | 15 skipped (need trained models; ML training is longer-running) |
| `test_person2.py` | All 5 modules — network graph, stress test, satellite, GST, DNA matching (49 tests) | All assertions tested with edge cases |
| `test_person3.py` | All LLM agents with mocked APIs — research, bull, bear, CEO interview, CAM generator | Fully mocked to run without API keys |

---

## 🔑 Environment Variables

Copy `.env.example` → `.env` and fill in:

```bash
ANTHROPIC_API_KEY=sk-ant-...         # Required for LLM agents (Claude)
TAVILY_API_KEY=tvly-...              # Required for web research agent
OPENAI_API_KEY=sk-...                # Optional (fallback for Whisper)
SENTINEL_HUB_CLIENT_ID=...          # Optional (satellite imagery)
SENTINEL_HUB_CLIENT_SECRET=...      # Optional (satellite imagery)
```

> **Note:** All modules gracefully degrade to demo/synthetic mode when API keys are not set.

---

## 🛠️ Tech Stack

| Category | Technologies |
|---|---|
| **ML/DL** | XGBoost, LightGBM, scikit-learn, PyTorch (LSTM), SHAP, imbalanced-learn |
| **LLM** | Claude (Anthropic), LangGraph, LangChain |
| **NLP** | Whisper (OpenAI), VADER Sentiment |
| **Search** | Tavily API |
| **Data** | Pandas, NumPy, NetworkX |
| **Visualization** | Plotly, Matplotlib, Streamlit |
| **Document** | python-docx (CAM generation) |
| **Testing** | pytest (75+ tests) |

---

## 📝 License

Built for the Vivriti Capital AI/ML Hackathon. All rights reserved.
