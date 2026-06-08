# Specialist Recommender API

FastAPI service for symptom-based specialist recommendation. Part of the **Med360** platform.

This repository contains:

- a reusable FastAPI backend in `app/`
- a Streamlit demo client in `streamlit_app.py`
- a simple CLI demo client in `specialist_recommender.py`
- an Obsidian documentation vault in `docs/`

The main team integration target is the FastAPI app.

## Documentation

Full documentation is in the `docs/` folder (open as an Obsidian vault):

| Doc | Contents |
|-----|---------|
| [docs/Home.md](docs/Home.md) | Index and quick links |
| [docs/Architecture.md](docs/Architecture.md) | System design and request flow |
| [docs/API-Reference.md](docs/API-Reference.md) | All endpoints with examples |
| [docs/Data-Models.md](docs/Data-Models.md) | Pydantic request/response contracts |
| [docs/LLM-Integration.md](docs/LLM-Integration.md) | OpenRouter setup and fallback strategy |
| [docs/Configuration.md](docs/Configuration.md) | Environment variables |
| [docs/Development-Guide.md](docs/Development-Guide.md) | Local setup and dev workflow |
| [docs/Roadmap.md](docs/Roadmap.md) | Known gaps and planned improvements |

## What This Service Does

The API accepts basic patient symptom details, sends them to an LLM through OpenRouter, and returns:

- one recommended specialist
- a short patient-facing summary
- a plain-language explanation
- alternate specialist pathways
- urgent red flags
- token, cost, and rate-limit metadata

This is an AI-assisted triage helper for consultation booking. It is not a medical diagnosis service.

## Current Status

This project is in a good state for local integration and internal team workflows.

What is ready:

- FastAPI app with documented routes
- typed request and response models
- configurable CORS
- provider fallback handling across multiple models
- response-shape validation for LLM output
- local usage logging
- Swagger docs at `/docs`

What is not production-ready yet:

- no authentication
- no automated test suite yet
- usage logging is local-file based, not centralized
- no container setup yet

## Project Structure

```text
recommender/
|-- app/
|   |-- __init__.py
|   |-- config.py
|   |-- constants.py
|   |-- main.py
|   |-- models.py
|   |-- prompts.py
|   |-- tracker.py
|   `-- services/
|       |-- __init__.py
|       `-- llm.py
|-- logs/
|-- .env.example
|-- .gitignore
|-- README.md
|-- requirements.txt
|-- specialist_recommender.py
`-- streamlit_app.py
```

## Architecture Overview

### `app/main.py`

FastAPI entrypoint. Exposes:

- `GET /`
- `GET /health`
- `GET /usage`
- `POST /recommend`

### `app/models.py`

Pydantic request and response contracts for the API plus internal validation of LLM output.

### `app/services/llm.py`

Provider integration layer. This is the only module that talks to OpenRouter/OpenAI-compatible APIs.

Responsibilities:

- send prompt to the provider
- iterate over fallback models
- validate the returned JSON shape
- return normalized recommendation data

### `app/prompts.py`

System prompt and schema instructions sent to the model.

### `app/tracker.py`

Local usage tracker.

Responsibilities:

- parse rate-limit headers
- estimate token costs
- store request metadata in `logs/usage.json`
- aggregate totals for `/usage`

### `streamlit_app.py`

Quick local demo UI. Useful for manual testing but not required for backend/frontend team integration.

### `specialist_recommender.py`

Simple terminal client for local manual checks.

## Request Flow

1. Client sends a payload to `POST /recommend`.
2. FastAPI validates the payload using `PatientInput`.
3. `build_patient_info(...)` converts the request into an LLM-friendly string.
4. `app/services/llm.py` sends the prompt to OpenRouter.
5. The service tries the configured primary model first, then fallback models if needed.
6. The returned JSON is validated against the internal LLM payload model.
7. The API converts the result into the public `RecommendationResponse`.
8. Usage data is written to `logs/usage.json`.

## API Endpoints

### `GET /`

Returns basic service metadata.

Example response:

```json
{
  "name": "Specialist Recommender API",
  "version": "0.2.0",
  "docs_url": "/docs",
  "health_url": "/health"
}
```

### `GET /health`

Basic health check endpoint.

Example response:

```json
{
  "status": "ok",
  "service": "Specialist Recommender API",
  "version": "0.2.0"
}
```

### `GET /usage`

Aggregated totals from local usage logs.

Example response:

```json
{
  "total_requests": 3,
  "total_tokens": 2818,
  "total_cost_usd": 0.0
}
```

### `POST /recommend`

Primary integration endpoint.

Request body:

```json
{
  "age": 25,
  "gender": "female",
  "severity": "medium",
  "duration_days": 3,
  "symptoms": "skin rash, itching, hives after eating"
}
```

Response shape:

```json
{
  "recommended_specialist": "Dermatologist",
  "primary_recommendation_summary": "Your symptoms suggest an allergic skin reaction that should be evaluated by a specialist.",
  "symptom_explanation": "The combination of rash, itching, and hives after eating can indicate the body is reacting to a food or environmental trigger.",
  "specialist_pathway": [
    {
      "specialist": "Dermatologist",
      "reason": "Best fit for evaluating skin-based allergic reactions"
    },
    {
      "specialist": "General Physician",
      "reason": "Starting point if specialist access is delayed"
    }
  ],
  "red_flags": [
    "difficulty breathing",
    "swelling of lips or tongue"
  ],
  "disclaimer": "This recommendation is an AI-assisted triage suggestion for consultation booking only. It is not a medical diagnosis or emergency advice. Please consult a qualified clinician for confirmation, and seek urgent care immediately for severe or worsening symptoms.",
  "usage": {
    "model_used": "google/gemma-3n-e4b-it:free",
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0,
    "cost_usd": 0.0,
    "rate_limits": {
      "requests": {
        "limit": null,
        "remaining": null,
        "reset": null
      },
      "tokens": {
        "limit": null,
        "remaining": null,
        "reset": null
      }
    }
  }
}
```

## Environment Variables

Create a `.env` file in the repo root based on `.env.example`.

### Required

```env
OPENAI_API_KEY=your_openai_key_here
```

This is the primary provider. Without it the service falls back to OpenRouter. If both are missing, `/recommend` returns `503`.

### Optional — OpenAI

```env
OPENAI_MODEL=gpt-4o
```

### Optional — OpenRouter fallback

```env
OPENROUTER_API_KEY=your_openrouter_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

