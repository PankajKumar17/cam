# Intelli-Credit — GitHub Copilot Prompt Guide
## Sequential Prompts for All 3 Team Members

> **How to use:** Open GitHub Copilot Chat in VS Code (select Claude Opus 4.6 model).
> Copy each prompt EXACTLY as written. Run them in ORDER — each builds on the previous.
> After each prompt, test the output before moving to the next.

---

# ════════════════════════════════════════════════════════
# PERSON 1 — DATA PIPELINE + ML CORE
# Owns: Innovations 1, 2, 9, 11 + Dataset + Feature Engineering
# ════════════════════════════════════════════════════════

---

## PROMPT P1-1: Understand the Dataset

```
I am building an AI-powered Credit Decisioning Engine called Intelli-Credit
for the Vivriti Capital hackathon. I am Person 1 responsible for the ML core.

First, read the file modules/person1_ml_core/data_generator.py completely.

Then explain to me:
1. What companies are in the synthetic dataset and why
2. What the deterioration_factor does for defaulted companies
3. What all computed features mean (ratios, velocity, Beneish, Altman, Piotroski)
4. How to run the generator and what output files it creates

Do not write any code yet. Just explain everything clearly.
```

---

## PROMPT P1-2: Run and Validate the Dataset

```
Now help me run and validate the synthetic dataset generator.

File: modules/person1_ml_core/data_generator.py

Step 1: Run the generator and show me how to verify:
- Total rows count
- Label distribution (should be ~35% defaults)
- No completely null columns
- DSCR values are realistic (healthy companies: 1.5-3.5, defaulted: 0.5-1.2)
- Beneish M-Score correctly flags defaulted companies above -2.22

Step 2: Write a validation function that checks all of the above
and prints a PASS/FAIL report for each check.

Step 3: Create a simple visualization showing:
- DSCR distribution for healthy vs defaulted companies (histogram)
- Beneish M-Score distribution for both groups
- DSCR trajectory over years for 3 defaulted companies

Save validation code to: modules/person1_ml_core/validate_dataset.py
Save charts to: data/synthetic/validation_charts/
```

---

## PROMPT P1-3: Feature Engineering Pipeline

```
Now build the complete feature engineering pipeline.

Context: The dataset at data/synthetic/intelli_credit_dataset.csv already has
raw financials and basic ratios. I need to add all remaining features.

Build: modules/person1_ml_core/feature_engineering.py

This module must:

1. LOAD the dataset from CSV

2. COMPUTE velocity features (year-on-year changes):
   For each of: revenue, ebitda, pat, cfo, total_equity, total_debt
   Compute: growth rate = (value_t - value_t-1) / abs(value_t-1)
   Also compute: dscr_velocity, icr_velocity, de_velocity
   Also compute: dscr_acceleration (change in velocity)
   Also compute: dscr_3yr_slope using linear regression over rolling 3 years
   Also compute: months_to_dscr_danger (at current velocity, months until DSCR < 1.0)

3. VALIDATE Beneish M-Score on known fraud case (Satyam):
   Load Satyam rows from dataset
   Compute M-Score
   Assert M-Score > -2.22 for years near default
   Print result as: PASS or FAIL

4. COMPUTE Default DNA similarity scores:
   Build fingerprint vectors for 5 historical defaults:
   IL&FS pattern: high st_debt_to_assets, low cfo_to_debt, high cwip_to_assets
   DHFL pattern: high related_party_tx_to_rev, high receivables_days, promoter_pledge > 0.5
   Jet Airways pattern: negative revenue_growth, high employee_cost_to_rev, low current_ratio
   Videocon pattern: high contagion_risk_score, high promoter_pledge, negative roe
   Satyam pattern: high beneish_dsri, positive beneish_tata, auditor_distress_score > 3

   For each borrower row, compute cosine similarity to each fingerprint
   Add columns: similarity_to_ilfs, similarity_to_dhfl, similarity_to_jet,
                similarity_to_videocon, similarity_to_satyam,
                closest_default_archetype, max_archetype_similarity

5. SAVE final feature matrix to: data/processed/feature_matrix.csv

The function signature must be:
def build_feature_matrix(raw_csv_path: str, output_path: str) -> pd.DataFrame

Use pandas, numpy, and sklearn.metrics.pairwise.cosine_similarity only.
Add clear docstrings to every function.
```

---

## PROMPT P1-4: XGBoost + Ensemble Credit Scorer

