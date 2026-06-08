# Medical LLM Benchmark Evidence
*For Med360 Recommender — model selection rationale*

---

## 1. Benchmark Datasets — Primary Citations

### MedQA (USMLE)
> **What it is:** Multiple-choice questions from the US Medical Licensing Examination (USMLE).
> Covers Step 1 (basic science), Step 2 & 3 (clinical application). 4-option format.

- **Paper:** Jin, D., Pan, E., Oufattole, N., Weng, W-H., Fang, H., & Szolovits, P. (2020).
  *What Disease does this Patient Have? A Large-scale Open Domain Question Answering Dataset from Medical Exams.*
  arXiv:2009.13081
- **Dataset:** 12,723 English questions (10,178 train / 1,273 test)
- **HuggingFace:** `GBaker/MedQA-USMLE-4-options`
- **License:** MIT

---

### MedMCQA (AIIMS / NEET PG)
> **What it is:** Large-scale multiple-choice QA from Indian medical entrance exams
> (AIIMS PG and NEET PG). Covers 2,400+ healthcare topics across 21 medical subjects.
> **Most relevant for Med360** — Indian medical context.

- **Paper:** Pal, A., Umapathi, L. K., & Sankarasubbu, M. (2022).
  *MedMCQA: A Large-scale Multi-Subject Multi-Choice Dataset for Medical domain Question Answering.*
  Proceedings of the Conference on Health, Inference, and Learning (CHIL), 2022.
  arXiv:2203.14371
- **Dataset:** 194,000+ questions (182,822 train / 4,183 validation / 6,150 test)
- **HuggingFace:** `medmcqa`
- **License:** MIT

---

### PubMedQA
> **What it is:** Biomedical research question answering based on PubMed abstracts.
> Format: Yes / No / Maybe given an abstract as context.

- **Paper:** Jin, Q., Dhingra, B., Liu, Z., Cohen, W. W., & Lu, X. (2019).
  *PubMedQA: A Dataset for Biomedical Research Question Answering.*
  Proceedings of EMNLP-IJCNLP 2019.
  arXiv:1909.06146
- **Dataset:** 1,000 expert-labeled QA pairs (500 dev / 500 test) + 211,300 artificially generated
- **HuggingFace:** `pubmed_qa`

---

### MMLU — Medical Subsets
> **What it is:** Massive Multitask Language Understanding benchmark.
> 6 medical/biology subsets used for evaluating LLMs on clinical knowledge.

- **Paper:** Hendrycks, D., Burns, C., Basart, S., Zou, A., Mazeika, M., Song, D., & Steinhardt, J. (2020).
  *Measuring Massive Multitask Language Understanding.*
  International Conference on Learning Representations (ICLR) 2021.
  arXiv:2009.03300
- **Medical subsets used:**

| Subset | Questions |
|---|---|
| Clinical Knowledge | 265 |
| Medical Genetics | 100 |
| Anatomy | 135 |
| Professional Medicine | 272 |
| College Biology | 144 |
| College Medicine | 173 |
| **Total** | **1,089** |

---

## 2. Model Performance — Published Scores

### Source: Nori et al., 2023 — GPT-4 on Medical Challenges
> **Paper:** Nori, H., King, N., McKinney, S. M., Carignan, D., & Horvitz, E. (2023).
> *Capabilities of GPT-4 on Medical Challenge Problems.*
> arXiv:2303.13375

| Benchmark | GPT-3.5 | GPT-4 |
|---|---|---|
| USMLE Step 1 (MedQA-style) | ~53% | ~86% |
| USMLE Step 2 & 3 | ~59% | ~87% |
| MMLU Clinical Knowledge | 69.8% | 86.0% |
| MMLU Medical Genetics | 70.0% | 91.0% |
| MMLU Anatomy | 56.3% | 80.0% |
| MMLU Professional Medicine | 70.2% | 93.0% |
| MMLU College Biology | 72.9% | 95.8% |
| MMLU College Medicine | 61.3% | 76.9% |

> GPT-4 "exceeds the passing score on USMLE by over 20 points and outperforms models specifically fine-tuned on medical knowledge." — Nori et al., 2023

---

### Source: Singhal et al., 2023 — Med-PaLM 2
> **Paper:** Singhal, K., Tu, T., Gottweis, J., et al. (2023).
> *Towards Expert-Level Medical Question Answering with Large Language Models.*
> arXiv:2305.09617

| Benchmark | Med-PaLM (v1) | Med-PaLM 2 |
|---|---|---|
| MedQA (USMLE 4-option) | 67.2% | 86.5% |

---

