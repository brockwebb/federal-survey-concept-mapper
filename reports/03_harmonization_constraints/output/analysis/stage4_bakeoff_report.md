# Stage 4: Scoring Bake-Off Report

**Generated:** 2026-02-02T15:03:30.230673
**Pairs scored:** 1598
**Vote sources:** 3 raters + 2–3 arbitrators per pair

## Methods

| # | Method | Approach | Inputs |
|---|--------|----------|--------|
| 1 | Composite | Feasibility weight × confidence weight | Final verdict + confidence |
| 2 | Entropy | Inverted Shannon entropy × feasibility weight | All 5–6 votes |
| 3 | Bayesian | Beta-Binomial posterior P(consolidable) | All 5–6 votes (binary) |
| 4 | Borda | Normalized point sum (F1=2, F2=1, F3=0) | All 5–6 votes |
| E | Ensemble | Mean of min-max normalized scores | Methods 1–4 |

## Score Distributions

| Method | Mean | Std | Min | Q25 | Median | Q75 | Max |
|--------|-----:|----:|----:|----:|-------:|----:|----:|
| composite | 1.183 | 0.488 | 0.330 | 1.000 | 1.000 | 1.000 | 3.000 |
| entropy | 0.343 | 0.155 | 0.013 | 0.330 | 0.330 | 0.330 | 1.000 |
| bayesian | 0.224 | 0.273 | 0.049 | 0.056 | 0.056 | 0.199 | 0.799 |
| borda | 0.143 | 0.253 | 0.000 | 0.000 | 0.000 | 0.100 | 1.000 |
| ensemble | 0.258 | 0.218 | 0.112 | 0.145 | 0.145 | 0.180 | 1.000 |

### Mean Score by Final Feasibility

| Method | F1 Mean | F2 Mean | F3 Mean |
|--------|--------:|--------:|--------:|
| composite | 2.690 | 1.785 | 0.983 |
| entropy | 0.692 | 0.502 | 0.293 |
| bayesian | 0.766 | 0.736 | 0.097 |
| borda | 0.903 | 0.512 | 0.030 |
| ensemble | 0.858 | 0.617 | 0.155 |

## Spearman Rank Correlations

| | composite | entropy | bayesian | borda | ensemble |
|---|----:|----:|----:|----:|----:|
| composite | 1.000 | 0.622 | 0.523 | 0.561 | 0.582 |
| entropy | 0.622 | 1.000 | 0.083 | 0.073 | 0.109 |
| bayesian | 0.523 | 0.083 | 1.000 | 0.909 | 0.977 |
| borda | 0.561 | 0.073 | 0.909 | 1.000 | 0.894 |
| ensemble | 0.582 | 0.109 | 0.977 | 0.894 | 1.000 |

### Interpretation

**Most divergent pairs** (ρ < 0.85):
- composite ↔ entropy: ρ = 0.622
- composite ↔ bayesian: ρ = 0.523
- composite ↔ borda: ρ = 0.561
- entropy ↔ bayesian: ρ = 0.083
- entropy ↔ borda: ρ = 0.073

## Most Divergent Pairs (Top 20)

Pairs where the 4 methods disagree most on ranking (highest rank std dev):

| pair_id | feas | conf | composite | entropy | bayesian | borda | rank_std |
|---------|------|------|----------:|--------:|---------:|------:|---------:|
| FOODAPS_0590 | F2 | LOW | 0.66 | 0.027 | 0.628 | 0.600 | 809.5 |
| CPS_0502 | F3 | MODERATE | 0.67 | 0.026 | 0.674 | 0.667 | 802.7 |
| CPS_0017 | F2 | LOW | 0.66 | 0.282 | 0.799 | 0.667 | 800.5 |
| CPS_1063 | F3 | MODERATE | 0.67 | 0.013 | 0.628 | 0.600 | 795.1 |
| CPS_1067 | F2 | LOW | 0.66 | 0.260 | 0.771 | 0.800 | 784.6 |
| CPS_1068 | F2 | LOW | 0.66 | 0.260 | 0.771 | 0.800 | 784.6 |
| FOODAPS_0165 | F2 | LOW | 0.66 | 0.260 | 0.771 | 0.800 | 784.6 |
| FOODAPS_0326 | F2 | LOW | 0.66 | 0.260 | 0.771 | 0.800 | 784.6 |
| FOODAPS_0330 | F2 | LOW | 0.66 | 0.260 | 0.771 | 0.800 | 784.6 |
| FOODAPS_0446 | F2 | LOW | 0.66 | 0.260 | 0.771 | 0.800 | 784.6 |
| CPS_0422 | F1 | LOW | 0.99 | 0.079 | 0.549 | 0.583 | 774.7 |
| FOODAPS_0140 | F3 | LOW | 0.33 | 0.180 | 0.628 | 0.800 | 762.4 |
| CPS_1052 | F2 | LOW | 0.66 | 0.365 | 0.771 | 0.900 | 733.9 |
| FOODAPS_0608 | F2 | LOW | 0.66 | 0.365 | 0.771 | 0.900 | 733.9 |
| CPS_0912 | F3 | MODERATE | 0.67 | 0.013 | 0.485 | 0.400 | 728.8 |
| FOODAPS_0390 | F3 | MODERATE | 0.67 | 0.013 | 0.485 | 0.400 | 728.8 |
| CPS_1036 | F3 | LOW | 0.33 | 0.128 | 0.485 | 0.300 | 726.8 |
| FOODAPS_0404 | F3 | LOW | 0.33 | 0.128 | 0.485 | 0.300 | 726.8 |
| FOODAPS_0485 | F3 | LOW | 0.33 | 0.128 | 0.485 | 0.300 | 726.8 |
| CPS_0105 | F1 | LOW | 0.99 | 0.369 | 0.799 | 0.750 | 714.6 |

## Recommendation

### Separability Check

A good scoring method should separate consolidable (F1/F2) from non-consolidable (F3):

- **composite:** F1/F2 min=0.660, F3 max=1.000, gap=OVERLAP
- **entropy:** F1/F2 min=0.027, F3 max=0.330, gap=OVERLAP
- **bayesian:** F1/F2 min=0.199, F3 max=0.674, gap=OVERLAP
- **borda:** F1/F2 min=0.100, F3 max=0.800, gap=OVERLAP
- **ensemble:** F1/F2 min=0.241, F3 max=0.435, gap=OVERLAP

### Summary

- **Composite** is the simplest and most interpretable for stakeholders
- **Entropy** and **Borda** leverage full vote distributions
- **Bayesian** provides a probabilistic interpretation
- **Ensemble** smooths over method-specific quirks and is recommended for final ranking when no single method clearly dominates

---

**Methodology:** Each pair scored by 3 raters (Stage 1) and 2–3 arbitrators (Stage 3). Votes converted to feasibility classifications (F1/F2/F3). Four scoring methods applied independently, then combined via mean of min-max normalized scores.