### Optional — API & CORS

```env
API_TITLE=Specialist Recommender API
API_VERSION=0.2.0
CORS_ALLOW_ORIGINS=http://localhost:3000,https://your-frontend-domain.com
```

## Local Setup

### 1. Create virtual environment and install dependencies

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows
# source .venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
```

### 2. Create `.env`

Copy `.env.example` and fill in your OpenAI key (and optionally OpenRouter).

### 3. Run the FastAPI app

```bash
uvicorn app.main:app --reload
```

Open:

- API docs: `http://127.0.0.1:8000/docs`
- OpenAPI spec: `http://127.0.0.1:8000/openapi.json`

### 4. Optional demo clients

Run Streamlit:

```bash
streamlit run streamlit_app.py
```

Run CLI:

```bash
python specialist_recommender.py
```

## Quick API Example

Using `curl`:

```bash
curl -X POST "http://127.0.0.1:8000/recommend" \
  -H "Content-Type: application/json" \
  -d '{
    "age": 30,
    "gender": "male",
    "severity": "medium",
    "duration_days": 4,
    "symptoms": "persistent cough with chest tightness"
  }'
```

Using JavaScript:

```js
const response = await fetch("http://127.0.0.1:8000/recommend", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    age: 30,
    gender: "male",
    severity: "medium",
    duration_days: 4,
    symptoms: "persistent cough with chest tightness"
  })
});

const data = await response.json();
console.log(data);
```

## Notes For Frontend Team

- Use `POST /recommend` as the main endpoint.
- The `usage` block is useful for debugging or admin UIs, but the core patient UI can ignore it.
- `GET /health` is the easiest endpoint for local connectivity checks.
- If you get a `503` from `/recommend`, both `OPENAI_API_KEY` and `OPENROUTER_API_KEY` are missing or all provider models are temporarily unavailable.
- CORS defaults to `*` locally, but should be restricted before deployment.

## Notes For Backend Team

- The public API contract lives in `app/models.py`.
- The provider-specific logic is isolated in `app/services/llm.py`.
- If you want to swap providers later, start there.
- The current log store is file-based and should be replaced in shared or deployed environments.
- The route layer in `app/main.py` is intentionally thin and should stay that way.

## Known Limitations

- No automated tests yet
- No request authentication
- No database or centralized logging
- No Dockerfile yet

## Recommended Next Improvements

1. Add FastAPI tests with the LLM service mocked.
2. Replace local usage logging with structured logging or persistent storage.
3. Add auth if this service will be exposed beyond trusted internal environments.
4. Add containerization for consistent local and deployment workflows.

## Git Notes

If `.claude/settings.local.json` was committed earlier, remove it from tracking with:

```bash
git rm --cached .claude/settings.local.json
git commit -m "Remove local Claude settings from repo"
```

The repo already ignores `.claude/` going forward.
