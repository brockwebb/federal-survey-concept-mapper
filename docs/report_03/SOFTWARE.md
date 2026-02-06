# Software Library Documentation

## Report 03: Harmonization Constraints

**Version:** 4.1
**Last Updated:** 2026-02-02
**Author:** Brock Webb

---
## Document Relationship

> **This document defines the pipeline validated by `docs/ANALYSIS_VV_PLAN.md`.**
>
> | Stage | Name | Purpose | Key Scripts | Status |
> |-------|------|---------|-------------|--------|
> | 1 | Rating | Get rater classifications | `01_barrier_pipeline.py`, `clean_rater_data.py` | ✅ Validated |
> | 2 | Agreement | Validate rater reliability | `analyze_barrier_results.py`, `confusion_matrix_analysis.py` | ✅ Validated |
> | 3 | Arbitration | Adjudicate + validate arbitration quality | `02_arbitration_pipeline.py`, `clean_arbitration_data.py`, `analyze_arbitration_agreement.py` | ✅ Validated |
> | 4 | Findings | Question-level consolidability, scoring, best-match rollup | `04_findings_pipeline.py`, `stage4_scoring_bakeoff.py`, `stage4_best_match_rollup.py` | ✅ Complete |
> | 5 | Deliverables | Expert review tables, stakeholder outputs | `05_deliverables_pipeline.py`, `build_expert_review_table.py` | ✅ Complete |
>
> **Note:** Data cleaning scripts (e.g., `clean_rater_data.py`, `clean_arbitration_data.py`) are ETL within stages, not separate stages.
>
> **Pipeline execution may run ahead of validation.** Check V&V plan for validation status before drawing conclusions.

---
## Quick Reference

| Script | Purpose | Run Command |
|--------|---------|-------------|
| `01_barrier_pipeline.py` | Rate pairs (3 raters) | `python 01_barrier_pipeline.py --rater {openai,anthropic,google}` |
| `02_arbitration_pipeline.py` | Arbitrate (3 arbitrators) | `python 02_arbitration_pipeline.py --arbitrator {anthropic,openai,google}` |
| `03_analysis_pipeline.py` | Post-arbitration analysis | `python 03_analysis_pipeline.py` |
| `04_findings_pipeline.py` | Question-level consolidability | `python 04_findings_pipeline.py` |
| `05_deliverables_pipeline.py` | Scoring, rollup, expert tables, visuals, PDF | `python 05_deliverables_pipeline.py --stage all` |
| `run_pipeline.py` | Orchestrate full pipeline | `python run_pipeline.py --stage all` |
| `scripts/analyze_barrier_results.py` | Basic agreement stats | `python scripts/analyze_barrier_results.py` |
| `scripts/confusion_matrix_analysis.py` | Confusion matrices | `python scripts/confusion_matrix_analysis.py` |
| `scripts/compare_arbitrators.py` | Inter-arbitrator analysis | `python scripts/compare_arbitrators.py` |
| `scripts/clean_arbitration_data.py` | Dedupe/validate arbitration | `python scripts/clean_arbitration_data.py` |
| `scripts/analyze_arbitration_agreement.py` | Arbitrator agreement/bias | `python scripts/analyze_arbitration_agreement.py` |
| `scripts/post_arbitration_analysis.py` | Final visualizations | `python scripts/post_arbitration_analysis.py` |
| `scripts/descriptive_stats.py` | Reproducible descriptive stats | `python scripts/descriptive_stats.py --stage all` |
| `scripts/stage4_scoring_bakeoff.py` | 4-method scoring comparison | `python scripts/stage4_scoring_bakeoff.py` |
| `scripts/stage4_best_match_rollup.py` | Best ACS match + triage quadrant | `python scripts/stage4_best_match_rollup.py` |
| `scripts/build_expert_review_table.py` | Expert review deliverables | `python scripts/build_expert_review_table.py` |
| `scripts/stage4_model_validation_visuals.py` | Model validation visualizations + narratives | `python scripts/stage4_model_validation_visuals.py` |
| `scripts/04_stage3_arbitration.py` | Stage 3 analysis + final verdicts | `python scripts/04_stage3_arbitration.py` |
| `scripts/qc_stage3_arbitration.py` | Stage 3 QC (11 checks) | `python scripts/qc_stage3_arbitration.py` |
| `scripts/clean_rater_data.py` | Dedupe/validate rater data | `python scripts/clean_rater_data.py` |
| `scripts/extract_low_confidence_pairs.py` | Extract low-confidence pairs | `python scripts/extract_low_confidence_pairs.py` |
| `scripts/fix_google_selected_rater_key.py` | One-off: fix Google rater key | `python scripts/fix_google_selected_rater_key.py` |

