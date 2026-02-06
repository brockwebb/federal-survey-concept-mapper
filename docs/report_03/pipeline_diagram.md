# Report 03: Analysis Pipeline Data Flow

*Updated: 2026-01-31 (v4.0)*

## Overview Diagram

```mermaid
flowchart TD
    subgraph Input["Input Data"]
        IN["1,598 question pairs<br/>(CPS 958 + FoodAPS 640)<br/>from Report 02"]
    end

    subgraph Stage1["Stage 1: Three-Model Rating"]
        S1_PROC["3 raters classify each pair<br/>Anthropic haiku · OpenAI gpt-5-mini · Google gemini-3-flash"]
        S1_CLEAN["clean_rater_data.py<br/>Dedupe, validate, merge"]
        S1_OUT["barrier_coding_merged_3rater.csv<br/>3 ratings per pair"]
        S1_PROC --> S1_CLEAN --> S1_OUT
    end

    subgraph Stage2["Stage 2: Inter-Rater Agreement"]
        S2_PROC["03_stage2_agreement.py<br/>03b_stage2_extended.py"]
        S2_OUT["Agreement metrics<br/>κ = 0.845 feasibility<br/>Confusion matrices"]
        S2_PROC --> S2_OUT
    end

    subgraph Stage3["Stage 3: Three-Arbitrator Adjudication"]
        S3_PROC["3 arbitrators review ALL pairs<br/>Anthropic opus · OpenAI gpt-5.2 · Google gemini-3-pro<br/>Blind masking + order randomization"]
        S3_CLEAN["clean_arbitration_data.py<br/>Dedupe, validate, merge"]
        S3_ANALYSIS["04_stage3_arbitration.py<br/>Agreement, bias, verdicts"]
        S3_QC["qc_stage3_arbitration.py<br/>11-check QC validation"]
        S3_OUT["final_verdicts.csv<br/>1,598 pairs with consensus classification"]
        S3_PROC --> S3_CLEAN --> S3_ANALYSIS --> S3_QC --> S3_OUT
    end

    subgraph Stage4["Stage 4: Question-Level Findings"]
        S4_PROC["04_findings_pipeline.py<br/>Pair → question aggregation"]
        S4_OUT["stage4_question_level.csv<br/>380 questions<br/>CPS 41.7% · FoodAPS 48.6% consolidable"]
        S4_PROC --> S4_OUT
    end

    subgraph Stage5["Stage 5: Deliverables"]
        S5A["5a: stage4_scoring_bakeoff.py<br/>Composite · Entropy · Bayesian · Borda"]
        S5B["5b: stage4_best_match_rollup.py<br/>Best ACS match + triage quadrant"]
        S5C["5c: build_expert_review_table.py<br/>Expert review tables"]
        S5_OUT["expert_review_combined.csv<br/>380 rows, 17 columns<br/>Q1=151 · Q2=136 · Q3=40 · Q4=53"]
        S5A --> S5B --> S5C --> S5_OUT
    end

    Input --> Stage1
    Stage1 --> Stage2
    Stage1 --> Stage3
    Stage2 -.->|"informs methodology<br/>(not a data dependency)"| Stage3
    Stage3 --> Stage4
    Stage4 --> Stage5
```

## Pipeline Orchestration

```mermaid
flowchart LR
    subgraph Orchestrators
        RP["run_pipeline.py<br/>(all stages)"]
        AP["03_analysis_pipeline.py<br/>(post-arbitration)"]
        DP["05_deliverables_pipeline.py<br/>(5a → 5b → 5c)"]
    end

    RP --> |"--stage rate"| S1["01_barrier_pipeline.py"]
    RP --> |"--stage arbitrate"| S3["02_arbitration_pipeline.py"]
    RP --> |"--stage analyze"| AP
    RP --> |"--stage findings"| S4["04_findings_pipeline.py"]
    RP --> |"--stage deliverables"| DP
```

## Stage Descriptions

### Stage 1: Three-Model Barrier Classification

**Script:** `01_barrier_pipeline.py`

**Input:** 1,598 question pairs from Report 02 (CPS-ACS and FoodAPS-ACS comparisons).

**Process:** Each pair is independently classified by three LLMs using identical prompts and the v1.1 barrier taxonomy (7 L1 categories, 22 L2 subcodes). Models assign:
- Primary harmonization barrier code (e.g., CC.1, TC.2, NHB.0)
- Feasibility rating (F1: directly consolidable, F2: with transformation, F3: not consolidable)
- Confidence score and reasoning

