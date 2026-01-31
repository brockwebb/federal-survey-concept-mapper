# Analysis Validation and Verification Plan

**Report:** 03 - Harmonization Constraints Analysis  
**Created:** 2026-01-30  
**Status:** Stage 3 In Progress

---

## Document Relationship

> **This document validates the pipeline defined in `SOFTWARE.md`.**
>
> | Stage | Name | Purpose | Key Scripts |
> |-------|------|---------|-------------|
> | 1 | Rating | Get rater classifications | `01_barrier_pipeline.py`, `clean_rater_data.py` |
> | 2 | Agreement | Validate rater reliability | `analyze_barrier_results.py`, `confusion_matrix_analysis.py` |
> | 3 | Arbitration | Adjudicate + validate arbitration quality | `02_arbitration_pipeline.py`, `clean_arbitration_data.py`, `analyze_arbitration_agreement.py` |
> | 4 | Findings | Answer research question (question-level consolidation, domain analysis) | TBD |
> | 5 | Communication | Stakeholder outputs (visualizations, executive summary) | TBD |
>
> **Note:** Data cleaning scripts are ETL within stages, not separate stages.
>
> **Pipeline execution may run ahead of validation. Do not draw conclusions from unvalidated stages.**
> See `SOFTWARE.md` for script documentation; see this document for validation status and findings.

---

## Overview

This document tracks systematic validation and verification (V&V) of the Report 03 analysis pipeline. Each stage must be validated before proceeding to the next (waterfall method). If upstream issues are discovered, iteration restarts from that stage.

**Purpose:**
- Ensure each pipeline stage produces correct, interpretable outputs
- Document statistical methods and rationale
- Identify issues before drawing conclusions
- Provide audit trail for methodology section and appendix

**Validation Criteria:**
- Data structures match expectations
- Computations are mathematically correct
- Edge cases handled appropriately
- Outputs are interpretable and meaningful

---

## Stage Status Tracker

| Stage | Name | Status | Last Validated |
|-------|------|--------|----------------|
| 1 | Rating | **COMPLETE** | 2026-01-30 |
| 2 | Agreement | **COMPLETE** | 2026-01-30 |
| 3 | Arbitration | IN PROGRESS | - |
| 4 | Findings | NOT STARTED | - |
| 5 | Communication | NOT STARTED | - |

**Status values:** NOT STARTED → IN PROGRESS → BLOCKED (upstream issue) → **COMPLETE**

**Current state (2026-01-31):**
- Stages 1-2: VALIDATED
- Stage 3: Arbitration complete, validation in progress (see FINDINGS_R03_S3_001)
  - Open issues: 8.1 (synthesis interpretation), 8.2 (Google behavior), 8.3 (L1 quality gate)
- Google arbitration at 503/1,598 (31.5%, CPS only) due to rate limits
- Stages 4-5: Will be spec'd after Stage 3 sign-off

---

## Stage 1: Rating (Dual-Model Classification)

### Purpose

Independently classify harmonization barriers for question pairs that were identified as non-consolidatable in Report 02. Uses three LLM raters operating in parallel to enable inter-rater reliability assessment.

### Inputs

**Source files:**
- `data/cps_comparison_merged.csv` - CPS vs ACS question pairs from Report 02
- `data/foodaps_comparison_merged.csv` - FoodAPS vs ACS question pairs from Report 02

**Filtering criteria:**
- Include pairs where `claude_consolidation_potential` OR `gpt_consolidation_potential` equals 'partial' or 'no'
- These are pairs that Report 02 identified as NOT directly consolidatable

**Input record structure (key fields):**
| Field | Description |
|-------|-------------|
| `pair_id` | Unique identifier (e.g., CPS_0023, FoodAPS_0156) |
| `survey_text` | Question text from source survey (CPS or FoodAPS) |
| `acs_text` | Comparison question text from ACS |
| `subtopic` | Topical category from Report 02 |
| `claude_classification` | Report 02 classification (e.g., response_format_mismatch) |
| `claude_consolidation_potential` | Report 02 judgment: yes/partial/no |
| `gpt_consolidation_potential` | Report 02 judgment: yes/partial/no |

**Verified counts:**
- [x] CPS pairs: 1,030
- [x] FoodAPS pairs: 568
- [x] Total: 1,598 pairs

### Process

**Script:** `01_barrier_pipeline.py`

