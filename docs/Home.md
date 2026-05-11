# Specialist Recommender — Knowledge Base

> AI-assisted medical triage service for symptom-based specialist recommendation.
> Part of the **Med360** platform.

---

## Quick Links

| Note | Purpose |
|------|---------|
| [[Architecture]] | System design, components, request flow |
| [[API-Reference]] | All endpoints with request/response shapes |
| [[Data-Models]] | Pydantic contracts for API and LLM output |
| [[LLM-Integration]] | OpenRouter setup, fallback strategy, prompting |
| [[Configuration]] | Environment variables and deployment config |
| [[Development-Guide]] | Local setup, running the app, demo clients |
| [[Roadmap]] | Known gaps, planned improvements |

---

## What This Service Does

The **Specialist Recommender API** accepts basic patient symptom details and returns a structured triage recommendation — which specialist to see, why, alternate pathways, and urgent red flags.

It is an **AI-assisted triage helper**, not a diagnostic engine. It helps patients navigate to the right specialist faster and supports consultation booking workflows in the Med360 platform.

---

## Tech Stack at a Glance

```
Backend    FastAPI + Uvicorn + Pydantic v2
LLM        OpenRouter (OpenAI-compatible) — free model tier with fallbacks
Demo UI    Streamlit
Demo CLI   Python terminal client
Logging    Local file (logs/usage.json)
```

---

## Current Version

**v0.2.0** — Internal integration ready, not production-hardened.

What works:
- Full typed API with Swagger at `/docs`
- Multi-model fallback strategy (12 free models)
- CORS-configurable for frontend integration
- Local usage tracking with cost estimation

What's missing: auth, tests, Docker, centralized logging, mock mode.

See [[Roadmap]] for details.

---

## Project Structure

```
recommender/
├── app/
│   ├── main.py          ← FastAPI entrypoint (routes)
│   ├── models.py        ← Pydantic request/response contracts
│   ├── config.py        ← Env vars & settings
│   ├── constants.py     ← Specialist list & disclaimers
│   ├── prompts.py       ← LLM system prompt & schema
│   ├── tracker.py       ← Usage logging & cost calc
│   └── services/
│       └── llm.py       ← OpenRouter provider integration
├── logs/
│   └── usage.json       ← Local usage log
├── docs/                ← This Obsidian vault
├── .env                 ← Local secrets (git-ignored)
├── .env.example         ← Env template
├── requirements.txt
├── streamlit_app.py     ← Streamlit demo UI
└── specialist_recommender.py  ← CLI demo client
```

---

*Last updated: 2026-05-11*
