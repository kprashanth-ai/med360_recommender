# Decision Record 001

## Decision: Training Pipeline Architecture — ICMR Knowledge Extraction + RAG + Attribution-Based Training Data

| Field | Value |
|---|---|
| **Date** | 2026-06-01 |
| **Time** | 07:13 IST |
| **Status** | `accepted` |
| **Supersedes** | None — first major architecture decision |
| **Participants** | Prashanth (Med360) |

---

## Context

The Med360 Specialist Recommender currently calls the OpenAI API (gpt-4o) for every triage request. The long-term goal is to replace this with a self-hosted, fine-tuned model that is:

1. **Indian-grounded** — trained on ICMR clinical guidelines, not Western medical datasets
2. **Citation-backed** — every recommendation traceable to an authoritative ICMR source
3. **Cost-free at inference** — no per-call API cost after training
4. **Medically defensible** — outputs that can be validated against official Indian clinical standards

The hardware available for training is an HP OMEN with an RTX 5050 (8 GB VRAM). Training large models (70B) is not feasible locally; 7B models with QLoRA are feasible.

The planning session explored three progressively better approaches before arriving at this architecture.

---

## Options Considered

### Option A — Direct Fine-Tuning on MedMCQA + gpt-4o Responses
Use MedMCQA (194k Indian questions) as query bank, run through gpt-4o to generate responses, fine-tune BioMistral 7B.

**Pros:** Simple pipeline, well-understood approach, fast to start.

**Cons:**
- gpt-4o generates from memory — no ICMR grounding
- Citations are hallucinated or absent
- Training data quality depends entirely on gpt-4o's medical knowledge, which may not reflect Indian clinical practice
- No way to validate correctness against authoritative sources

---

### Option B — RAG-Based Training Data Generation
Convert ICMR STWs to Markdown, build a RAG system, use retrieved ICMR context + gpt-4o to generate Q&A pairs with real citations, fine-tune on those pairs.

**Pros:** Responses grounded in actual ICMR documents. Citations are real.

**Cons:**
- Retrieval can silently fail — wrong ICMR chunks retrieved → wrong citations in training data
- Training data quality depends on retrieval accuracy
- No systematic way to validate coverage or correctness
- Bad training data corrupts the model quietly

---

### Option C — Structured Knowledge Extraction + RAG + Per-Field Attribution (Selected)
Extract structured clinical facts from ICMR STWs first (via gpt-4o) to build a verified knowledge base. Use RAG for serving. Generate training data with per-field source attribution (icmr_rag vs model_knowledge). Cross-reference MedMCQA scenarios with the knowledge base for scale.

**Pros:**
- Training data is grounded in structured facts — no retrieval failures
- Per-field attribution shows exactly what came from ICMR vs model memory
- ICMR knowledge base enables systematic output validation
- Scale: 194k MedMCQA scenarios × ICMR conditions
- Two products from one effort: RAG system (usable immediately) + training dataset
- Medically defensible: every output is either ICMR-aligned or explicitly flagged

**Cons:**
- More upfront work (knowledge extraction before RAG)
- Knowledge base becomes stale when ICMR updates STWs (requires re-extraction)
- Structured extraction quality depends on LLM accuracy

---

## Decision

**Adopt Option C.**

Build the training pipeline in the following sequence:

### The 14-Step Plan

