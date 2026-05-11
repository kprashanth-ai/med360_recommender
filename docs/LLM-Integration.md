# LLM Integration

All LLM communication is isolated in `app/services/llm.py`.

---

## Provider

**OpenRouter** — an OpenAI-compatible API aggregator that routes to multiple model providers. The service uses the OpenAI Python SDK pointed at OpenRouter's base URL.

```
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

OpenRouter provides access to both free and paid models under a single API key, making the fallback strategy simple to implement.

---

## Model Strategy

### Primary Model

Configured via `OPENROUTER_MODEL` env var. Default:

```
google/gemma-3n-e4b-it:free
```

### Fallback Chain

If the primary model fails (rate limit, model not found, API error, or JSON validation failure), the service iterates through this list in order:

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

All models are free-tier, so cost is $0.00 under normal operation.

### Fallback Triggers

A fallback is triggered when:
- `RateLimitError` from OpenRouter
- `NotFoundError` (model unavailable or removed)
- `APIConnectionError`
- LLM returns malformed JSON (fails `LLMRecommendationPayload` validation)
- Any unexpected exception

If all models in the chain fail, the service raises an exception and the API returns `503 Service Unavailable`.

---

## Prompt Design

Defined in `app/prompts.py`.

### System Prompt Structure

The system prompt does three things:

1. **Role definition** — instructs the model it is a medical triage assistant, not a diagnostician
2. **Specialist constraint** — provides the full list of 20 valid specialist names; model must choose exactly one
3. **Output schema** — provides the exact JSON structure the model must return

```
You are a medical triage assistant...
Choose ONE specialist from: [list]
Return ONLY valid JSON matching this schema: {...}
```

### User Message

The patient details are formatted by `build_patient_info()` and sent as the user turn:

```
Patient Information:
Age: 30
Gender: male
Symptoms: persistent cough with chest tightness
Severity: medium
Duration: 4 days
```

### Output Format

The model is instructed to return raw JSON only — no markdown fences, no preamble. The response is then parsed and validated against `LLMRecommendationPayload`.

---

## Rate Limit Parsing

After each successful call, `parse_rate_limits()` in `app/tracker.py` reads these HTTP response headers:

```
x-ratelimit-limit-requests
x-ratelimit-remaining-requests
x-ratelimit-reset-requests
x-ratelimit-limit-tokens
x-ratelimit-remaining-tokens
x-ratelimit-reset-tokens
```

These values are surfaced in `RecommendationResponse.usage.rate_limits` so clients can monitor quota consumption.

---

## Cost Estimation

`app/tracker.py` maintains a pricing table for known models (in USD per 1M tokens):

| Model | Prompt | Completion |
|-------|--------|------------|
| Free-tier (all `:free` models) | $0.00 | $0.00 |
| `gpt-4o-mini` | $0.15 | $0.60 |
| `gpt-4o` | $5.00 | $15.00 |
| `claude-3-5-sonnet` | $3.00 | $15.00 |
| `claude-3-haiku` | $0.25 | $1.25 |

Cost is logged per request and aggregated by `GET /usage`.

---

## Swapping Providers

The LLM layer is fully isolated in `app/services/llm.py`. To swap to a different provider:

1. Change `OPENROUTER_BASE_URL` and `OPENROUTER_API_KEY` in `.env`
2. Update the model names in `FREE_MODEL_FALLBACKS` to match the new provider's model IDs
3. Verify the new provider returns the same OpenAI-compatible response shape

No changes needed outside `llm.py` and `config.py`.

---

*See also: [[Architecture]] | [[Configuration]] | [[Data-Models]]*
