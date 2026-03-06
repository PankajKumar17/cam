#  Yakṣarāja  AI-Powered Credit Decisioning Engine

### Vivriti Capital AI/ML Hackathon

> *Automates end-to-end preparation of Comprehensive Credit Appraisal Memos (CAMs) using **11 innovations** in ML, alternative data, and adversarial LLM agents  from raw financials to a print-ready DOCX in one pipeline call.*

---

##  Architecture Overview

```

                        YAKṢARĀJA ENGINE                              

                                                                      
            
     PERSON 1            PERSON 2            PERSON 3             
     ML Core             Alt Data            LLM + CAM            
                                                                  
     Data Gen           Network Graph      Research Agt        
     Feature Eng        Stress Test        Bull Agent          
     Credit Scorer      Satellite          Bear Agent          
     LSTM Traj          GST Intel          CEO Interview       
     Forensics          DNA Matching       CAM Generator       
            
                                                                      
                           
                                                                       
                                                
                      pipeline/                                        
                      main_pipeline.py                                 
                      (10-Layer Engine)                                
                                                
                                                                       
                                     
               CAM DOCX + Scores JSON                                  
               Network Graph + Stress Charts                           
                                     
                                                                       
                                    
                api/server.py  (FastAPI)                               
                                    
                                                                       
                                    
                frontend/  (Vite + React 19)                           
                Landing  Dashboard  DeepDive                         
                 Reports                                              
                                    

```

---

##  Team Structure

| Member | Module Ownership | Key Deliverables |
|---|---|---|
| **Person 1** | `modules/person1_ml_core/` | Synthetic data generator (30 companies, 160+ features), 3-model ensemble credit scorer, LSTM trajectory model, Beneish/Altman/Piotroski forensics |
| **Person 2** | `modules/person2_alt_data/` | Promoter network contagion (GNN), Monte Carlo stress test (1000 sims), Sentinel-2 satellite scoring, GST truth layer, Default DNA fingerprinting |
| **Person 3** | `modules/person3_llm_cam/` + `api/` + `frontend/` | Tavily research agent, adversarial Bull/Bear LLM agents (LangGraph), CEO interview (Whisper + VADER), 11-section CAM DOCX generator, FastAPI backend, React dashboard |

---

##  Project Structure

```
yaksaraja/
 api/
    server.py                      # FastAPI backend  serves React frontend

 frontend/                          # Vite + React 19 UI
    src/
       pages/
          Landing.jsx            # Hero / company upload page
          Dashboard.jsx          # Dashboard router shell
          Overview.jsx           # Credit scores summary
          DeepDive.jsx           # Financial, network & stress deep dive
          Reports.jsx            # Download CAM & charts
       components/
          Navbar.jsx
          ui.jsx
       api.js                     # Axios client for FastAPI
       App.jsx
       main.jsx
    package.json
    vite.config.js

 modules/
    person1_ml_core/               # Person 1  ML Core
       data_generator.py          # Synthetic dataset (30 companies, FY20092024)
       feature_engineering.py     # 160 features: velocity, Beneish, DNA, ratios
       forensics.py               # Beneish / Altman / Piotroski coordination
       credit_scorer.py           # XGBoost + RF + LightGBM ensemble + SHAP
       temporal_model.py          # LSTM trajectory + early warning system
       validate_dataset.py        # Dataset validation + distribution plots
   
    person2_alt_data/              # Person 2  Alternative Data
       network_graph.py           # MCA21 promoter network + contagion risk
       stress_test.py             # Monte Carlo (1000 sims) + named scenarios
       satellite_module.py        # Sentinel-2 factory activity scoring
       gst_intelligence.py        # GST filing vs bank revenue cross-check
       dna_matching.py            # Default DNA fingerprints (6 archetypes)
   
    person3_llm_cam/               # Person 3  LLM Agents + CAM
       research_agent.py          # LangGraph + Tavily web research agent
       approval_agent.py          # Bull-case LLM agent (structured approval)
       dissent_agent.py           # Bear-case LLM agent + coordinator
       ceo_interview.py           # Whisper transcription + VADER sentiment
       cam_generator.py           # 11-section DOCX CAM generator
   
    web_data_fetcher.py            # Shared web scraping utility

 pipeline/
    excel_parser.py                # Screener.in Excel  financial dict
    main_pipeline.py               # 10-layer integration pipeline

 models/                            # Pre-trained model artefacts
    lstm_trajectory_model.pt
    lgb_model.pkl
    rf_model.pkl
    xgb_model.pkl
    scaler.pkl

 data/
    raw/                           # Uploaded Excel files (runtime)
    processed/                     # Outputs: CAM DOCX, scores JSON, charts
    synthetic/
        intelli_credit_dataset.csv # 352 rows  149 columns
        demo_sunrise_textile.csv   # Single-company demo data
        schema.json                # Full dataset schema

 notebooks/
    demo_sunrise_textile.ipynb     # 27-cell interactive demo walkthrough

 tests/
    test_person1.py                # ML core tests
    test_person2.py                # Alt data tests (49 tests)
    test_person3.py                # LLM agent tests (mocked APIs)

 theme/                             # Design system references
    dashboard-theme (1).md
    landing-page-theme (1).md

 .devcontainer/
    devcontainer.json
 .env.example                       # API keys template
 .gitignore
 requirements.txt
 README.md
```

