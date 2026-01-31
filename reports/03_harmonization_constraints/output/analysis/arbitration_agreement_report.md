# Arbitration Agreement Analysis Report

**Generated:** 2026-01-31T06:20:14.737087
**Total pairs analyzed:** 1598

---

## 1. Inter-Arbitrator Agreement

### Pairwise Agreement (Cohen's Kappa)

| Pair | N | Level | Kappa | Observed | Expected | Interpretation |
|------|---|-------|-------|----------|----------|----------------|
| anthropic-openai | 1598 | L1_barrier | 0.796 | 94.7% | 74.2% | Substantial |
| anthropic-openai | 1598 | full_barrier | 0.755 | 85.0% | 39.0% | Substantial |
| anthropic-openai | 1598 | feasibility | 0.843 | 94.7% | 66.6% | Almost Perfect |
| anthropic-google | 751 | L1_barrier | 0.894 | 97.2% | 73.6% | Almost Perfect |
| anthropic-google | 751 | full_barrier | 0.835 | 91.3% | 47.7% | Almost Perfect |
| anthropic-google | 751 | feasibility | 0.907 | 97.2% | 69.8% | Almost Perfect |
| openai-google | 751 | L1_barrier | 0.807 | 95.3% | 75.9% | Almost Perfect |
| openai-google | 751 | full_barrier | 0.673 | 82.7% | 47.0% | Substantial |
| openai-google | 751 | feasibility | 0.855 | 95.9% | 71.5% | Almost Perfect |

### Three-Way Agreement (Fleiss' Kappa)

| Level | N | Kappa | Observed | Expected | Interpretation |
|-------|---|-------|----------|----------|----------------|
| L1_barrier | 751 | 0.843 | 96.1% | 75.1% | Almost Perfect |
| full_barrier | 751 | 0.733 | 85.9% | 47.2% | Substantial |
| feasibility | 751 | 0.864 | 96.0% | 70.9% | Almost Perfect |

---

## 2. Synthesis Rate (Unanimous Agreement)

When all 3 raters agree, arbitrators return `synthesis` - no selection needed.

| Arbitrator | Total Pairs | Synthesis | Arbitration Needed | Synthesis % |
|------------|-------------|-----------|-------------------|-------------|
| anthropic | 1598 | 1234 | 364 | 77.2% |
| openai | 1598 | 949 | 649 | 59.4% |
| google | 751 | 40 | 711 | 5.3% |

---

## 3. Family Bias Analysis

Do arbitrators prefer raters from their own vendor family?

| Arbitrator | Total | Same Family | Cross Family | Same % | Expected % | Bias Ratio |
|------------|-------|-------------|--------------|--------|------------|------------|
| anthropic | 364 | 0 | 364 | 0.0% | 33.3% | 0.00 |
| openai | 649 | 0 | 649 | 0.0% | 33.3% | 0.00 |
| google | 711 | 0 | 711 | 0.0% | 33.3% | 0.00 |

*Bias ratio > 1.0 indicates preference for same-family raters.*

---

## 4. Coverage Notes

- **Two-way analysis:** 1598 pairs (Anthropic + OpenAI)
- **Three-way analysis:** 751 pairs (all 3 arbitrators)
- **Google limitation:** Rate-limited, only CPS pairs covered
