# Configuration

All configuration is managed via environment variables loaded from `.env` using `python-dotenv`. Values are centralized in `app/config.py`.

---

## Setup

```bash
cp .env.example .env
# Edit .env — at minimum set OPENAI_API_KEY
```

---

## Environment Variables

### Required

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key. Primary provider. Get one at platform.openai.com |

Without `OPENAI_API_KEY`, the service will skip OpenAI and attempt OpenRouter fallbacks. If `OPENROUTER_API_KEY` is also missing, every `/recommend` call returns `503`.

### Optional — OpenAI (Primary)

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_MODEL` | `gpt-4o` | Primary model to use for recommendations |

### Optional — OpenRouter (Fallback)

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | *(empty)* | OpenRouter key, used only if OpenAI fails |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | OpenRouter API base URL |

### Optional — Mock Mode

| Variable | Default | Description |
|----------|---------|-------------|
| `MOCK_MODE` | `false` | Set to `true` to return a static response without calling any LLM. Useful for frontend development without API keys |

### Optional — API Metadata

| Variable | Default | Description |
|----------|---------|-------------|
| `API_TITLE` | `Specialist Recommender API` | Name shown in Swagger UI |
| `API_VERSION` | `0.2.0` | Version shown in Swagger and `/` endpoint |
| `API_DESCRIPTION` | *(see config.py)* | Description in Swagger UI |
| `CORS_ALLOW_ORIGINS` | `*` | Comma-separated allowed CORS origins |

---

## Example `.env` Files

### Minimal (OpenAI only)

```env
OPENAI_API_KEY=sk-proj-your-key-here
```

### With OpenRouter fallback (recommended)

```env
OPENAI_API_KEY=sk-proj-your-key-here
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

### Local dev with frontend on port 3000

```env
OPENAI_API_KEY=sk-proj-your-key-here
OPENROUTER_API_KEY=sk-or-v1-your-key-here
CORS_ALLOW_ORIGINS=http://localhost:3000
```

### Using a different OpenAI model

```env
OPENAI_API_KEY=sk-proj-your-key-here
OPENAI_MODEL=gpt-4o-mini
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

### Production-like

```env
OPENAI_API_KEY=sk-proj-your-key-here
OPENAI_MODEL=gpt-4o
OPENROUTER_API_KEY=sk-or-v1-your-key-here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
API_TITLE=Specialist Recommender API
API_VERSION=0.2.0
CORS_ALLOW_ORIGINS=https://app.med360.com,https://admin.med360.com
```

---

## CORS Notes

- Default `*` is fine for local development
- For any shared or deployed environment, explicitly set `CORS_ALLOW_ORIGINS`
- Multiple origins: comma-separated, no spaces — `https://a.com,https://b.com`

---

## Provider Fallback Logic

```
Request arrives
    │
    ▼
OPENAI_API_KEY set?
    ├─ Yes → Try gpt-4o (or OPENAI_MODEL)
    │           ├─ Success → return response
    │           └─ Any error → fall through to OpenRouter
    └─ No  → skip to OpenRouter
    │
    ▼
OPENROUTER_API_KEY set?
    ├─ Yes → Try 11 free models in order
    │           ├─ First success → return response
    │           └─ All fail → 503
    └─ No  → 503 (no providers available)
```

---

## Config in Code (`app/config.py`)

```python
OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL     = os.getenv("OPENAI_MODEL", "gpt-4o")

OPENROUTER_API_KEY  = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

MOCK_MODE        = os.getenv("MOCK_MODE", "false").lower() == "true"

API_TITLE        = os.getenv("API_TITLE", "Specialist Recommender API")
API_VERSION      = os.getenv("API_VERSION", "0.2.0")
CORS_ALLOW_ORIGINS = os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")
```

---

*See also: [[Development-Guide]] | [[LLM-Integration]] | [[Architecture]]*