---

## Directory Structure

```
reports/03_harmonization_constraints/
├── config.yaml                 # SINGLE SOURCE OF TRUTH for all parameters
├── methodology_log.md          # Decision documentation
├── taxonomy_v1.md              # Barrier taxonomy (v1.1 with NHB.0)
├── SOFTWARE.md                 # This file
│
├── 01_barrier_pipeline.py      # Stage 1: Rating (renamed from barrier_coding_pipeline.py)
├── 02_arbitration_pipeline.py  # Stage 3: Arbitration (renamed from arbitration_pipeline.py)
├── 03_analysis_pipeline.py     # Post-arbitration analysis orchestrator
├── 04_findings_pipeline.py     # Stage 4: Question-level consolidability findings
├── 05_deliverables_pipeline.py # Stage 5: Scoring bake-off, rollup, expert tables
├── run_pipeline.py             # Full pipeline orchestrator (all stages)
├── run_full_pipeline.py        # Legacy orchestrator (deprecated)
│
├── scripts/
│   ├── lib/
│   │   ├── __init__.py         # Shared utilities package
│   │   ├── stats.py            # Agreement statistics (kappa, fleiss)
│   │   ├── taxonomy.py         # L1/L2 extraction, barrier code utils
│   │   └── io_utils.py         # Config loading, JSONL/CSV I/O
│   ├── clean_arbitration_data.py        # Stage 4: Arbitration cleanup
│   ├── analyze_arbitration_agreement.py # Stage 5: Agreement/bias analysis
│   ├── analyze_barrier_results.py       # Stage 2: Rater QC
│   ├── confusion_matrix_analysis.py     # Stage 2: Confusion matrices
│   ├── compare_arbitrators.py           # Stage 5: Inter-arbitrator comparison
│   ├── analyze_agreement.py             # Stage 2: Agreement statistics
│   ├── post_arbitration_analysis.py     # Stage 6: Final visualizations
│   ├── descriptive_stats.py             # Reproducible descriptive statistics
│   ├── 04_stage3_arbitration.py         # Stage 3: Agreement, bias, final verdicts
│   ├── qc_stage3_arbitration.py         # Stage 3: QC validation (11 checks)
│   ├── clean_rater_data.py              # Stage 1: Dedupe/validate/merge rater data
│   ├── extract_low_confidence_pairs.py  # Ad-hoc: Extract low-confidence pairs
│   ├── fix_google_selected_rater_key.py # One-off: Fix Google rater key bug
│   ├── stage4_scoring_bakeoff.py        # Stage 5a: 4-method scoring comparison
│   ├── stage4_best_match_rollup.py      # Stage 5b: Best match per question + triage
│   ├── stage4_triage_assignment.py      # Pair-level triage (superseded by best_match_rollup)
│   ├── build_expert_review_table.py     # Stage 5c: Expert review deliverables
│   └── stage4_model_validation_visuals.py  # Stage 5f: Model validation visualizations
│
├── docs/
│   └── pipeline_diagram.md     # Pipeline data flow diagram (Mermaid)
│
├── data/
│   ├── cps_comparison_merged.csv      # CPS-ACS pairs (Report 02 output)
│   └── foodaps_comparison_merged.csv  # FoodAPS-ACS pairs (Report 02 output)
│
├── output/
│   ├── results/                # Raw JSONL outputs from raters/arbitrators
│   ├── analysis/               # Merged CSVs, stage4_*, expert_review_*
│   │   ├── stage4_question_level.csv         # 380 questions with consolidability
│   │   ├── stage4_bakeoff_scores.csv         # 1,598 pairs with 4 scoring methods
│   │   ├── stage4_question_best_matches.csv  # Best ACS match + triage quadrant
│   │   ├── expert_review_combined.csv        # 380-row stakeholder table
│   │   ├── expert_review_cps.csv             # CPS subset (240)
│   │   ├── expert_review_foodaps.csv         # FoodAPS subset (140)
│   │   └── ...                               # Other merged CSVs
│   └── checkpoints/            # Resume points for interrupted runs
│
└── output_archive_gpt4omini_error/  # Archived outputs from buggy run
```

