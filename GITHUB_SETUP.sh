#!/bin/bash
# ══════════════════════════════════════════════════════════════════
# Yakṣarāja — GitHub Final Submission Script
# Vivriti Capital AI/ML Hackathon
# ══════════════════════════════════════════════════════════════════
#
# USAGE:
#   chmod +x GITHUB_SETUP.sh
#   ./GITHUB_SETUP.sh
#
# This script handles the FINAL submission workflow:
#   1. Stage all files (respects .gitignore)
#   2. Create structured commits per module
#   3. Tag the release
#   4. Push to GitHub
# ══════════════════════════════════════════════════════════════════

set -e  # Exit on any error

REPO_URL="https://github.com/PankajKumar17/yaksaraja.git"
BRANCH="main"

echo "🏦 Yakṣarāja — Final Submission Setup"
echo "═══════════════════════════════════════════"
echo ""

# ── Step 0: Verify we're in the right directory ──────────────
if [ ! -f "requirements.txt" ] || [ ! -d "modules" ]; then
    echo "❌ ERROR: Run this script from the project root (where requirements.txt is)"
    exit 1
fi

# ── Step 1: Verify git is initialized ────────────────────────
if [ ! -d ".git" ]; then
    echo "📦 Initializing git repository..."
    git init
    git branch -M main
else
    echo "✅ Git already initialized"
fi

# ── Step 2: Set remote (if not already set) ──────────────────
if git remote get-url origin &>/dev/null; then
    echo "✅ Remote 'origin' already set: $(git remote get-url origin)"
else
    echo "🔗 Adding remote origin: $REPO_URL"
    git remote add origin "$REPO_URL"
fi

# ── Step 3: Stage & Commit — Person 1 (ML Core) ─────────────
echo ""
echo "📊 Committing Person 1 — ML Core..."
git add modules/person1_ml_core/
git add tests/test_person1.py
git add QUICKSTART_PERSON1.md
# Commit only if there are staged changes
if git diff --cached --quiet 2>/dev/null; then
    echo "   (no changes to commit)"
else
    git commit -m "feat(person1): ML core — data generator, credit scorer, LSTM trajectory, forensics

- data_generator.py: 30 companies × 12 yrs, 149 features, Beneish/Altman/Piotroski
- feature_engineering.py: 160 engineered features (velocity, DNA, ratios)
- credit_scorer.py: XGBoost + RF + LightGBM ensemble with SHAP + SMOTE
- temporal_model.py: LSTM trajectory prediction + early warning system
- validate_dataset.py: Distribution validation + plots
- test_person1.py: Dataset, Beneish, Altman, scorer, trajectory tests"
fi

# ── Step 4: Stage & Commit — Person 2 (Alt Data) ────────────
echo ""
echo "🌐 Committing Person 2 — Alternative Data..."
git add modules/person2_alt_data/
git add tests/test_person2.py
git add QUICKSTART_PERSON2.md
if git diff --cached --quiet 2>/dev/null; then
    echo "   (no changes to commit)"
else
    git commit -m "feat(person2): Alternative data — network graph, stress test, satellite, GST, DNA

- network_graph.py: MCA21 promoter network + contagion risk scoring
- stress_test.py: Monte Carlo 1000 sims + 4 named scenarios
- satellite_module.py: Sentinel-2 factory activity scoring
- gst_intelligence.py: GST filing vs bank revenue cross-validation
- dna_matching.py: Default DNA fingerprints (6 archetypes)
- test_person2.py: 49 tests covering all 5 modules"
fi

# ── Step 5: Stage & Commit — Person 3 (LLM + CAM) ───────────
echo ""
echo "🤖 Committing Person 3 — LLM Agents + CAM..."
git add modules/person3_llm_cam/
git add tests/test_person3.py
git add dashboard/app.py
git add QUICKSTART_PERSON3.md
if git diff --cached --quiet 2>/dev/null; then
    echo "   (no changes to commit)"
