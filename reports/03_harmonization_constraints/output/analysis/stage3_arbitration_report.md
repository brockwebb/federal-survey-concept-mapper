# Stage 3 Arbitration Analysis Report

**Generated:** 2026-02-04T13:54:36.640014
**OpenAI pairs:** 1,598
**Anthropic pairs:** 1,598
**Google pairs:** 751

## 1. Executive Summary

- **Two-way (OA vs AN) L1 agreement:** 94.7% (κ=0.796)
- **Two-way feasibility agreement:** 94.7% (κ=0.843)
- **Two-way binary consolidability:** 96.7% (κ=0.896)
- **Three-way (CPS subset) L1 Fleiss' κ:** 0.843
- **Final verdicts:** 1,458 HIGH, 112 MODERATE, 28 LOW
- **Synthesis detection F1:** google=0.121, anthropic=0.885
- **Openai synthesis pattern:** backwards (unanimous: 64.0%, split: 40.1%)
- **Anthropic synthesis pattern:** backwards (unanimous: 86.7%, split: 37.9%)
- **Google synthesis pattern:** deferential (unanimous: 6.5%, split: 2.5%)

## 2. Inter-Arbitrator Agreement (Two-Way)

**Coverage:** 1,598 pairs (OpenAI + Anthropic)

| Metric | % Agreement | Cohen's κ | Interpretation | Quality Gate |
|--------|-------------|-----------|----------------|--------------|
| L1 | 94.7% | 0.796 | Substantial | NOT PASSED |
| full_barrier_code | 85.0% | 0.755 | Substantial | NOT PASSED |
| feasibility | 94.7% | 0.843 | Almost Perfect | PASSED |
| binary_consolidability | 96.7% | 0.896 | Almost Perfect | PASSED |

## 3. Inter-Arbitrator Agreement (Three-Way)

**Coverage:** 751 pairs (CPS only — Google limited)

### Three-Way Metrics

| Metric | Fleiss' κ | Krippendorff's α | Interpretation |
|--------|-----------|------------------|----------------|
| L1 | 0.843 | 0.843 | Almost Perfect |
| full_barrier_code | 0.733 | 0.733 | Substantial |
| feasibility | 0.864 | 0.864 | Almost Perfect |
| binary_consolidability | 0.893 | 0.893 | Almost Perfect |

### Pairwise L1 (Three-Way Subset)

| Comparison | % Agreement | Cohen's κ | Interpretation |
|------------|-------------|-----------|----------------|
| OA vs AN | 95.7% | 0.823 | Almost Perfect |
| OA vs GO | 95.3% | 0.807 | Almost Perfect |
| AN vs GO | 97.2% | 0.894 | Almost Perfect |

### Pairwise L2/Full Barrier Code (Three-Way Subset)

| Comparison | % Agreement | Cohen's κ | Interpretation |
|------------|-------------|-----------|----------------|
| OA vs AN | 83.6% | 0.692 | Substantial |
| OA vs GO | 82.7% | 0.673 | Substantial |
| AN vs GO | 91.3% | 0.835 | Almost Perfect |

## 4. Arbitrator-Rater Concordance

| Arbitrator | n | L1 vs Maj | L2 vs Maj | Feas vs Maj | L1 vs Unan | L2 vs Unan | Feas vs Unan | L1 Overrides | L2 Overrides |
|------------|---|-----------|-----------|-------------|------------|------------|--------------|--------------|--------------|
| openai | 1,598 | 92.1% | 83.5% | 93.4% | 96.7% | 94.9% | 98.7% | 42 / 1289 | 42 / 831 |
| anthropic | 1,598 | 95.6% | 93.7% | 96.7% | 99.8% | 99.5% | 100.0% | 3 / 1289 | 4 / 831 |
| google | 751 | 97.0% | 94.9% | 97.7% | 100.0% | 100.0% | 100.0% | 0 / 631 | 0 / 361 |

## 4b. Synthesis Behavior Analysis

**Question:** How does each arbitrator approach synthesis vs. single-rater selection?