```
Now build the core ML credit scoring engine.

Build: modules/person1_ml_core/credit_scorer.py

This is the most important ML file in the project. It must implement:

PART A — Data Preparation:
1. Load feature matrix from data/processed/feature_matrix.csv
2. Split into train (FY2009-FY2020) and test (FY2021-FY2024) by year
   This prevents data leakage — never use future data to predict past
3. Apply SMOTE to training data to handle class imbalance
   Use sampling_strategy=0.5 (make defaults 50% of majority class size)
4. Scale features using StandardScaler
   Save scaler to models/scaler.pkl for inference

PART B — Three Models (as validated by Addo et al. 2018 research paper):
Train all three:
1. XGBoost (primary model):
   params: n_estimators=300, max_depth=6, learning_rate=0.05,
           subsample=0.8, colsample_bytree=0.8, eval_metric='auc'
   Use early stopping on validation set

2. Random Forest (secondary):
   params: n_estimators=200, max_depth=8, min_samples_leaf=5

3. LightGBM (tertiary):
   params: n_estimators=300, max_depth=6, learning_rate=0.05,
           num_leaves=31

PART C — Ensemble and Disagreement Signal:
1. Weighted ensemble: final_pd = 0.5*xgb + 0.3*lgb + 0.2*rf
2. Model disagreement: disagreement = max(pd_xgb, pd_rf, pd_lgb) - min(...)
3. If disagreement > 0.30: flag = "HIGH_UNCERTAINTY"
   If disagreement > 0.15: flag = "MODERATE_UNCERTAINTY"
   Else: flag = "CONSENSUS"
   Add column: model_disagreement_flag to output

PART D — Three Outputs:
Using the ensemble PD score:
1. lending_decision: "APPROVE" if pd < 0.35, "REVIEW" if 0.35-0.60, "REJECT" if > 0.60
2. credit_limit: If approved, recommended limit in Crores
   Formula: base_limit * (1 - pd) * dscr_factor
   base_limit = revenue * 0.25 (working capital heuristic)
3. risk_premium: base_spread + pd_adjustment
   base_spread = 2.5% (above repo rate)
   pd_adjustment = pd * 8.0 (higher PD = higher spread)

PART E — Evaluation:
Print both AUC and RMSE (both metrics as recommended by research paper)
Print classification report with precision, recall, F1
Save all three models to: models/xgb_model.pkl, models/rf_model.pkl, models/lgb_model.pkl

PART F — SHAP Explanations:
For any single prediction, generate SHAP waterfall chart
showing top 10 features that drove the decision
Save function: explain_prediction(company_name, fiscal_year) -> dict

Main function signature:
def train_and_evaluate() -> dict  # returns all metrics
def predict(feature_row: pd.Series) -> dict  # returns PD, limit, spread, SHAP

Save models directory. Add clear comments explaining every step.
```

---

## PROMPT P1-5: Temporal Fusion Model

```
Now build the temporal trajectory model.

Build: modules/person1_ml_core/temporal_model.py

Context: The research paper proved that trajectory predicts default better
than snapshots. A company with DSCR falling from 3.2 → 2.1 → 1.8 over 3 years
is far more dangerous than one with stable DSCR of 1.8.

PART A — Data Preparation:
1. Load feature_matrix.csv
2. For each company, create time-series sequences of length 5 years
3. Features per timestep: dscr, interest_coverage, debt_to_equity,
   ebitda_margin, net_margin, cfo_to_assets, revenue_growth
4. Label: 1 if company defaulted within 2 years of the sequence end, else 0
5. Split: 80% train, 20% test (by company, not by row — prevent leakage)

PART B — LSTM Model:
Build a simple LSTM using PyTorch:
- Input: (batch, 5 timesteps, 7 features)
- LSTM layer: hidden_size=64, num_layers=2, dropout=0.3
- Fully connected: 64 → 32 → 1
- Output: probability of default within 2 years

Train for 50 epochs, batch size 32, Adam optimizer, BCELoss
Save model to: models/lstm_trajectory_model.pt

PART C — Early Warning Score:
For any company's last 5 years of data:
Run through LSTM
Output: trajectory_risk_score (0-1)
Output: estimated_months_to_distress based on DSCR velocity
Output: warning_level: GREEN / YELLOW / ORANGE / RED

PART D — Visualization:
For demo company Sunrise Textile Mills:
Plot DSCR trajectory with trendline
Mark the point where trajectory crosses 1.0
Show: "Model predicts DSCR below 1.0 in X months"

Function signatures:
def train_lstm() -> dict  # returns loss history and AUC
def get_trajectory_score(company_name: str, data: pd.DataFrame) -> dict
def plot_trajectory(company_name: str, data: pd.DataFrame)

Use PyTorch only. Add clear comments.
```

---

## PROMPT P1-6: Test Suite for Person 1

```
Write a complete test suite for all Person 1 modules.

Create: tests/test_person1.py

Tests to include:

1. test_dataset_generates_correctly:
   Run data_generator.py
   Assert output CSV exists
   Assert 200+ rows
   Assert columns match expected schema (at least 50 key columns)
   Assert label column has both 0 and 1 values

2. test_beneish_flags_satyam:
   Load Satyam rows from dataset
   Run Beneish M-Score
   Assert M-Score > -2.22 in at least one year near default
   This is the academic validation test

3. test_altman_zones_make_sense:
   Healthy companies: Assert majority in SAFE zone
   Defaulted companies: Assert majority in DANGER zone 2 years before default

4. test_model_produces_three_outputs:
   Run credit_scorer on one row
   Assert output contains: pd_score, credit_limit, risk_premium
   Assert pd_score is between 0 and 1
   Assert credit_limit > 0 for approved companies
   Assert risk_premium between 2.5 and 15.0

5. test_model_disagreement_signal:
   Construct a row where financials look contradictory
   Assert disagreement_flag != CONSENSUS

6. test_no_data_leakage:
   Assert test set years are all > 2020
   Assert train set years are all <= 2020

Use pytest. Run with: pytest tests/test_person1.py -v
```

