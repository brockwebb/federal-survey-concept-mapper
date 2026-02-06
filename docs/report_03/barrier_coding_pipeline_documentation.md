# Dual-Model Barrier Coding Pipeline with Arbitration

## Overview

This document describes the complete pipeline for barrier coding of non-consolidatable survey question pairs using dual-model classification with third-model arbitration. The approach provides built-in inter-rater reliability metrics and principled resolution of disagreements.

**Pipeline Version:** 1.0  
**Report:** 03 - Harmonization Constraints  
**Date:** 2026-01-29

---

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BARRIER CODING PIPELINE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │   Phase 1    │───▶│   Phase 2    │───▶│   Phase 3    │                   │
│  │ Dual-Model   │    │  Agreement   │    │ Arbitration  │                   │
│  │   Coding     │    │  Analysis    │    │  (if needed) │                   │
│  └──────────────┘    └──────────────┘    └──────────────┘                   │
│         │                   │                   │                            │
│         ▼                   ▼                   ▼                            │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │   Phase 4    │◀───│   Outputs    │◀───│   Phase 5    │                   │
│  │   Final      │    │              │    │  Validation  │                   │
│  │  Compilation │    │              │    │   & QC       │                   │
│  └──────────────┘    └──────────────┘    └──────────────┘                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Dual-Model Coding

### Purpose
Classify each non-consolidatable question pair with barrier type and feasibility code using two independent LLM models.

### Script
`barrier_coding_pipeline.py`

### Models Used
- **Model A:** gpt-4o-mini (OpenAI)
- **Model B:** claude-haiku-4-5-20251001 (Anthropic)

### Input
- `data/cps_comparison_merged.csv` - CPS vs ACS question pairs
- `data/foodaps_comparison_merged.csv` - FoodAPS vs ACS question pairs

Filter: Pairs classified as non-consolidatable in Report 02 analysis.

### Output
- `output/results/barrier_results_openai.jsonl`
- `output/results/barrier_results_claude.jsonl`

### Coding Schema

**Level 1 Barrier Types:**
| Code | Type | Definition |
|------|------|------------|
| TC | Temporal | Reference period or timing differences |
| CC | Construct | Concept definition or operationalization differences |
| PC | Population/Coverage | Universe, frame, or sample design differences |
| RS | Response Scale | Scale type, categories, or format differences |
| MC | Mode/Context | Interview mode or questionnaire context differences |
| PM | Processing/Metadata | Coding, weighting, or documentation differences |

**Level 2 Subtypes:** See `taxonomy_v1.md` for complete subtype definitions.

**Feasibility Codes:**
| Code | Feasibility | Definition |
|------|-------------|------------|
| F1 | Direct recode | Mechanically transformable |
| F2 | Statistical adjustment | Requires modeling or assumptions |
| F3 | Incompatible | Fundamentally different, not harmonizable |

### Configuration
```python
BATCH_SIZE = 10
MAX_WORKERS = 6  # Parallel API calls per model
CHECKPOINT_INTERVAL = 10  # Save progress every N pairs
```

### Run Command
```bash
cd reports/03_harmonization_constraints
python barrier_coding_pipeline.py
```

### Runtime
~15-20 minutes for 1,598 pairs (both models)

### Cost
~$0.50-1.00 total (economical model tier)

---

## Phase 2: Agreement Analysis

### Purpose
Merge model outputs, compute inter-rater reliability metrics, and generate confusion matrices to understand disagreement patterns.

### Script
`analyze_barrier_results.py` → `confusion_matrix_analysis.py`

### Metrics Computed

**Agreement Rates:**
- Level 1 barrier agreement (%)
- Full barrier code agreement (L1 + L2) (%)
- Feasibility agreement (%)

**Cohen's Kappa:**
- Accounts for chance agreement
- Interpretation: <0.20 poor, 0.21-0.40 fair, 0.41-0.60 moderate, 0.61-0.80 substantial, >0.80 near-perfect

**Note on Kappa Paradox:**
When one category dominates (e.g., 79% CC), kappa can appear low even with high raw agreement because expected chance agreement is also high. Always interpret kappa alongside raw agreement and class distribution.

### Output Files
- `output/analysis/barrier_coding_merged.csv` - Combined model results
- `output/analysis/barrier_coding_summary.json` - Agreement statistics
- `output/analysis/confusion_analysis/barrier_L1_confusion_matrix.png`
- `output/analysis/confusion_analysis/barrier_full_confusion_matrix.png`
- `output/analysis/confusion_analysis/feasibility_confusion_matrix.png`
- `output/analysis/confusion_analysis/*.csv` - Matrix data

### Run Command
```bash
python analyze_barrier_results.py
python confusion_matrix_analysis.py
```

### Key Analysis Questions
1. Are disagreements random or systematic?
2. Which L1 categories have highest confusion?
3. Do subcategory disagreements cluster within agreed L1 categories?
4. Is one model systematically more conservative/liberal?

---

## Phase 3: Arbitration

### Purpose
Resolve disagreements using a third, more capable model as tiebreaker.

### Script
`arbitration_pipeline.py`

