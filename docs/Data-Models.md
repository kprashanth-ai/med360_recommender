# Data Models

All models are defined in `app/models.py` using Pydantic v2.

---

## PatientInput (Request)

Used as the request body for `POST /recommend`.

```python
class PatientInput(BaseModel):
    age: int                              # 1–120
    gender: Literal["male", "female", "other"]
    severity: Literal["low", "medium", "high"]
    duration_days: int                    # 1–365
    symptoms: str                         # min_length=5
```

| Field | Type | Validation | Notes |
|-------|------|------------|-------|
| `age` | `int` | 1 ≤ age ≤ 120 | Patient age in years |
| `gender` | `str` | `male`, `female`, `other` | Literal enum |
| `severity` | `str` | `low`, `medium`, `high` | Self-reported severity |
| `duration_days` | `int` | 1 ≤ days ≤ 365 | Duration of symptoms |
| `symptoms` | `str` | min 5 chars | Free-text description |

Pydantic returns `422 Unprocessable Entity` with field-level error details if validation fails.

---

## LLMRecommendationPayload (Internal)

Used internally to validate the raw JSON string returned by the LLM. Never exposed to API clients.

```python
class SpecialistPathwayItem(BaseModel):
    specialist: str
    reason: str

class LLMRecommendationPayload(BaseModel):
    recommended_specialist: str
    primary_recommendation_summary: str
    symptom_explanation: str
    specialist_pathway: list[SpecialistPathwayItem]  # up to 3 items
    red_flags: list[str]                              # 3–5 items (LLM guideline)
    disclaimer: str
```

If the LLM returns malformed JSON or a schema mismatch, the LLM service retries with the next fallback model.

**Notes:**
- `specialist_pathway` — the prompt instructs the LLM to return up to 3 items; this is a guideline, not enforced by Pydantic
- `red_flags` — the prompt instructs 3 to 5 items; the count is not Pydantic-validated
- `recommended_specialist` — must be one of the 19 values in `app/constants.py SPECIALISTS`, enforced by the system prompt not by Pydantic

---

## RecommendationResponse (Public API Response)

Returned to clients from `POST /recommend`. Extends the LLM payload with usage metadata.

```python
class RateLimitQuota(BaseModel):
    limit: int | None
    remaining: int | None
    reset: str | None

class RateLimitInfo(BaseModel):
    requests: RateLimitQuota
    tokens: RateLimitQuota

class UsageInfo(BaseModel):
    model_used: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    rate_limits: RateLimits

class RecommendationResponse(BaseModel):
    recommended_specialist: str
    primary_recommendation_summary: str
    symptom_explanation: str
    specialist_pathway: list[SpecialistPathwayItem]
    red_flags: list[str]
    disclaimer: str
    usage: UsageInfo
```

### Field Semantics

**Core recommendation fields** (sourced from LLM):

| Field | Description |
|-------|-------------|
| `recommended_specialist` | Single specialist from the 19-item `SPECIALISTS` list |
| `primary_recommendation_summary` | 2–3 sentences for the patient, not clinical language |
| `symptom_explanation` | Why these symptoms point to this specialist |
| `specialist_pathway` | Up to 3 alternative pathways (ordered by relevance) |
| `red_flags` | 3–5 symptoms warranting emergency/urgent care |
| `disclaimer` | Static text from `RECOMMENDATION_DISCLAIMER` in `app/constants.py` |

**Usage metadata** (sourced from provider response):

| Field | Description |
|-------|-------------|
| `model_used` | Actual model that produced the response (may be OpenAI or an OpenRouter fallback) |
| `prompt_tokens` | Tokens in the input (system prompt + patient info) |
| `completion_tokens` | Tokens in the LLM output |
| `total_tokens` | Sum of prompt + completion |
| `cost_usd` | Estimated cost; ~$0.004 for gpt-4o, $0.00 for OpenRouter free models |
| `rate_limits.requests` | Provider rate-limit quota for requests |
| `rate_limits.tokens` | Provider rate-limit quota for tokens (often null for OpenAI direct) |

---

## Static Data (`app/constants.py`)

### `SPECIALISTS`

The 19 valid specialist categories. The system prompt embeds this list and instructs the LLM to pick exactly one.

```
General Physician          Cardiologist               Neurologist
Orthopedician              Dermatologist              Nephrologist
Diabetologist              Urologist                  Obstetrician & Gynaecologist
General Surgeon            Gastroenterologist         Oncologist
ENT                        Ophthalmologist            Pulmonologist
Radiologist                Dentist                    Psychiatrist
Rheumatologist
```

### `RECOMMENDATION_DISCLAIMER`

Static medical/legal text appended to every response:

> "This recommendation is an AI-assisted triage suggestion for consultation booking only. It is not a medical diagnosis or emergency advice. Please consult a qualified clinician for confirmation, and seek urgent care immediately for severe or worsening symptoms."

---

## Model Relationships

```
PatientInput ──► (validated request)
                       │
                       ▼
              LLM Service builds prompt
                       │
                       ▼
         LLMRecommendationPayload ──► (internal validation)
                       │
                       ▼
          + UsageInfo (from provider headers + tracker)
                       │
                       ▼
         RecommendationResponse ──► (API response to client)
```

---

*See also: [[API-Reference]] | [[LLM-Integration]] | [[Architecture]]*
