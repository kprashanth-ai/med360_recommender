# API Reference

Base URL (local): `http://127.0.0.1:8000`

Interactive docs: `http://127.0.0.1:8000/docs`

OpenAPI spec: `http://127.0.0.1:8000/openapi.json`

---

## GET /

Service metadata.

**Response**
```json
{
  "name": "Specialist Recommender API",
  "version": "0.2.0",
  "docs_url": "/docs",
  "health_url": "/health"
}
```

---

## GET /health

Liveness check. Use this for connectivity verification in frontend and infra checks.

**Response**
```json
{
  "status": "ok",
  "service": "Specialist Recommender API",
  "version": "0.2.0"
}
```

---

## GET /usage

Aggregated totals from the local usage log (`logs/usage.json`).

**Response**
```json
{
  "total_requests": 14,
  "total_tokens": 18420,
  "total_cost_usd": 0.0
}
```

> Cost is 0.0 when using free-tier OpenRouter models.

---

## POST /recommend

Primary integration endpoint. Accepts patient symptoms, returns triage recommendation.

### Request Body

```json
{
  "age": 25,
  "gender": "female",
  "severity": "medium",
  "duration_days": 3,
  "symptoms": "skin rash, itching, hives after eating"
}
```

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `age` | integer | 1–120 | Patient age |
| `gender` | string | `male` \| `female` \| `other` | Patient gender |
| `severity` | string | `low` \| `medium` \| `high` | Self-reported severity |
| `duration_days` | integer | 1–365 | How long symptoms have persisted |
| `symptoms` | string | min 5 chars | Free-text symptom description |

### Response Body

```json
{
  "recommended_specialist": "Allergist/Immunologist",
  "primary_recommendation_summary": "Your symptoms suggest an allergic reaction that should be evaluated by a specialist.",
  "symptom_explanation": "The rash, itching, and hives occurring after eating are classic signs that the immune system may be reacting to a food or environmental trigger.",
  "specialist_pathway": [
    {
      "specialist": "Allergist/Immunologist",
      "reason": "Best fit for evaluating allergic reactions and identifying triggers"
    },
    {
      "specialist": "Dermatologist",
      "reason": "If the presentation is primarily skin-focused without systemic symptoms"
    },
    {
      "specialist": "General Physician",
      "reason": "Starting point if access to a specialist is delayed"
    }
  ],
  "red_flags": [
    "difficulty breathing or swallowing",
    "swelling of lips, tongue, or throat",
    "sudden drop in blood pressure or fainting",
    "rapid worsening of symptoms"
  ],
  "disclaimer": "This recommendation is an AI-assisted triage suggestion for consultation booking only. It is not a medical diagnosis or emergency advice. Please consult a qualified clinician for confirmation, and seek urgent care immediately for severe or worsening symptoms.",
  "usage": {
    "model_used": "google/gemma-3n-e4b-it:free",
    "prompt_tokens": 412,
    "completion_tokens": 318,
    "total_tokens": 730,
    "cost_usd": 0.0,
    "rate_limits": {
      "requests": {
        "limit": 200,
        "remaining": 187,
        "reset": "2026-05-11T18:00:00Z"
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

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `recommended_specialist` | string | One of 20 valid specialists |
| `primary_recommendation_summary` | string | 2–3 sentence patient-facing summary |
| `symptom_explanation` | string | 2–3 sentence plain-language explanation |
| `specialist_pathway` | array | 3 alternate specialists with reasons |
| `red_flags` | array | 3–5 urgent symptoms requiring immediate care |
| `disclaimer` | string | Legal/medical disclaimer |
| `usage.model_used` | string | Which LLM model was actually used |
| `usage.prompt_tokens` | integer | Input token count |
| `usage.completion_tokens` | integer | Output token count |
| `usage.total_tokens` | integer | Total tokens consumed |
| `usage.cost_usd` | float | Estimated cost (0.0 for free models) |
| `usage.rate_limits` | object | Provider rate-limit quota from response headers |

### Error Responses

| Status | Condition |
|--------|-----------|
| `422 Unprocessable Entity` | Invalid request body (wrong types, out-of-range values) |
| `503 Service Unavailable` | All LLM models failed or API key missing |

---

## Valid Specialist Values

The `recommended_specialist` field will always be one of:

```
General Physician        Dermatologist          Cardiologist
Neurologist              Orthopedic Surgeon     Gastroenterologist
Pulmonologist            Endocrinologist        Psychiatrist
Ophthalmologist          ENT Specialist         Urologist
Gynecologist             Rheumatologist         Allergist/Immunologist
Oncologist               Nephrologist           Infectious Disease Specialist
Hematologist             Pediatrician
```

---

## Integration Examples

### curl

```bash
curl -X POST "http://127.0.0.1:8000/recommend" \
  -H "Content-Type: application/json" \
  -d '{
    "age": 30,
    "gender": "male",
    "severity": "medium",
    "duration_days": 4,
    "symptoms": "persistent cough with chest tightness"
  }'
```

### JavaScript (fetch)

```js
const res = await fetch("http://127.0.0.1:8000/recommend", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    age: 30,
    gender: "male",
    severity: "medium",
    duration_days: 4,
    symptoms: "persistent cough with chest tightness"
  })
});

const data = await res.json();
console.log(data.recommended_specialist);
```

### Python (requests)

```python
import requests

payload = {
    "age": 30,
    "gender": "male",
    "severity": "medium",
    "duration_days": 4,
    "symptoms": "persistent cough with chest tightness"
}

res = requests.post("http://127.0.0.1:8000/recommend", json=payload)
data = res.json()
print(data["recommended_specialist"])
```

---

## Notes for Frontend Team

- The `usage` block is for debugging or admin UIs — core patient UI can ignore it
- Use `GET /health` for local connectivity checks before rendering the form
- A `503` from `/recommend` means the backend is missing an API key or all provider models are down
- CORS is open (`*`) locally — production deployment should restrict this

---

*See also: [[Data-Models]] | [[Architecture]] | [[Configuration]]*