---

## Core Pipeline Scripts

### 1. `01_barrier_pipeline.py`

**Purpose:** Multi-rater barrier classification using LLM models.

**Stage:** 1 - Rating

**Version:** 2.0 (config-driven, three vendors)

**Inputs:**
- `config.yaml` — Model names, API keys, parameters
- `data/cps_comparison_merged.csv` — CPS question pairs
- `data/foodaps_comparison_merged.csv` — FoodAPS question pairs

**Outputs:**
- `output/results/barrier_results_{rater}_{model}.jsonl` — Raw classifications
- `output/checkpoints/barrier_checkpoint_{rater}.json` — Resume state

**Output Schema (per record):**
```json
{
  "pair_id": "CPS_0001",
  "primary_barrier": "CC.1",
  "feasibility": "F3",
  "specific_conflict": "Different definition of employment",
  "reasoning": "...",
  "rater": "openai",
  "model": "gpt-5-mini"
}
```

**Usage:**
```bash
# Run single rater
python 01_barrier_pipeline.py --rater openai
python 01_barrier_pipeline.py --rater anthropic
python 01_barrier_pipeline.py --rater google

# Or run all via orchestrator
python run_pipeline.py --stage rating
```

**Runtime:** ~20-30 min per rater (1,598 pairs, 6 workers)

**Cost:** ~$1-3 per rater

---

### 2. `02_arbitration_pipeline.py`

**Purpose:** Three-arbitrator adjudication with blind masking and order randomization.

**Stage:** 3 - Arbitration

**Version:** 3.1 (Decision 008)

**Key Features:**
- Processes ALL 1,598 pairs (not just disagreements)
- Blind masking: Raters shown as "Rater A/B/C"
- 50% fixed order, 50% randomized (position bias detection)
- Tracks `rater_order`, `order_type` per record

**Inputs:**
- `config.yaml` — Arbitrator models, parameters
- `output/results/barrier_results_*.jsonl` — Three rater outputs

**Outputs:**
- `output/results/arbitration_v3_results_{arb}_{model}.jsonl` — Arbitration results
- `output/checkpoints/arbitration_v3_checkpoint_{arb}.json` — Resume state

**Output Schema (per record):**
```json
{
  "pair_id": "CPS_0001",
  "final_barrier_code": "CC.1",
  "final_feasibility": "F3",
  "selected_rater": "B",
  "selected_rater_key": "anthropic",
  "reasoning": "...",
  "specific_conflict": "...",
  "rater_order": ["openai", "anthropic", "google"],
  "order_type": "fixed",
  "arbitrator": "anthropic",
  "arbitrator_model": "claude-opus-4-5-20251101",
  "openai_barrier": "CC.2",
  "anthropic_barrier": "CC.1",
  "google_barrier": "CC.1"
}
```

**Usage:**
```bash
# Run one arbitrator at a time (recommended)
python 02_arbitration_pipeline.py --arbitrator anthropic
python 02_arbitration_pipeline.py --arbitrator openai
python 02_arbitration_pipeline.py --arbitrator google
```

**Runtime:** ~45-90 min per arbitrator (1,598 pairs, longer prompts)

**Cost:** ~$15-25 per arbitrator (flagship models)

---

### 3. `run_pipeline.py`

**Purpose:** Orchestrate multi-stage pipeline execution.

**Stage:** Orchestrator (all stages)

**Stages available:** `rate`, `arbitrate`, `analyze`, `findings`, `deliverables`, `all`

**Usage:**
```bash
python run_pipeline.py                           # Full pipeline (all stages)
python run_pipeline.py --stage rate              # Rating only
python run_pipeline.py --stage arbitrate         # Arbitration only
python run_pipeline.py --stage analyze           # Post-arbitration analysis
python run_pipeline.py --stage findings          # Stage 4: Question-level findings
python run_pipeline.py --stage deliverables      # Stage 5: Scoring, rollup, expert tables
python run_pipeline.py --validate-config         # Check API keys and config
python run_pipeline.py --dry-run --stage all     # Show plan without running
```

