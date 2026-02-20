# Stage 2 Extended Analytics Report

**Generated:** 2026-01-30T14:46:38.917549
**Total Pairs:** 1,598

## Binary Consolidability (F1+F2 vs F3)

- Consolidable (F1+F2): 571
- Not Consolidable (F3): 1,027

- **Fleiss' kappa:** 0.621 (Substantial)
- **Krippendorff's alpha:** 0.621
- **Quality Gate:** NOT PASSED

### Pairwise

| Comparison | % Agreement | Cohen's kappa | Interpretation |
|------------|-------------|---------------|----------------|
| OA vs AN | 81.4% | 0.549 | Moderate |
| OA vs GO | 82.1% | 0.574 | Moderate |
| AN vs GO | 93.0% | 0.788 | Substantial |

## Disagreement Patterns

- **L1 unanimous:** 1,289 (80.7%)
- **L1 disagreements:** 309 (19.3%)
- **Feasibility unanimous:** 1,153 (72.2%)
- **Feasibility disagreements:** 445 (27.8%)

### Disagreement Cross-Tabulation

| | L1 Agree | L1 Disagree |
|---|---|---|
| **Feas Agree** | 983 | 170 |
| **Feas Disagree** | 306 | 139 |

**Arbitration workload:** 615 pairs (38.5%)

## Unanimous F3 Barrier Agreement

- **n:** 983 (61.5% of total)
- **L1 Fleiss' kappa:** 0.396 (Fair)

### L1 Distribution (within unanimous F3)

| Category | Count |
|----------|-------|
| CC | 930 |
| TC | 30 |
| RS | 13 |
| PC | 10 |

## Multi-Model Value

### Vote Patterns (L1)

- **unanimous:** 1,289 (80.7%)
- **2-1_split:** 274 (17.1%)
- **3-way_split:** 35 (2.2%)

### Single-Model Risk

| Model | L1 matches majority | Feasibility matches majority |
|-------|---------------------|------------------------------|
| openai | 94.7% | 82.7% |
| anthropic | 93.0% | 94.1% |
| google | 90.7% | 94.7% |

**L1 disagreements:** 309 pairs
**Feasibility disagreements:** 445 pairs

## Reasoning Keyword Analysis (Disagreement Cases)

- Cases analyzed: 309
- Reasoning texts: 927

| Keyword | Frequency |
|---------|-----------|
| reference | 237 |
| harmoniz | 233 |
| format | 209 |
| construct | 199 |
| response | 199 |
| time | 190 |
| temporal | 182 |
| consolidat | 133 |
| period | 126 |
| mode | 87 |
| context | 76 |
| numeric | 73 |
| compatibl | 71 |
| scale | 69 |
| concept | 65 |

---
*Report generated from `stage2_agreement_metrics.json` extended_analytics section*