---

# ════════════════════════════════════════════════════════
# PERSON 2 — ALTERNATIVE DATA + GRAPH
# Owns: Innovations 3, 4, 6, 7, 8
# ════════════════════════════════════════════════════════

---

## PROMPT P2-1: Network Graph Module

```
I am Person 2 on the Intelli-Credit project. I am building the
Alternative Data modules. My work feeds into the main ML model.

Build: modules/person2_alt_data/network_graph.py

This module builds a Knowledge Graph of promoter-company relationships
and computes a Network Contagion Risk Score using the MCA21 dataset.

PART A — Graph Construction:
1. Load MCA director-company linkage data
   For now, generate synthetic MCA-like data with these columns:
   din (Director ID), company_cin (Company ID), company_name,
   director_name, appointment_date, cessation_date, company_status
   Generate 500 directors, 1000 companies, ~2500 linkages

2. Build NetworkX bipartite graph:
   Nodes: Directors (type=director) and Companies (type=company)
   Edges: Director directed a Company (with appointment date as attribute)

3. For any target company (e.g., Sunrise Textile Mills):
   Find all its directors
   Find all other companies those directors run
   Build the promoter's complete company network
   Identify: which of those companies are NPA / struck off

PART B — Contagion Risk Score:
Compute these network metrics for any borrower:
1. promoter_total_companies: total companies in network
2. promoter_npa_companies: companies with status = NPA
3. network_npa_ratio: npa_companies / total_companies
4. network_clustering_coefficient: how interconnected the promoter group is
5. contagion_risk_score: weighted combination
   = 0.4 * network_npa_ratio + 0.3 * clustering + 0.3 * size_factor
   Output: 0 to 1 (1 = maximum contagion risk)

PART C — Visualization:
Generate an interactive network graph using plotly or networkx + matplotlib
showing:
- Target company in RED
- Related companies (color by status: GREEN=healthy, ORANGE=stressed, RED=NPA)
- Directors as small grey nodes connecting companies
- Node size proportional to company debt
Save as: data/processed/network_graph_[company_name].html

Function signatures:
def build_promoter_network(company_cin: str) -> nx.Graph
def compute_contagion_score(company_cin: str) -> dict
def visualize_network(company_cin: str, output_path: str)

Use networkx, pandas, plotly. Add clear docstrings.
```

---

## PROMPT P2-2: Monte Carlo Stress Test Engine

```
Build the Monte Carlo stress testing engine.

Build: modules/person2_alt_data/stress_test.py

Context: Instead of a binary approve/reject, we output a PROBABILITY
DISTRIBUTION of outcomes across 1000 macro scenarios. This is how
real credit committees think — in distributions, not binary decisions.

PART A — Macro Scenario Engine:
Define 5 macro shock variables with historical distributions from RBI:
1. repo_rate_shock: normal(0, 1.5) → range -2% to +4%
2. inflation_shock: normal(0, 2.0) → range -1% to +6%
3. revenue_shock: normal(0, 0.15) → range -40% to +20%
4. commodity_price_shock: normal(0, 0.20) → range -30% to +50%
5. customer_default_probability: uniform(0, 0.3)

PART B — DSCR Simulation:
For a given borrower's current financials:
Run 1000 Monte Carlo simulations:
For each simulation:
1. Draw random values for all 5 shock variables
2. Recompute EBITDA = base_ebitda * (1 + revenue_shock) * margin_impact(shocks)
3. Recompute interest = base_interest * (1 + rate_shock * 0.5)
4. Recompute DSCR = (new_pat + depreciation) / new_debt_service
5. Record: simulated DSCR at maturity (3 years forward)

PART C — Outputs:
From 1000 simulated DSCR values:
1. P10 DSCR: worst 10% scenario
2. P50 DSCR: median scenario (base case)
3. P90 DSCR: best 90% scenario
4. default_probability_3yr: % of simulations where DSCR < 1.0
5. covenant_trigger_level: DSCR level where 20% of simulations are below
   (this becomes the recommended covenant trigger)

PART D — Visualization:
Plot probability distribution of DSCR outcomes as histogram
Mark: P10, P50, P90 lines
Mark: danger zone (DSCR < 1.0) in red
Add title: "1000 Macro Scenarios — DSCR Distribution at Loan Maturity"
Save to: data/processed/stress_test_[company_name].png

PART E — Named Scenarios:
Also run 4 named stress scenarios:
1. "RBI Rate Hike +200bps": repo_rate_shock = +2.0, all others = 0
2. "Revenue Decline -20%": revenue_shock = -0.20, all others = 0
3. "Cotton Price +30%": commodity_shock = +0.30, all others = 0 (for textile)
4. "Combined Adverse": all shocks at P10 levels simultaneously
Report DSCR for each named scenario explicitly.

Function signatures:
def run_monte_carlo(company_financials: dict, n_simulations: int = 1000) -> dict
def get_named_scenarios(company_financials: dict) -> dict
def plot_stress_distribution(results: dict, company_name: str, output_path: str)

Use numpy, pandas, matplotlib only. No external ML libraries needed.
```