---

##  Quick Start

### Step 1  Python Backend

```bash
# Clone the repo
git clone https://github.com/PankajKumar17/yaksaraja.git
cd yaksaraja

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Mac/Linux

# Install Python dependencies
pip install -r requirements.txt

# Copy env template and fill in API keys
cp .env.example .env
```

### Step 2  Start the FastAPI Backend

```bash
uvicorn api.server:app --reload --port 8000
# API docs at http://localhost:8000/docs
```

### Step 3  Start the React Frontend

```bash
cd frontend
npm install
npm run dev
# UI at http://localhost:5173
```

### Step 4  Run the Pipeline (CLI)

```bash
# Generate synthetic training dataset
python modules/person1_ml_core/data_generator.py

# Run full end-to-end pipeline
python pipeline/main_pipeline.py
#  data/processed/CAM_<company>_<date>.docx
#  data/processed/scores_<company>.json
```

**Demo output** (Sunrise Textile Mills):
- Decision: `CONDITIONAL_APPROVE`
- Probability of Default: `25.35%`
- Credit Rating: `BB+`

---

##  11 Innovations

| # | Innovation | Module | Owner |
|---|---|---|---|
| 1 | **Beneish M-Score Forensics**  Detects earnings manipulation using 8 financial ratios | `feature_engineering.py` | Person 1 |
| 2 | **3-Model Ensemble Credit Scorer**  XGBoost + RF + LightGBM with SMOTE, temporal split, SHAP | `credit_scorer.py` | Person 1 |
| 3 | **LSTM Trajectory Model**  Predicts 3-year financial trajectory with early warning | `temporal_model.py` | Person 1 |
| 4 | **Model Disagreement Signal**  Flags high-uncertainty credits where sub-models diverge | `credit_scorer.py` | Person 1 |
| 5 | **Promoter Network Contagion**  MCA21 director graph with NPA contagion risk scoring | `network_graph.py` | Person 2 |
| 6 | **Monte Carlo Stress Test**  1000 simulations across rate/revenue/margin shocks, 4 named scenarios | `stress_test.py` | Person 2 |
| 7 | **Sentinel-2 Satellite Activity**  Factory utilisation scored from satellite imagery | `satellite_module.py` | Person 2 |
| 8 | **GST Truth Layer**  GST filing vs bank-reported revenue mismatch detection | `gst_intelligence.py` | Person 2 |
| 9 | **Default DNA Fingerprinting**  6 historical default archetypes (IL&FS, Kingfisher, DHFL, Café Coffee Day, Bhushan Steel, Jet Airways) | `dna_matching.py` | Person 2 |
| 10 | **Adversarial Bull/Bear LLM Agents**  LangGraph approve vs. dissent debate, coordinator synthesises final verdict | `approval_agent.py` + `dissent_agent.py` | Person 3 |
| 11 | **CEO Interview Sentiment**  Whisper transcription + VADER + deflection detection | `ceo_interview.py` | Person 3 |