**Note:** For large runs, recommend running raters/arbitrators individually to isolate failures.

---

## Analysis Scripts

### 4. `scripts/analyze_barrier_results.py`

**Purpose:** Merge rater outputs, compute basic agreement statistics.

**Stage:** 2 - Rater QC

**Inputs:**
- `output/results/barrier_results_*.jsonl`

**Outputs:**
- `output/analysis/barrier_coding_merged.csv` — Merged rater results
- `output/analysis/barrier_coding_summary.json` — Agreement stats
- Console: Agreement percentages, Cohen's kappa

**Metrics:**
- L1 barrier agreement (%)
- Full code agreement (L1.L2) (%)
- Feasibility agreement (%)
- Cohen's kappa (chance-corrected)

**Usage:**
```bash
python scripts/analyze_barrier_results.py
```

---

### 5. `scripts/confusion_matrix_analysis.py`

**Purpose:** Generate confusion matrices for rater disagreement patterns.

**Stage:** 2 - Rater QC

**Inputs:**
- `output/analysis/barrier_coding_merged.csv`

**Outputs:**
- `output/analysis/confusion_analysis/barrier_L1_confusion_matrix.png`
- `output/analysis/confusion_analysis/barrier_L1_confusion_matrix.csv`
- `output/analysis/confusion_analysis/barrier_full_confusion_matrix.png`
- `output/analysis/confusion_analysis/feasibility_confusion_matrix.png`

**Usage:**
```bash
python scripts/confusion_matrix_analysis.py
```

---

### 6. `scripts/compare_arbitrators.py`

**Purpose:** Analyze inter-arbitrator agreement and inter-family bias.

**Stage:** 3 - Arbitration (may be superseded by `analyze_arbitration_agreement.py`)

**Inputs:**
- `output/results/arbitration_v3_results_*.jsonl`

**Outputs:**
- Console: Pairwise agreement, bias analysis
- `output/analysis/arbitrator_comparison.csv` (TBD)
- `output/analysis/position_bias_analysis.csv` (TBD)

**Analyses:**
1. Three-way arbitrator agreement at L1, subcode, feasibility
2. Inter-family bias: Does opus favor haiku? Does gpt-5.2 favor gpt-5-mini?
3. Position bias: Do arbitrators favor "Rater A" position?

**Usage:**
```bash
python scripts/compare_arbitrators.py
```

**Note:** May need updates after arbitration runs complete.

---

### 7. `scripts/post_arbitration_analysis.py`

**Purpose:** Generate final visualizations and summary statistics.

**Stage:** 5 - Communication

**Inputs:**
- `output/analysis/barrier_coding_final.csv` (or merged + arbitration)

**Outputs:**
- `output/analysis/post_arbitration/barrier_distribution.png`
- `output/analysis/post_arbitration/feasibility_distribution.png`
- `output/analysis/post_arbitration/barrier_feasibility_heatmap.png`
- `output/analysis/post_arbitration/arbitration_analysis.png`
- `output/analysis/post_arbitration/summary_stats.json`

**Usage:**
```bash
python scripts/post_arbitration_analysis.py
```

---

### 8. `scripts/analyze_agreement.py`

**Purpose:** Detailed agreement analysis (may overlap with analyze_barrier_results.py).

**Stage:** 2 - Rater QC (verify if redundant with `analyze_barrier_results.py`)

**Status:** Verify functionality, may be legacy.

---

### 9. `scripts/clean_arbitration_data.py`

**Purpose:** Deduplicate and validate arbitration results for analysis.

**Stage:** 3 - Arbitration (ETL)

**Version:** 1.0

**Inputs:**
- `output/results/arbitration_v3_results_*.jsonl` — Raw arbitration outputs

**Outputs:**
- `output/analysis/arbitration_deduped_{arbitrator}.jsonl` — Cleaned per-arbitrator files
- `output/analysis/arbitration_merged.csv` — All arbitrators joined on pair_id
- `output/analysis/data_cleaning_log.json` — Audit trail

**Processing Steps:**
1. Load raw JSONL files
2. Deduplicate by pair_id (keep first occurrence)
3. Validate schema (required fields present)
4. Recode null/None barriers to NHB.0
5. Merge on pair_id (inner join for three-way, preserving unmatched for two-way)
6. Write outputs with cleaning log

