# Architecture

## Overview

The Specialist Recommender is a single FastAPI service. It has no database — state is limited to a local usage log file. All intelligence comes from an LLM accessed via OpenRouter.

```
Client (browser / frontend / CLI)
        │
        ▼
  FastAPI app (app/main.py)
        │
        ▼
  Input validation (Pydantic — app/models.py)
        │
        ▼
  Prompt builder (app/prompts.py)
        │
        ▼
  LLM Service (app/services/llm.py)
        │
        ▼
  OpenRouter API ──► Primary model
                 └──► Fallback models (if primary fails)
        │
        ▼
  Response validation (Pydantic internal model)
        │
        ▼
  Usage logger (app/tracker.py ──► logs/usage.json)
        │
        ▼
  RecommendationResponse → Client
```

---

## Components

### `app/main.py` — FastAPI Entrypoint

- Thin route layer, no business logic
- CORS middleware (configurable via `CORS_ALLOW_ORIGINS`)
- 4 routes: `/`, `/health`, `/usage`, `/recommend`
- All route handlers delegate immediately to service layer

### `app/models.py` — Data Contracts

Three Pydantic models:
- `PatientInput` — validated request body for `POST /recommend`
- `LLMRecommendationPayload` — internal model for validating raw LLM JSON
- `RecommendationResponse` — public response shape returned to clients

See [[Data-Models]] for full field definitions.

### `app/services/llm.py` — LLM Integration Layer

The only module that talks to OpenRouter. Responsibilities:
- Build the OpenAI-compatible chat request
- Try primary model, iterate fallbacks on failure
- Parse and validate the JSON response
- Extract rate-limit headers from the HTTP response
- Return a normalized `LLMRecommendationPayload`

See [[LLM-Integration]] for full details.

### `app/prompts.py` — Prompt Engineering

- System prompt instructs the model to act as a triage assistant
- Embeds the full specialist list and output JSON schema
- Patient details are injected as user message content

### `app/tracker.py` — Usage Tracking

- Thread-safe local file logger (JSON append)
- Parses `x-ratelimit-*` response headers
- Estimates per-request cost using a pricing table
- Provides aggregation for `GET /usage`

### `app/config.py` — Configuration

Reads environment variables via `python-dotenv`. All config is centralized here — no scattered `os.getenv()` calls elsewhere.

See [[Configuration]] for all variables.

### `app/constants.py` — Static Data

- `SPECIALIST_LIST` — 20 valid specialist categories the LLM must choose from
- `DISCLAIMER` — Standard medical/legal disclaimer appended to every response

---

## Request Flow (Detailed)

1. `POST /recommend` receives JSON body
2. Pydantic validates and coerces `PatientInput`
3. `build_patient_info(patient)` formats the patient details into a readable string
4. `get_recommendation(patient_info)` is called in `llm.py`
5. System prompt + patient string are sent to OpenRouter as a chat completion request
6. If the primary model returns a rate limit or error, the service iterates through `FREE_MODEL_FALLBACKS`
7. The raw JSON string from the LLM is parsed and validated against `LLMRecommendationPayload`
8. `parse_rate_limits(headers)` extracts quota info from response headers
9. `record_usage(...)` appends a log entry to `logs/usage.json`
10. A `RecommendationResponse` is assembled and returned to the client

---

## Error Handling

| Scenario | Behaviour |
|----------|-----------|
| Invalid request body | 422 Unprocessable Entity (Pydantic) |
| All LLM models fail | 503 Service Unavailable |
| LLM returns malformed JSON | Retried with next fallback model |
| Missing API key | 503 (caught at LLM service init) |

---

## Concurrency Notes

- FastAPI + Uvicorn is async; the LLM call is the only I/O-heavy operation
- Usage logger uses a threading lock for file safety under concurrent requests
- No shared mutable state beyond the log file

---

*See also: [[API-Reference]] | [[LLM-Integration]] | [[Data-Models]]*
