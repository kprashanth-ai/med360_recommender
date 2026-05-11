# LLM Integration

All LLM communication is isolated in `app/services/llm.py`.

---

## Provider Strategy

The service uses a **two-tier provider strategy**:

1. **Primary — OpenAI** (`api.openai.com` via `openai_client`)
2. **Fallback — OpenRouter** (`openrouter.ai` via `openrouter_client`)

OpenAI is always tried first. OpenRouter free models are only used if OpenAI fails. Both clients use the OpenAI Python SDK — OpenRouter is OpenAI-compatible so the same SDK works for both.

---

## Primary: OpenAI

Configured via `.env`:

```env
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o          # optional, defaults to gpt-4o
```

**Default model:** `gpt-4o`

The service sends a structured JSON chat completion request to `api.openai.com`. The primary model runs on every request as long as it responds successfully.

> Using `gpt-4o` as primary incurs cost. See the pricing table below.

---

## Fallback: OpenRouter Free Models

Used only when OpenAI fails. Configured via `.env`:

```env
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

The service iterates through this list in order until one succeeds:

```
1.  mistralai/mistral-7b-instruct:free
2.  mistralai/mistral-small-3.1-24b-instruct:free
3.  meta-llama/llama-3.1-8b-instruct:free
4.  meta-llama/llama-3.2-3b-instruct:free
5.  deepseek/deepseek-r1:free
6.  deepseek/deepseek-chat-v3-0324:free
7.  google/gemma-3-27b-it:free
8.  google/gemma-3-12b-it:free
9.  google/gemma-3-4b-it:free
10. qwen/qwen3-8b:free
11. qwen/qwen-2.5-7b-instruct:free
```

All fallback models are free-tier — cost is $0.00 when any of these handle the request.

---

## Fallback Triggers

A fallback to the next model is triggered when:

- `RateLimitError` — provider quota exceeded
- `AuthenticationError` — invalid API key
- `NotFoundError` — model unavailable or removed
- `APIConnectionError` / `APITimeoutError` — network failure
- `BadRequestError` — malformed request
- `APIError` — other API-level error
- `json.JSONDecodeError` / `ValidationError` — LLM returned malformed or schema-mismatched JSON

If OpenAI fails → iterate OpenRouter fallbacks.
If all OpenRouter fallbacks fail → raise `RuntimeError` → API returns `503 Service Unavailable`.

---

## Prompt Design

Defined in `app/prompts.py`.

### System Prompt Structure

1. **Role definition** — triage assistant, not a diagnostician; picks exactly one specialist or defaults to General Physician if uncertain
2. **Output fields** — instructs the model to return `primary_recommendation_summary`, `symptom_explanation`, `specialist_pathway` (up to 3), `red_flags` (3 to 5)
3. **Output schema** — the exact JSON structure the model must return, with the full specialist list embedded

### User Message

Patient details formatted by `build_patient_info()`:

```
Patient info: Age: 30, Gender: male, Severity: medium, Duration: 4 days, Symptoms: persistent cough with chest tightness
```

### JSON Enforcement

`response_format={"type": "json_object"}` is sent with every request. This forces the model to return raw JSON — no markdown fences, no preamble. The response is then validated against `LLMRecommendationPayload` using Pydantic.

---

## Rate Limit Parsing

After each call, `parse_rate_limits()` in `app/tracker.py` reads these HTTP response headers (normalized to lowercase by httpx):

```
x-ratelimit-limit-requests       x-ratelimit-limit
x-ratelimit-remaining-requests   x-ratelimit-remaining
x-ratelimit-reset-requests       x-ratelimit-reset
x-ratelimit-limit-tokens
x-ratelimit-remaining-tokens
x-ratelimit-reset-tokens
```

These are surfaced in `RecommendationResponse.usage.rate_limits`. OpenAI returns request-count limits; token limits are typically null for OpenAI direct calls.

---

## Cost Estimation

`app/tracker.py` maintains a pricing table (USD per 1M tokens):

| Model | Input | Output | Notes |
|-------|-------|--------|-------|
| `gpt-4o` | $2.50 | $10.00 | OpenAI primary |
| `gpt-4o-mini` | $0.15 | $0.60 | OpenAI alternative |
| `openai/gpt-4o` | $2.50 | $10.00 | Via OpenRouter |
| `openai/gpt-4o-mini` | $0.15 | $0.60 | Via OpenRouter |
| All `:free` models | $0.00 | $0.00 | OpenRouter fallbacks |
| Unknown models | $0.00 | $0.00 | Default fallback pricing |

Cost is logged per request and aggregated by `GET /usage`.

---

## Swapping Providers

The LLM layer is fully isolated in `app/services/llm.py`. To change the primary provider:

1. Update `OPENAI_API_KEY` and `OPENAI_MODEL` in `.env` (or swap the `openai_client` initialization in `llm.py`)
2. To change fallback models, edit `OPENROUTER_FALLBACKS` in `app/config.py`
3. Add any new paid model IDs to `MODEL_PRICING` in `app/tracker.py` for accurate cost tracking

---

*See also: [[Architecture]] | [[Configuration]] | [[Data-Models]]*