**Usage:**
```bash
python scripts/clean_arbitration_data.py
```

**Dedup Statistics (expected):**
- Anthropic: 1,600 → 1,598 (drop 2)
- OpenAI: 1,598 → 1,598 (no change)
- Google: 252 → 251 (drop 1)

**Note:** Google data limited to CPS pairs only (rate limit hit before FoodAPS).

---

### 10. `scripts/analyze_arbitration_agreement.py`

**Purpose:** Inter-arbitrator agreement analysis and bias detection.

**Stage:** 3 - Arbitration (V&V)

**Version:** 1.0

**Inputs:**
- `output/analysis/arbitration_merged.csv` (from Stage 4)
- `config.yaml` (rater/arbitrator configuration)

**Outputs:**
- `output/analysis/arbitration_agreement_report.json` - Full statistics
- `output/analysis/arbitration_agreement_report.md` - Human-readable report
- `output/analysis/position_bias_analysis.csv` - Rater position effects
- `output/analysis/family_bias_analysis.csv` - Same-family preference

**Analyses:**

| Analysis | Method | Purpose |
|----------|--------|---------|
| Pairwise agreement | Cohen's Kappa | Agreement between arbitrator pairs |
| Three-way agreement | Fleiss' Kappa | Agreement across all 3 arbitrators |
| Synthesis rate | Frequency count | How often all raters agreed |
| Family bias | Chi-square | Same-vendor preference detection |
| Position bias | Frequency count | First-position selection bias |

**Agreement levels analyzed:**
- L1 barrier (TMP, CON, RSC, etc.)
- Full barrier code (TMP.1, CON.2, etc.)
- Feasibility classification (feasible, conditional, not_feasible)

**Usage:**
```bash
python scripts/analyze_arbitration_agreement.py
```

**Dependencies:** pandas, numpy, pyyaml

---

### 11. `scripts/descriptive_stats.py`

**Purpose:** Generate reproducible descriptive statistics. Captures ad-hoc analyses from conversation.

**Stage:** 4 - Findings / 5 - Communication

**Analyses:**
1. L1/L2 barrier distributions (per rater)
2. Agreement rates at L1, L2, feasibility levels
3. Synthesis detection performance (precision/recall)
4. Ground truth rater agreement calculations

**Usage:**
```bash
python scripts/descriptive_stats.py --stage rater
python scripts/descriptive_stats.py --stage arbitration
python scripts/descriptive_stats.py --stage all
```

---

### 12. `scripts/extract_low_confidence_pairs.py`

**Purpose:** Extract LOW confidence pairs with question text for manual expert review.

**Stage:** Ad-hoc diagnostic (not part of automated pipeline)

**Version:** 1.0

**Inputs:**
- `output/analysis/final_verdicts.csv` — Stage 3 verdicts with confidence levels
- `output/question_matching/cps/cps_candidate_pairs_all.csv` — CPS question text
- `output/question_matching/foodaps/foodaps_candidate_pairs_all.csv` — FoodAPS question text

**Outputs:**
- `output/analysis/low_confidence_pairs_detail.csv` — Full extract with question text and all arbitrator verdicts

**Usage:**
```bash
python scripts/extract_low_confidence_pairs.py
```

**Context:** Stage 3 arbitration identifies 28 pairs (1.8%) where arbitrators disagreed (three-way split or two-way disagreement without Google tiebreaker). This script extracts those pairs with full question text for manual inspection and expert review.

**Related:** `output/analysis/low_confidence_pairs_review.md` contains qualitative analysis of disagreement patterns.

---

### 13. `03_analysis_pipeline.py`

**Purpose:** Orchestrate post-arbitration analysis stages (4-6).

**Stages:** 4 (Cleanup), 5 (Agreement Analysis), 6 (Descriptive Stats)

**Usage:**
```bash
python 03_analysis_pipeline.py              # Run all stages
python 03_analysis_pipeline.py --stage 4    # Run specific stage
python 03_analysis_pipeline.py --stage 4-5  # Run stage range
python 03_analysis_pipeline.py --dry-run    # Show plan without executing
```

---

### 14. `04_findings_pipeline.py`

**Purpose:** Aggregate pair-level verdicts to question-level consolidability findings.