### Arbitration Model
**claude-opus-4-5-20251101** (Anthropic's most capable model)

### Trigger Conditions
Arbitration is invoked when Model A and Model B disagree on:
- Full barrier code (L1.L2), OR
- Feasibility code

### Arbitration Prompt Structure
The arbitration model receives:
1. Original question pair texts
2. Model A's coding + reasoning
3. Model B's coding + reasoning
4. Full taxonomy reference
5. Coding rules (hierarchy for ambiguous cases)

### Arbitration Outcomes
| Source | Meaning |
|--------|---------|
| model_a | Opus selected OpenAI's coding |
| model_b | Opus selected Claude-Haiku's coding |
| synthesis | Opus provided a different coding than either model |

### Output
- `output/analysis/confusion_analysis/arbitration_results.jsonl`
- Checkpoint: `output/arbitration_checkpoint.json`

### Run Command
```bash
python arbitration_pipeline.py
```

### Configuration
```python
BATCH_SIZE = 5  # Smaller for expensive model
MAX_WORKERS = 3  # Conservative for rate limits
RATE_LIMIT_DELAY = 0.5  # Seconds between calls
```

### Runtime
~15-25 minutes for ~900 disagreement pairs

### Cost
~$3-5 (opus pricing)

---

## Phase 4: Final Compilation

### Purpose
Merge arbitration results with original codings to produce final classified dataset.

### Logic
```
For each pair:
    IF Model A == Model B:
        final_code = agreed_value
    ELSE:
        final_code = arbitrated_value
```

### Output
- `output/analysis/confusion_analysis/barrier_coding_final.csv`

### Final Dataset Schema
| Column | Description |
|--------|-------------|
| pair_id | Unique identifier |
| survey_text | Original survey question |
| acs_text | ACS comparison question |
| primary_barrier_openai | Model A barrier code |
| primary_barrier_claude | Model B barrier code |
| feasibility_openai | Model A feasibility |
| feasibility_claude | Model B feasibility |
| final_barrier | Resolved barrier code |
| final_feasibility | Resolved feasibility |
| final_barrier_L1 | Resolved L1 category |
| arbitration_source | model_a / model_b / synthesis / NULL (if agreed) |
| arbitration_reasoning | Opus explanation (if arbitrated) |

---

## Phase 5: Validation & Quality Control

### Automated Checks
1. **Completeness:** All pairs have final codes
2. **Valid codes:** All codes match taxonomy
3. **Consistency:** L1 matches L1.L2 prefix

### Distribution Sanity Checks
- Compare pre/post arbitration distributions
- Flag if arbitration drastically shifts distribution (suggests systematic model bias)

### Manual Spot-Check (Recommended)
- Review 5-10 arbitrated cases per L1 category
- Verify opus reasoning aligns with taxonomy definitions
- Document any taxonomy ambiguities discovered

---

## Complete Execution Sequence

```bash
# Navigate to report directory
cd reports/03_harmonization_constraints

# Phase 1: Dual-model coding
python barrier_coding_pipeline.py

# Phase 2: Agreement analysis
python analyze_barrier_results.py
python confusion_matrix_analysis.py

# Review confusion matrices before proceeding
# Decision point: Is arbitration needed? (Check methodology_log.md)

# Phase 3: Arbitration (if disagreements exist)
python arbitration_pipeline.py

# Phase 4: Final compilation (built into arbitration_pipeline.py)
# Output: barrier_coding_final.csv

# Phase 5: Validation
python validate_final_results.py  # TODO: Create if needed
```

---

## Methodology Justification

### Why Dual-Model?
1. **Built-in reliability:** Agreement rate = inter-rater reliability without human coding
2. **Disagreement = ambiguity:** Flags genuinely difficult cases
3. **Cost-effective:** Cheaper than human coders for large N
4. **Reproducible:** Same inputs → same outputs

### Why Third-Model Arbitration?
1. **Principled resolution:** Not arbitrary (vs. "trust Model A")
2. **Quality upgrade:** Opus is more capable than haiku/mini
3. **Documented reasoning:** Every arbitration has justification
4. **Methodological consistency:** Same approach as Report 02

### Why Not Conservative Default?
Default to majority class (CC) would:
- Inflate already-dominant category (79% → 87%)
- Mask real TC/RS cases the analysis aims to surface
- Reduce taxonomy validity

Cost of arbitration (~$5) is trivial vs. methodological compromise.

---

## Reproducibility Checklist

- [ ] Environment: Python 3.9+, packages in requirements.txt
- [ ] API keys: ANTHROPIC_API_KEY, OPENAI_API_KEY in .env
- [ ] Input data: CPS and FoodAPS merged comparison files
- [ ] Taxonomy: taxonomy_v1.md unchanged
- [ ] Random seed: N/A (deterministic prompts, temperature=0)

---

## References

- `methodology_log.md` - Decision rationale documentation
- `coding_procedure.md` - Detailed coding rules and examples
- `taxonomy_v1.md` - Full barrier taxonomy definitions
- Report 02 pipeline for precedent on dual-model approach
