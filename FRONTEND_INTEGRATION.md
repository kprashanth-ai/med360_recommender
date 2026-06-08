# Frontend Integration Guide

Everything you need to integrate the Specialist Recommender API into the frontend. Skip the rest of the docs — this is the one page for frontend teams.

---

## Base URL

| Environment | URL |
|-------------|-----|
| Local (dev) | `http://127.0.0.1:8000` |
| Production | *(TBD — to be provided by backend team)* |

---

## Running the Backend Locally

If you need to run the backend yourself:

```bash
git clone https://github.com/kprashanth-ai/med360_recommender.git
cd med360_recommender

python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows
# source .venv/bin/activate       # Mac/Linux

pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` — choose one of:

**Option A — No API keys (mock responses):**
```env
MOCK_MODE=true
```

**Option B — Real responses (needs an OpenAI key):**
```env
OPENAI_API_KEY=sk-proj-your-key-here
```

Then start the server:
```bash
uvicorn app.main:app --reload
```

---

## Endpoints

### Connectivity check
```
GET /health
```
```json
{ "status": "ok", "service": "Specialist Recommender API", "version": "0.2.0" }
```
Use this to confirm the backend is reachable before rendering the form.

---

### Get recommendation
```
POST /recommend
Content-Type: application/json
```

**Request:**
```json
{
  "age": 35,
  "gender": "female",
  "severity": "medium",
  "duration_days": 3,
  "symptoms": "skin rash, itching, hives after eating"
}
```

| Field | Type | Values | Required |
|-------|------|--------|----------|
| `age` | integer | 1–120 | Yes |
| `gender` | string | `"male"` `"female"` `"other"` | Yes |
| `severity` | string | `"low"` `"medium"` `"high"` | Yes |
| `duration_days` | integer | 1–365 | Yes |
| `symptoms` | string | min 5 characters | Yes |

**Response:**
```json
{
  "recommended_specialist": "Dermatologist",
  "primary_recommendation_summary": "Your symptoms suggest an allergic skin reaction that should be evaluated by a specialist.",
  "symptom_explanation": "The rash, itching, and hives occurring after eating can indicate a reaction to a food or environmental trigger.",
  "specialist_pathway": [
    { "specialist": "Dermatologist", "reason": "Best fit for skin-based allergic reactions" },
    { "specialist": "General Physician", "reason": "Starting point if specialist access is delayed" },
    { "specialist": "Gastroenterologist", "reason": "If food intolerance with GI involvement is suspected" }
  ],
  "red_flags": [
    "difficulty breathing or swallowing",
    "swelling of lips, tongue, or throat",
    "sudden drop in blood pressure"
  ],
  "disclaimer": "This recommendation is an AI-assisted triage suggestion...",
  "usage": {
    "model_used": "gpt-4o",
    "prompt_tokens": 481,
    "completion_tokens": 308,
    "total_tokens": 789,
    "cost_usd": 0.00428,
    "rate_limits": { ... }
  }
}
```

**Fields to display in UI:**

| Field | Show to patient? | Notes |
|-------|-----------------|-------|
| `recommended_specialist` | Yes | Primary result |
| `primary_recommendation_summary` | Yes | Main patient-facing text |
| `symptom_explanation` | Yes | Explain why |
| `specialist_pathway` | Yes | Show as alternatives list |
| `red_flags` | Yes | Highlight prominently |
| `disclaimer` | Yes | Required — show at bottom |
| `usage` | No | Debug/admin only |

---

## Error Handling

### 422 — Validation error (your form input was invalid)

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "age"],
      "msg": "Field required",
      "input": {}
    }
  ]
}
```

Each item in `detail` has:
- `loc` — where the error is (e.g. `["body", "age"]`)
- `msg` — human-readable message
- `type` — error type

### 503 — Service unavailable (backend provider issue)

```json
{
  "detail": "All 12 models failed:\n  OpenAI/gpt-4o -> rate limited\n  ..."
}
```

Show the user a generic "service temporarily unavailable, please try again" message.

---

## JavaScript Example

```js
async function getRecommendation(formData) {
  const res = await fetch("http://127.0.0.1:8000/recommend", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      age: formData.age,
      gender: formData.gender,
      severity: formData.severity,
      duration_days: formData.durationDays,
      symptoms: formData.symptoms,
    }),
  });

  if (res.status === 422) {
    const err = await res.json();
    // err.detail is an array of field-level errors
    throw new Error(err.detail.map(e => e.msg).join(", "));
  }

  if (res.status === 503) {
    throw new Error("Service temporarily unavailable. Please try again.");
  }

  if (!res.ok) {
    throw new Error("Unexpected error. Please try again.");
  }

  return res.json();
}
```

---

## Mock Mode

If you don't have an OpenAI key, set `MOCK_MODE=true` in `.env`. The backend will return a static response with clearly labelled mock data — no API key needed, no LLM called. The response shape is identical to a real response so your UI integration will work without modification.

---

## CORS

CORS is open (`*`) for local development — no extra headers needed. For production, the backend team will restrict this to your frontend domain.

---

## Interactive API Explorer

With the backend running: `http://127.0.0.1:8000/docs`

You can test every endpoint directly from the browser — useful for exploring the response shape before writing any code.
