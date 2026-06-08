# Feedback System

*Design for the human evaluation and feedback loop that validates training data quality and drives continuous improvement of the triage model.*

---

## Purpose

The feedback system serves two goals:
1. **Data quality gate** — ensure only clinically correct responses become training data
2. **Continuous improvement loop** — feed failure patterns back into prompt fixes and model retraining

---

## Human Evaluators

**Profile:** Medical or pharmacy interns with coursework in diagnosis and clinical reasoning (AIIMS/NEET level knowledge).

**Why this level:**
- Know symptom-to-specialist mapping (core of their training)
- Can evaluate red flag appropriateness
- Familiar with AIIMS/NEET clinical presentations (matches MedMCQA source material)
- More available and cost-effective than practising doctors
- Can read ICMR STWs to validate citations

**Escalation path:** Cases flagged as "unsure" by interns go to a senior clinician for review.

---

## Three-Layer Feedback Architecture

```
Layer 1 — Automatic (instant, zero cost)
Layer 2 — Expert annotation (interns, targeted)
Layer 3 — Real-world outcome (future, post-production)
```

### Layer 1 — Automatic Signal
Runs at batch time with no human involvement:
- **Format check:** Valid JSON? All required fields present?
- **Specialist check:** Is `recommended_specialist` in the 19-specialist list?
- **Label match:** Does recommended specialist match derived `subject_name` ground truth?
- **LLM-as-judge:** Panel of 3 smaller models score the response 1–5. Average ≥ 4 passes.

Output: Each run tagged `auto_pass`, `auto_fail`, or `pending_review`.

### Layer 2 — Expert Annotation (Interns)
Human review of cases selected by active sampling. Interns use the annotation UI (Streamlit).

### Layer 3 — Real-World Outcome (Future)
Once in production:
- Did the patient book with the recommended specialist?
- After consultation: did the specialist confirm the referral was appropriate?
- Even a binary "referral accepted" signal is strong ground truth.

---

## Active Sampling — What Gets Sent to Interns

Do not annotate randomly. Prioritize:

| Priority | Criterion | Reason |
|---|---|---|
| 1 | High severity cases | Patient safety — get these right first |
| 2 | Layer 1 failures (label mismatch) | Model got it wrong — highest learning value |
| 3 | Rare specialists | Rheumatologist, Nephrologist, Oncologist — undertested |
| 4 | Low-confidence auto matches | `subject_name` = "Medicine" (too broad, ambiguous) |
| 5 | Random sample | Coverage, prevent sampling bias |

---

## Annotation UI — What Interns See

Each annotation task shows:

```
CASE
────────────────────────────────────────────────
Patient:  35F, severity: high, duration: 3 days
Symptoms: chest pain, shortness of breath, sweating

RECOMMENDER OUTPUT
────────────────────────────────────────────────
Recommended Specialist : Cardiologist
Summary                : [2-3 sentence patient summary]
Symptom Explanation    : [why these symptoms point here]
Pathway                : Cardiologist → Pulmonologist → General Physician
Red Flags              : sudden severe chest pain, pain radiating to arm...
ICMR Citation          : STW Cardiology — Acute Coronary Syndrome [PDF link]

ANNOTATION FORM
────────────────────────────────────────────────
1. Specialist Correct?
   ○ Yes, clearly right
   ○ Yes, but another could also work
   ○ No, wrong specialist → [which specialist would you choose?]
   ○ Unsure — escalate

2. Red Flags Quality         [1  2  3  4  5]
   Are they specific to this case and clinically important?

3. Pathway Makes Sense?      [1  2  3  4  5]
   Are the 3 follow-up specialists reasonable and ordered correctly?

4. Summary Clarity           [1  2  3  4  5]
   Clear for a non-clinical patient? Appropriate tone? No jargon?

5. ICMR Citation Correct?
   ○ Right specialty, right condition
   ○ Right specialty, wrong condition
   ○ Wrong specialty
   ○ No STW exists for this case

6. Safety Pass?
   ○ Pass — no diagnosis made, no treatment advice given
   ○ Fail — explain: [free text]

7. If specialist is wrong — failure reason:
   ○ Wrong symptom interpretation
   ○ Missing red flag consideration
   ○ Wrong severity assessment
   ○ Multi-system case (ambiguous)
   ○ Other: [free text]

8. Notes (optional)
```

**Overall score** = mean of items 2, 3, 4 (numeric rubric items).
`Specialist Correct = Yes` + `Safety = Pass` are hard gates — fail either = discard.

---

## Comparative Annotation (DPO Training Data)

In addition to single-response scoring, interns also do pairwise comparison:

```
Same patient case, two different responses (e.g. gpt-4o vs mistral-7b)

Which response is better overall?
  ○ Response A
  ○ Response B
  ○ Roughly equal

Why is it better?
  ○ More appropriate specialist
  ○ Better red flags
  ○ Clearer summary
  ○ Better pathway order
  ○ Other: [free text]
```

These pairs become the DPO training dataset (`chosen` vs `rejected`).

---

## Inter-Rater Agreement

For hard / ambiguous cases (escalated or flagged), assign **two interns** independently:
- If they agree on specialist → high confidence, use as gold
- If they disagree → escalate to senior clinician
- Track agreement rate per intern over time (quality control)

---

## Feedback Loop Closure

Feedback must feed back into the system — not just sit in a database.

```
Annotations accumulate in MongoDB
         ↓
Weekly pattern analysis:
  "Model fails Orthopedics 40% of the time"
  "Red flags are generic for Neurology cases"
  "Duration parsing fails for chronic presentations"
         ↓
Route fix by failure type:
  Systematic routing failure → update system prompt in app/prompts.py
  Red flag quality failure   → update prompt instructions for red_flags field
  Citation failure           → update ICMR subject_name → STW mapping
  Knowledge gap              → add to fine-tuning batch
         ↓
A/B test: new prompt vs current on the same failed cases
         ↓
If improvement confirmed → deploy
```

---

## Rubric Score Interpretation

| Score | Meaning | Action |
|---|---|---|
| 4.5 – 5.0 | Excellent | Add to gold training set |
| 4.0 – 4.4 | Good | Add to silver training set |
| 3.0 – 3.9 | Acceptable | Review failure reason, fix and re-score |
| < 3.0 | Poor | Discard or use as rejected response in DPO pair |

---

## MongoDB Collections Used

- `runs` — stores each recommender output with auto-filter status
- `annotations` — stores intern scores, failure reasons, comparative results
- See [[MongoDB-Schema]] for full field definitions

---

*See also: [[Training-Data-Pipeline]] | [[MongoDB-Schema]] | [[Roadmap]]*
