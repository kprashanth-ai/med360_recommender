# Roadmap

Current version: **0.2.0**

This note tracks what is missing, what is planned, and rough priority.

---

## Known Gaps (Blocking for Production)

These should be resolved before exposing the service beyond trusted internal environments.

### No Authentication
- The `/recommend` endpoint is open with no API keys, JWT, or session validation
- Any client with network access can call it
- **Fix:** Add FastAPI dependency for API key validation or integrate with Med360 auth

### No Automated Tests
- No pytest suite exists
- LLM responses are hard to test deterministically — the service layer needs to be mockable
- **Fix:** Add tests with `unittest.mock` patching the OpenRouter client; test validation logic, fallback triggering, and error paths separately

### No Mock Mode
- Frontend developers cannot work without a real `OPENROUTER_API_KEY`
- **Fix:** Add a `MOCK_MODE=true` env flag that returns a static example response, bypassing the LLM call entirely

### File-Based Usage Logging
- `logs/usage.json` is local to the running process — not shared across instances or persistent across redeployments
- **Fix:** Replace with structured logging to a database, a centralized log sink, or a cloud metrics service

### No Dockerfile
- Local setup requires Python environment management manually
- **Fix:** Add a `Dockerfile` + `docker-compose.yml` for consistent local and deployment workflows

### CORS Defaults to `*`
- Open CORS is fine locally but must be restricted before any shared deployment
- **Fix:** Ensure `CORS_ALLOW_ORIGINS` is explicitly set in any non-local environment

---

## Near-Term Improvements

Lower urgency but valuable for quality and developer experience.

### Request Rate Limiting
- No client-side rate limiting on the API itself (separate from the provider rate limits)
- Consider `slowapi` or a reverse-proxy rate limit for abuse prevention

### Structured Logging
- Current print/exception logging is not structured
- Add `structlog` or standard Python logging with JSON formatter for searchable logs

### Observability
- No metrics for response latency, error rates, or model distribution
- Add Prometheus metrics or integrate with an APM tool

### Paid Model Hybrid Strategy
- Free models have lower quality and rate limits compared to paid models
- Consider routing `severity: high` requests to a paid model while keeping low/medium on free tier

---

## Future Considerations

Longer-term ideas, not yet scoped.

- **Multi-language support** — non-English symptom input
- **Symptom history** — incorporate past visits or chronic conditions into the recommendation context
- **Feedback loop** — let clinicians rate recommendations to improve prompt tuning
- **Specialty confidence scoring** — return a confidence level alongside the recommendation
- **Triage urgency tier** — distinct from severity input; model-assessed urgency (routine / urgent / emergency)

---

## Completed

- [x] FastAPI app with typed request/response models
- [x] OpenRouter integration with multi-model fallback chain
- [x] CORS middleware
- [x] Response shape validation for LLM output
- [x] Local usage logging with cost estimation
- [x] Swagger docs at `/docs`
- [x] Streamlit demo UI
- [x] CLI demo client
- [x] Obsidian documentation vault

---

*See also: [[Architecture]] | [[Development-Guide]] | [[Configuration]]*