**Stage:** 4 - Findings

**Inputs:**
- `output/analysis/final_verdicts.csv` — Stage 3 verdicts (1,598 pairs)
- `data/cps_comparison_merged.csv` — CPS question mappings
- `data/foodaps_comparison_merged.csv` — FoodAPS question mappings

**Outputs:**
- `output/analysis/stage4_question_level.csv` — 380 questions with consolidability flags
- `output/analysis/stage4_survey_summary.json` — Aggregate rates (CPS 41.7%, FoodAPS 48.6%)
- `output/analysis/stage4_findings_report.md` — Pipeline-generated summary
- `output/analysis/stage4_topic_breakdown.csv` — By-topic consolidability
- `output/analysis/stage4_f2_transformations.csv` — F2 pairs needing statistical adjustment
- `output/analysis/stage4_barrier_patterns.csv` — F3 barrier distribution

**Usage:**
```bash
python 04_findings_pipeline.py
```

---

### 15. `05_deliverables_pipeline.py`

**Purpose:** Orchestrate scoring, rollup, expert review, and presentation deliverables.

**Stage:** 5 - Deliverables

**Sub-stages:**
- 5a: Scoring bake-off (`scripts/stage4_scoring_bakeoff.py`)
- 5b: Best-match rollup (`scripts/stage4_best_match_rollup.py`)
- 5c: Expert review tables (`scripts/build_expert_review_table.py`)
- 5d: Example pairs for presentation (`scripts/extract_example_pairs.py`)
- 5e: Sync visuals to presentation (built-in function)

**Usage:**
```bash
python 05_deliverables_pipeline.py              # Run all sub-stages
python 05_deliverables_pipeline.py --stage 5a   # Scoring only
python 05_deliverables_pipeline.py --stage 5b   # Best-match only
python 05_deliverables_pipeline.py --stage 5c   # Expert tables only
python 05_deliverables_pipeline.py --stage 5d   # Example pairs only
python 05_deliverables_pipeline.py --stage 5e   # Sync visuals only
python 05_deliverables_pipeline.py --dry-run    # Show plan without running
```

**Stage 5e Details:**
- Copies all PNG files from `output/visuals/` to `presentation/images/`
- Ensures presentation is self-contained with latest visuals
- Preserves original modification timestamps
- No script dependency — built-in Python function

---

### 16. `scripts/stage4_scoring_bakeoff.py`

**Purpose:** Compare 4 scoring methods for ranking consolidable pairs.

**Stage:** 5a - Scoring Bake-Off

**Methods:**
1. **Composite** — Feasibility × confidence weighted score
2. **Entropy** — Shannon entropy (inverted: low entropy = high agreement stability)
3. **Bayesian** — Beta-Binomial posterior with calibrated prior (0.197)
4. **Borda** — Normalized point sum from vote rankings
5. **Ensemble** — Average of all 4 normalized scores

**Inputs:**
- `output/analysis/final_verdicts.csv`
- `output/analysis/barrier_coding_merged_3rater.csv`

**Outputs:**
- `output/analysis/stage4_bakeoff_scores.csv` — 1,598 pairs with all scoring columns
- `output/analysis/stage4_bakeoff_correlations.csv` — Pairwise Spearman correlations
- `output/analysis/stage4_bakeoff_report.md` — Summary report
- `output/analysis/stage4_divergent_pairs.csv` — Pairs where methods disagree most
- `output/analysis/stage4_score_distributions.json` — Distributional summaries

**Key Finding:** Entropy is orthogonal to Borda/Bayesian (ρ≈0.08), motivating two-axis triage.

**Usage:**
```bash
python scripts/stage4_scoring_bakeoff.py
```

---

### 17. `scripts/stage4_best_match_rollup.py`

**Purpose:** Identify best ACS match per source question and assign triage quadrants.

**Stage:** 5b - Best-Match Rollup

**Logic:**
1. Join bakeoff scores with question mappings
2. Per source question, select best match (F1 > F2 > F3, then highest Borda)
3. Assign triage quadrant using two-axis framework:
   - Q1: High Borda + High Entropy (confident consolidable)
   - Q2: Low Borda + High Entropy (confident non-consolidable)
   - Q3: High Borda + Low Entropy (edge case — expert review)
   - Q4: Low Borda + Low Entropy (ambiguous — expert review)

