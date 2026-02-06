# Methodology

<!-- Pull from: docs/pipeline_diagram.md, docs/stage4_ensemble_methodology.md -->

## Overview

We developed a 5-stage pipeline for AI-assisted survey harmonization analysis. The pipeline characterizes harmonization potential across federal surveys, identifying bridge variables for cross-survey data enrichment and characterizing linkage quality constraints that define where cross-survey integration is viable.

```
Stage 1: Rating (3-model ensemble)
   ↓
Stage 2: Agreement Analysis (inter-rater reliability)
   ↓
Stage 3: Arbitration (disagreement resolution)
   ↓
Stage 4: Question-Level Rollup (best-match + triage)
   ↓
Stage 5: Deliverables (expert review tables)
```

All code is available in `reports/03_harmonization_constraints/scripts/`.

---

## Stage 1: Rating

<!-- Pull from: docs/SPEC_R03_S2_001_agreement_analysis.md -->

### Objective
Classify 1,598 question pairs using harmonization framework (F1/F2/F3 + barrier codes).

### Multi-Model Ensemble

We employed three frontier LLMs as independent raters:

| Model | Version | Behavior Profile |
|-------|---------|------------------|
| **OpenAI** | gpt-4o-mini | Moderate synthesis, slight self-consistency bias |
| **Anthropic** | claude-3-5-haiku-20241022 | High synthesis, neutral |
| **Google** | gemini-2.0-flash-exp | Deferential, conservative |

**Why three models?**
- Reduces single-model bias
- Different training data and architectures
- Behavioral diversity improves coverage

### Prompt Design

Each model received:
1. **Harmonization framework definitions** (F1/F2/F3)
2. **Barrier taxonomy** (CC, TC, RS, PC, MC, PM)
3. **Question pair** (source + target text)
4. **Task**: Classify feasibility + provide reasoning

**Output format** (structured JSON):
```json
{
  "feasibility": "F1|F2|F3",
  "barrier_code": "CC.1|TC.2|..." (if F3),
  "confidence": "HIGH|MODERATE|LOW",
  "reasoning": "Explanation..."
}
```

### Execution

- **Parallel processing**: 6 workers per model
- **Batch size**: 10 question pairs per API call
- **Error handling**: Exponential backoff for rate limits
- **Checkpointing**: Resume capability for interrupted runs
- **Output**: `output/results/stage1_{model}_results.jsonl`

### Data Quality

| Metric | OpenAI | Anthropic | Google |
|--------|--------|-----------|--------|
| **Pairs rated** | 1,598 | 1,598 | 751 (47%) |
| **Success rate** | 100% | 100% | 47% |
| **Avg confidence** | 0.89 | 0.91 | 0.87 |

**Note**: Google rate-limited at 751 pairs. Remaining analysis uses OpenAI-Anthropic two-way comparison with Google as validation subset.

---

## Stage 2: Agreement Analysis

<!-- Pull from: docs/FINDINGS_R03_S2_agreement_analysis.md -->

### Objective
Quantify inter-rater reliability and identify disagreements for arbitration.

### Metrics Calculated

#### Cohen's Kappa (Pairwise)
- **OpenAI-Anthropic**: κ = 0.845 (almost perfect)
- **OpenAI-Google**: κ = 0.796 (substantial)
- **Anthropic-Google**: κ = 0.833 (almost perfect)

#### Fleiss' Kappa (Three-Way)
- **All three models** (751 pairs with Google): κ = 0.833

**Interpretation**: High agreement validates that harmonization judgments are consistent across models, even with different architectures and training data.

### Agreement Patterns

| Level | OpenAI-Anthropic | Description |
|-------|------------------|-------------|
| **Topic (L1)** | 91.2% | High-level feasibility |
| **Subtopic (L2)** | 84.5% | Barrier category |
| **Full code** | 78.9% | Complete barrier sub-code |

**Finding**: Models agree more on broad feasibility than specific barrier codes, consistent with hierarchical classification difficulty.

### Disagreement Identification

- **Pairs needing arbitration**: 339 (21.2% of 1,598)
- **Criteria**: OpenAI ≠ Anthropic on feasibility or barrier code
- **Output**: `output/analysis/arbitration_candidates.csv`

---

