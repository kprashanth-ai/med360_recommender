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

Pydantic will return a `422 Unprocessable Entity` with field-level error details if validation fails.

---

## LLMRecommendationPayload (Internal)

Used internally to validate the raw JSON string returned by the LLM. Never exposed to API clients directly.

```python
class SpecialistPathwayItem(BaseModel):
    specialist: str
    reason: str

class LLMRecommendationPayload(BaseModel):
    recommended_specialist: str
    primary_recommendation_summary: str
    symptom_explanation: str
    specialist_pathway: list[SpecialistPathwayItem]  # exactly 3
    red_flags: list[str]                              # 3–5 items
```

If the LLM returns malformed JSON or a schema mismatch, the LLM service retries with the next fallback model.

---

## RecommendationResponse (Response)

Public API response for `POST /recommend`. Extends `LLMRecommendationPayload` with usage metadata.

```python
class RateLimitInfo(BaseModel):
    limit: int | None
    remaining: int | None
    reset: str | None

class RateLimits(BaseModel):
    requests: RateLimitInfo
    tokens: RateLimitInfo

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
| `recommended_specialist` | Single specialist chosen from the 20-item list |
| `primary_recommendation_summary` | 2–3 sentences for the patient, not clinical language |
| `symptom_explanation` | Why these symptoms point to this specialist |
| `specialist_pathway` | 3 alternative pathways (ordered by relevance) |
| `red_flags` | 3–5 symptoms that warrant emergency/urgent care |
| `disclaimer` | Static medical/legal disclaimer from `app/constants.py` |

**Usage metadata** (sourced from OpenRouter response):

| Field | Description |
|-------|-------------|
| `model_used` | Actual model that produced the response (may differ from configured primary) |
| `prompt_tokens` | Tokens in the input (system prompt + patient info) |
| `completion_tokens` | Tokens in the LLM output |
| `total_tokens` | Sum of prompt + completion |
| `cost_usd` | Estimated cost; 0.0 for all free-tier models |
| `rate_limits.requests` | Provider rate-limit quota for requests |
| `rate_limits.tokens` | Provider rate-limit quota for tokens (often null) |

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
          + disclaimer + UsageInfo
                       │
                       ▼
         RecommendationResponse ──► (API response)
```

---

*See also: [[API-Reference]] | [[LLM-Integration]] | [[Architecture]]*