**Inputs:**
- `output/analysis/stage4_bakeoff_scores.csv`
- `output/analysis/stage4_question_level.csv`
- `output/analysis/final_verdicts.csv`

**Outputs:**
- `output/analysis/stage4_question_best_matches.csv` — 380 rows with triage quadrants

**Triage Distribution:** Q1=151, Q2=136, Q3=40, Q4=53 (93 needing expert review = 24.5%)

**Usage:**
```bash
python scripts/stage4_best_match_rollup.py
```

---

### 18. `scripts/build_expert_review_table.py`

**Purpose:** Generate stakeholder-ready review tables with arbitrator reasoning.

**Stage:** 5c - Expert Review Tables

**Inputs:**
- `output/analysis/stage4_question_best_matches.csv`
- `output/analysis/final_verdicts.csv`
- `output/analysis/arbitration_merged.csv`

**Outputs:**
- `output/analysis/expert_review_combined.csv` — All 380 questions (17 columns)
- `output/analysis/expert_review_cps.csv` — CPS only (240 questions)
- `output/analysis/expert_review_foodaps.csv` — FoodAPS only (140 questions)
- `output/analysis/taxonomy_reference.md` — Barrier code definitions
- `output/analysis/classification_distribution.md` — Distribution summary

**Columns:** pair_id, source_survey, source_question_id, source_question_text, acs_question_id, acs_question_text, final_feasibility, final_barrier_code, confidence_level, score_borda, score_entropy, triage_quadrant, expert_review_needed, combined_reasoning, rater_agreement, topic, notes

**Sort Order:** Q3/Q4 first (need review), then Q1, then Q2.

**Usage:**
```bash
python scripts/build_expert_review_table.py
```

---

### 19. `scripts/extract_example_pairs.py`

**Purpose:** Extract compelling example question pairs for presentation materials. Selects high/medium/low consolidability examples with full question text, LLM reasoning, and barrier codes.

**Stage:** 5d - Presentation Materials

**Inputs:**
- `output/analysis/stage4_question_best_matches.csv`
- `output/analysis/arbitration_merged.csv`
- `data/cps_comparison_merged.csv`
- `data/foodaps_comparison_merged.csv`

**Outputs:**
- `output/analysis/example_pairs_for_presentation.md` — Formatted examples ready for slides
- `output/analysis/example_pairs_candidates.csv` — Top 5 candidates per category
- `output/analysis/example_pairs_README.md` — Usage guide

**Selection Criteria:**
- **High (F1):** Borda > 0.70, Entropy > 0.80, non-demographic content
- **Medium (F2):** Borda 0.40-0.70, shows transformation needs
- **Low (F3):** Borda < 0.30, CC barrier preferred, non-administrative

**Filters:** Excludes demographic questions (age, race, sex) and administrative/metadata questions for more compelling presentation examples.

**Usage:**
```bash
python scripts/extract_example_pairs.py
```

---

## Configuration

### `config.yaml`

**SINGLE SOURCE OF TRUTH** for all model names and parameters.

```yaml
raters:
  openai:
    model: 'gpt-5-mini'
    provider: 'openai'
    api_key_env: 'OPENAI_API_KEY'
  anthropic:
    model: 'claude-haiku-4-5-20251001'
    provider: 'anthropic'
    temperature: 0.0
  google:
    model: 'gemini-3-flash-preview'
    provider: 'google'
    temperature: 1.0  # MUST be 1.0 per Google docs

arbitrators:
  anthropic:
    model: 'claude-opus-4-5-20251101'
    temperature: 0.0
  openai:
    model: 'gpt-5.2'
    temperature: null  # OMIT param entirely
  google:
    model: 'gemini-3-pro-preview'
    temperature: 1.0

pipeline:
  max_tokens: 8192
  rating_max_workers: 6
  arbitration_max_workers: 3
  random_seed: 42

taxonomy:
  version: '1.1'
  categories: ['TC', 'CC', 'PC', 'RS', 'MC', 'PM', 'NHB']
```

---

## Environment Setup

### Required Environment Variables
```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GEMINI_API_KEY="..."  # or GOOGLE_API_KEY
```