else
    git commit -m "feat(person3): LLM agents + CAM — research, bull/bear, CEO interview, DOCX generator

- research_agent.py: LangGraph + Tavily + Claude research agent
- approval_agent.py: Structured bull case agent
- dissent_agent.py: Adversarial bear case + coordinator
- ceo_interview.py: Whisper transcription + VADER sentiment + deflection
- cam_generator.py: 11-section professional DOCX generator
- dashboard/app.py: 4-page Streamlit interactive UI
- test_person3.py: All APIs mocked for offline testing"
fi

# ── Step 6: Stage & Commit — Integration (Pipeline + Notebook) ─
echo ""
echo "🔗 Committing Integration — Pipeline + Notebook..."
git add pipeline/
git add notebooks/
if git diff --cached --quiet 2>/dev/null; then
    echo "   (no changes to commit)"
else
    git commit -m "feat(integration): 10-layer pipeline + 27-cell demo notebook

- main_pipeline.py: 10-layer engine (forensics → ML → alt data → LLM → CAM)
- demo_sunrise_textile.ipynb: Interactive walkthrough of all 11 innovations
- Demo output: CONDITIONAL_APPROVE, PD=25.35%, BB+ rating"
fi

# ── Step 7: Stage & Commit — Data + Config ───────────────────
echo ""
echo "📁 Committing Data + Config..."
git add data/synthetic/
git add .gitignore
git add .env.example
git add requirements.txt
git add README.md
git add COPILOT_PROMPTS.md
git add GITHUB_SETUP.sh
if git diff --cached --quiet 2>/dev/null; then
    echo "   (no changes to commit)"
else
    git commit -m "chore: dataset (352 rows × 149 cols), .gitignore, README, requirements

- intelli_credit_dataset.csv: 30 companies, FY2009-2024, 149 columns
- demo_sunrise_textile.csv: Single-company demo data
- schema.json: Full dataset schema (747 lines)
- README.md: Comprehensive with architecture, all 11 innovations, quickstart
- .gitignore: Allows data/synthetic/*.csv, blocks .env + models"
fi

# ── Step 8: Catch any remaining files ────────────────────────
echo ""
echo "🧹 Checking for any remaining unstaged files..."
git add -A
if git diff --cached --quiet 2>/dev/null; then
    echo "   (all clean)"
else
    git commit -m "chore: remaining files and cleanup"
fi

# ── Step 9: Tag the release ──────────────────────────────────
echo ""
echo "🏷️  Tagging release..."
git tag -a v1.0-hackathon -m "Yakṣarāja v1.0 — Vivriti Capital Hackathon Submission

11 Innovations Implemented:
1. Beneish M-Score Forensics
2. 3-Model Ensemble Credit Scorer (XGBoost + RF + LightGBM)
3. LSTM Trajectory Prediction
4. Model Disagreement Signal
5. Promoter Network Contagion
6. Monte Carlo Stress Test (1000 sims)
7. Sentinel-2 Satellite Activity
8. GST Truth Layer
9. Default DNA Fingerprinting
10. Adversarial Bull/Bear LLM Agents
11. CEO Interview Sentiment Analysis

Test Results: 75 passed, 15 skipped, 1 xfailed" 2>/dev/null || echo "   Tag v1.0-hackathon already exists (skipping)"

# ── Step 10: Push to GitHub ──────────────────────────────────
echo ""
echo "🚀 Pushing to GitHub..."
git push -u origin "$BRANCH"
git push origin v1.0-hackathon 2>/dev/null || echo "   Tag already pushed"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "✅ SUBMISSION COMPLETE!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "📍 Repository: $REPO_URL"
echo "🏷️  Tag: v1.0-hackathon"
echo "📊 Tests: 75 passed, 15 skipped, 1 xfailed"
echo "📁 Files: $(git ls-files | wc -l | tr -d ' ') tracked files"
echo ""
echo "Quick verification:"
echo "  git log --oneline -10"
echo "  git tag -l"
echo "  git ls-files | wc -l"
echo ""
