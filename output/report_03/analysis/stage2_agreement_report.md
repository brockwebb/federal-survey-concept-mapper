# Stage 2: Inter-Rater Agreement Analysis Report

**Generated:** 2026-01-30T14:05:23.431634
**Input:** barrier_coding_merged_3rater.csv
**Total Pairs:** 1,598

## Executive Summary

- **L1 Fleiss' kappa:** 0.611 (Substantial)
- **L1 Krippendorff's alpha:** 0.611 (Substantial)
- **Quality Gate (kappa/alpha >= 0.80):** NOT PASSED

## Statistical Validity

**Overall:** n=1,598 (required: 200) -- **ADEQUATE**

### By Survey

| Survey | n | Status |
|--------|---|--------|
| CPS | 1,030 | ADEQUATE |
| FOODAPS | 568 | ADEQUATE |

### By L1 Category

| Category | n | Status |
|----------|---|--------|
| CC | 1,284 | ADEQUATE |
| TC | 177 | MARGINAL |
| RS | 69 | MARGINAL |
| PC | 34 | UNDERPOWERED |
| MC | 22 | UNDERPOWERED |
| PM | 9 | UNDERPOWERED |
| NHB | 3 | UNDERPOWERED |
| Other_combined | 68 | MARGINAL |

*Per Krippendorff (2004) via ATLAS.ti guidance. Categories with n<50 flagged as underpowered for independent reliability estimation.*

## L1 Agreement Results

### Pairwise Metrics

| Comparison | % Agreement | Cohen's kappa | Interpretation |
|------------|-------------|---------------|----------------|
| OA vs AN | 87.9% | 0.655 | Substantial |
| OA vs GO | 86.0% | 0.595 | Moderate |
| AN vs GO | 85.2% | 0.585 | Moderate |

### Three-Way Metrics

- **Fleiss' kappa:** 0.611 (Substantial)
- **Krippendorff's alpha:** 0.611 (Substantial)

### L1 by Survey

| Survey | n | Fleiss' kappa | Krippendorff's alpha |
|--------|---|---------------|----------------------|
| CPS | 1,030 | 0.625 | 0.625 |
| FOODAPS | 568 | 0.586 | 0.586 |

### L1 by Dominant Category

| Category | n | Fleiss' kappa | Krippendorff's alpha |
|----------|---|---------------|----------------------|
| CC | 1,284 | 0.128 | 0.128 |
| TC | 177 | 0.122 | 0.124 |
| RS | 69 | -0.050 | -0.045 |
| Other_combined | 68 | 0.158 | 0.162 |

## L2 Agreement Results

### Pairwise Metrics

| Comparison | % Agreement | Cohen's kappa | Interpretation |
|------------|-------------|---------------|----------------|
| OA vs AN | 65.3% | 0.471 | Moderate |
| OA vs GO | 66.6% | 0.488 | Moderate |
| AN vs GO | 64.1% | 0.460 | Moderate |

### Three-Way Metrics

- **Fleiss' kappa:** 0.472 (Moderate)
- **Krippendorff's alpha:** 0.472 (Moderate)

## Feasibility Agreement Results

### Pairwise Metrics

| Comparison | % Agreement | Cohen's kappa | Interpretation |
|------------|-------------|---------------|----------------|
| OA vs AN | 76.8% | 0.472 | Moderate |
| OA vs GO | 77.9% | 0.505 | Moderate |
| AN vs GO | 89.0% | 0.684 | Substantial |

### Three-Way Metrics

- **Fleiss' kappa:** 0.537 (Moderate)
- **Krippendorff's alpha:** 0.538 (Moderate)

## Disagreement Analysis

### L1 Top Confusions

**OA AN:** 1,404 agreements, 194 disagreements
  - Top confusions: CC->RS (37), CC->TC (30), TC->CC (29)

**OA GO:** 1,375 agreements, 223 disagreements
  - Top confusions: CC->RS (70), TC->CC (47), PC->CC (24)

**AN GO:** 1,362 agreements, 236 disagreements
  - Top confusions: CC->RS (63), TC->CC (55), RS->CC (27)

## Methodology

Metrics computed per McHugh (2012) and Krippendorff (2004) guidelines:
- **Cohen's kappa:** Pairwise chance-corrected agreement
- **Fleiss' kappa:** Multi-rater extension of Cohen's kappa
- **Krippendorff's alpha:** Robust to prevalence imbalance and missing data

**Quality Gate Threshold:** kappa/alpha >= 0.80 (McHugh 2012: "Almost Perfect" for health research)

---
*Report generated from `stage2_agreement_metrics.json`*