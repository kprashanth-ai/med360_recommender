# Training Data Pipeline

*Planned system for building a labeled dataset to fine-tune a specialist triage model that replaces the OpenAI dependency.*

---

## Goal

Use existing public medical datasets (MedQA, MedMCQA) as a free query bank, run them through gpt-4o to generate responses (knowledge distillation), validate with human annotators, and fine-tune an open-source model (Llama 3.1 8B or Mistral 7B) to replicate gpt-4o quality on the triage task.

**End state:** Self-hosted triage model that replaces the OpenAI API call in `app/services/llm.py`.

---

## Source Datasets

### MedQA (USMLE)
- **Paper:** Jin et al., 2020. arXiv:2009.13081
- **HuggingFace:** `GBaker/MedQA-USMLE-4-options`
- **Total:** 12,723 questions (10,247 train / 1,268 test)
- **Fields:** `question`, `options {A,B,C,D}`, `answer`, `answer_idx`, `meta_info` (step1 / step2&3), `metamap_phrases`
- **Nature:** USMLE clinical vignettes. Step 2&3 = clinical patient scenarios. Step 1 = basic science (no patient).
- **Usable for triage:** ~7,000 (~55%) — Step 2&3 questions with clear patient presentations
- **Limitation:** Answer is a drug or diagnosis, NOT a specialist. Specialist label needs LLM inference.

### MedMCQA (AIIMS / NEET PG)
- **Paper:** Pal et al., 2022. arXiv:2203.14371. CHIL 2022.
- **HuggingFace:** `openlifescienceai/medmcqa`
- **Total:** 193,155 questions (182,822 train / 4,183 val / 6,150 test)
- **Fields:** `question`, `opa/opb/opc/opd`, `cop`, `choice_type`, `exp`, `subject_name` (21 categories), `topic_name`
- **Nature:** AIIMS/NEET PG exam questions. Mix of patient scenarios and pure knowledge questions.
- **Usable for triage:** ~55,000 (~28%) — patient scenario questions from clinical subjects
- **Key advantage:** `subject_name` gives weak ground truth specialist label for ~45% of usable questions.
- **Indian context:** Primary dataset — directly aligned with Med360's patient base.

### PubMedQA
- **Paper:** Jin et al., 2019. arXiv:1909.06146. EMNLP 2019.
- **Total:** 1,000 expert-labeled
- **Nature:** Biomedical RESEARCH questions. "Does X reduce Y?" format. Not clinical triage scenarios.
- **Verdict:** Not useful as query bank. Less than 5% extractable. Skip.

### MMLU Medical Subsets
- **Paper:** Hendrycks et al., 2020. arXiv:2009.03300. ICLR 2021.
- **Total:** 1,089 questions across 6 medical subsets
- **Usable for triage:** ~360 (~33%) — Professional Medicine + Clinical Knowledge subsets
- **Verdict:** Supplementary only. Useful as an additional test set, not primary training source.

---

## PatientInput Field Coverage (Gap Analysis)

Your `PatientInput` requires: `age`, `gender`, `severity`, `duration_days`, `symptoms`

| Field | MedQA | MedMCQA | Gap / Notes |
|---|---|---|---|
| `age` | ~85% | ~75% | Explicit "A 45-year-old man..." |
| `gender` | ~85% | ~80% | Explicit "woman/man/boy/girl" |
| `symptoms` | ~90% | ~90% | Main body of question |
| `duration_days` | ~60% | ~50% | 40–50% vague ("for years", "chronic") |
| `severity` | **0%** | **0%** | Never explicit in either dataset |
| `specialist_label` | **0%** | **45%** | MedMCQA: subject_name; MedQA: needs LLM |

### Filling the Gaps

**Severity (0% everywhere — biggest gap)**
```
Rule-based first:
  HIGH   → "sudden", "acute", "severe", "crushing", "radiating to arm",
            "cannot breathe", "seizure", "unconscious", "emergency"
  MEDIUM → "worsening", "progressive", "persistent", "recurring",
            "moderate", "spreading", "affecting daily life"
  LOW    → "mild", "occasional", "intermittent", "chronic",
            "for years", "slight", "minor", "comes and goes"
  DEFAULT → "medium" if no keyword matches

LLM fallback for edge cases:
  Ask gpt-4o: "Classify severity as low/medium/high for: [scenario]"
  Use only when rule-based returns no match.
```

**Duration (40–50% missing)**
```
Explicit patterns:
  "for X days"   → X
  "for X weeks"  → X × 7
  "for X months" → X × 30

Vague patterns:
  "for years" / "chronic"        → 365
  "for months"                   → 90
  "for weeks"                    → 21
  "recent" / "sudden" / "acute"  → 1

Default if nothing found → 7
```

**Specialist label**
```
MedMCQA (45% via subject_name):
  ENT                    → ENT
  Ophthalmology          → Ophthalmologist
  Psychiatry             → Psychiatrist
  Surgery                → General Surgeon
  Gynecology & Obstetrics → Obstetrician & Gynaecologist
  Orthopedics            → Orthopedician
  Skin                   → Dermatologist
  Radiology              → Radiologist
  Dental                 → Dentist
  Pediatrics             → General Physician
  Medicine               → General Physician (broad — flag for LLM inference)

MedQA / MMLU / remaining MedMCQA (LLM inference):
  Prompt: "Given this clinical scenario and correct answer,
           which specialist from [list] should this patient see?"
  → gpt-4o returns specialist label
  → Sample validated by human interns
```

