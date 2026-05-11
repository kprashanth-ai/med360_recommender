# Development Guide

## Prerequisites

- Python 3.10+
- An OpenRouter API key (free at openrouter.ai)

---

## Local Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Create `.env`

```bash
cp .env.example .env
```

Edit `.env` and set your `OPENROUTER_API_KEY`.

### 3. Run the FastAPI server

```bash
uvicorn app.main:app --reload
```

The server starts at `http://127.0.0.1:8000`.

Open the interactive Swagger docs at `http://127.0.0.1:8000/docs`.

---

## Demo Clients

### Streamlit UI

A visual form for testing recommendations without writing any code.

```bash
streamlit run streamlit_app.py
```

Opens at `http://localhost:8501` by default.

Features:
- Age, gender, severity, duration inputs
- Free-text symptom textarea
- Displays specialist recommendation, pathway, red flags
- Shows usage metrics and rate-limit quotas
- Session totals in the footer

### CLI Client

A terminal walkthrough for quick local checks.

```bash
python specialist_recommender.py
```

Prompts interactively for all patient fields, then prints the full recommendation.

---

## Key Files to Know

| File | What to touch here |
|------|--------------------|
| `app/models.py` | Adding fields to request or response |
| `app/prompts.py` | Changing what the LLM is instructed to do |
| `app/services/llm.py` | Swapping or configuring the LLM provider |
| `app/constants.py` | Adding/removing specialist categories |
| `app/tracker.py` | Usage logging or cost table updates |
| `app/main.py` | Adding new API routes |

---

## Making a Test Request

### curl

```bash
curl -s -X POST http://127.0.0.1:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{"age": 45, "gender": "male", "severity": "high", "duration_days": 7, "symptoms": "chest pain radiating to left arm, shortness of breath"}' \
  | python -m json.tool
```

### Health check

```bash
curl http://127.0.0.1:8000/health
```

### Check usage totals

```bash
curl http://127.0.0.1:8000/usage
```

---

## Logs

Usage is logged to `logs/usage.json` after each successful recommendation. The file is created automatically on first request.

Format per entry:
```json
{
  "timestamp": "2026-05-11T10:32:14.123Z",
  "model_used": "google/gemma-3n-e4b-it:free",
  "prompt_tokens": 412,
  "completion_tokens": 318,
  "total_tokens": 730,
  "cost_usd": 0.0,
  "rate_limits": { ... }
}
```

---

## Adding a New Specialist

1. Add the specialist name to `SPECIALIST_LIST` in `app/constants.py`
2. The system prompt in `app/prompts.py` reads from `SPECIALIST_LIST` — no changes needed there
3. Update the valid values documentation in [[API-Reference]]

---

## Common Issues

**`503` on `/recommend`**
- Missing or invalid `OPENROUTER_API_KEY` in `.env`
- All free models rate-limited simultaneously (rare — try again in a few minutes)

**`422` on `/recommend`**
- Request body fails validation — check field names, types, and value ranges
- See [[Data-Models]] for all constraints

**Streamlit shows connection error**
- Make sure `uvicorn` is running before starting Streamlit
- Both must be running simultaneously

---

*See also: [[Configuration]] | [[API-Reference]] | [[Architecture]]*
