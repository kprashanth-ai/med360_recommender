# Specialist Recommender API

This repository started as a symptom-to-specialist recommendation prototype with two thin clients:

- `streamlit_app.py` for a quick UI demo
- `specialist_recommender.py` for local CLI testing

The reusable backend now lives in the `app/` package and is exposed as a FastAPI service for team integration.

## Project Structure

```text
recommender/
├── app/
│   ├── config.py            # environment-driven settings
│   ├── constants.py         # specialist list and shared disclaimer
│   ├── main.py              # FastAPI application entrypoint
│   ├── models.py            # request/response schemas
│   ├── prompts.py           # system prompt and JSON schema instructions
│   ├── tracker.py           # token/cost logging
│   └── services/
│       └── llm.py           # OpenRouter/OpenAI call logic
├── logs/                    # runtime usage log output
├── specialist_recommender.py
├── streamlit_app.py
└── requirements.txt
```

## Current Flow

1. The client sends patient details to `POST /recommend`.
2. FastAPI validates the payload with Pydantic models.
3. `app/services/llm.py` builds an LLM request using the shared prompt.
4. The service tries the configured primary model and then fallback models.
5. The response is parsed as JSON and normalized into the API response schema.
6. Token usage, rate limits, and estimated cost are logged to `logs/usage.json`.

## API Endpoints

### `GET /`

Returns basic service metadata and useful URLs.

### `GET /health`

Health check for load balancers, backend orchestration, and frontend environment verification.

Example response:

```json
{
  "status": "ok",
  "service": "Specialist Recommender API",
  "version": "0.2.0"
}
```

### `GET /usage`

Returns aggregated totals from `logs/usage.json`.

Example response:

```json
{
  "total_requests": 8,
  "total_tokens": 5621,
  "total_cost_usd": 0.0
}
```

### `POST /recommend`

Request:

```json
{
  "age": 25,
  "gender": "female",
  "severity": "medium",
  "duration_days": 3,
  "symptoms": "skin rash, itching, hives after eating"
}
```

Response:

```json
{
  "recommended_specialist": "Allergist/Immunologist",
  "primary_recommendation_summary": "Your symptoms may be related to an allergic reaction pattern and should be assessed by a specialist.",
  "symptom_explanation": "The combination of rash, itching, and hives after eating can suggest the body is reacting to a trigger.",
  "specialist_pathway": [
    {
      "specialist": "Allergist/Immunologist",
      "reason": "Best fit for food-related allergy evaluation"
    },
    {
      "specialist": "Dermatologist",
      "reason": "Helpful if symptoms are primarily skin-focused"
    },
    {
      "specialist": "General Physician",
      "reason": "Useful first step if symptoms broaden or diagnosis is unclear"
    }
  ],
  "red_flags": [
    "difficulty breathing",
    "swelling of the lips or tongue",
    "fainting",
    "rapid worsening rash",
    "persistent vomiting"
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

## Environment Setup

Create a `.env` file from `.env.example`.

Required:

```env
OPENROUTER_API_KEY=your_key_here
```

Optional:

```env
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=google/gemma-3n-e4b-it:free
API_TITLE=Specialist Recommender API
API_VERSION=0.2.0
CORS_ALLOW_ORIGINS=*
```

If the frontend team knows the deployed origins already, replace `*` with a comma-separated list such as:

```env
CORS_ALLOW_ORIGINS=http://localhost:3000,https://frontend.example.com
```

## Run Locally

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the API:

```bash
uvicorn app.main:app --reload
```

Open Swagger docs:

```text
http://127.0.0.1:8000/docs
```

## Integration Notes

### Backend Team

- The main backend contract is the `PatientInput` request model and `RecommendationResponse` schema in `app/models.py`.
- `app/services/llm.py` is the only place that talks to the LLM provider, so provider swaps can stay isolated there.
- `app/tracker.py` currently writes to a local JSON file; that is fine for development but should move to structured logging or a database for shared environments.
- CORS is configurable through `CORS_ALLOW_ORIGINS`.

### Frontend Team

- Use `POST /recommend` as the primary integration endpoint.
- The response already includes user-facing fields for summary, explanation, red flags, and alternate specialists.
- The `usage` block is optional from a product perspective; it is useful for debugging/admin panels but can be hidden in the main UI.
- `GET /health` is useful for connectivity checks in local and staging environments.

## Recommended Next Steps Before Production

1. Add automated tests for `POST /recommend` with the LLM layer mocked.
2. Move usage logging from `logs/usage.json` to a shared store or observability pipeline.
3. Restrict CORS to known frontend origins.
4. Add request authentication if this service will be exposed beyond internal use.
5. Containerize the service for consistent backend/frontend team environments.

## GitHub Push Workflow

Once the repo is ready to publish:

```bash
git init
git add .
git commit -m "Prepare FastAPI specialist recommender service"
git remote add origin <your-github-repo-url>
git branch -M main
git push -u origin main
```

If this directory is already a git repository on your machine, use the existing remote instead of reinitializing it.
