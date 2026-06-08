# MongoDB Schema

*Central database design for the training data pipeline, ICMR citation layer, and human feedback system.*

---

## Overview

MongoDB replaces the current file-based `logs/usage.json`. All pipeline state — queries, model runs, annotations, ICMR PDFs, and training exports — lives here.

**5 collections:**

| Collection | Purpose |
|---|---|
| `icmr_stws` | ICMR Standard Treatment Workflow PDF metadata |
| `query_bank` | Patient input queries (from MedMCQA, MedQA, hand-crafted) |
| `runs` | Recommender responses + auto-filter results |
| `annotations` | Human intern evaluations and preference pairs |
| `training_exports` | Versioned training dataset export records |

---

## Collection: `icmr_stws`

Stores metadata for every ICMR Standard Treatment Workflow PDF.

```json
{
  "_id": "ObjectId",
  "volume": "I",
  "specialty": "Cardiology",
  "condition": "Acute Coronary Syndrome",
  "title": "STW for Acute Coronary Syndrome",
  "url": "https://www.icmr.gov.in/...",
  "local_path": "data/icmr_pdfs/cardiology/acs.pdf",
  "file_size_kb": 340,
  "is_combined": false,
  "parsed_text": null,
  "scraped_at": "2026-05-29T10:00:00Z"
}
```

| Field | Notes |
|---|---|
| `volume` | I, II, III, or IV |
| `specialty` | Matches our 19-specialist list |
| `condition` | Specific condition within specialty |
| `is_combined` | true = "All conditions" combined PDF for that specialty |
| `parsed_text` | null until Phase 3 PDF parsing is implemented |

---

## Collection: `query_bank`

Every patient input query used in the pipeline.

```json
{
  "_id": "ObjectId",
  "query_id": "q_medmcqa_001",
  "age": 40,
  "gender": "male",
  "severity": "high",
  "duration_days": 5,
  "symptoms": "productive cough and fever, difficulty breathing",
  "source": "medmcqa",
  "source_id": "4e1715fe-0bc3-494e-b6eb-2d4617245aef",
  "source_subject": "Medicine",
  "derived_specialist_label": "General Physician",
  "label_confidence": "low",
  "tags": ["respiratory", "infectious"],
  "created_at": "2026-05-29T10:00:00Z"
}
```

| Field | Notes |
|---|---|
| `source` | `medmcqa`, `medqa`, `mmlu`, `manual`, `production` |
| `source_id` | Original dataset question ID for traceability |
| `source_subject` | MedMCQA `subject_name` (if applicable) |
| `derived_specialist_label` | Inferred ground truth specialist |
| `label_confidence` | `high` (direct subject_name map) / `medium` (LLM-inferred) / `low` (broad subject) |

---

## Collection: `runs`

Every recommender API response, with auto-filter results attached.

```json
{
  "_id": "ObjectId",
  "run_id": "run_001",
  "query_id": "q_medmcqa_001",
  "input_snapshot": {
    "age": 40,
    "gender": "male",
    "severity": "high",
    "duration_days": 5,
    "symptoms": "productive cough and fever, difficulty breathing"
  },
  "response": {
    "recommended_specialist": "Pulmonologist",
    "primary_recommendation_summary": "...",
    "symptom_explanation": "...",
    "specialist_pathway": [
      {"specialist": "Pulmonologist", "reason": "..."},
      {"specialist": "General Physician", "reason": "..."},
      {"specialist": "Infectious Disease", "reason": "..."}
    ],
    "red_flags": ["..."],
    "disclaimer": "..."
  },
  "citations": [
    {
      "stw_id": "ObjectId",
      "specialty": "Pulmonology",
      "condition": "Community Acquired Pneumonia",
      "url": "https://www.icmr.gov.in/...",
      "match_level": "condition"
    }
  ],
  "model_used": "gpt-4o",
  "prompt_tokens": 481,
  "completion_tokens": 308,
  "total_tokens": 789,
  "cost_usd": 0.00428,
  "auto_filter": {
    "format_valid": true,
    "specialist_valid": true,
    "label_match": false,
    "llm_judge_score": 4.2,
    "status": "pending_review"
  },
  "status": "pending_review",
  "created_at": "2026-05-29T10:00:00Z"
}
```

| `auto_filter.status` | Meaning |
|---|---|
| `auto_pass` | All auto checks passed, score ≥ 4 |
| `auto_fail` | Failed format/specialist/safety check |
| `pending_review` | Passed format but needs human review |
| `annotated` | Human annotation complete |

---

## Collection: `annotations`

Intern evaluation for each run, plus comparative preference pairs.

```json
{
  "_id": "ObjectId",
  "run_id": "ObjectId → runs",
  "annotator_id": "intern_priya",
  "annotation_type": "single",
  "rubric": {
    "specialist_correct": "yes_clearly",
    "specialist_override": null,
    "red_flag_quality": 4,
    "pathway_quality": 5,
    "summary_clarity": 4,
    "citation_correct": "right_specialty_right_condition",
    "safety_pass": true,
    "failure_reason": null
  },
  "overall_score": 4.33,
  "notes": "Pathway order is good. Red flags could be more specific.",
  "annotated_at": "2026-05-29T11:00:00Z"
}
```

For comparative (DPO) annotation:

```json
{
  "_id": "ObjectId",
  "run_id_a": "ObjectId → runs",
  "run_id_b": "ObjectId → runs",
  "annotator_id": "intern_priya",
  "annotation_type": "comparative",
  "preferred": "a",
  "reason": "better_red_flags",
  "notes": "Response A had more case-specific red flags",
  "annotated_at": "2026-05-29T11:00:00Z"
}
```

| `rubric.specialist_correct` values |
|---|
| `yes_clearly` |
| `yes_acceptable` |
| `no_wrong` |
| `unsure_escalate` |

| `rubric.citation_correct` values |
|---|
| `right_specialty_right_condition` |
| `right_specialty_wrong_condition` |
| `wrong_specialty` |
| `no_stw_exists` |

---

## Collection: `training_exports`

Versioned snapshots of exported training datasets.

```json
{
  "_id": "ObjectId",
  "version": "v1.0",
  "export_type": "sft",
  "min_score_threshold": 4.0,
  "total_samples": 3124,
  "gold_samples": 2800,
  "silver_samples": 324,
  "format": "instruction_tuning_jsonl",
  "export_path": "data/exports/sft_v1.0.jsonl",
  "base_model_target": "meta-llama/Llama-3.1-8B",
  "created_at": "2026-05-29T12:00:00Z"
}
```

---

## Indexes to Create

```javascript
// Query fast lookups
db.query_bank.createIndex({ source: 1, derived_specialist_label: 1 })
db.runs.createIndex({ status: 1, created_at: -1 })
db.runs.createIndex({ query_id: 1 })
db.annotations.createIndex({ run_id: 1, annotator_id: 1 })
db.icmr_stws.createIndex({ specialty: 1, is_combined: 1 })
```

---

*See also: [[Training-Data-Pipeline]] | [[Feedback-System]] | [[Architecture]]*
