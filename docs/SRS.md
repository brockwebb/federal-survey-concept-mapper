# Software Requirements Specification (SRS)
## Federal Survey Concept Mapper

*Version 1.0 — March 2026*

---

## 1. Introduction

### 1.1 Purpose
This document specifies the functional, data, structural, and validation requirements for the Federal Survey Concept Mapper research pipeline. It governs what gets built, where it goes, what constraints apply, and critically, what validation scripts certify every number before it appears in any deliverable.

### 1.2 Scope
AI-assisted survey harmonization analysis across 47 Census Bureau demographic survey instruments (~7,000 questions). NOT cross-agency. NOT all federal surveys. Census Bureau only. ACS is the anchor survey; CPS and FoodAPS are the two source surveys evaluated so far.

### 1.3 Definitions

| Term | Definition |
|------|-----------|
| Instrument | A single survey questionnaire form. Some survey programs have multiple instruments (e.g., NTPS × 6, FoodAPS × 4) |
| Deduplication | Removing exact-duplicate question text rows from the raw dataset |
| Consensus path | Questions where both classifiers agree at the subtopic level — no arbitration needed |
| Auto dual-modal | Questions where both classifiers are highly confident but assign different categories — both are accepted as valid |
| Arbitration | A third model reviews disagreements and selects or synthesizes a resolution |
| Pair | A (source_question, ACS_question) tuple sharing a subtopic classification, evaluated for harmonization feasibility |
| Feasibility | F1 (direct recode), F2 (statistical adjustment needed), F3 (not feasible) |
| Barrier code | Why a pair is not feasible: CC (Construct), TC (Temporal), RS (Response Scale), PC (Population), MC (Mode), PM (Precision) |
| Consolidable | A source question with at least one F1 or F2 pair — it has a harmonization path to ACS |
| Bridge variable | An ACS question that serves as an F1/F2 target for at least one source survey question |
| Fan-in | Average number of source questions per ACS bridge target |

---

## 2. Repository Structure

This section is law. Code and content go where specified. See CLAUDE.md for the full layout. Key locations for this SRS:

```
├── report/                     # Master report (Quarto book) — only build target
├── fact_sheet/                 # Executive one-page fact sheet
├── docs/
│   ├── SRS.md                  # THIS FILE
│   ├── NUMBERS_MAP.md          # Generated reference — validated by V&V scripts
│   ├── SCRIPT_ARTIFACT_MAP.md  # Script → artifact traceability
│   ├── FIGURE_MAP.md           # Figure provenance
│   ├── validation/             # V&V outputs (JSON, logs)
│   └── stages/                 # Pipeline working materials by stage
├── data/
│   ├── raw/                    # Input data (untouched)
│   └── processed/              # Pipeline outputs
├── src/
│   ├── validation/             # V&V scripts (THE authority for all numbers)
│   ├── pipelines/              # Pipeline stages (01-05)
│   ├── figures/                # Figure generation scripts
│   └── lib/                    # Shared utilities
├── config/                     # Configuration files
└── assets/diagrams/            # Diagram sources and outputs
```

### 2.1 Placement Rules

| Content Type | Location |
|-------------|----------|
| V&V scripts | `src/validation/` |
| V&V outputs (JSON, logs) | `docs/validation/` |
| Pipeline stage code | `src/pipelines/` |
| Pipeline stage data | `docs/stages/0X_*/data/` |
| Configuration | `config/` |
| Report chapters | `report/chapters/` |
| Diagram source specs | `assets/diagrams/paperbanana/` |
| Diagram outputs | `assets/diagrams/` |

---

## 3. Pipeline Stages

### 3.1 Stage 1: Topic and Subtopic Classification

