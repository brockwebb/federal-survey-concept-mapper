# Arbitration Agreement Analysis Report

**Generated:** 2026-01-29T18:07:28.486973
**Total pairs analyzed:** 1598

---

## 1. Inter-Arbitrator Agreement

### Pairwise Agreement (Cohen's Kappa)

| Pair | N | Level | Kappa | Observed | Expected | Interpretation |
|------|---|-------|-------|----------|----------|----------------|
| anthropic-openai | 1598 | L1_barrier | 0.796 | 94.7% | 74.2% | Substantial |
| anthropic-openai | 1598 | full_barrier | 0.755 | 85.0% | 39.0% | Substantial |
| anthropic-openai | 1598 | feasibility | 0.843 | 94.7% | 66.6% | Almost Perfect |
| anthropic-google | 251 | L1_barrier | 0.898 | 96.0% | 60.8% | Almost Perfect |
| anthropic-google | 251 | full_barrier | 0.827 | 88.4% | 33.1% | Almost Perfect |
| anthropic-google | 251 | feasibility | 0.904 | 96.4% | 62.7% | Almost Perfect |
| openai-google | 251 | L1_barrier | 0.740 | 90.8% | 64.8% | Substantial |
| openai-google | 251 | full_barrier | 0.669 | 77.3% | 31.4% | Substantial |
| openai-google | 251 | feasibility | 0.888 | 96.0% | 64.4% | Almost Perfect |

### Three-Way Agreement (Fleiss' Kappa)

| Level | N | Kappa | Observed | Expected | Interpretation |
|-------|---|-------|----------|----------|----------------|
| L1_barrier | 251 | 0.805 | 92.8% | 63.2% | Almost Perfect |
| full_barrier | 251 | 0.716 | 80.7% | 32.3% | Substantial |
| feasibility | 251 | 0.875 | 95.5% | 63.9% | Almost Perfect |

---

## 2. Synthesis Rate (Unanimous Agreement)

When all 3 raters agree, arbitrators return `synthesis` - no selection needed.

| Arbitrator | Total Pairs | Synthesis | Arbitration Needed | Synthesis % |
|------------|-------------|-----------|-------------------|-------------|
| anthropic | 1598 | 1234 | 364 | 77.2% |
| openai | 1598 | 949 | 649 | 59.4% |
| google | 251 | 15 | 236 | 6.0% |

---

## 3. Family Bias Analysis

Do arbitrators prefer raters from their own vendor family?

| Arbitrator | Total | Same Family | Cross Family | Same % | Expected % | Bias Ratio |
|------------|-------|-------------|--------------|--------|------------|------------|
| anthropic | 364 | 0 | 364 | 0.0% | 33.3% | 0.00 |
| openai | 649 | 0 | 649 | 0.0% | 33.3% | 0.00 |
| google | 236 | 0 | 236 | 0.0% | 33.3% | 0.00 |

*Bias ratio > 1.0 indicates preference for same-family raters.*

---

## 4. Coverage Notes

- **Two-way analysis:** 1598 pairs (Anthropic + OpenAI)
- **Three-way analysis:** 251 pairs (all 3 arbitrators)
- **Google limitation:** Rate-limited, only CPS pairs covered
