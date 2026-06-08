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
| [[LLM-Integration]] | OpenAI primary + OpenRouter fallback strategy |
| [[Configuration]] | Environment variables and deployment config |
| [[Development-Guide]] | Local setup, running the app, demo clients |
| [[Roadmap]] | Known gaps, planned improvements |
| [[Training-Data-Pipeline]] | MedQA/MedMCQA → gpt-4o → fine-tune own model |
| [[Feedback-System]] | Human annotation design, rubric, feedback loop |
| [[MongoDB-Schema]] | All collection schemas for the training pipeline |
| [[ICMR-Citation-Layer]] | Linking responses to ICMR STW clinical guidelines |
| [[benchmark-evidence]] | Medical LLM benchmark citations and model scores |
| [[decisions/000-decisions-index\|Decision Records]] | All architectural and strategic decisions with date, rationale, and consequences |

---

## What This Service Does

The **Specialist Recommender API** accepts basic patient symptom details and returns a structured triage recommendation — which specialist to see, why, alternate pathways, and urgent red flags.

It is an **AI-assisted triage helper**, not a diagnostic engine. It helps patients navigate to the right specialist faster and supports consultation booking workflows in the Med360 platform.

---

## Tech Stack at a Glance

```
Backend      FastAPI + Uvicorn + Pydantic v2
Primary LLM  OpenAI gpt-4o (direct API)
Fallback LLM OpenRouter — 11 free models (cascaded)
Demo UI      Streamlit
Demo CLI     Python terminal client
Logging      Local file (logs/usage.json)
```

---

## Provider Strategy

**OpenAI is the primary provider** — every request tries `gpt-4o` first via the OpenAI API.

If OpenAI fails (rate limit, auth error, network issue, bad response), the service automatically cascades through **11 free models on OpenRouter** as fallback. Responses from OpenAI cost ~$0.004 per request; OpenRouter fallbacks are free.

See [[LLM-Integration]] for the full fallback chain and cost details.

---

## Current Version

**v0.2.0** — Internal integration ready, not production-hardened.

What works:
- Full typed API with Swagger at `/docs`
- OpenAI primary + 11-model OpenRouter fallback chain
- CORS-configurable for frontend integration
- Local usage tracking with cost estimation

What's missing: auth, tests, Docker, centralized logging.

See [[Roadmap]] for details.

---

## Project Structure

```
recommender/
├── app/
│   ├── main.py          ← FastAPI entrypoint (routes)
│   ├── models.py        ← Pydantic request/response contracts
│   ├── config.py        ← Env vars & settings
│   ├── constants.py     ← SPECIALISTS list & RECOMMENDATION_DISCLAIMER
│   ├── prompts.py       ← LLM system prompt & JSON schema
│   ├── tracker.py       ← Usage logging & cost calculation
│   └── services/
│       └── llm.py       ← OpenAI + OpenRouter provider integration
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

*Last updated: 2026-06-08*
