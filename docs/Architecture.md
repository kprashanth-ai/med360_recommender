# Architecture

## Overview

The Specialist Recommender is a single FastAPI service with no database. State is limited to a local usage log file. All intelligence comes from an LLM — OpenAI is the primary provider, OpenRouter free models are the fallback.

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
        ├──► openai_client → OpenAI API (gpt-4o) [PRIMARY]
        │         │
        │    success? ──► return
        │    failure? ──► try OpenRouter
        │
        └──► openrouter_client → OpenRouter free models [FALLBACK]
                  │
             iterate 11 models until one succeeds
        │
        ▼
  Response validation (LLMRecommendationPayload — Pydantic)
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
- All route handlers delegate immediately to the service layer

### `app/models.py` — Data Contracts

Three Pydantic models:
- `PatientInput` — validated request body for `POST /recommend`
- `LLMRecommendationPayload` — internal model for validating raw LLM JSON
- `RecommendationResponse` — public response shape returned to clients

See [[Data-Models]] for full field definitions.

### `app/services/llm.py` — LLM Integration Layer

The only module that talks to external AI providers. Two clients:
- `openai_client` — `OpenAI(api_key=OPENAI_API_KEY)` → hits `api.openai.com`
- `openrouter_client` — `OpenAI(api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_BASE_URL)` → hits `openrouter.ai`

Responsibilities:
- Try OpenAI primary model first
- On any failure, iterate OpenRouter fallback models
- Validate returned JSON against `LLMRecommendationPayload`
- Extract rate-limit headers from HTTP response
- Return normalized `(data, model_used, usage_entry)`

See [[LLM-Integration]] for full details.

### `app/prompts.py` — Prompt Engineering

- System prompt defines the triage assistant role and output format
- Embeds the full `SPECIALISTS` list from `app/constants.py`
- Enforces `response_format={"type": "json_object"}` at the API call level
- Patient details are injected as the user message

### `app/tracker.py` — Usage Tracking

- Thread-safe local file logger using `threading.Lock()`
- Writes atomically via temp file + `replace()` to prevent corruption
- Parses `x-ratelimit-*` response headers
- Estimates cost per request using `MODEL_PRICING` table
- Provides `get_session_totals()` for `GET /usage`

### `app/config.py` — Configuration

Reads environment variables via `python-dotenv`. All config is centralized here.
- `OPENAI_API_KEY`, `OPENAI_MODEL` — primary provider
- `OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL` — fallback provider
- `OPENROUTER_FALLBACKS` — ordered list of 11 fallback model IDs

See [[Configuration]] for all variables.

### `app/constants.py` — Static Data

- `SPECIALISTS` — list of 20 valid specialist categories the LLM must choose from
- `RECOMMENDATION_DISCLAIMER` — medical/legal disclaimer appended to every response

---

## Request Flow (Detailed)

1. `POST /recommend` receives JSON body
2. Pydantic validates and coerces `PatientInput`
3. `build_patient_info(patient)` formats patient details into a string
4. `get_recommendation(patient_info)` is called in `llm.py`
5. System prompt + patient string sent to **OpenAI** as a chat completion (with `response_format=json_object`)
6. If OpenAI fails for any reason → iterate through `OPENROUTER_FALLBACKS` on `openrouter_client`
7. Raw JSON from the LLM is validated against `LLMRecommendationPayload`
8. `parse_rate_limits(headers)` extracts quota info from HTTP response headers
9. `record_usage(...)` writes a log entry to `logs/usage.json` (thread-safe)
10. `RecommendationResponse` is assembled and returned to the client

---

## Error Handling

| Scenario | Behaviour |
|----------|-----------|
| Invalid request body | 422 Unprocessable Entity (Pydantic) |
| OpenAI fails, all OpenRouter fallbacks fail | 503 Service Unavailable |
| LLM returns malformed JSON | Retry with next model |
| Both API keys missing | 503 (no providers available) |

---

## Concurrency Notes

- FastAPI + Uvicorn is async; the LLM HTTP call is the primary I/O operation
- Usage logger uses `threading.Lock` for file safety under concurrent requests
- No shared mutable state beyond the log file

---

*See also: [[API-Reference]] | [[LLM-Integration]] | [[Data-Models]]*