---

## PROMPT P2-3: Satellite Activity Module

```
Build the satellite activity scoring module.

Build: modules/person2_alt_data/satellite_module.py

Context: We verify that the factory is actually running — not just on paper.
We use Sentinel-2 free satellite imagery (European Space Agency).

PART A — Sentinel Hub Integration:
1. Configure Sentinel Hub API using credentials from .env file
2. Build function to fetch Sentinel-2 imagery for any GPS coordinates
3. Default to Suzlon Energy Pune factory for testing:
   GPS: latitude=18.52, longitude=73.85
   Date range: last 6 months (two dates: 6 months ago and today)

PART B — Activity Score Computation:
From satellite image:
1. Compute NDVI (Normalized Difference Vegetation Index):
   NDVI = (NIR - Red) / (NIR + Red)
   For industrial areas: low NDVI = active (no vegetation = paved/built)
2. Compute mean pixel brightness (proxy for heat/activity)
3. Compare current vs 12 months ago:
   brightness_delta = current_brightness - year_ago_brightness
   If large negative delta → activity has dropped → concern
4. Activity Score = 100 * (normalized combination of brightness + consistency)

PART C — Classification:
activity_score > 70: ACTIVE
activity_score 50-70: MODERATE
activity_score 30-50: LOW
activity_score < 30: DORMANT

PART D — Fallback (if API unavailable):
If Sentinel Hub API fails or is not configured:
Return synthetic activity score based on company financial health
Print warning: "Satellite API unavailable — using proxy score"
This ensures demo works even without API keys

PART E — Revenue Consistency Check:
For manufacturers: E-way bill volume should be proportional to revenue
satellite_vs_revenue_flag = 1 if activity_score < 40 but revenue > industry_avg

Function signatures:
def fetch_satellite_image(lat: float, lon: float, date: str) -> np.ndarray
def compute_activity_score(image_current, image_baseline) -> dict
def get_factory_activity(company_name: str, lat: float, lon: float) -> dict

Handle all API exceptions gracefully. Include fallback mode.
```

---

## PROMPT P2-4: GST Intelligence + Default DNA Modules

```
Build two modules:

MODULE 1: modules/person2_alt_data/gst_intelligence.py

Context: GST data is filed to the government — harder to fake than P&L.
We compare GST-declared revenue vs bank-declared revenue to detect fraud.

Build:
1. Synthetic GST data generator for demo company:
   For healthy companies: gst_revenue ≈ bank_revenue (within 5%)
   For distressed companies: gst_revenue = bank_revenue * random(0.55, 0.85)
   This simulates companies inflating revenue shown to banks

2. Key computations:
   gst_vs_bank_divergence = (bank_revenue - gst_revenue) / gst_revenue
   gst_divergence_flag = 1 if divergence > 0.20 (>20% inflation = red flag)
   filing_delay_score = avg days late for last 12 GST filings
   ewaybill_consistency = ewaybill_implied_revenue / gst_declared_revenue

3. Fraud risk level:
   HIGH: divergence > 40%
   MEDIUM: divergence 20-40%
   LOW: divergence < 20%

Function: def analyze_gst_data(company_name: str, bank_revenue: float) -> dict

---

MODULE 2: modules/person2_alt_data/dna_matching.py

Context: Encode financial fingerprints of India's major corporate collapses
and check if the borrower resembles any of them 12-24 months before their collapse.

Build:
1. Define 6 default archetypes as feature vectors:

IL_IFS_FINGERPRINT = {
   "st_debt_to_lt_assets_ratio": 2.1,  # short funding long assets
   "cfo_to_debt": 0.02,                 # terrible cash coverage of debt
   "debt_growth_3yr": 0.45,             # rapid debt accumulation
   "current_ratio": 0.6,               # severe liquidity stress
}

DHFL_FINGERPRINT = {
   "related_party_tx_to_rev": 0.35,    # massive fund diversion
   "receivables_days": 180,            # fake receivables
   "promoter_pledge_pct": 0.72,        # desperate pledging
   "gst_vs_bank_divergence": 0.42,     # revenue inflation
}

JET_AIRWAYS_FINGERPRINT = {
   "revenue_growth": -0.15,            # declining revenue
   "employee_cost_to_rev": 0.35,       # cost not reducing with revenue
   "current_ratio": 0.45,              # severe working capital stress
   "free_cash_flow_margin": -0.08,     # burning cash
}

VIDEOCON_FINGERPRINT = {
   "contagion_risk_score": 0.75,       # group contagion
   "promoter_pledge_pct": 0.85,        # extreme pledging
   "roe": -0.12,                       # destroying equity value
   "network_npa_ratio": 0.45,          # group companies failing
}

SATYAM_FINGERPRINT = {
   "beneish_dsri": 1.35,              # receivables manipulation
   "beneish_tata": 0.09,              # accruals = manipulation
   "cfo_to_pat": 0.08,               # cash flow disconnected from profit
   "auditor_distress_score": 1,       # auditor discomfort
}

KINGFISHER_FINGERPRINT = {
   "revenue_growth": -0.25,
   "debt_to_equity": 12.0,
   "interest_coverage": 0.3,
   "promoter_pledge_pct": 0.90,
}

2. For any borrower row, compute similarity to each fingerprint:
   Normalize both vectors
   Compute cosine similarity
   Return: {archetype: similarity_score} dict
   Return: closest_archetype and max_similarity
   Return: warning text if max_similarity > 0.75

Function signatures:
def compute_dna_similarity(borrower_features: dict) -> dict
def get_dna_warning(similarity_results: dict) -> str
```