### Python Dependencies
```
anthropic
openai
google-genai  # NOT google.generativeai (deprecated)
pandas
pydantic
tqdm
pyyaml
python-dotenv
matplotlib
seaborn
scikit-learn  # for confusion matrix
```

---

## Execution Order

### Full Pipeline (Recommended Order)

```bash
cd reports/03_harmonization_constraints

# 1. Rating Stage (run separately for isolation)
python 01_barrier_pipeline.py --rater openai
python 01_barrier_pipeline.py --rater anthropic
python 01_barrier_pipeline.py --rater google

# 2. Pre-Arbitration Analysis
python scripts/analyze_barrier_results.py
python scripts/confusion_matrix_analysis.py
# Review outputs, document in methodology_log.md

# 3. Arbitration Stage (run separately)
python 02_arbitration_pipeline.py --arbitrator anthropic
python 02_arbitration_pipeline.py --arbitrator openai
python 02_arbitration_pipeline.py --arbitrator google

# 3b. Post-Arbitration Analysis (orchestrated)
python 03_analysis_pipeline.py
# Or run stages individually:
# python scripts/clean_arbitration_data.py         # Cleanup
# python scripts/analyze_arbitration_agreement.py  # Agreement
# python scripts/descriptive_stats.py --stage all  # Stats

# 4. Findings Stage
python 04_findings_pipeline.py

# 5. Model Validation Visuals (must run BEFORE deliverables)
python scripts/stage4_model_validation_visuals.py

# 6. Deliverables Stage (requires Stage 4 + visuals)
python 05_deliverables_pipeline.py
# Or run sub-stages individually:
# python scripts/stage4_scoring_bakeoff.py         # 5a: Scoring
# python scripts/stage4_best_match_rollup.py       # 5b: Rollup
# python scripts/build_expert_review_table.py      # 5c: Expert tables

# Or run everything via orchestrator:
# python run_pipeline.py --stage all
```

---

## Checkpointing & Recovery

All long-running scripts checkpoint progress:
- `output/checkpoints/barrier_checkpoint_{rater}.json`
- `output/checkpoints/arbitration_v3_checkpoint_{arb}.json`

**To resume:** Just re-run the same command. Script loads checkpoint and skips processed pairs.

**To restart from scratch:** Delete the checkpoint file.

---

## Archived Outputs

`output_archive_gpt4omini_error/` contains outputs from a run that used wrong model name (gpt-4o-mini instead of gpt-5-mini). Preserved for reference but **do not use** for analysis.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-28 | Initial dual-model pipeline |
| 2.0 | 2026-01-29 | Config-driven, three raters, vendor-specific fixes |
| 3.0 | 2026-01-29 | Three arbitrators, blind masking, order randomization |
| 3.1 | 2026-01-30 | Analysis scripts modularized, lib/ created |
| 4.0 | 2026-01-31 | Stage 4 (findings) + Stage 5 (deliverables) complete, integrated into run_pipeline.py |

---

## Related Documentation

| Document | Purpose |
|----------|---------|
| `methodology_log.md` | Decision rationale (Decisions 001-013) + Pipeline Architecture |
| `taxonomy_v1.md` | Barrier taxonomy (v1.1 with NHB.0) |
| `coding_procedure.md` | Detailed coding rules |
| `docs/pipeline_diagram.md` | Pipeline data flow diagram (methodology communication) |
| `docs/FINDINGS_R03_S4_consolidability_analysis.md` | Formal Stage 4 findings document |
| `docs/stage4_research_framing.md` | Stage 4 research question framing |
| `docs/stage4_ensemble_methodology.md` | Ensemble scoring theory (entropy, Bayesian, Borda) |
| `docs/ANALYSIS_VV_PLAN.md` | Validation & verification plan and status |
| `barrier_coding_pipeline_documentation.md` | Legacy pipeline docs (v1.0) |
| `HANDOFF.md` | Session handoff notes |

---

## TODO / Known Issues

1. `scripts/compare_arbitrators.py` — May need updates for v3.0 output schema
2. `scripts/post_arbitration_analysis.py` — Verify works with three-arbitrator outputs
3. `scripts/analyze_agreement.py` — Verify not redundant with analyze_barrier_results.py
4. `scripts/stage4_triage_assignment.py` — Pair-level triage script, superseded by `stage4_best_match_rollup.py` (question-level). Kept for reference.
