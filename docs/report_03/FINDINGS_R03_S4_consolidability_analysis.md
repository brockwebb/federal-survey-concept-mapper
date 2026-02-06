# Stage 4 Findings: Consolidability Analysis

**Document:** `FINDINGS_R03_S4_consolidability_analysis.md`
**Date:** 2026-01-31
**Status:** COMPLETE
**Inputs:** `output/analysis/final_verdicts.csv`, `stage4_question_best_matches.csv`, `stage4_bakeoff_scores.csv`

---

## Executive Summary

Of 380 unique source survey questions (240 CPS, 140 FoodAPS), **168 (44.2%) have at least one consolidable path to ACS** — meaning a feasibility rating of F1 (direct recode) or F2 (statistical adjustment). CPS consolidability is 41.7% and FoodAPS is 48.6%. Pair-level rates (~20%) significantly understate this potential because each source question is paired with multiple irrelevant ACS questions.

A two-axis triage framework (Borda direction × Entropy stability) classifies 76% of questions as high-confidence decisions (Q1 + Q2), with 24% flagged for expert review (Q3 + Q4).

---

## 1. Research Questions Addressed

| Question | Finding |
|----------|---------|
| What proportion of source questions can consolidate with ACS? | 44.2% overall (41.7% CPS, 48.6% FoodAPS) |
| Which specific ACS questions match each source question? | Best-match rollup in `stage4_question_best_matches.csv` |
| How confident are we in each mapping? | 4-method scoring bake-off + triage quadrant assignment |

---

## 2. Question-Level Consolidation Rates

### 2.1 Overall

| Survey | Total Questions | Consolidable | Rate |
|--------|---------------:|-------------:|-----:|
| CPS | 240 | 100 | 41.7% |
| FoodAPS | 140 | 68 | 48.6% |
| **Total** | **380** | **168** | **44.2%** |

### 2.2 Quality of Consolidation Paths

| Feasibility | CPS | FoodAPS | Total | Meaning |
|-------------|----:|--------:|------:|---------|
| F1 (Direct Recode) | 37 (15.4%) | 23 (16.4%) | 60 (15.8%) | Mechanically transformable |
| F2 (Statistical Adjustment) | 63 (26.2%) | 45 (32.1%) | 108 (28.4%) | Requires modeling/assumptions |
| F3 (Not Consolidable) | 140 (58.3%) | 72 (51.4%) | 212 (55.8%) | No viable path |

### 2.3 Pair-Level vs Question-Level Comparison

| Survey | Pair-Level Rate | Question-Level Rate | Pairs | Questions |
|--------|:-:|:-:|--:|--:|
| CPS | 19.2% | 41.7% | 1,030 | 240 |
| FoodAPS | 20.6% | 48.6% | 568 | 140 |

Pair-level rates understate consolidation potential because each source question is paired with multiple ACS questions, most of which are topically unrelated (e.g., a food security question paired with a commuting question). The question-level metric — "does this source question have at least one viable ACS match?" — is the stakeholder-relevant answer.

---

## 3. Triage Framework

### 3.1 Two-Axis Scoring

Four scoring methods were tested in a bake-off:

| Method | What It Measures | Correlation with Others |
|--------|-----------------|------------------------|
| Composite | Feasibility × confidence (simple product) | Moderate (ρ=0.52–0.62) |
| Entropy | Vote agreement strength (Shannon entropy) | **Near-zero** with Bayesian/Borda (ρ≈0.08) |
| Bayesian | P(consolidable \| votes), Beta-Binomial | High with Borda (ρ=0.91) |
| Borda | Normalized point sum (F1=2, F2=1, F3=0) | High with Bayesian (ρ=0.91) |

**Key finding:** Entropy is empirically orthogonal to vote-count methods, providing an independent axis of information. This motivates a two-axis triage:
- **X-axis (Borda):** Direction — are classifiers saying consolidable or not?
- **Y-axis (Entropy):** Stability — do classifiers agree with each other?

See `docs/stage4_ensemble_methodology.md` for full methodology and sober assessment. The math is not novel; the operational utility is the contribution.

### 3.2 Quadrant Distribution

| Quadrant | Description | Count | % | Recommended Action |
|----------|-------------|------:|--:|-------------------|
| Q1 | High direction + High stability | 151 | 39.7% | Accept — confident consolidable |
| Q2 | Low direction + High stability | 136 | 35.8% | Reject — confident non-consolidable |
| Q3 | High direction + Low stability | 40 | 10.5% | Expert review — leaning yes, contested |
| Q4 | Low direction + Low stability | 53 | 13.9% | Expert review — genuinely ambiguous |

**Per-survey breakdown:**

| Survey | Q1 | Q2 | Q3 | Q4 |
|--------|---:|---:|---:|---:|
| CPS | 92 | 82 | 25 | 41 |
| FoodAPS | 59 | 54 | 15 | 12 |

75.5% of questions (Q1 + Q2) can be auto-triaged with high confidence. The remaining 24.5% (Q3 + Q4 = 93 questions) would benefit from expert review.