**Post-processing:** `clean_rater_data.py` deduplicates checkpoint restarts, validates schema, recodes null barriers to NHB.0, and merges into `barrier_coding_merged_3rater.csv`.

**Output:** Three independent ratings per pair.

---

### Stage 2: Inter-Rater Agreement Analysis

**Scripts:** `03_stage2_agreement.py`, `03b_stage2_extended.py`

**Input:** Merged rater results from Stage 1.

**Process:** Compute inter-rater reliability at multiple levels:
- Pairwise Cohen's Kappa (L1, full code, feasibility)
- Three-way Fleiss' Kappa
- Confusion matrices for systematic disagreement patterns
- Per-rater distribution analysis

**Output:** `stage2_agreement_metrics.json`, `stage2_agreement_report.md`, confusion matrices. Key result: feasibility κ = 0.845.

**Supporting scripts:** `analyze_barrier_results.py`, `confusion_matrix_analysis.py`, `analyze_agreement.py`

---

### Stage 3: Three-Arbitrator Adjudication

**Script:** `02_arbitration_pipeline.py`

**Input:** Three rater outputs from Stage 1. All 1,598 pairs are arbitrated (not just disagreements).

**Process:**
1. Blind masking: Raters shown as "Rater A/B/C" (identity hidden from arbitrators)
2. Order randomization: 50% fixed order, 50% randomized (position bias detection)
3. Three arbitrators independently review each pair with full question text and all rater reasoning
4. Post-processing: `clean_arbitration_data.py` deduplicates and merges
5. Analysis: `04_stage3_arbitration.py` computes agreement, bias, and constructs final verdicts via majority vote
6. QC: `qc_stage3_arbitration.py` runs 11 validation checks

**Output:** `final_verdicts.csv` — 1,598 pairs with consensus feasibility, barrier code, and confidence level.

**Supporting scripts:** `analyze_arbitration_agreement.py`, `compare_arbitrators.py`, `extract_low_confidence_pairs.py`

---

### Stage 4: Question-Level Consolidability Findings

**Script:** `04_findings_pipeline.py`

**Input:** `final_verdicts.csv` + question mappings from `data/`.

**Process:**
1. Join verdicts with question metadata (source survey, topic, question text)
2. Aggregate pairs → questions: "Does this source question have ANY consolidable ACS match?"
3. Compute per-survey consolidability rates
4. Analyze by topic and barrier category
5. Inventory F2 pairs needing statistical transformation

**Output:**
- `stage4_question_level.csv` — 380 questions (240 CPS + 140 FoodAPS) with consolidability flags
- `stage4_survey_summary.json` — CPS 41.7%, FoodAPS 48.6% consolidable
- `stage4_findings_report.md`, `stage4_topic_breakdown.csv`, `stage4_f2_transformations.csv`, `stage4_barrier_patterns.csv`

---

### Stage 5: Deliverables

**Orchestrator:** `05_deliverables_pipeline.py`

#### 5a: Scoring Bake-Off
**Script:** `scripts/stage4_scoring_bakeoff.py`

Compares 4 scoring methods for ranking consolidability confidence:
- **Composite:** Feasibility × confidence weighted score
- **Entropy:** Shannon entropy (inverted — low entropy = stable agreement)
- **Bayesian:** Beta-Binomial posterior (calibrated prior = 0.197)
- **Borda:** Normalized point sum from vote rankings

Key finding: Entropy is orthogonal to vote-count methods (ρ ≈ 0.08), providing an independent axis.

#### 5b: Best-Match Rollup
**Script:** `scripts/stage4_best_match_rollup.py`

Per source question, identifies the best ACS match (F1 > F2 > F3, then highest Borda). Assigns triage quadrant using two-axis framework:

| Quadrant | Borda | Entropy | Count | Action |
|----------|-------|---------|-------|--------|
| Q1 | High | High | 151 | Auto-accept (confident consolidable) |
| Q2 | Low | High | 136 | Auto-reject (confident non-consolidable) |
| Q3 | High | Low | 40 | Expert review (edge case) |
| Q4 | Low | Low | 53 | Expert review (ambiguous) |

93 questions (24.5%) flagged for expert review.

#### 5c: Expert Review Tables
**Script:** `scripts/build_expert_review_table.py`

Generates stakeholder-ready tables with 17 columns including question text, classifications, scores, triage quadrant, and combined arbitrator reasoning. Sorted with Q3/Q4 first.

**Output:** `expert_review_combined.csv`, `expert_review_cps.csv`, `expert_review_foodaps.csv`, `taxonomy_reference.md`, `classification_distribution.md`