---

## PROMPT P2-5: Test Suite for Person 2

```
Write complete tests for all Person 2 modules.

Create: tests/test_person2.py

1. test_network_graph_builds_correctly:
   Build network for demo company
   Assert graph has nodes and edges
   Assert contagion_risk_score is between 0 and 1
   Assert output dict has all required keys

2. test_monte_carlo_produces_distribution:
   Run 1000 simulations for demo company
   Assert output contains P10, P50, P90
   Assert P10 < P50 < P90 (correct ordering)
   Assert default_probability_3yr is between 0 and 1
   Assert covenant_trigger_level is between 0.8 and 2.0

3. test_stress_named_scenarios:
   Run 4 named scenarios
   Assert rate hike scenario has lower DSCR than base case
   Assert revenue decline scenario has lower DSCR than base case

4. test_gst_divergence_detection:
   Create company with 45% revenue inflation
   Assert gst_divergence_flag = 1
   Assert fraud_risk_level = HIGH
   Create company with 5% divergence
   Assert gst_divergence_flag = 0

5. test_dna_satyam_fingerprint:
   Create a borrower with Satyam-like features
   (high beneish_dsri, positive beneish_tata, low cfo_to_pat)
   Assert closest_archetype = SATYAM
   Assert similarity > 0.70

6. test_satellite_fallback:
   Disable API key in test
   Run satellite module
   Assert returns valid dict (fallback mode)
   Assert activity_category is one of: ACTIVE/MODERATE/LOW/DORMANT

Use pytest. Run with: pytest tests/test_person2.py -v
```

---

# ════════════════════════════════════════════════════════
# PERSON 3 — LLM AGENTS + CAM + DASHBOARD
# Owns: Innovations 5, 10, 11 + Final Output + UI
# ════════════════════════════════════════════════════════

---

## PROMPT P3-1: Research Agent

```
I am Person 3 on the Intelli-Credit project. I own the LLM agents,
CAM generation, CEO interview analysis, and the Streamlit dashboard.

Build: modules/person3_llm_cam/research_agent.py

Context: The research agent performs web-scale secondary research
on the borrower company and their industry before the CAM is written.

Build a LangGraph-based research agent that:

PART A — Web Research:
Uses Tavily Search API to find:
1. Recent news about the company (last 12 months)
   Query: "[Company Name] news 2024 financial"
2. Industry outlook
   Query: "[Sector] industry India outlook 2024 challenges"
3. Regulatory environment
   Query: "[Sector] India regulatory RBI SEBI 2024"
4. Key competitors health
   Query: "[Sector] India major companies performance"
5. Promoter background
   Query: "[Promoter Name] company India news"

PART B — Intelligence Extraction:
For each search result, use Claude API to extract:
- Sentiment: POSITIVE / NEGATIVE / NEUTRAL
- Key facts relevant to credit assessment
- Any red flags mentioned
- Any positive signals mentioned

PART C — Structured Output:
Return a structured research summary dict:
{
  "company_news_summary": "...",
  "industry_outlook": "POSITIVE/NEUTRAL/NEGATIVE",
  "key_risks_found": ["risk1", "risk2"],
  "key_positives_found": ["positive1"],
  "promoter_red_flags": [],
  "research_sources": ["url1", "url2"],
  "research_sentiment_score": 0.65  # 0=very negative, 1=very positive
}

PART D — Fallback:
If Tavily API is unavailable:
Return synthetic research summary for demo company
This ensures demo works without API keys

Function signatures:
def run_research(company_name: str, sector: str, promoter_name: str) -> dict

Use langchain, anthropic, and tavily-python.
Handle all API errors gracefully.
Load API keys from .env file using python-dotenv.
```

---

## PROMPT P3-2: Adversarial CAM Agents