**Rater models (from config.yaml):**
| Rater Key | Model | Provider | Temperature |
|-----------|-------|----------|-------------|
| openai | gpt-5-mini | OpenAI | not set (minimal params) |
| anthropic | claude-haiku-4-5-20251001 | Anthropic | 0.0 |
| google | gemini-3-flash-preview | Google | 1.0 (required by Google) |

**Classification task:**
Each rater receives batches of question pairs and must assign:
1. **Primary barrier code** - L1.L2 format (e.g., TC.1, CC.2)
2. **Feasibility rating** - F1, F2, or F3
3. **Specific conflict** - Brief description of the exact difference
4. **Additional barriers** - Optional secondary barriers
5. **Reasoning** - Explanation for the classification

**Barrier Taxonomy (embedded in prompt):**

| L1 Code | Type | L2 Subtypes |
|---------|------|-------------|
| TC | Temporal/Chronological | TC.1 (period length), TC.2 (temporal framing), TC.3 (calendar alignment) |
| CC | Construct/Concept | CC.1 (definition), CC.2 (operationalization), CC.3 (boundaries), CC.4 (scope) |
| PC | Population/Coverage | PC.1 (universe), PC.2 (frame exclusions), PC.3 (age bounds), PC.4 (geography) |
| RS | Response Scale | RS.1 (scale type), RS.2 (category structure), RS.3 (anchoring), RS.4 (numeric vs verbal) |
| MC | Mode/Context | MC.1 (interview mode), MC.2 (routing), MC.3 (priming), MC.4 (proxy response) |
| PM | Processing/Metadata | PM.1 (coding), PM.2 (derived variables), PM.3 (documentation gaps) |
| NHB | No Harmonization Barrier | NHB.0 (questions functionally equivalent) |

**Feasibility scale:**
| Code | Level | Definition |
|------|-------|------------|
| F1 | Direct recode | Mechanically transformable |
| F2 | Statistical adjustment | Requires modeling or assumptions |
| F3 | Incompatible | Fundamentally different, not harmonizable |

**Batching:**
- Batch size: 10 pairs per API call
- Checkpoint interval: Every 10 batches
- Rate limit delay: 0.3 seconds between calls

### Outputs

**Output files (per rater):**
- `output/results/barrier_results_anthropic_claude-haiku-4-5-20251001.jsonl`
- `output/results/barrier_results_openai_gpt-5-mini.jsonl`
- `output/results/barrier_results_google_gemini-3-flash-preview.jsonl`

**Cleaned outputs (per rater):**
- `output/analysis/barrier_deduped_anthropic.jsonl`
- `output/analysis/barrier_deduped_openai.jsonl`
- `output/analysis/barrier_deduped_google.jsonl`

**Output record structure:**
| Field | Type | Description |
|-------|------|-------------|
| `pair_id` | string | Links back to input |
| `primary_barrier` | string | L1.L2 code (e.g., "TC.1", "CC.2") |
| `feasibility` | string | F1, F2, or F3 |
| `specific_conflict` | string | Plain language description |
| `additional_barriers` | array | Optional secondary barrier codes |
| `reasoning` | string | Explanation for classification |
| `rater` | string | Which rater produced this (anthropic/openai/google) |

**Merged output:**
- `output/analysis/barrier_coding_merged_3rater.csv` - All three raters' outputs joined on pair_id

### Validation Checklist

- [x] **Input data loads correctly**
  - Verified both CSV files exist and load
  - Verified filtering criteria applied correctly
  
- [x] **Output record count matches input**
  - Each rater has 1,598 records after cleaning
  - Merged file has 1,598 rows with all three raters' columns
  
- [x] **All expected fields present**
  - JSONL files have all required fields
  - Merged CSV has columns for all three raters
  
- [x] **No unexpected null/missing values (or documented why)**
  - Anthropic: 10 null primary_barrier → recoded to NHB.0
  - OpenAI: 3 null primary_barrier → recoded to NHB.0
  - Google: 0 null values
  - **RESOLVED:** Nulls are legitimate "no barrier" cases (all had F1 feasibility)
  
- [x] **Barrier codes conform to taxonomy**
  - All primary_barrier values match L1.L2 pattern after NHB.0 recoding
  - L1 values: {TC, CC, PC, RS, MC, PM, NHB}
  
- [x] **Feasibility ratings conform to expected values**
  - All feasibility values are F1, F2, or F3

### Verification Questions

