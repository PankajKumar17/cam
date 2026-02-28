# 🏦 Intelli-Credit — AI-Powered Credit Decisioning Engine
### Vivriti Capital AI/ML Hackathon

> *Automates end-to-end preparation of Comprehensive Credit Appraisal Memos (CAMs) using 11 innovations in ML, alternative data, and adversarial LLM agents.*

---

## Team Structure

| Member | Module Ownership |
|---|---|
| **Person 1** | Data Pipeline + ML Core (Innovations 1–4) |
| **Person 2** | Alternative Data + Graph (Innovations 5–8) |
| **Person 3** | LLM Agents + Dashboard + CAM (Innovations 9–11) |

---

## Project Structure

```
intelli_credit/
│
├── data/
│   ├── raw/                        # Raw uploaded files
│   ├── processed/                  # Cleaned, computed features
│   └── synthetic/                  # Generated dataset (replace with Prowess)
│
├── modules/
│   ├── person1_ml_core/            # Person 1
│   │   ├── data_generator.py       # Synthetic dataset generator
│   │   ├── feature_engineering.py  # All 146 features
│   │   ├── forensics.py            # Beneish + Piotroski + Altman
│   │   ├── temporal_model.py       # TFT / LSTM trajectory model
│   │   └── credit_scorer.py        # XGBoost + RF + LightGBM ensemble
│   │
│   ├── person2_alt_data/           # Person 2
│   │   ├── satellite_module.py     # Sentinel-2 activity score
│   │   ├── gst_intelligence.py     # GST truth layer
│   │   ├── network_graph.py        # MCA21 director network + GNN
│   │   ├── stress_test.py          # Monte Carlo stress engine
│   │   └── dna_matching.py         # Default DNA fingerprints
│   │
│   └── person3_llm_cam/            # Person 3
│       ├── research_agent.py       # Tavily web research agent
│       ├── approval_agent.py       # Bull case LLM agent
│       ├── dissent_agent.py        # Bear case adversarial agent
│       ├── cam_generator.py        # Final CAM DOCX/PDF writer
│       └── ceo_interview.py        # Whisper + sentiment analysis
│
├── pipeline/
│   └── main_pipeline.py            # Integrates all modules end-to-end
│
├── dashboard/
│   └── app.py                      # Streamlit UI
│
├── notebooks/
│   └── demo_sunrise_textile.ipynb  # Hackathon demo notebook
│
├── tests/
│   ├── test_person1.py
│   ├── test_person2.py
│   └── test_person3.py
│
├── .env.example                    # API keys template
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Quick Start

```bash
# Clone repo
git clone https://github.com/YOUR_ORG/intelli-credit.git
cd intelli-credit

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Copy env template
cp .env.example .env
# Fill in your API keys in .env

# Generate synthetic dataset
python modules/person1_ml_core/data_generator.py

# Run demo
streamlit run dashboard/app.py
```

---

## Innovations Implemented

| # | Innovation | Owner | Status |
|---|---|---|---|
| 1 | Beneish M-Score Forensics | Person 1 | ⬜ |
| 2 | Temporal Fusion Transformer | Person 1 | ⬜ |
| 3 | Network Contagion GNN | Person 2 | ⬜ |
| 4 | Monte Carlo Stress Test | Person 2 | ⬜ |
| 5 | Adversarial CAM Agents | Person 3 | ⬜ |
| 6 | Satellite Activity Score | Person 2 | ⬜ |
| 7 | GST Truth Layer | Person 2 | ⬜ |
| 8 | Default DNA Matching | Person 2 | ⬜ |
| 9 | Auditor Signal NLP | Person 1 | ⬜ |
| 10 | CEO Interview Sentiment | Person 3 | ⬜ |
| 11 | Model Disagreement Signal | Person 1 | ⬜ |