```
Build the adversarial two-agent CAM writing system.
This is the most important innovation in Person 3's work.

Build: modules/person3_llm_cam/approval_agent.py
Build: modules/person3_llm_cam/dissent_agent.py

Context: Instead of one LLM writing a CAM, we have TWO agents with
OPPOSITE objectives debating the credit decision. This mirrors how
real credit committees operate with a devil's advocate.

PART A — Approval Agent (modules/person3_llm_cam/approval_agent.py):

System prompt for Approval Agent:
"You are a senior credit analyst at Vivriti Capital. Your job is to
write the strongest possible case FOR approving this loan application.
Use all available data — financial ratios, industry research, management
quality, collateral — to build a compelling bull case for lending.
Be specific with numbers. Reference actual data points."

Build function: def write_bull_case(company_data: dict, research: dict) -> str
Input: all company financials, ML scores, research summary
Output: structured bull case text (400-600 words)

Structure of bull case:
1. Executive Summary (positive framing)
2. Financial Strengths (top 3-5 positive ratios)
3. Business Momentum (growth signals)
4. Management Quality (positive signals from CEO interview)
5. Industry Tailwinds
6. Risk Mitigants

---

PART B — Dissent Agent (modules/person3_llm_cam/dissent_agent.py):

System prompt for Dissent Agent:
"You are the devil's advocate on Vivriti Capital's credit committee.
Your ONLY job is to find every possible reason NOT to approve this loan.
Challenge every optimistic assumption. Find every red flag in the data.
Be specific and cite exact numbers. You must produce at least 4-5 
counter-arguments regardless of how strong the application looks."

Build function: def write_bear_case(company_data: dict, approval_text: str, research: dict) -> str
Input: all company data + the approval agent's text (to argue against)
Output: structured bear case text (400-600 words)

Structure of bear case:
1. Critical Concerns (top 3-5 red flags with exact numbers)
2. Challenges to Bull Case Assumptions (specifically address approval agent's claims)
3. Hidden Risks (network risk, trajectory, audit signals)
4. Stress Scenario Impact
5. Recommended Conditions if Approved (covenants, guarantees)

---

PART C — Coordinator (in dissent_agent.py):

Build function: def synthesize_cam_recommendation(bull_case: str, bear_case: str, scores: dict) -> dict

Produces final balanced recommendation:
{
  "lending_decision": "CONDITIONAL_APPROVE" / "REJECT" / "APPROVE",
  "recommended_limit_cr": float,
  "recommended_rate_pct": float,
  "key_conditions": ["DSCR covenant at 1.2", "Promoter guarantee", ...],
  "bull_summary": "...",  # 2-3 sentence summary of bull case
  "bear_summary": "...",  # 2-3 sentence summary of bear case
  "final_rationale": "...",  # balanced final paragraph
}

Use Anthropic API (Claude). Load key from .env.
Add retry logic for API failures.
```

---

## PROMPT P3-3: CEO Interview Sentiment Module

```
Build the CEO interview sentiment analysis module.

Build: modules/person3_llm_cam/ceo_interview.py

Context: A 5-minute interview with the CEO/promoter is recorded.
We analyze it for linguistic deception markers, sentiment trajectory,
and topic-specific confidence. "We don't score personality — we score
consistency between what the financials show and what the CEO says."

PART A — Transcription:
1. Accept input: audio file path (mp3/wav/mp4)
2. Use OpenAI Whisper to transcribe
3. Return: full transcript text

PART B — Topic Segmentation:
Identify segments about these topics in the transcript:
- revenue_and_growth
- debt_and_liabilities
- competition_and_market
- future_outlook
- receivables_and_working_capital
- management_team

PART C — Sentiment Analysis per Topic:
For each topic segment:
1. VADER sentiment score (-1 to +1)
2. Hedging language count: words like "approximately", "we expect",
   "should", "might", "we believe", "around", "roughly"
3. Overconfidence markers: "will definitely", "guaranteed", "certain",
   "absolutely", "no doubt"
4. Deflection detection: did they answer the question or pivot?
   (use Claude API to classify each answer as DIRECT / PARTIAL / DEFLECTED)

PART D — Key Scores:
ceo_sentiment_overall: average VADER across all segments
ceo_sentiment_debt: VADER score for debt segment specifically
   (negative score when discussing debt = honest acknowledgment)
   (positive score when discussing debt = possible denial)
ceo_deflection_score: deflected_answers / total_questions
ceo_overconfidence_score: overconfidence_markers / total_words * 100
ceo_specificity_score: sentences_with_numbers / total_sentences

PART E — Red Flag Detection:
Flag if:
- Deflection score > 0.4 (avoiding questions)
- Sentiment_debt > 0.5 (too positive about debt — suspicious)
- Sentiment divergence > 0.6 (very positive on revenue, very negative on debt)
- Overconfidence score > 0.3 (too many guarantees)

PART F — Fallback:
If no audio file provided:
Return synthetic scores based on company financial health
Print: "No interview provided — using proxy scores from financial data"

Function signatures:
def transcribe_interview(audio_path: str) -> str
def analyze_interview(transcript: str) -> dict
def get_management_quality_score(analysis: dict) -> float  # 0-100

Use whisper, vaderSentiment, anthropic. Handle all exceptions.
```

---

## PROMPT P3-4: CAM Generator