**Q1: What exactly does each rater output?**

Each rater produces one JSON object per pair with:
- Barrier classification (primary + additional)
- Feasibility rating
- Free-text reasoning

Output is structurally identical across raters—only the classifications differ.

**Q2: How are confidence scores calculated?**

**FINDING:** Stage 1 does NOT output confidence scores. The prompt asks for classification but does not request confidence. The `claude_confidence` and `gpt_confidence` fields in the input are from Report 02, not this pipeline.

**Q3: What happens when a model can't classify?**

The pipeline has retry logic (5 attempts with exponential backoff). If all retries fail:
- Empty list returned for that batch
- Batch recorded as "failed"
- Those pairs would be missing from output

**RESOLVED:** The null values were NOT parse failures. They were valid responses where raters judged no barrier existed.

### Findings

**2026-01-30 Initial Review:**

1. **Pipeline structure is clear** - Config-driven, three parallel raters, JSONL outputs merged into CSV

2. **Taxonomy is embedded in prompt** - Raters receive the full taxonomy definition. Good for reproducibility.

3. **nan values resolved** - 10 Anthropic, 3 OpenAI, 0 Google records had null primary_barrier. Root cause: legitimate "no harmonization barrier" judgments. All had F1 feasibility, indicating raters saw questions as functionally equivalent.
   
4. **NHB.0 now visible** - After recoding null values to NHB.0, this category appears in distributions.
   
5. **Temperature differences across raters** - OpenAI uses default (no temperature set), Anthropic uses 0.0, Google must use 1.0. This affects reproducibility but is documented in config.

**2026-01-30 Rater Cleaning Results:**

| Rater | Raw Records | Duplicates | Recoded to NHB.0 | Schema Valid |
|-------|-------------|------------|------------------|--------------|
| OpenAI | 1,598 | 0 | 3 | 1,598 |
| Anthropic | 1,598 | 0 | 10 | 1,598 |
| Google | 1,598 | 0 | 0 | 1,598 |

**L1 Barrier Distribution by Rater:**

| L1 Code | OpenAI | Anthropic | Google |
|---------|--------|-----------|--------|
| CC (Construct) | 1,284 | 1,257 | 1,276 |
| TC (Temporal) | 177 | 185 | 129 |
| RS (Response Scale) | 69 | 99 | 160 |
| PC (Population) | 34 | 10 | 7 |
| MC (Mode/Context) | 22 | 37 | 26 |
| PM (Processing) | 9 | 0 | 0 |
| NHB (No Barrier) | 3 | 10 | 0 |

**Key observations:**
- **80.7% unanimous L1 agreement** across all three raters (1,289/1,598)
- **CC dominates** (~80% of classifications) - construct differences are the primary barrier
- **RS varies most** (69-160) - raters disagree on response scale classification
- **PM rare** - only OpenAI coded any processing/metadata barriers
- **NHB sparse** - 0-10 per rater, Google never used it

### Open Items for Resolution

| ID | Item | Status | Resolution |
|----|------|--------|------------|
| S1.1 | Investigate nan values in L1 distribution | ✅ RESOLVED | Null values are legitimate NHB.0 cases; recoded in `clean_rater_data.py` |
| S1.2 | Verify input record counts | ✅ RESOLVED | CPS=1,030, FoodAPS=568, Total=1,598 |
| S1.3 | Validate barrier code conformance | ✅ RESOLVED | All codes conform after NHB.0 recoding |
| S1.4 | Check for NHB classifications | ✅ RESOLVED | NHB now visible: OpenAI=3, Anthropic=10, Google=0 |

### Sign-off

- [x] **Stage 1 validated**
- **Date:** 2026-01-30
- **Validated by:** Brock Webb / Claude
- **Notes:** All open items resolved. Created `scripts/clean_rater_data.py` for reproducible data cleaning. Null values recoded to NHB.0 per taxonomy v1.1. 80.7% three-way L1 agreement provides strong inter-rater reliability baseline.

---

## Stage 2: Agreement

### Purpose
Analyze inter-rater agreement patterns to understand where raters align and diverge. This informs the arbitration stage and provides reliability metrics for the methodology section.

### Inputs
- [x] `output/analysis/barrier_deduped_*.jsonl` - Cleaned per-rater data from Stage 1
- [x] `output/analysis/barrier_coding_merged_3rater.csv` - Merged three-rater data

### Validation Summary

