# Configuration

All configuration is managed via environment variables loaded from `.env` using `python-dotenv`. The values are centralized in `app/config.py` — no scattered `os.getenv()` elsewhere.

---

## Setup

```bash
cp .env.example .env
# Edit .env and fill in OPENROUTER_API_KEY
```

---

## Environment Variables

### Required

| Variable | Description |
|----------|-------------|
| `OPENROUTER_API_KEY` | Your OpenRouter API key. Get one at openrouter.ai |

Without this key, `POST /recommend` will return a `503` error.

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | OpenRouter API base URL |
| `OPENROUTER_MODEL` | `google/gemma-3n-e4b-it:free` | Primary LLM model to use |
| `API_TITLE` | `Specialist Recommender API` | Name shown in Swagger UI |
| `API_VERSION` | `0.2.0` | Version shown in Swagger UI and `/` endpoint |
| `API_DESCRIPTION` | *(see config.py)* | Description in Swagger UI |
| `CORS_ALLOW_ORIGINS` | `*` | Comma-separated allowed origins for CORS |

---

## Example `.env` Files

### Local development (minimal)

```env
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

### Local with frontend on port 3000

```env
OPENROUTER_API_KEY=sk-or-v1-your-key-here
CORS_ALLOW_ORIGINS=http://localhost:3000
```

### Using a paid/specific model

```env
OPENROUTER_API_KEY=sk-or-v1-your-key-here
OPENROUTER_MODEL=anthropic/claude-3-5-sonnet
```

### Production-like

```env
OPENROUTER_API_KEY=sk-or-v1-your-key-here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=google/gemma-3n-e4b-it:free
API_TITLE=Specialist Recommender API
API_VERSION=0.2.0
CORS_ALLOW_ORIGINS=https://app.med360.com,https://admin.med360.com
```

---

## CORS Notes

- Default `*` is fine for local development
- For any shared or deployed environment, explicitly set `CORS_ALLOW_ORIGINS` to the frontend domains
- Multiple origins: comma-separated with no spaces — `https://a.com,https://b.com`

---

## Model Selection Notes

- The `OPENROUTER_MODEL` variable sets the **primary** model
- If the primary model is rate-limited or unavailable, the service falls back through 11 additional free models automatically
- See [[LLM-Integration]] for the full fallback list
- To use a paid model as primary, set `OPENROUTER_MODEL` to the paid model's ID — fallbacks will still be free models

---

## Config in Code (`app/config.py`)

```python
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemma-3n-e4b-it:free")
API_TITLE = os.getenv("API_TITLE", "Specialist Recommender API")
API_VERSION = os.getenv("API_VERSION", "0.2.0")
API_DESCRIPTION = os.getenv("API_DESCRIPTION", "...")
CORS_ALLOW_ORIGINS = os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")
```

---

*See also: [[Development-Guide]] | [[LLM-Integration]] | [[Architecture]]*