## Stage 3: Arbitration

<!-- Pull from: docs/FINDINGS_R03_S3_001_arbitration_analysis.md -->

### Objective
Resolve disagreements through higher-capability model arbitration.

### Arbitration Models

| Model | Version | Role |
|-------|---------|------|
| **OpenAI** | gpt-4o | Arbitrator (stronger than rater) |
| **Anthropic** | claude-3-5-sonnet-20241022 | Arbitrator |
| **Google** | gemini-2.0-flash-thinking-exp | Arbitrator (experimental reasoning) |

### Arbitration Prompt

Arbitrators received:
1. **Source and target question text**
2. **Initial ratings** from 2-3 raters (with reasoning)
3. **Disagreement summary**
4. **Task**: Provide final verdict with detailed justification

### Voting Logic

When arbitrators disagree, final verdict determined by:
1. **Majority vote** (if 2+ agree)
2. **Borda count** (ranked preference if no majority)
3. **Entropy check** (flag high disagreement for expert review)

### Arbitration Results

| Metric | Value |
|--------|-------|
| **Pairs arbitrated** | 339 |
| **Arbitrator agreement** | 87.6% |
| **Confidence distribution** | HIGH: 68%, MODERATE: 24%, LOW: 8% |

**Quality check** (11 validation tests): ✅ All passed

### Behavioral Findings

- **OpenAI**: Tends toward F2 when uncertain (optimistic about statistical adjustment)
- **Anthropic**: Balanced, detailed reasoning
- **Google**: Conservative, often defers to initial raters

**See**: `docs/FINDINGS_R03_S3_001_arbitration_analysis.md` for detailed behavioral analysis.

---

## Stage 4: Question-Level Rollup

<!-- Pull from: docs/stage4_ensemble_methodology.md, docs/stage4_research_framing.md -->

### Objective
Convert 1,598 pair-level results to 380 question-level consolidability assessments with triage.

### Challenge: Pair-Level Inflation

Each of 380 source questions was compared against multiple ACS questions:
- **Average**: 4.2 comparisons per question
- **Range**: 1-12 comparisons per question
- **Problem**: One F1 match makes a question consolidable, even if 11 other comparisons failed

**Solution**: Best-match rollup + two-axis triage.

### Best-Match Selection

For each source question:
1. Identify all pairs involving that question
2. Select pair with highest consolidability:
   - F1 > F2 > F3 (feasibility hierarchy)
   - Within same feasibility, highest Borda score
3. Output: One best match per question

**Result**: 380 question-level records with best ACS match.

### Scoring Methods (Ensemble Approach)

We computed four complementary scores for each pair:

#### 1. Composite Score (Baseline)
```
score = {
  1.0 if unanimous F1/F2,
  0.5 if majority F1/F2,
  0.0 if unanimous F3,
  NA otherwise
}
```

#### 2. Entropy Score (Stability)
```
H = -Σ p(x) log₂ p(x)
normalized to [0, 1]
```
- Low entropy = high agreement (stable)
- High entropy = disagreement (unstable)

#### 3. Bayesian Score (Probabilistic)
```
P(consolidable | ratings) = (positives + α) / (total + α + β)
```
- Incorporates prior beliefs
- Shrinks toward population mean

#### 4. Borda Count (Direction)
```
Borda = Σ ranks / max_possible_ranks
```
- F1 = 2 points, F2 = 1 point, F3 = 0 points
- Captures direction of ensemble

### Two-Axis Triage Framework

<!-- Key methodological contribution -->

**Purpose**: Separate "what's the answer?" (Borda) from "how much did they argue?" (Entropy).

**Thresholds**: Median split on question-level best-match scores
- Borda median: 0.167
- Entropy median: 0.330

**Why question-level medians?**
- Pair-level distribution dominated by unanimous F3 pairs (median ≈ 0)
- Question-level reflects actual decision space for triage
- N=380 questions, not N=1,598 pairs

**Quadrant Definitions**:

| Quadrant | Borda | Entropy | Interpretation | Action |
|----------|-------|---------|----------------|--------|
| **Q1** | High | High | Confident consolidable | Auto-accept, spot-check |
| **Q2** | Low | High | Confident non-consolidable | Auto-reject, low priority |
| **Q3** | High | Low | Uncertain accept (leaning yes but contested) | **Expert review priority** |
| **Q4** | Low | Low | Uncertain reject (genuinely ambiguous) | Expert review secondary |