See `FINDINGS_R03_S2_agreement_analysis.md` for complete Stage 2 validation.

**Key findings:**
- 80.7% three-way L1 agreement (1,289/1,598 pairs)
- Cohen's kappa: 0.57-0.73 pairwise (substantial agreement)
- Confusion matrices show CC→TC and RS→CC as primary disagreement patterns

### Sign-off

- [x] **Stage 2 validated**
- **Date:** 2026-01-30
- **Validated by:** Brock Webb / Claude
- **Notes:** See FINDINGS_R03_S2_agreement_analysis.md for details.

---

## Stage 3: Arbitration

### Purpose
Use flagship LLM arbitrators to adjudicate ALL question pairs (not just disagreements), enabling inter-arbitrator agreement analysis and bias detection. This stage includes data cleaning (ETL) and V&V analysis.

### Inputs
- [x] `output/analysis/barrier_deduped_*.jsonl` - Cleaned rater outputs
- [x] Three rater perspectives presented blind (Rater A/B/C masking)

### Outputs
- [x] `output/results/arbitration_v3_results_anthropic_*.jsonl` - 1,598 pairs
- [x] `output/results/arbitration_v3_results_openai_*.jsonl` - 1,598 pairs  
- [x] `output/results/arbitration_v3_results_google_*.jsonl` - 503 pairs (rate limited, CPS only)
- [x] `output/analysis/final_verdicts.csv` - Consolidated verdicts with confidence levels

### Validation Summary

See `FINDINGS_R03_S3_001_arbitration_analysis.md` for complete Stage 3 validation.

**Key metrics (from Sections 1-7):**
- Inter-arbitrator L1 agreement: 89.2% pairwise (Anthropic-OpenAI)
- Three-way Fleiss' kappa (L1): 0.796 (substantial, near threshold)
- Final verdicts: 98.2% HIGH confidence, 1.8% LOW confidence
- CC dominates at 85-89% of barriers
- F3 (not feasible) at ~80% of pairs

**Open Issues:**
- 8.1: Synthesis interpretation (examine reasoning text) - DEFERRED pending complete Google data
- 8.2: Google behavior investigation - ✅ RESOLVED: 7% synthesis is real behavioral difference, not labeling artifact (bug fix applied 2026-01-30)
- 8.3: L1 quality gate decision - ✅ ACCEPT: κ=0.796 accepted with kappa paradox context; three-way κ=0.833 confirms reliability

### Sign-off

- [ ] **Stage 3 validated**
- **Date:** ___
- **Validated by:** ___
- **Notes:** Pending resolution of open issues 8.1, 8.2, 8.3

---

## Stage 4: Findings

### Purpose
Answer the research question: What proportion of source survey questions can be consolidated with ACS via record linkage? Analysis at question-level (not pair-level) to provide actionable metrics.

### Critical Distinction: Pair-Level vs Question-Level

**Problem:** Current metrics are pair-level, but stakeholders need question-level.

**Example:** FoodAPS has 52 food security questions paired with 6 ACS questions = 312 pairs. Even 100% ACS coverage = 6/312 = 1.9% at pair level. But the stakeholder question is: "Of FoodAPS's 52 questions, how many have at least one consolidable ACS match?"

**Solution:** Aggregate from pair-level to question-level by checking if ANY pair for a given source question is consolidable (F1 or F2).

### Definitions

**Consolidability:**
- F1 (Direct Recode): Mechanically transformable, fully consolidable
- F2 (Statistical Adjustment): Requires modeling, conditionally consolidable  
- F3 (Incompatible): Not consolidable

**Question-Level Consolidability:** A source question is consolidable if it has at least one pair with F1 or F2 feasibility.

### Inputs
- [x] `output/analysis/final_verdicts.csv` - Pair-level arbitration results
- [x] `data/cps_comparison_merged.csv` - CPS question mapping (pair_id → survey_q_id)
- [x] `data/foodaps_comparison_merged.csv` - FoodAPS question mapping

### Key Analyses
1. **Question-level consolidation rates** - Per survey: X% of questions have consolidable path
2. **Quality breakdown** - Of consolidable: X% F1 (direct), Y% F2 (needs adjustment)
3. **Domain/topic analysis** - Which content areas consolidate best?
4. **F2 transformation inventory** - What statistical adjustments needed?
5. **Barrier patterns** - For F3 pairs, which barriers dominate?

### Outputs