```
Build the final CAM document generator.

Build: modules/person3_llm_cam/cam_generator.py

Context: This module takes ALL outputs from Person 1 + Person 2 + Person 3
and assembles them into a professional 20-page Credit Appraisal Memo as a DOCX file.

PART A — Data Assembly:
Accept this input dict (assembled by pipeline/main_pipeline.py):
{
  "company_name": str,
  "fiscal_year": int,
  "financial_data": pd.Series,  # from Person 1 feature matrix
  "forensics": dict,            # from Person 1 forensics
  "ml_scores": dict,            # PD, limit, spread, SHAP from Person 1
  "trajectory": dict,           # from Person 1 LSTM
  "network": dict,              # from Person 2 network graph
  "stress_test": dict,          # from Person 2 Monte Carlo
  "dna_match": dict,            # from Person 2 DNA matching
  "satellite": dict,            # from Person 2 satellite
  "gst": dict,                  # from Person 2 GST
  "research": dict,             # from Person 3 research agent
  "ceo_interview": dict,        # from Person 3 CEO module
  "bull_case": str,             # from Person 3 approval agent
  "bear_case": str,             # from Person 3 dissent agent
  "recommendation": dict,       # from Person 3 coordinator
}

PART B — CAM Sections (build each as a function):
1. generate_cover_page(data) → title, company, date, confidential
2. generate_executive_summary(data) → decision, limit, rate, key points
3. generate_company_background(data) → sector, history, ownership
4. generate_financial_analysis(data) → tables of 5-year ratios + commentary
5. generate_forensics_section(data) → Beneish score, Altman Z, manipulation flags
6. generate_network_section(data) → promoter network description + risk score
7. generate_satellite_section(data) → operational reality assessment
8. generate_stress_test_section(data) → P10/P50/P90 table + named scenarios
9. generate_management_section(data) → CEO interview insights
10. generate_bull_bear_section(data) → side-by-side bull vs bear arguments
11. generate_recommendation(data) → final verdict with conditions

PART C — DOCX Assembly:
Use python-docx to build professional document:
- Company logo placeholder
- Consistent heading styles
- Financial tables with borders
- Color-coded risk indicators (RED/AMBER/GREEN)
- Page numbers and headers
- Confidentiality notice

PART D — Save Output:
Save to: data/processed/CAM_[company_name]_[date].docx
Also save summary JSON: data/processed/scores_[company_name].json

Function signatures:
def generate_cam(all_data: dict, output_dir: str = "data/processed/") -> str
  # Returns path to generated DOCX file

Use python-docx only for document generation.
Handle missing data gracefully (show N/A if module output unavailable).
```

---

## PROMPT P3-5: Streamlit Dashboard

```
Build the complete Streamlit dashboard for the hackathon demo.

Build: dashboard/app.py

This is what judges will SEE and INTERACT with.
Make it professional, fast, and impressive.

LAYOUT — 4 Pages (using st.sidebar for navigation):

PAGE 1 — Upload & Process:
- Company name input field
- File upload: Financial statements (Excel/CSV)
- File upload: CEO interview (mp3/mp4) — optional
- Big "RUN FULL ANALYSIS" button
- Progress bar showing which module is running
- Estimated time remaining

PAGE 2 — Credit Decision Dashboard:
Top row — 3 large metric cards:
  Card 1: LENDING DECISION (APPROVE / CONDITIONAL / REJECT) with color
  Card 2: RECOMMENDED LIMIT (e.g., ₹12.5 Cr) with color
  Card 3: RISK PREMIUM (e.g., Base + 4.8%) with color

Second row — Risk Signal Overview:
  Show all 11 innovations as a grid of signal cards:
  Each card: Innovation name, score/status, GREEN/AMBER/RED indicator
  Examples:
  "Forensics: M-Score -1.8 ⚠️ SUSPICIOUS"
  "Network Risk: Contagion 0.72 🔴 HIGH"
  "Trajectory: DSCR in danger zone in 14 months 🔴"
  "Satellite: MODERATE activity 🟡"
  "CEO Interview: High deflection score ⚠️"

Third row — Model Consensus:
  Show 3 model PD scores as gauge charts
  Show disagreement flag prominently

PAGE 3 — Deep Dive:
Tab 1 — Financial Analysis:
  5-year ratio table (DSCR, D/E, ICR, margins)
  DSCR trajectory chart with trendline
  Beneish M-Score chart with threshold line

Tab 2 — Network Graph:
  Embed the plotly network graph from Person 2
  Show contagion risk score

Tab 3 — Stress Test:
  DSCR distribution histogram (Monte Carlo results)
  Named scenarios table (P10/P50/P90)
  Covenant recommendation

Tab 4 — Bull vs Bear:
  Two-column layout
  Left: Bull Case (green header)
  Right: Bear Case (red header)
  Final recommendation below both

PAGE 4 — Download CAM:
  "Generate Full CAM Report" button
  Progress indicator while generating
  Download button for DOCX file
  Summary of key scores as JSON

STYLING:
- Use Vivriti Capital brand colors if known, else: dark navy + orange accent
- Professional fonts
- All charts using plotly (not matplotlib)
- Mobile-responsive layout
- Sidebar with Intelli-Credit logo placeholder

DEMO MODE:
Add a "Load Demo Company (Sunrise Textile Mills)" button on Page 1
This loads pre-computed results instantly for the demo
So demo does not depend on live API calls working perfectly

Use streamlit, plotly, pandas only.
Run with: streamlit run dashboard/app.py
```