| ID | Requirement | Priority |
|----|------------|----------|
| PS-1-001 | Pipeline SHALL classify all deduplicated questions (6,987) by Census topic and subtopic using two independent LLM classifiers | Must |
| PS-1-002 | Classifiers SHALL be from different vendors (currently OpenAI gpt-5-mini, Anthropic claude-haiku-4-5) for vendor independence | Must |
| PS-1-003 | Agreement SHALL be evaluated at both topic and subtopic level. Routing to resolution SHALL use the stricter subtopic criterion | Must |
| PS-1-004 | Questions with subtopic agreement SHALL proceed directly to the final dataset (consensus path) | Must |
| PS-1-005 | Questions where both models are highly confident but disagree SHALL be flagged as dual-modal (auto dual-modal path) | Must |
| PS-1-006 | Remaining disagreements SHALL be resolved by a single arbitrator model (currently claude-sonnet-4-5) | Must |
| PS-1-007 | The arbitrator SHALL review both classifications and select one, synthesize a new one, or flag for human review | Must |
| PS-1-008 | Output SHALL be `master_dataset.csv` containing every input question with its final topic, subtopic, decision method, and dual-modal flag | Must |
| PS-1-009 | All model names SHALL come from `config/report_03.yaml`, never hardcoded | Must |

### 3.2 Stage 2: Concept Overlap Identification

| ID | Requirement | Priority |
|----|------------|----------|
| PS-2-001 | Pipeline SHALL identify surveys with concept overlap to ACS using subtopic intersection analysis | Must |
| PS-2-002 | Pipeline SHALL generate question pairs: every source question paired with every ACS question sharing its subtopic | Must |
| PS-2-003 | Pair generation SHALL be documented with counts traceable to raw data | Must |

### 3.3 Stage 3: Multi-Model Barrier Rating

| ID | Requirement | Priority |
|----|------------|----------|
| PS-3-001 | All 1,598 pairs SHALL be independently rated by 3 LLM raters from different vendors | Must |
| PS-3-002 | Each rater SHALL assign feasibility (F1/F2/F3) and barrier code (if F3) per pair | Must |
| PS-3-003 | Raters SHALL have no communication — full independence | Must |
| PS-3-004 | Inter-rater agreement SHALL be measured using Fleiss' kappa | Must |

### 3.4 Stage 4: Structured Arbitration

| ID | Requirement | Priority |
|----|------------|----------|
| PS-4-001 | All 1,598 pairs SHALL proceed to arbitration by 3 independent arbitrator models | Must |
| PS-4-002 | Arbitration SHALL use blind masking (raters shown as A, B, C) and order randomization | Must |
| PS-4-003 | Post-arbitration agreement SHALL be measured using Cohen's kappa (2-way) | Must |
| PS-4-004 | Quality gates SHALL require κ ≥ 0.75 for feasibility and binary consolidability | Must |

### 3.5 Stage 5: Question-Level Aggregation

| ID | Requirement | Priority |
|----|------------|----------|
| PS-5-001 | Results SHALL collapse from pair-level to question-level: best feasibility per unique question text | Must |
| PS-5-002 | Deduplication SHALL be by question text, not question ID (IDs inflate due to multi-subtopic assignment) | Must |
| PS-5-003 | A question is consolidable if ANY of its pairs is rated F1 or F2 | Must |
| PS-5-004 | ACS-side participation SHALL be computed: how many ACS questions serve as bridge targets | Must |

---

## 4. Validation Requirements

### 4.1 Core Principle

**V&V scripts are the single source of truth for all numbers.** NUMBERS_MAP, report chapters, diagram specs, fact sheets, and all other documents are downstream consumers. If a V&V script disagrees with a document, the document is wrong.

Every number cited in any deliverable MUST trace to a V&V script that independently computes it from source data files. No number is trusted because a document says so. No number is trusted because a previous session computed it. Numbers are trusted when a V&V script recomputes them from source data and exits 0.

### 4.2 V&V Script Standards

| ID | Requirement | Priority |
|----|------------|----------|
| VR-001 | Every V&V script SHALL compute values from source data files, never from intermediate summaries or documents | Must |
| VR-002 | Every V&V script SHALL output both machine-readable (JSON) and human-readable (log) results to `docs/validation/` | Must |
| VR-003 | Every V&V script SHALL use exit codes: 0=pass, 1=fail, 2=warn | Must |
| VR-004 | V&V scripts SHALL NOT import from the pipeline scripts they verify (independence requirement) | Must |
| VR-005 | V&V scripts SHALL be runnable standalone: `python src/validation/<script>.py` | Must |
| VR-006 | V&V scripts SHALL use the check/warn/skip framework established in `validate_complete.py` | Should |
| VR-007 | V&V scripts SHALL print a routing ledger or equivalent summary showing the complete data flow with counts at each branch point | Must |

