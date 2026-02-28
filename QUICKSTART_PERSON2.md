# Person 2 Quick Start — Alternative Data

## Your Branch
```bash
git checkout person2/alt-data
```

## Your Files
```
modules/person2_alt_data/
├── network_graph.py    ← You build this
├── stress_test.py      ← You build this
├── satellite_module.py ← You build this
├── gst_intelligence.py ← You build this
└── dna_matching.py     ← You build this
```

## Step 1 — Wait for Person 1 to generate dataset first
OR use the synthetic dataset already in: data/synthetic/

## Step 2 — Open Copilot Chat
Select model: Claude Opus 4.6
Open file: COPILOT_PROMPTS.md
Run prompts P2-1 through P2-5 in order

## Step 3 — API Keys you need (get from .env.example)
- SENTINEL_HUB_CLIENT_ID (satellite) → sentinel-hub.com (free account)
- No other APIs strictly needed — all have fallback modes

## Step 4 — When done, push your branch
```bash
git add modules/person2_alt_data/
git commit -m "Person 2: Alternative data modules complete"
git push origin person2/alt-data
```
