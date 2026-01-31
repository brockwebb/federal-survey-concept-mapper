# Stage 3 Arbitration Analysis Report

**Generated:** 2026-01-30T22:19:35.538839
**OpenAI pairs:** 1,598
**Anthropic pairs:** 1,598
**Google pairs:** 503

## 1. Executive Summary

- **Two-way (OA vs AN) L1 agreement:** 94.7% (κ=0.796)
- **Two-way feasibility agreement:** 94.7% (κ=0.843)
- **Two-way binary consolidability:** 96.7% (κ=0.896)
- **Three-way (CPS subset) L1 Fleiss' κ:** 0.833
- **Final verdicts:** 1,458 HIGH, 112 MODERATE, 28 LOW
- **Synthesis detection F1:** google=0.153, anthropic=0.885
- **Openai synthesis pattern:** backwards (unanimous: 64.0%, split: 40.1%)
- **Anthropic synthesis pattern:** backwards (unanimous: 86.7%, split: 37.9%)
- **Google synthesis pattern:** deferential (unanimous: 8.4%, split: 2.5%)

## 2. Inter-Arbitrator Agreement (Two-Way)

**Coverage:** 1,598 pairs (OpenAI + Anthropic)

| Metric | % Agreement | Cohen's κ | Interpretation | Quality Gate |
|--------|-------------|-----------|----------------|--------------|
| L1 | 94.7% | 0.796 | Substantial | NOT PASSED |
| full_barrier_code | 85.0% | 0.755 | Substantial | NOT PASSED |
| feasibility | 94.7% | 0.843 | Almost Perfect | PASSED |
| binary_consolidability | 96.7% | 0.896 | Almost Perfect | PASSED |

## 3. Inter-Arbitrator Agreement (Three-Way)

**Coverage:** 503 pairs (CPS only — Google limited)

### Three-Way Metrics

| Metric | Fleiss' κ | Krippendorff's α | Interpretation |
|--------|-----------|------------------|----------------|
| L1 | 0.833 | 0.833 | Almost Perfect |
| full_barrier_code | 0.747 | 0.747 | Substantial |
| feasibility | 0.871 | 0.872 | Almost Perfect |
| binary_consolidability | 0.903 | 0.903 | Almost Perfect |

### Pairwise L1 (Three-Way Subset)

| Comparison | % Agreement | Cohen's κ | Interpretation |
|------------|-------------|-----------|----------------|
| OA vs AN | 93.6% | 0.813 | Almost Perfect |
| OA vs GO | 93.0% | 0.795 | Substantial |
| AN vs GO | 95.8% | 0.887 | Almost Perfect |

### Pairwise L2/Full Barrier Code (Three-Way Subset)

| Comparison | % Agreement | Cohen's κ | Interpretation |
|------------|-------------|-----------|----------------|
| OA vs AN | 81.9% | 0.714 | Substantial |
| OA vs GO | 81.1% | 0.702 | Substantial |
| AN vs GO | 89.3% | 0.827 | Almost Perfect |

## 4. Arbitrator-Rater Concordance

| Arbitrator | n | L1 vs Maj | L2 vs Maj | Feas vs Maj | L1 vs Unan | L2 vs Unan | Feas vs Unan | L1 Overrides | L2 Overrides |
|------------|---|-----------|-----------|-------------|------------|------------|--------------|--------------|--------------|
| openai | 1,598 | 92.1% | 83.5% | 93.4% | 96.7% | 94.9% | 98.7% | 42 / 1289 | 42 / 831 |
| anthropic | 1,598 | 95.6% | 93.7% | 96.7% | 99.8% | 99.5% | 100.0% | 3 / 1289 | 4 / 831 |
| google | 503 | 95.5% | 93.0% | 97.0% | 100.0% | 100.0% | 100.0% | 0 / 383 | 0 / 244 |

## 4b. Synthesis Behavior Analysis

**Question:** How does each arbitrator approach synthesis vs. single-rater selection?

| Arbitrator | n | Unanimous N | Unan Synth % | Split N | Split Synth % | Pattern | F1 |
|------------|---|-------------|--------------|---------|---------------|---------|-----|
| openai | 1,598 | 1,289 | 64.0% | 309 | 40.1% | backwards | 0.737 |
| anthropic | 1,598 | 1,289 | 86.7% | 309 | 37.9% | backwards | 0.885 |
| google | 503 | 383 | 8.4% | 120 | 2.5% | deferential | 0.153 |

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

**google** (n=503):
  - A: 240, B: 158, C: 70, synthesis: 35 (7.0%)
  - χ²=92.667, p=0.0, significant: YES

### Family Bias (Same-Vendor Preference)

| Arbitrator | Same-Family Rate | Expected | χ² | p | Significant |
|------------|------------------|----------|----|----|-------------|
| openai | 51.8% | 33.3% | 99.292 | 0.0 | YES |
| anthropic | 36.8% | 33.3% | 1.984 | 0.159 | no |
| google | 16.2% | 33.3% | 61.538 | 0.0 | YES |

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
- F2: 151 (14.7%)
- F3: 832 (80.8%)
- **Consolidable (F1+F2):** 198
- **Not Consolidable (F3):** 832

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
**Three-way coverage:** 31.5%

**Tiebreaker rule:** OpenAI arbitrator verdict used when OA and AN disagree (two-way); majority vote when three-way data available.

## 8. Limitations

- Google arbitrator data is incomplete (503/1598 pairs, CPS only).
- Three-way analysis is CPS-only. FoodAPS has only two-way arbitration.
- OpenAI used as tiebreaker for two-way disagreements (arbitrary choice, documented for transparency).

---
*Report generated from `stage3_arbitration_metrics.json`*