---

## Full 8-Step Pipeline

```
STEP 1 — FILTER
  Input:  207,967 raw questions
  Action: Remove Step 1 (basic science), PubMedQA, non-patient scenario questions
  Output: ~62,000 usable clinical patient scenarios

STEP 2 — EXTRACT PatientInput
  Input:  62,000 filtered questions
  Action: NLP parsing for age/gender/symptoms
          Rule-based extraction for duration
          Rule-based + LLM inference for severity
          subject_name map + LLM inference for specialist_label
  Output: 62,000 structured PatientInput records

STEP 3 — GENERATE RESPONSES (gpt-4o as teacher)
  Input:  62,000 PatientInput records
  Action: Feed each through POST /recommend (gpt-4o)
          Store full response: specialist, summary, pathway, red_flags, disclaimer
  Cost:   ~$0.004 × 62,000 = ~$248 total
  Output: 62,000 (input → gpt-4o response) pairs — Silver dataset

STEP 4 — AUTO-FILTER
  Input:  62,000 silver pairs
  Action: Layer A: Format check — valid JSON? All fields present?
          Layer B: Specialist check — is it in the 19-specialist list?
          Layer C: Label match — does it match derived specialist_label?
          Layer D: LLM-as-judge — panel of 3 smaller models score 1–5, keep ≥ 4
  Output: ~20,000–25,000 high-confidence silver pairs

STEP 5 — HUMAN ANNOTATION (medical/pharma interns)
  Input:  ~25,000 filtered silver pairs
  Action: Active sampling — prioritize by:
            1. High severity cases (patient safety)
            2. Label mismatch (auto-filter failed)
            3. Rare specialists (Rheumatologist, Nephrologist, Oncologist)
            4. Random sample for coverage
          Interns score on rubric (see Feedback-System.md)
          Two interns per hard/ambiguous case
  Target: 3,000 gold-standard validated pairs
          500–1,000 preference pairs (comparative annotation)

STEP 6 — ICMR CITATION LAYER
  Input:  Validated responses
  Action: Attach ICMR STW citations (see ICMR-Citation-Layer.md)
          Interns validate citation correctness during Step 5
  Output: Responses with verified ICMR STW links

STEP 7 — BUILD TRAINING DATASETS
  Dataset A — SFT (Supervised Fine-Tuning):
    Format: { "instruction": "[system prompt]", "input": "[patient info]", "output": "[JSON response]" }
    Size:   3,000 gold + 20,000 silver = ~23,000 examples
    Use:    Teach base model the triage task

  Dataset B — DPO (Preference Pairs):
    Format: { "input": "[patient info]", "chosen": "[good response]", "rejected": "[bad response]" }
    Size:   500–1,000 pairs from comparative annotation
    Use:    Improve quality and alignment beyond SFT

STEP 8 — FINE-TUNE + EVALUATE
  Base model:  Llama 3.1 8B  OR  Mistral 7B
  Phase 1:     SFT on Dataset A (~6–8 hours on 1× A100 80GB)
  Phase 2:     DPO on Dataset B (~2–3 hours)
  Evaluation:  See confidence scoring below
```

---

## Model Confidence Scoring (6 Tests)

| Test | What it measures | Pass threshold |
|---|---|---|
| MedMCQA test set (6,150 Q) | Routing accuracy vs gpt-4o | ≥ 85% of gpt-4o score |
| Custom triage eval (200 Q) | Specialist accuracy on hand-crafted cases | ≥ 90% |
| Human rubric (100 cases) | Expert quality score | ≥ 4.0 / 5.0 average |
| ICMR citation alignment | Does recommendation match ICMR STW? | ≥ 80% match |
| Consistency (50 Q × 5 runs) | Same answer across runs | ≥ 90% agreement |
| Safety test (adversarial) | Never diagnoses or gives treatment | 100% pass |

All 6 must pass before replacing the OpenAI API call.

---

## Dataset Size Summary

| Stage | Size |
|---|---|
| Raw datasets | 207,967 |
| After filter | ~62,000 |
| After gpt-4o generation (silver) | ~62,000 |
| After auto-filter | ~20,000–25,000 |
| Gold (human validated) | ~3,000 |
| DPO preference pairs | ~500–1,000 |
| **Final training set (SFT + DPO)** | **~23,000** |

---

## Key Research Backing

- **LIMA (Zhou et al., 2023):** 1,000 carefully curated examples outperform large noisy datasets. Quality > quantity. arXiv:2305.11206
- **DPO (Rafailov et al., 2023):** Direct Preference Optimization is simpler than RLHF and effective for alignment on preference pairs.
- **Panel of LLM judges (Verga et al., 2024):** Multiple smaller LLM evaluators outperform a single GPT-4 judge at 7× lower cost. arXiv:2404.18796

---

*See also: [[Feedback-System]] | [[MongoDB-Schema]] | [[Roadmap]] | [[benchmark-evidence]]*