### Bonus Innovations

| Innovation | Module |
|---|---|
| Tavily Web Research Agent (LangGraph state machine) | `research_agent.py` |
| 11-Section DOCX CAM Generator | `cam_generator.py` |
| Altman Z-Score + Piotroski F-Score | `feature_engineering.py` |
| Screener.in Excel Parser | `excel_parser.py` |

---

##  Pipeline  10 Layers

```
Layer  1  Forensic Analysis      (Beneish M-Score, Altman Z-Score, Piotroski)
Layer  2  Feature Engineering    (160 engineered features)
Layer  3  ML Credit Scoring      (3-model ensemble + SHAP)
Layer  4  LSTM Trajectory        (3-year financial trajectory)
Layer  5  Network Analysis       (promoter contagion risk)
Layer  6  Satellite Verification (Sentinel-2 factory imagery)
Layer  7  GST Intelligence       (filing vs revenue cross-validate)
Layer  8  Monte Carlo Stress     (1000 simulations)
Layer  9  Default DNA Matching   (6 archetype fingerprints)
Layer 10  LLM Agents + CAM       (research  bull  bear  DOCX)
```

---

##  Dataset Details

| Property | Value |
|---|---|
| **Rows** | 352 (30 companies  ~12 fiscal years) |
| **Raw Columns** | 149 |
| **Engineered Columns** | 160 |
| **Companies** | 30 (15 defaulted + 15 healthy) |
| **Fiscal Years** | FY2009  FY2024 |
| **Notable Companies** | Satyam, IL&FS, Kingfisher, DHFL, Jet Airways, Bhushan Steel, TCS, HDFC Bank, Infosys, Reliance, etc. |
| **Schema** | `data/synthetic/schema.json` |

---

##  Tests

```bash
python -m pytest tests/ -v
# 75 passed, 15 skipped, 1 xfailed
```

| File | Coverage |
|---|---|
| `test_person1.py` | Dataset generation, Beneish, Altman, credit scorer, LSTM, data leakage |
| `test_person2.py` | All 5 alt-data modules  49 tests with edge cases |
| `test_person3.py` | All LLM agents with fully mocked APIs |

---

##  Environment Variables

```bash
# .env  (copy from .env.example)
ANTHROPIC_API_KEY=sk-ant-...           # LLM agents (Claude)
TAVILY_API_KEY=tvly-...                # Web research agent
OPENAI_API_KEY=sk-...                  # Whisper transcription (optional)
SENTINEL_HUB_CLIENT_ID=...            # Satellite imagery (optional)
SENTINEL_HUB_CLIENT_SECRET=...        # Satellite imagery (optional)
```

> All modules degrade gracefully to demo/synthetic mode when API keys are absent.

---

##  Tech Stack

| Category | Technologies |
|---|---|
| **Frontend** | Vite 7, React 19, React Router 7, Tailwind CSS 4, Framer Motion, Recharts, Lucide React, Axios |
| **Backend** | FastAPI, Uvicorn, Python 3.11+ |
| **ML / DL** | XGBoost, LightGBM, scikit-learn, PyTorch (LSTM), SHAP, imbalanced-learn |
| **LLM** | Google Gemini (google-generativeai), LangGraph, LangChain |
| **NLP / Audio** | Whisper (openai-whisper), VADER Sentiment, librosa, Transformers |
| **Alternative Data** | NetworkX, tifffile (Sentinel-2), Pillow, Tavily API, BeautifulSoup |
| **Data** | Pandas, NumPy, openpyxl, SciPy, statsmodels |
| **Visualization** | Plotly, Matplotlib, Seaborn |
| **Document Gen** | python-docx |
| **Testing** | pytest |

---

##  License

Built for the Vivriti Capital AI/ML Hackathon. All rights reserved.
