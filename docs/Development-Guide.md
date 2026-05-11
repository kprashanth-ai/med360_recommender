# Development Guide

## Prerequisites

- Python 3.10+
- An OpenAI API key (primary provider — get one at platform.openai.com)
- An OpenRouter API key (fallback — optional but recommended, free at openrouter.ai)

---

## Local Setup

### 1. Create virtual environment

```bash
python -m venv .venv
```

Activate it:

```powershell
# Windows
.venv\Scripts\Activate.ps1

# Mac/Linux
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create `.env`

```bash
cp .env.example .env
```

Edit `.env` and set your keys:

```env
OPENAI_API_KEY=sk-proj-your-key-here
OPENROUTER_API_KEY=sk-or-v1-your-key-here   # optional but recommended
```

### 4. Run the FastAPI server

```bash
uvicorn app.main:app --reload
```

The server starts at `http://127.0.0.1:8000`.

Open the interactive Swagger docs at `http://127.0.0.1:8000/docs`.

---

## Demo Clients

### CLI Client (no server needed)

The fastest way to test end-to-end. Calls the LLM service directly — the FastAPI server does not need to be running.

```bash
python specialist_recommender.py
# or with venv
.venv\Scripts\python specialist_recommender.py
```

Prompts interactively:
```
Age: 35
Gender (male/female/other): male
Severity (low/medium/high): medium
Duration (in days): 5
Describe your symptoms: persistent cough with chest tightness
```

Then prints the full recommendation, specialist pathway, red flags, token usage, and cost.

### Streamlit UI

A visual form for testing without writing any code. Requires the FastAPI server to be running.

```bash
streamlit run streamlit_app.py
```

Opens at `http://localhost:8501`. Features: form inputs, displays recommendation with specialist pathway, red flags, usage metrics, and session totals.

---

## Key Files to Know

| File | What to touch here |
|------|--------------------|
| `app/models.py` | Adding fields to request or response |
| `app/prompts.py` | Changing what the LLM is instructed to do |
| `app/services/llm.py` | Swapping or configuring providers |
| `app/config.py` | Adding env vars or changing fallback model list |
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

Usage is written to `logs/usage.json` after each successful recommendation. Created automatically on first request.

Format per entry:

```json
{
  "timestamp": "2026-05-11T10:32:14.123Z",
  "model": "gpt-4o",
  "prompt_tokens": 481,
  "completion_tokens": 308,
  "total_tokens": 789,
  "cost_usd": 0.00428,
  "rate_limits": { ... }
}
```

---

## Adding a New Specialist

1. Add the name to `SPECIALISTS` in `app/constants.py`
2. The system prompt reads from `SPECIALISTS` automatically — no other code changes needed
3. Update the valid values table in [[API-Reference]]

---

## Adding a New Paid Model to Cost Tracking

Add an entry to `MODEL_PRICING` in `app/tracker.py`:

```python
"your-model-id": {"input": 1.00, "output": 3.00},  # per 1M tokens
```

---

## Common Issues

**`503` on `/recommend`**
- `OPENAI_API_KEY` is missing or invalid AND `OPENROUTER_API_KEY` is also missing — at least one provider must be configured
- All OpenRouter free models are rate-limited simultaneously (rare — try again in a few minutes)

**`422` on `/recommend`**
- Request body fails validation — check field names, types, and value ranges
- See [[Data-Models]] for all constraints

**Streamlit shows connection error**
- Make sure `uvicorn` is running before starting Streamlit
- Both must be running simultaneously

**CLI works but server doesn't (or vice versa)**
- The CLI (`specialist_recommender.py`) imports directly from `app/` — it doesn't go through HTTP
- The FastAPI server is the HTTP interface; the CLI is a direct Python import

---

*See also: [[Configuration]] | [[API-Reference]] | [[Architecture]]*
