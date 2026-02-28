# Person 3 Quick Start — LLM Agents + Dashboard

## Your Branch
```bash
git checkout person3/llm-cam
```

## Your Files
```
modules/person3_llm_cam/
├── research_agent.py  ← You build this
├── approval_agent.py  ← You build this
├── dissent_agent.py   ← You build this
├── cam_generator.py   ← You build this
└── ceo_interview.py   ← You build this

dashboard/
└── app.py             ← You build this (Streamlit UI)
```

## Step 1 — API Keys you need
- OPENAI_API_KEY (Whisper transcription)
- ANTHROPIC_API_KEY (LLM agents — get free trial credits)
- TAVILY_API_KEY (web research — free tier available)

## Step 2 — Open Copilot Chat
Select model: Claude Opus 4.6
Open file: COPILOT_PROMPTS.md
Run prompts P3-1 through P3-6 in order

## Step 3 — Run dashboard locally
```bash
streamlit run dashboard/app.py
```

## Step 4 — When done, push your branch
```bash
git add modules/person3_llm_cam/ dashboard/
git commit -m "Person 3: LLM agents and dashboard complete"
git push origin person3/llm-cam
```