---

## PROMPT P3-6: Test Suite for Person 3

```
Write tests for all Person 3 modules.

Create: tests/test_person3.py

1. test_research_agent_returns_structured_output:
   Run research agent for "Sunrise Textile Mills", sector "Textiles"
   Assert output dict has keys: company_news_summary, industry_outlook,
   key_risks_found, research_sentiment_score
   Assert research_sentiment_score between 0 and 1

2. test_approval_agent_produces_bull_case:
   Create synthetic company_data dict
   Run approval agent
   Assert output is string with length > 200
   Assert output mentions at least one financial ratio

3. test_dissent_agent_produces_bear_case:
   Run dissent agent on same data + approval agent output
   Assert output contains at least 3 counter-arguments
   Assert output is different from bull case

4. test_coordinator_produces_valid_recommendation:
   Run coordinator on bull + bear cases
   Assert output contains: lending_decision, recommended_limit_cr,
   recommended_rate_pct, key_conditions
   Assert lending_decision in ["APPROVE", "CONDITIONAL_APPROVE", "REJECT"]
   Assert recommended_rate_pct between 8.0 and 20.0

5. test_cam_generator_creates_docx:
   Run cam_generator with synthetic all_data dict
   Assert output file exists
   Assert file size > 10KB
   Assert file is valid DOCX (can be opened by python-docx)

6. test_ceo_interview_fallback:
   Run ceo_interview module with no audio file
   Assert returns valid dict with all required keys
   Assert management_quality_score between 0 and 100

Use pytest. Mock all external API calls using unittest.mock.
Run with: pytest tests/test_person3.py -v
```

---

# ════════════════════════════════════════════════════════
# INTEGRATION PROMPTS (All Three Together — Final Step)
# ════════════════════════════════════════════════════════

---

## PROMPT INTEGRATE-1: Connect All Modules

```
All three persons have built their modules. Now connect everything.

Update: pipeline/main_pipeline.py

Uncomment all the import statements and function calls.
Connect Person 1 → Person 2 → Person 3 in sequence.
The final output should be a complete CAM DOCX file.

Also build: notebooks/demo_sunrise_textile.ipynb

This notebook should:
1. Run the complete pipeline for "Sunrise Textile Mills"
2. Display all 11 innovation outputs inline
3. Show the network graph
4. Show the stress test distribution
5. Show the bull vs bear CAM sections
6. End with: "Download CAM" button

This is the DEMO NOTEBOOK for hackathon presentation day.
Every cell should run without errors.
Expected runtime: under 3 minutes total.
```

---

## PROMPT INTEGRATE-2: Final GitHub Push

```
Help me prepare the final GitHub commit before the hackathon submission.

1. Verify all files exist:
   modules/person1_ml_core/ (5 files)
   modules/person2_alt_data/ (5 files)
   modules/person3_llm_cam/ (5 files)
   pipeline/main_pipeline.py
   dashboard/app.py
   notebooks/demo_sunrise_textile.ipynb
   tests/ (3 test files)
   requirements.txt
   README.md
   .env.example
   .gitignore

2. Verify .env is NOT committed (should be in .gitignore)

3. Verify data/synthetic/intelli_credit_dataset.csv EXISTS and is committed

4. Run all tests: pytest tests/ -v
   Show me which tests pass and which fail

5. Write git commands to:
   - Initialize repo
   - Create three branches: person1/ml-core, person2/alt-data, person3/llm-cam
   - Merge all to main
   - Tag final version: v1.0-hackathon

6. Update README.md with:
   - Final feature count
   - How to run demo in 3 steps
   - Team member names and module ownership
```

---

# SUMMARY — WHO DOES WHAT

```
PERSON 1 — Run These Prompts in Order:
P1-1 → Understand dataset
P1-2 → Validate dataset
P1-3 → Feature engineering
P1-4 → XGBoost + Ensemble scorer
P1-5 → LSTM trajectory model
P1-6 → Tests

PERSON 2 — Run These Prompts in Order:
P2-1 → Network graph
P2-2 → Monte Carlo stress test
P2-3 → Satellite module
P2-4 → GST + Default DNA
P2-5 → Tests

PERSON 3 — Run These Prompts in Order:
P3-1 → Research agent
P3-2 → Adversarial CAM agents
P3-3 → CEO interview module
P3-4 → CAM document generator
P3-5 → Streamlit dashboard
P3-6 → Tests

ALL TOGETHER (Day 6-7):
INTEGRATE-1 → Connect all modules
INTEGRATE-2 → Final GitHub push
```