| Arbitrator | n | Unanimous N | Unan Synth % | Split N | Split Synth % | Pattern | F1 |
|------------|---|-------------|--------------|---------|---------------|---------|-----|
| openai | 1,598 | 1,289 | 64.0% | 309 | 40.1% | backwards | 0.737 |
| anthropic | 1,598 | 1,289 | 86.7% | 309 | 37.9% | backwards | 0.885 |
| google | 751 | 631 | 6.5% | 120 | 2.5% | deferential | 0.121 |

**Pattern Interpretation:**
- *efficient*: Synthesizes only when raters disagree (ideal)
- *always_synthesizes*: Synthesizes regardless of rater agreement
- *deferential*: Rarely synthesizes, prefers to pick a rater
- *backwards*: Synthesizes more when raters agree than disagree (problematic)
- *moderate*: No strong pattern

## 5. Bias Analysis

### Position Bias

**openai** (n=1,598):
  - A: 310, B: 278, C: 61, synthesis: 949 (59.4%)
  - χ²=169.667, p=0.0, significant: YES

**anthropic** (n=1,598):
  - A: 152, B: 133, C: 79, synthesis: 1234 (77.2%)
  - χ²=23.643, p=0.0, significant: YES

**google** (n=751):
  - A: 305, B: 271, C: 131, synthesis: 44 (5.9%)
  - χ²=72.181, p=0.0, significant: YES

### Family Bias (Same-Vendor Preference)

| Arbitrator | Same-Family Rate | Expected | χ² | p | Significant |
|------------|------------------|----------|----|----|-------------|
| openai | 51.8% | 33.3% | 99.292 | 0.0 | YES |
| anthropic | 36.8% | 33.3% | 1.984 | 0.159 | no |
| google | 18.5% | 33.3% | 69.728 | 0.0 | YES |

## 6. Barriers by Survey

### CPS (n=1,030)

**L1 Barrier Distribution:**

| L1 Code | Count | % |
|---------|-------|---|
| CC | 877 | 85.1% |
| TC | 81 | 7.9% |
| RS | 42 | 4.1% |
| NHB | 11 | 1.1% |
| MC | 10 | 1.0% |
| PC | 7 | 0.7% |
| PM | 2 | 0.2% |

**Feasibility:**

- F1: 47 (4.6%)
- F2: 154 (15.0%)
- F3: 829 (80.5%)
- **Consolidable (F1+F2):** 201
- **Not Consolidable (F3):** 829

**Top 5 Specific Barriers:**

- CC.1: 610
- CC.2: 186
- CC.4: 80
- TC.2: 51
- RS.1: 35

### FOODAPS (n=568)

**L1 Barrier Distribution:**

| L1 Code | Count | % |
|---------|-------|---|
| CC | 505 | 88.9% |
| TC | 31 | 5.5% |
| RS | 19 | 3.3% |
| PC | 5 | 0.9% |
| MC | 4 | 0.7% |
| NHB | 3 | 0.5% |
| PM | 1 | 0.2% |

**Feasibility:**

- F1: 27 (4.8%)
- F2: 90 (15.8%)
- F3: 451 (79.4%)
- **Consolidable (F1+F2):** 117
- **Not Consolidable (F3):** 451

**Top 5 Specific Barriers:**

- CC.1: 311
- CC.2: 135
- CC.4: 56
- TC.2: 23
- RS.1: 12

## 7. Final Verdicts

**Confidence Distribution:**

- HIGH: 1,458 (91.2%)
- MODERATE: 112 (7.0%)
- LOW: 28 (1.8%)

**Unanimous rate (OA+AN agree on both):** 91.2%
**Two-way partial agreement rate (L1 or feas):** 98.2%
**Three-way coverage:** 47.0%

**Tiebreaker rule:** OpenAI arbitrator verdict used when OA and AN disagree (two-way); majority vote when three-way data available.

## 8. Limitations

- Google arbitrator data is incomplete (751/1598 pairs, CPS only).
- Three-way analysis is CPS-only. FoodAPS has only two-way arbitration.
- OpenAI used as tiebreaker for two-way disagreements (arbitrary choice, documented for transparency).

---
*Report generated from `stage3_arbitration_metrics.json`*