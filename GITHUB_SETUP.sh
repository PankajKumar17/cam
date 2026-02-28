#!/bin/bash
# ══════════════════════════════════════════════════════════
# Intelli-Credit — GitHub Setup Script
# Run this ONCE after cloning the repo
# ══════════════════════════════════════════════════════════

echo "Setting up Intelli-Credit repository..."

# Step 1: Initialize git (if not already)
git init
git add .
git commit -m "Initial project setup — Intelli-Credit Hackathon"

# Step 2: Add remote (replace with your GitHub URL)
# git remote add origin https://github.com/YOUR_ORG/intelli-credit.git

# Step 3: Create branches for each person
git checkout -b person1/ml-core
git checkout main
git checkout -b person2/alt-data
git checkout main
git checkout -b person3/llm-cam
git checkout main

echo ""
echo "✅ Repository ready!"
echo ""
echo "PERSON 1 → git checkout person1/ml-core"
echo "PERSON 2 → git checkout person2/alt-data"
echo "PERSON 3 → git checkout person3/llm-cam"
echo ""
echo "When done → Create Pull Request to merge into main"