### 4.3 Validation Coverage Requirements

| ID | What Must Be Validated | V&V Script | Priority |
|----|----------------------|------------|----------|
| VC-001 | Raw data integrity: row counts, column counts, survey instrument count | `validate_complete.py` | Must |
| VC-002 | Stage 1 classification routing: consensus / auto_dual_modal / arbitrated counts, routing equation, agreement metrics recomputed from raw labels, kappa recomputed from raw labels | `validate_stage1_classification.py` | Must |
| VC-003 | Pairing chain integrity: pair counts, ID non-overlap, verdicts subset of candidates | `validate_complete.py` | Must |
| VC-004 | Rating/arbitration metrics: Fleiss' κ, Cohen's κ, quality gates | `validate_complete.py` | Must |
| VC-005 | Question-level dedup: unique counts by survey, F1/F2/F3 breakdown, rate computation | `validate_complete.py` + `validate_question_counts.py` | Must |
| VC-006 | ACS-side participation: target counts, three-way bridges, fan-in, set arithmetic | `validate_complete.py` | Must |
| VC-007 | Round-trip spot checks: F1 questions trace to F1 pairs, F3 questions have no F1/F2 pairs | `validate_complete.py` | Must |
| VC-008 | Cross-document consistency: NUMBERS_MAP, NARRATIVE_CHECKLIST, README contain validated values | `validate_complete.py` | Must |

---

## 5. Verification & Validation Registry

Every number cited in deliverables MUST trace to a certified output. A script is certified when it exits 0 against current data. This table is the master registry.

### 5.1 V&V Script Registry

| V&V Script | What It Validates | Source Data Files | Output Artifacts Certified | SRS Requirements Traced | Exit Behavior |
|------------|-------------------|-------------------|---------------------------|------------------------|---------------|
| `src/validation/validate_complete.py` | End-to-end pipeline numbers: raw data integrity, pairing chain, rating metrics, question-level dedup, ACS-side participation, round-trip traces, cross-document consistency | `PublicSurveyQuestionsMap.csv`, `stage4_question_level.csv`, `final_verdicts.csv`, `cps_candidate_pairs_all.csv`, `foodaps_candidate_pairs_all.csv`, `stage2_agreement_metrics.json`, `stage3_arbitration_metrics.json`, `question_counts.json` | `docs/validation/validation_report.json`, `docs/validation/validation_report.log` | VC-001, VC-003, VC-004, VC-005, VC-006, VC-007, VC-008 | Exit 0=pass, 1=fail, 2=warn. ~80 checks. |
| `src/validation/validate_question_counts.py` | Ground-truth question counts at instrument, survey, and question-level. Computes reference JSON that all other scripts validate against | `PublicSurveyQuestionsMap.csv`, `stage4_question_level.csv`, `final_verdicts.csv` | `docs/validation/question_counts.json`, `docs/validation/question_counts.log` | VC-005 | Generates reference JSON. |
| `src/validation/validate_diagram_specs.py` | Diagram method spec factual content: numbers (routing counts, pair counts, kappa values, question counts, model names) checked against source data and `config/report_03.yaml` for all 5 active PaperBanana specs | `config/report_03.yaml`, `assets/diagrams/paperbanana/*_method.txt` | `docs/validation/diagram_spec_report.json`, `docs/validation/diagram_spec_report.log` | GAP-007 | Exit 0=pass, 1=fail, 2=warn. 6 layers, ~70 checks. |
| `src/validation/validate_stage1_classification.py` | Stage 1 classification routing paths: input counts, dual-model agreement recomputed from raw labels, routing split (consensus / auto_dual_modal / arbitrated) with exact counts, routing equation verification, master dataset reconciliation, input→output gap analysis, kappa applicability check, **arbitrator decision count cross-check (Layer 8, GAP-002)**, **dual-modal total verification (Layer 9, GAP-003)**, **model name verification against config/report_03.yaml (Layer 10, GAP-006)**, **Cohen's κ recomputation from raw labels via sklearn (Layer 11, GAP-001)** | `full_comparison.csv`, `agreement_summary.csv`, `disagreements.csv`, `arbitration_results.csv`, `auto_dual_modal_results.csv`, `all_disagreement_resolutions.csv`, `master_dataset.csv`, `config/report_03.yaml`, `stage3_rating_method.txt`, `stage4_arbitration_method.txt` | `docs/validation/stage1_classification_report.json`, `docs/validation/stage1_classification_report.log` | VC-002 | Exit 0=pass, 1=fail, 2=warn. Produces routing ledger. 11 layers, ~70 checks. |