---

## 4. Barrier Analysis

### 4.1 Why Pairs Are Not Consolidable

Among F3 (not consolidable) pairs, construct/concept differences dominate:

| Barrier | CPS (n=832) | FoodAPS (n=451) |
|---------|:-:|:-:|
| CC (Construct/Concept) | 96.2% | 97.3% |
| TC (Temporal/Chronological) | 2.4% | 0.9% |
| RS (Response Scale) | 1.0% | 1.1% |
| PC (Population/Coverage) | 0.5% | 0.4% |
| MC (Mode/Context) | — | 0.2% |

The overwhelming dominance of CC is expected: most non-consolidable pairs are topically unrelated questions that were paired in the combinatorial matching step.

### 4.2 F2 Transformation Requirements

241 pairs rated F2 require statistical adjustment. The barrier types needing transformation:

| Barrier | CPS | FoodAPS | Total |
|---------|----:|--------:|------:|
| CC (Construct/Concept) | 71 | 61 | 132 |
| TC (Temporal/Chronological) | 57 | 24 | 81 |
| RS (Response Scale) | 16 | 2 | 18 |
| MC (Mode/Context) | 4 | 2 | 6 |
| PC (Population/Coverage) | 3 | — | 3 |
| PM (Policy/Market) | — | 1 | 1 |

Temporal and construct differences are the primary barriers requiring statistical bridging for F2 pairs.

---

## 5. Topic Analysis

### 5.1 Most Consolidable Topics (pair-level, ≥3 pairs, ≥50% rate)

| Survey | Subtopic | Consolidable/Total | Rate |
|--------|----------|-------------------:|-----:|
| CPS | Race | 9/9 | 100% |
| FoodAPS | Age | 5/5 | 100% |
| FoodAPS | Race | 6/6 | 100% |
| FoodAPS | Relationship | 5/5 | 100% |
| CPS | Age | 5/6 | 83% |
| CPS | Relationship | 20/27 | 74% |
| CPS | Occupation | 7/13 | 54% |
| CPS | Education | 2/4 | 50% |
| CPS | Hispanic Origin | 2/4 | 50% |

Demographic topics (race, age, relationship) consolidate at near-100% rates — these use standardized question formats across federal surveys. Economic and labor topics consolidate at lower rates due to survey-specific framing.

---

## 6. Burden Reduction Potential

If consolidable questions could be replaced by ACS equivalents:

| Survey | Questions Reducible | Total | Rate |
|--------|--------------------:|------:|-----:|
| CPS | 100 | 240 | 41.7% |
| FoodAPS | 68 | 140 | 48.6% |

**Caveats:**
- This is an upper bound; practical consolidation depends on use case, statistical precision requirements, and institutional constraints
- F2 questions require statistical adjustment methods (not simple substitution)
- Only 60 of 168 consolidable questions have F1 (direct recode) paths

---

## 7. Outputs Inventory

| File | Description | Rows |
|------|-------------|-----:|
| `stage4_question_level.csv` | Binary consolidable flag per question | 380 |
| `stage4_question_best_matches.csv` | Best ACS match + triage quadrant per question | 380 |
| `stage4_survey_summary.json` | Aggregate rates by survey | — |
| `stage4_bakeoff_scores.csv` | Pair-level scores from 4 methods + ensemble | 1,598 |
| `stage4_bakeoff_report.md` | Scoring method comparison | — |
| `stage4_bakeoff_correlations.csv` | 5×5 Spearman correlation matrix | — |
| `stage4_findings_report.md` | Pipeline-generated narrative summary | — |
| `stage4_topic_breakdown.csv` | Consolidation rates by subtopic | — |
| `stage4_f2_transformations.csv` | F2 pairs with barrier details | 241 |
| `stage4_barrier_patterns.csv` | F3 barrier distribution | — |
| `stage4_divergent_pairs.csv` | Top 20 pairs where methods disagree | 20 |
| `stage4_score_distributions.json` | Summary statistics per method | — |

---

## 8. Limitations

1. **Google arbitrator incomplete:** Only 503/1,598 pairs (31%) have Google data, all CPS. Scores use 5 votes for most pairs, 6 for the CPS subset with Google.
2. **Triage thresholds are empirical:** Median-based thresholds from this dataset, not externally validated. Q3/Q4 boundaries would shift with different data.
3. **No human validation of triage:** Q3 and Q4 items have not been reviewed by domain experts. The triage framework routes items but doesn't validate classifications.
4. **Question-level metric is binary:** A question is "consolidable" if ANY pair has F1/F2. This doesn't capture the quality or number of viable paths.
5. **CC barrier dominance may be artifact:** The combinatorial pairing includes many topically unrelated questions, inflating CC (construct difference) counts in F3.

---

## 9. Next Steps (Stage 5)

1. Generate stakeholder-ready outputs (prioritized lists by quadrant)
2. Create executive-friendly visualizations (V5: consolidation rates, V6: domain breakdown)
3. Route Q3/Q4 items for expert validation if resources permit
4. Produce methodology appendix for the formal report