### GPT-4o, o1 — From Open Medical LLM Leaderboard
> **Leaderboard:** Open Medical LLM Leaderboard by openlifescienceai
> HuggingFace Space: `openlifescienceai/open_medical_llm_leaderboard`
> **Leaderboard paper:** Pal, A. & Sankarasubbu, M. (2024).
> *Gemini Goes to Med School: Exploring the Capabilities of Multimodal Large Language Models on Medical Challenge Problems & Hallucinations.*
> arXiv:2402.07023

| Benchmark | GPT-4o-mini | GPT-4o | o1 / o3 |
|---|---|---|---|
| MedQA (USMLE 4-opt) | ~72% | ~90% | ~96%+ |
| MedMCQA | ~55% | ~70% | ~75%+ |
| PubMedQA | ~72% | ~79% | ~82%+ |
| MMLU Medical avg | ~76% | ~91% | ~95%+ |

> ⚠️ **Note on GPT-4o / o1 scores:** The HuggingFace leaderboard space was unavailable at time of writing (runtime error). Scores above are sourced from the training corpus and community-reported evaluations. Verify at the leaderboard when it recovers, or from OpenAI's model cards.

---

### GPT-5 — No Published Medical Benchmark Data
> As of May 2026, OpenAI has not released formal medical benchmark numbers for GPT-5.
> The leaderboard does not yet include GPT-5.
> **Recommendation:** Run our own evaluation once GPT-5 API access is available (see Section 3).

---

## 3. What These Benchmarks Do and Do Not Tell Us for Med360

| What we need | Benchmark signal | Gap |
|---|---|---|
| Routing to correct specialist | MedMCQA — Indian clinical context, tests symptom-specialty association | Tests diagnosis, not routing |
| Red flag identification | MMLU Clinical Knowledge — urgency and danger recognition | Doesn't test case-specificity |
| Response safety (no diagnosis) | MedQA — USMLE clinical reasoning boundaries | No JSON or 19-specialist constraint |
| Pathway quality | None directly | Not tested in any public benchmark |
| JSON format compliance | None | All benchmarks are multiple choice |
| Consistency across runs | None | Not tested anywhere |
| Indian patient context | **MedMCQA only** | Only benchmark with AIIMS/NEET origin |

**Conclusion:** Public benchmarks serve as a *model floor check* — they eliminate clearly weak models. They do not measure triage routing quality directly. A custom evaluation set and human annotation pipeline are required for that.

---

## 4. References (BibTeX)

```bibtex
@article{jin2020medqa,
  title={What Disease does this Patient Have? A Large-scale Open Domain Question Answering Dataset from Medical Exams},
  author={Jin, Di and Pan, Eileen and Oufattole, Nassim and Weng, Wei-Hung and Fang, Hanyi and Szolovits, Peter},
  journal={arXiv preprint arXiv:2009.13081},
  year={2020}
}

@inproceedings{pal2022medmcqa,
  title={MedMCQA: A Large-scale Multi-Subject Multi-Choice Dataset for Medical domain Question Answering},
  author={Pal, Ankit and Umapathi, Logesh Kumar and Sankarasubbu, Malaikannan},
  booktitle={Proceedings of the Conference on Health, Inference, and Learning (CHIL)},
  year={2022}
}

@inproceedings{jin2019pubmedqa,
  title={PubMedQA: A Dataset for Biomedical Research Question Answering},
  author={Jin, Qiao and Dhingra, Bhuwan and Liu, Zhengping and Cohen, William W and Lu, Xinghua},
  booktitle={Proceedings of EMNLP-IJCNLP 2019},
  year={2019}
}

@inproceedings{hendrycks2021mmlu,
  title={Measuring Massive Multitask Language Understanding},
  author={Hendrycks, Dan and Burns, Collin and Basart, Steven and Zou, Andy and Mazeika, Mantas and Song, Dawn and Steinhardt, Jacob},
  booktitle={International Conference on Learning Representations (ICLR)},
  year={2021}
}

@article{nori2023gpt4medical,
  title={Capabilities of GPT-4 on Medical Challenge Problems},
  author={Nori, Harsha and King, Nicholas and McKinney, Scott Mayer and Carignan, Dean and Horvitz, Eric},
  journal={arXiv preprint arXiv:2303.13375},
  year={2023}
}

@article{singhal2023medpalm2,
  title={Towards Expert-Level Medical Question Answering with Large Language Models},
  author={Singhal, Karan and Tu, Tao and Gottweis, Juraj and others},
  journal={arXiv preprint arXiv:2305.09617},
  year={2023}
}

@article{pal2024geminimedschool,
  title={Gemini Goes to Med School: Exploring the Capabilities of Multimodal Large Language Models on Medical Challenge Problems \& Hallucinations},
  author={Pal, Ankit and Sankarasubbu, Malaikannan},
  journal={arXiv preprint arXiv:2402.07023},
  year={2024}
}
```

---

*Document prepared: May 2026 | Med360 Recommender project*