**Primary:**
- `output/analysis/stage4_question_level.csv` - One row per source question
- `output/analysis/stage4_survey_summary.json` - Aggregate statistics
- `output/analysis/stage4_findings_report.md` - Human-readable summary

**Secondary:**
- `output/analysis/stage4_topic_breakdown.csv` - Rates by subtopic
- `output/analysis/stage4_f2_transformations.csv` - F2 pairs needing adjustment
- `output/analysis/stage4_barrier_patterns.csv` - Barrier distribution for F3

### Script
`04_findings_pipeline.py` (root, following 01/02/03 pattern per SOFTWARE.md)

### Validation Checklist
- [ ] Join logic verified (pair_id matches across files)
- [ ] Question counts match source data
- [ ] Consolidable + non-consolidable = total (no missing)
- [ ] Rates are mathematically correct
- [ ] Domain/topic categories valid

### Sign-off

- [ ] **Stage 4 validated**
- **Date:** ___
- **Notes:** Spec complete. Pending Stage 3 QC and Google data completion.

---

## Stage 5: Communication

### Purpose
Produce stakeholder-ready outputs: visualizations, executive summary, and final report sections.

### Outputs (TBD)
- [ ] Executive summary (1-2 pages for senior leadership)
- [ ] Key visualizations for report
- [ ] Infographic (optional, for broader communication)
- [ ] Methodology appendix materials

### Sign-off

- [ ] **Stage 5 validated**
- **Date:** ___
- **Notes:** Will be spec'd after Stage 4

---

## Upstream Issue Log

Track issues that force iteration back to earlier stages.

| Date | Found In | Issue | Upstream Stage | Resolution | Status |
|------|----------|-------|----------------|------------|--------|
| 2026-01-30 | Stage 1 | Null primary_barrier values | Stage 1 | Created clean_rater_data.py, recoded to NHB.0 | RESOLVED |

---

## Visual/Table Requirements

Track what visuals and tables are needed for the report, identified during validation.

| ID | Description | Stage | Status | Notes |
|----|-------------|-------|--------|-------|
| V1 | L1 barrier distribution by rater (bar chart) | 1 | Identified | Compare rater tendencies |
| V2 | Feasibility distribution by rater | 1 | Identified | |
| V3 | Inter-arbitrator agreement heatmap | 3 | Identified | |
| V4 | Family bias visualization | 3 | Identified | |
| V5 | Question-level consolidation rates | 4 | TBD | Research question answer |
| V6 | Domain breakdown chart | 4 | TBD | Which topics consolidate best? |

---

## Discussion Points

Notable findings for the discussion section, identified during validation.

| ID | Finding | Stage | Implication | Notes |
|----|---------|-------|-------------|-------|
| D1 | Temperature settings differ by provider | 1 | Reproducibility consideration | Google requires 1.0 |
| D2 | No confidence scores in Stage 1 | 1 | Cannot weight by confidence | Design decision |
| D3 | 80.7% three-way L1 agreement | 1 | Strong inter-rater reliability | Supports methodology validity |
| D4 | CC dominates at ~80% | 1 | Most barriers are construct differences | Key finding |

---

## Appendix Materials

Items suitable for appendix/lab notebook, identified during validation.

| ID | Description | Stage | Format | Notes |
|----|-------------|-------|--------|-------|
| A1 | Full barrier taxonomy | 1 | Table | Embedded in prompt |
| A2 | Rater model specifications | 1 | Table | From config.yaml |
| A3 | Example prompt | 1 | Code block | For reproducibility |
| A4 | Rater cleaning log | 1 | JSON | From clean_rater_data.py |

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-01-30 | Initial V&V plan created | Brock/Claude |
| 2026-01-30 | Stage 1 documentation started, open items identified | Brock/Claude |
| 2026-01-30 | Stage 1 validation COMPLETE - all open items resolved | Brock/Claude |
| 2026-01-30 | Added document relationship header, updated stage status tracker | Brock/Claude |
| 2026-01-31 | **Pipeline restructure:** Merged old Stages 4-5 (Cleanup/Analysis) into Stage 3. New Stage 4 (Findings) and Stage 5 (Communication) added as placeholders. Cleanup scripts are ETL within stages, not separate stages. | Brock/Claude |
| 2026-01-31 | Stage 3 issues 8.2 and 8.3 marked RESOLVED. Stage 4 spec completed with question-level consolidability methodology. | Brock/Claude |
