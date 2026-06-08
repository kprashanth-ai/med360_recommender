# ICMR Citation Layer

*Design for linking recommender responses to ICMR Standard Treatment Workflow (STW) PDFs.*

---

## What This Is

Every recommender response gets **linked to one or more ICMR STW PDFs** as a citation. This is not RAG — we are not extracting content from the PDFs to generate responses. We are citing the relevant clinical guideline as supporting evidence for the recommendation.

---

## Why

- ICMR STWs are India's official clinical guidelines, published by the Indian Council of Medical Research
- Citing them makes each recommendation **traceable to authoritative Indian clinical guidance**
- Increases trust for clinicians reviewing the AI recommendation
- During human annotation, interns validate citation correctness → builds citation quality ground truth
- Long-term: parsed PDF content becomes training data and enables a proper RAG system

---

## Source: ICMR STW Website

- **URL:** https://www.icmr.gov.in/standard-treatment-workflows-stws
- **Structure:** 4 volumes → multiple specialties → individual condition PDFs
- **Total:** ~150+ individual PDFs
- **Sizes:** 26 KB to 68 MB (large files are combined/all-conditions PDFs)

---

## Phase 1 — Specialty-Level Linking (Build Now)

Simple lookup: `recommended_specialist` → list of relevant ICMR STW PDFs for that specialty.

Example:
```
recommended_specialist: "Cardiologist"
  → cite: ICMR STW Cardiology (Combined PDF) + most relevant condition PDF if symptoms match
```

Implementation: static `data/icmr_specialist_map.json` lookup table, hand-built once.

---

## Phase 2 — Condition-Level Linking (Future)

Match symptoms + specialist to the most specific condition PDF within the specialty.

```
symptoms: "chest pain, sweating, left arm numbness" + Cardiologist
  → cite: ICMR STW Cardiology — Acute Coronary Syndrome (specific PDF)
```

Requires either keyword matching or LLM-assisted condition identification.

---

## Phase 3 — PDF Content Parsing (Long-term)

Extract text from all 150+ PDFs:
- `pdfplumber` for text-selectable PDFs
- `pytesseract` (OCR) for scanned/image PDFs — many ICMR PDFs are scanned

Parsed content enables:
- Section-level citation (not just the whole PDF)
- RAG system on clinical guidelines
- Training data from structured clinical knowledge

---

## Specialty → ICMR STW Mapping

| Our Specialist | ICMR Volume | STW Subject |
|---|---|---|
| Cardiologist | I | Cardiology |
| ENT | I | ENT |
| Nephrologist | I | Nephrology |
| Neurologist | I | Neurology |
| Obstetrician & Gynaecologist | I | Obstetrics & Gynecology |
| Psychiatrist | I | Psychiatry |
| Pulmonologist | I | Pulmonology |
| Urologist | I | Urology |
| Dermatologist | III | Dermatology |
| Gastroenterologist | III | Gastroenterology |
| General Surgeon | III | General Surgery |
| Oncologist | III | Oncology |
| Ophthalmologist | III | Ophthalmology |
| Orthopedician | IV | Orthopaedics |
| Radiologist | IV | Interventional Radiology |
| Diabetologist | III | Endocrinology |
| Rheumatologist | — | Not covered in current STWs |
| General Physician | I | Multiple volumes |
| Dentist | — | Not in ICMR STW scope |

---

## Citation in API Response

The citation layer adds to each `run` in MongoDB:

```json
"citations": [
  {
    "stw_id": "ObjectId → icmr_stws",
    "specialty": "Cardiology",
    "condition": "Acute Coronary Syndrome",
    "url": "https://www.icmr.gov.in/...",
    "match_level": "condition"
  }
]
```

`match_level`: `"specialty"` (Phase 1) or `"condition"` (Phase 2)

---

## Intern Annotation for Citation Quality

During annotation, interns evaluate:

```
ICMR Citation Correct?
  ○ Right specialty, right condition  → high confidence citation
  ○ Right specialty, wrong condition  → partial credit
  ○ Wrong specialty                   → citation failure
  ○ No STW exists for this case       → gap in ICMR coverage
```

Over time, this builds a labeled dataset of correct citations per symptom cluster.

---

## ICMR Harvester Script (To Build)

```
scripts/harvest_icmr.py

Actions:
  1. Scrape https://www.icmr.gov.in/standard-treatment-workflows-stws
  2. Extract all PDF links, titles, specialty, volume
  3. Download PDFs to data/icmr_pdfs/[specialty]/[condition].pdf
  4. Write metadata to MongoDB icmr_stws collection
  5. Skip already-downloaded files (idempotent)
```

---

*See also: [[MongoDB-Schema]] | [[Training-Data-Pipeline]] | [[Feedback-System]]*