**Rationale**:
- Q1 (High Borda, High Entropy): Models agree it's consolidable → trust
- Q2 (Low Borda, High Entropy): Models agree it's not consolidable → trust
- Q3 (High Borda, Low Entropy): Leaning yes but unstable → expert validate
- Q4 (Low Borda, Low Entropy): Unclear direction → expert clarify

### Triage Assignment Results

| Quadrant | Count | % | Description |
|----------|-------|---|-------------|
| Q1 | 151 | 39.7% | Auto-accept (confident consolidable) |
| Q2 | 136 | 35.8% | Auto-reject (confident non-consolidable) |
| Q3 | 40 | 10.5% | Expert review (uncertain accept) |
| Q4 | 53 | 13.9% | Expert review (uncertain reject) |

**Expert review load**: 24.5% (93 of 380 questions)

---

## Stage 5: Deliverables

### Objective
Generate stakeholder-ready outputs for expert review and implementation.

### Expert Review Tables

Three CSV files generated:
1. **`expert_review_cps.csv`** (240 CPS questions)
2. **`expert_review_foodaps.csv`** (140 FoodAPS questions)
3. **`expert_review_combined.csv`** (380 questions, all surveys)

**Columns included**:
- Source question text
- Best ACS match text
- Feasibility (F1/F2/F3)
- Barrier code (if F3)
- Borda score (direction)
- Entropy score (stability)
- Triage quadrant (Q1-Q4)
- Confidence flags
- Reasoning summary

### Visualizations

All figures saved to `output/visuals/`:
- **Consolidation rates** by survey (bar chart)
- **Barrier distribution** (pie chart)
- **Expert review load** (stacked bar)
- **Triage quadrant heatmap**
- **Harmonization code distribution** (pair-level)
- **Question consolidation distribution** (question-level by survey)

### Summary Statistics

`output/analysis/stage4_survey_summary.json`:
```json
{
  "CPS": {
    "total": 240,
    "consolidable": 100,
    "rate": 0.417
  },
  "FoodAPS": {
    "total": 140,
    "consolidable": 68,
    "rate": 0.486
  }
}
```

---

## Quality Assurance

### Validation Checks

All pipeline stages include automated validation:
1. **Data completeness**: No missing required fields
2. **Schema compliance**: Output matches expected format
3. **Logical consistency**: No F1/F2 pairs with barrier codes
4. **Agreement metrics**: Kappa > 0.75 threshold
5. **Rollup integrity**: Every question has exactly one best match

**See**: `docs/ANALYSIS_VV_PLAN.md` for complete V&V checklist.

### Reproducibility

All analysis scripts are deterministic and produce identical results when re-run:
- Fixed random seeds
- Checkpoint/resume capability
- Version-controlled prompts
- Documented model versions

---

## Methodological Limitations

### 1. Model Selection
- Only three frontier models tested
- Results may differ with other models
- Behavioral profiles may change with model updates

### 2. Prompt Engineering
- Structured prompts guide but don't guarantee consistency
- Different prompt phrasings could yield different results
- No systematic prompt optimization performed

### 3. Barrier Taxonomy Application
- Models apply human-designed taxonomy, not discovered patterns
- Taxonomy completeness not validated empirically
- Some pairs may have multiple applicable codes (we select primary)

### 4. Triage Framework
- Two-axis approach is operational heuristic, not theoretical optimum
- Threshold selection (median split) is pragmatic, not optimized
- Quadrant interpretation requires domain context

### 5. Scope
- Only CPS and FoodAPS analyzed (not full federal survey ecosystem)
- Only ACS as target (other surveys could serve as consolidation targets)
- English-language surveys only

---

## Next Steps After This Report

1. **Expert validation**: Subject-matter experts review Q3/Q4 questions
2. **Consolidation pilots**: Test F1 recommendations in practice
3. **Expansion**: Apply methodology to additional survey pairs
4. **Refinement**: Incorporate expert feedback to improve classification

**Key principle**: AI assists, experts decide. This methodology accelerates analysis but does not replace human judgment.
