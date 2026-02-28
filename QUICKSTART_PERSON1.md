# Person 1 Quick Start — ML Core

## Your Branch
```bash
git checkout person1/ml-core
```

## Your Files
```
modules/person1_ml_core/
├── data_generator.py      ← ALREADY WRITTEN — run this first
├── feature_engineering.py ← You build this
├── forensics.py           ← You build this
├── temporal_model.py      ← You build this
└── credit_scorer.py       ← You build this
```

## Step 1 — Run the dataset generator (do this TODAY)
```bash
python modules/person1_ml_core/data_generator.py
```
Expected output: data/synthetic/intelli_credit_dataset.csv (300+ rows, 100+ columns)

## Step 2 — Open Copilot Chat
Select model: Claude Opus 4.6
Open file: COPILOT_PROMPTS.md
Run prompts P1-1 through P1-6 in order

## Step 3 — When done, push your branch
```bash
git add modules/person1_ml_core/
git commit -m "Person 1: ML core modules complete"
git push origin person1/ml-core
```