```
DATA FOUNDATION
1.  ICMR PDFs → Section-aware Markdown
    (pymupdf4llm for text PDFs, docling for complex layouts, pytesseract OCR for scanned)
    Preserve: section hierarchy, tables, metadata frontmatter per document

2.  ICMR Markdown → Structured Knowledge Base (JSON per condition)
    gpt-4o reads full STW sections and extracts:
    { condition, specialist, presenting_symptoms, diagnostic_criteria,
      red_flags, referral_urgency, severity_typical, icmr_citation }

3.  MedMCQA / MedQA → Extract PatientInput fields
    Parse: age, gender, symptoms from question text
    Infer: severity (rule-based + gpt-4o fallback)
    Map:   subject_name → specialist (weak ground truth label)
    Add:   clinical context summary (natural language, for RAG query)

QUERY GENERATION + RAG
4.  Build RAG system on ICMR Markdown
    Embedding: NeuML/pubmedbert-base-embeddings (medical-specific)
    Chunking:  Section-aware (not fixed token)
    Vector DB: ChromaDB (local dev), Pinecone (production)

5.  PatientInput queries → RAG retrieves relevant ICMR sections
    → gpt-4o generates response with per-field source attribution:
      source: "icmr_rag"       (came from retrieved ICMR document)
      source: "model_knowledge" (came from model training memory)
      source: "both"           (corroborated by both)
    Each claim includes exact ICMR citation: title, section, excerpt, url

6.  Save query + full attributed response to MongoDB (runs collection)

HUMAN VALIDATION
7.  Active sampling → intern rubric evaluation
    Priority order: high severity → label mismatch → rare specialists → random
    Rubric includes: specialist correct, red flag quality, pathway quality,
    summary clarity, citation relevance, attribution correct, safety pass

8.  Responses with overall rubric score ≥ 4.0 AND safety pass = true
    → promoted to training corpus

MODEL TRAINING
9.  DAPT (Domain Adaptive Pre-Training) on BioMistral 7B:
    Raw ICMR Markdown + MedMCQA text + MedQA Step2&3 + IJMR papers
    Model reads the "textbook" before task training
    Runs on cloud A100 (~$25 one-time cost)

10. SFT (Supervised Fine-Tuning):
    Instruction fine-tune on validated Q&A pairs with embedded citations
    Format: { instruction, input: PatientInput, output: attributed response JSON }
    Target: ~3,000 gold + ~20,000 silver examples

11. DPO (Direct Preference Optimization):
    Alignment pass using preference pairs from comparative intern annotation
    (intern chose Response A over Response B — becomes chosen/rejected pair)
    Target: 500–1,000 preference pairs

VALIDATION + DEPLOYMENT
12. 6-Test Confidence Evaluation before replacing OpenAI:
    a. MedMCQA test set (6,150 Q) — routing accuracy vs gpt-4o baseline
    b. Custom triage eval (200 hand-crafted cases) — specialist accuracy ≥ 90%
    c. Human rubric (100 cases) — expert score ≥ 4.0/5.0 average
    d. ICMR alignment — output vs knowledge base match rate ≥ 80%
    e. Consistency (50 Q × 5 runs) — same answer ≥ 90% of runs
    f. Safety (adversarial inputs) — never diagnoses, 100% pass rate

13. Validation Layer in production:
    Every model output checked against ICMR Knowledge Base
    Aligned → serve with high confidence
    Deviated → flag response, log for review

14. Improvement Flywheel:
    Deploy → collect real production queries → run through same pipeline
    → annotate → above threshold → add to training set
    → retrain when sufficient new data accumulates (monthly or per ICMR update)
```

---

## Rationale

**Why structured extraction before RAG:**
Retrieval can silently fail. A wrong chunk retrieved means a wrong citation in training data. The model learns from that mistake. Structured extraction is deterministic — the knowledge base is always correct, and training data quality does not depend on retrieval accuracy.

**Why per-field attribution:**
Knowing which parts of a response came from ICMR vs model memory is valuable at three points:
1. Training data quality — only ICMR-attributed claims become training targets
2. Trust for clinical users — they can see what is guideline-backed vs model opinion
3. Annotation efficiency — interns specifically validate citation attribution

**Why BioMistral 7B as target model:**
- Already pre-trained on PubMed (biomedical foundation)
- 7B is the minimum size for reliable clinical reasoning (below 7B, complex multi-symptom cases fail)
- 4-bit quantized inference fits in 8 GB VRAM (RTX 5050)
- DAPT on ICMR corpus adds Indian clinical grounding on top of biomedical foundation

**Why MedMCQA as primary query source:**
- 194k questions from AIIMS/NEET — Indian medical exams
- subject_name field provides weak specialist ground truth for ~45% of questions
- Directly aligned with Med360's Indian patient base
- Apache 2.0 license — usable for commercial training

**Why the validation layer matters:**
A medical product without systematic output validation is not defensible. The ICMR Knowledge Base as a ground truth checker means every response is either ICMR-aligned (serve with confidence) or flagged (review before serving). This is the difference between a useful tool and a trustworthy medical product.

---

## Consequences

### Positive
- Training data is the highest quality achievable with this approach
- Citations are real, verifiable, and traceable to specific ICMR sections
- The model will have Indian clinical grounding baked into its weights
- The RAG system is immediately deployable before training completes
- Systematic coverage gaps are visible (which specialists have no ICMR STW)
- Outputs are auditable against official Indian clinical standards

### Negative / Trade-offs
- More upfront engineering work than a simple fine-tuning pipeline
- ICMR Knowledge Base maintenance required when ICMR updates STWs
- DAPT requires cloud compute (one-time ~$25–40 cost)
- PDF extraction quality varies — scanned PDFs need OCR and manual review
- Some specialists have minimal ICMR STW coverage (Rheumatologist, Dentist) — gaps in training data

### Open Questions
- How to handle ICMR STW updates — version the knowledge base or rebuild?
- What to do for specialists with no ICMR STW coverage — use NMC/MCI guidelines as supplement?
- Should the attribution field be surfaced to end users in the API response, or kept internal?
- Threshold for DAPT corpus size — how many tokens are enough before task fine-tuning?

---

## Next Steps

- [ ] Build PDF → Markdown extraction pipeline (Step 1)
- [ ] Design and test structured knowledge extraction prompts (Step 2)
- [ ] Set up MongoDB collections (schema already in docs/MongoDB-Schema.md)
- [ ] Evaluate PDF quality across ICMR STW volumes to estimate OCR scope

---

*See also: [[Training-Data-Pipeline]] | [[Feedback-System]] | [[MongoDB-Schema]] | [[ICMR-Citation-Layer]] | [[benchmark-evidence]]*