### 5.2 Known Gaps (V&V scripts needed but not yet written)

| Gap ID | What's Missing | Why It Matters | Blocked By |
|--------|---------------|----------------|------------|
| ~~GAP-001~~ | ~~Stage 1: Cohen's κ recomputation from raw label columns in `full_comparison.csv`~~ | **RESOLVED 2026-03-01.** Layer 11 added to `validate_stage1_classification.py`. sklearn recompute from raw labels: κ(topics)=0.8399 vs stored 0.8389 (diff 0.0009), κ(subtopics)=0.6875 vs stored 0.6869 (diff 0.0005). Both within ±0.005 tolerance. NUMBERS_MAP ⚠️ warnings removed. | — |
| ~~GAP-002~~ | ~~Stage 1: Arbitrator decision count verification~~ | **RESOLVED 2026-03-01.** Layer 8 added to `validate_stage1_classification.py`. Verified: decision_method counts (522/482/340/19 = 1,363 resolved). Also discovered 5-row override gap: arb_decision has 487 pick_haiku45, but 5 were overridden to unresolved_disagreement downstream. 1,368 entered arbitration, 1,363 got final decisions, 5 overridden. | — |
| ~~GAP-003~~ | ~~Stage 1: Dual-modal total verification~~ | **RESOLVED 2026-03-01.** Layer 9 added to `validate_stage1_classification.py`. Verified: 821 auto + 19 arb = 840 total. `is_dual_modal==True` count matches. Rate = 12.0% of master (6,987). | — |
| ~~GAP-004~~ | ~~Stage 1: The 33-row input→output gap~~ | **RESOLVED 2026-03-01.** 38 = total `needs_human_review` in master (31 unresolved + 7 categorization_failed). 33 = rows never in `full_comparison.csv` (26 unresolved + 7 failed). 5 = went through comparison but remained unresolved after arbitration. 33 + 5 = 38. ✅ | — |
| ~~GAP-005~~ | ~~Stage 1: Subtopic agreement % discrepancy~~ | **RESOLVED 2026-03-01.** Two distinct metrics: subtopic *label* agreement = 69.69% (4,846/6,954, raw subtopic text match) vs subtopic *routing* agreement = 68.52% (4,765/6,954, compound criterion requiring BOTH topic AND subtopic match). The 81-row gap = questions where subtopic matched but topic did not. Both are correct; they measure different things. Pipeline routing uses the stricter 68.5%. | — |
| ~~GAP-006~~ | ~~Stage 3/4: Model names in diagram specs verified against config~~ | **PARTIALLY RESOLVED 2026-03-01.** Layer 10 added to `validate_stage1_classification.py`. Checks stage3/stage4 diagram spec model names against `config/report_03.yaml`. Also detects NUMBERS_MAP inaccuracy: config shows arbitrators DIFFER from raters (opus/gpt-5.2/gemini-3-pro vs gpt-5-mini/haiku/gemini-3-flash) but NUMBERS_MAP says "Same models in arbitrator role". | — |
| ~~GAP-007~~ | ~~Diagram spec numbers verified against V&V outputs~~ | **RESOLVED 2026-03-01.** `src/validation/validate_diagram_specs.py` created. Checks all 5 active method specs for correct numbers (routing counts, pair counts, kappa values, question counts) and model names (against `config/report_03.yaml`). 6 layers, ~70 checks. | — |
| ~~GAP-008~~ | ~~NUMBERS_MAP arbitrator model names~~ | **RESOLVED 2026-03-01.** NUMBERS_MAP Step 6 corrected: "Same models in arbitrator role" replaced with actual model names from config (claude-opus-4-5, gpt-5.2, gemini-3-pro-preview). V&V Layer 10 detects future drift. | — |
| ~~GAP-009~~ | ~~Stage 1: 5-row arbitrator override~~ | **ROOT CAUSE FOUND 2026-03-01. ACCEPTED AS KNOWN LIMITATION.** IDs 6200-6203, 6205. Arbitrator returned `arb_decision=pick_haiku45` but `arb_primary_topic` and `arb_primary_subtopic` are null (LLM said WHO was right but didn't echo WHAT the answer was). `create_final_outputs.py:reconcile_categorizations()` gates on `arb_primary_topic.notna()`, so these 5 fell through to `unresolved_disagreement`. Bug is in arbitrator JSON response (missing fields), not reconciliation logic. 5 of 6,987 (0.07%) — acceptable loss, folded into the existing 38 flagged for human review. Correctly routed to human review where the edge case would have been caught. No downstream reprocessing warranted. | — |

### 5.3 Registry Rules

1. This table grows as V&V scripts are added
2. Every deliverable number MUST reference a certified V&V script from this registry
3. A script is NOT certified until it exits 0 against current data
4. V&V scripts MUST NOT import from the pipeline scripts they verify (independence requirement)
5. NUMBERS_MAP is a convenience document generated from V&V outputs, NOT a source of truth
6. When a V&V script disagrees with NUMBERS_MAP, NUMBERS_MAP is wrong and must be regenerated
7. Gaps in this registry are tracked in §5.2 and prioritized for resolution

---

## 6. Configuration Management

| ID | Requirement | Priority |
|----|------------|----------|
| CM-001 | All model names SHALL come from `config/report_03.yaml`, never hardcoded in pipeline scripts, diagram specs, or documents | Must |
| CM-002 | All pipeline parameters that affect outputs SHALL be externalized to configuration files | Must |
| CM-003 | Diagram source specs (`*_method.txt`) are the authoritative source for diagrams. PNG outputs are disposable build artifacts | Must |
| CM-004 | Numbers in diagram specs SHALL be verified against V&V script outputs before generation | Must |
| CM-005 | The build system (`build.py`) SHALL run validation before rendering. Direct `quarto render` also triggers pre-render validation | Must |

---

## 7. Constraints

| ID | Constraint |
|----|-----------|
| C-001 | Scope: 47 Census Bureau demographic survey instruments. NOT 48. NOT cross-agency. NOT "federal surveys" broadly |
| C-002 | All pipeline values SHALL come from upstream data sources, not hardcoded. This includes question counts, model names, metric values |
| C-003 | No number SHALL appear in a deliverable without a V&V script that independently verifies it from source data |
| C-004 | Stage 1 has ONE arbitrator — no post-arbitration κ is computable or meaningful for Stage 1. κ values cited for Stage 1 are PRE-arbitration classifier agreement only. The κ = 0.843 belongs to Stage 4 barrier arbitration (3 arbitrators) and must never appear in Stage 1 context |
| C-005 | Question-level counts use deduplicated question text, NOT question IDs (IDs inflate due to multi-subtopic assignment) |
| C-006 | NUMBERS_MAP is a reference document, not a source of truth. V&V scripts are the source of truth |

---

## 8. Traceability

| From | To | Mechanism |
|------|----|-----------|
| Report chapter claims | NUMBERS_MAP | NARRATIVE_CHECKLIST cross-references |
| NUMBERS_MAP values | V&V script outputs | Source file paths and JSON paths cited per metric |
| V&V script computations | Raw data files | Direct file reads in each script |
| Diagram spec numbers | V&V script outputs | GAP-007 (not yet automated) |
| Figure scripts | Input data | SCRIPT_ARTIFACT_MAP |

---

*This document specifies what must be validated and how. V&V scripts implement the validation. Pipeline scripts implement the analysis. The two SHALL remain independent.*
