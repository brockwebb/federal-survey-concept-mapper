# Stage 2: Inter-Rater Agreement Analysis Specification

**Document ID:** `SPEC-R03-S2-001`  
**Version:** 1.0  
**Created:** 2025-01-30  
**Status:** APPROVED  
**Cross-References:** 
- `ANALYSIS_VV_PLAN.md` (parent V&V framework)
- `LIT-R03-IRR-001` (citations)
- `02_arbitration_pipeline.py` (downstream consumer)

---

## 1. Purpose

Quantify agreement among three LLM raters (OpenAI, Anthropic, Google) on barrier classification to:
1. Establish inter-rater reliability for methodology section
2. Identify systematic disagreement patterns for arbitration design
3. Validate taxonomy discriminant validity

---

## 2. Data Source

**Input:** `output/analysis/barrier_coding_merged_3rater.csv`

| Field | Description |
|-------|-------------|
| `pair_id` | Unique pair identifier (CPS_XXXX or FOODAPS_XXXX) |
| `primary_barrier_{rater}` | L1.L2 format (e.g., CC.1, TC.2, RS.1) |
| `feasibility_{rater}` | F1, F2, or F3 |
| `rater_coverage_count` | Number of raters (all = 3) |

**Sample Sizes:**
- Total: N = 1,598 pairs
- CPS→ACS: n = 1,030
- FoodAPS→ACS: n = 568

---

## 3. Metrics

### 3.1 Primary Metrics

| Metric | Statistic | Level | Scope | Rationale |
|--------|-----------|-------|-------|-----------|
| Raw Agreement | % | L1, L2, Feasibility | Overall, by survey | Transparency; kappa paradox check |
| Cohen's κ | Pairwise | L1, L2, Feasibility | 3 pairs | Model-vs-model comparison |
| Fleiss' κ | Multi-rater | L1, L2, Feasibility | All 3 raters | Standard multi-rater reliability |
| Krippendorff's α | Multi-rater | L1, L2, Feasibility | All 3 raters | Robustness to prevalence; recommended by literature |

**Pairwise Comparisons:**
1. OpenAI vs Anthropic
2. OpenAI vs Google
3. Anthropic vs Google

### 3.2 Threshold Interpretation

Per McHugh (2012) and Krippendorff (2004):

| Value | Interpretation | Action |
|-------|----------------|--------|
| ≥ 0.80 | Strong/Reliable | Quality gate passed |
| 0.67–0.79 | Substantial/Tentative | Flag; proceed with caution |
| 0.41–0.66 | Moderate/Insufficient | Requires investigation |
| < 0.41 | Poor | Taxonomy revision needed |

**Quality Gate:** κ/α ≥ 0.80 for L1 classification

---

## 4. Stratifications

### 4.1 By Survey (Independent Branches)

Rationale: CPS→ACS and FoodAPS→ACS are independent comparisons against ACS reference frame. Each survey may have different domain-specific challenges.

| Stratum | N | Purpose |
|---------|---|---------|
| CPS→ACS | 1,030 | Labor/demographic survey |
| FoodAPS→ACS | 568 | Food security survey |

### 4.2 By L1 Category (Category-Specific Difficulty)

Rationale: Some barrier types may be harder to classify than others. Literature recommends category-specific kappa when prevalence varies.

| L1 | N (OpenAI) | % | Analysis |
|----|------------|---|----------|
| CC | 1,284 | 80.4% | High prevalence; expect kappa paradox |
| TC | 177 | 11.1% | Temporal distinctions |
| RS | 69 | 4.3% | Response format |
| PC | 34 | 2.1% | Population/coverage |
| MC | 22 | 1.4% | Mode effects |
| PM | 9 | 0.6% | Policy/market (combine with "Other") |
| NHB | 3 | 0.2% | No harmonization barrier (combine) |

**Grouping for Analysis:**
- Individual: CC, TC, RS (n > 50)
- Combined "Other": PC + MC + PM + NHB (n = 68)

### 4.3 By Feasibility Level

| Feasibility | N (OpenAI) | % | Description |
|-------------|------------|---|-------------|
| F1 | 69 | 4.3% | Direct substitution |
| F2 | 502 | 31.4% | Statistical adjustment |
| F3 | 1,027 | 64.3% | Not consolidable |

---

## 5. Confusion Matrix Analysis

### 5.1 L1 Confusion Matrices

Generate 7×7 confusion matrix for each pairwise comparison:
- Rows: Rater A classification
- Columns: Rater B classification
- Cells: Count of pairs

**Report:**
- Diagonal sum (agreements)
- Off-diagonal patterns (systematic disagreements)
- Top 3 confusion pairs (e.g., CC↔TC confusion)

### 5.2 L2 Confusion Matrices

Generate full L2×L2 matrices for:
- Identifying subcategory confusion within same L1 parent
- Identifying cross-L1 misclassifications

**Visualization:** Heatmap with L1 grouping overlay

---

## 6. Statistical Power Verification

**REQUIRED OUTPUT:** Pipeline must compute and report power verification as validity evidence.

### 6.1 Minimum Sample Size Formula

Per Krippendorff (2004, via Bloch & Kraemer 1989):

For α_min = 0.80, significance = 0.05, k categories:
- k=2 categories: n_min ≈ 46
- k=4 categories: n_min ≈ 139  
- k=7 categories: n_min ≈ 200 (extrapolated)

### 6.2 Required Pipeline Output

The pipeline SHALL compute and include in `stage2_agreement_metrics.json`:

```json
{
  "power_verification": {
    "overall": {
      "n_observed": 1598,
      "n_required_k7_alpha80_p05": 200,
      "ratio": 7.99,
      "status": "ADEQUATE"
    },
    "by_stratum": {
      "CPS": {"n": 1030, "n_required": 200, "status": "ADEQUATE"},
      "FoodAPS": {"n": 568, "n_required": 200, "status": "ADEQUATE"}
    },
    "by_category": {
      "CC": {"n": 1284, "status": "ADEQUATE"},
      "TC": {"n": 177, "status": "ADEQUATE"},
      "RS": {"n": 69, "status": "MARGINAL"},
      "Other_combined": {"n": 68, "status": "MARGINAL"},
      "PM_individual": {"n": 9, "status": "UNDERPOWERED"},
      "NHB_individual": {"n": 3, "status": "UNDERPOWERED"}
    },
    "methodology_note": "Per Krippendorff (2004) via ATLAS.ti guidance. Categories with n<50 flagged as underpowered for independent reliability estimation."
  }
}
```

### 6.3 Status Thresholds

| N | Status | Interpretation |
|---|--------|----------------|
| ≥ 200 | ADEQUATE | Full statistical power for k=7 categories |
| 50-199 | MARGINAL | Interpret with caution; combine if possible |
| < 50 | UNDERPOWERED | Cannot draw independent conclusions; must combine |

### 6.4 Report Requirement

The human-readable report SHALL include a "Statistical Validity" section documenting:
1. Observed sample sizes
2. Required minimums (with citation)
3. Power status for each analysis level
4. Explicit acknowledgment of underpowered strata

---

## 7. Outputs

### 7.1 Data Files

| File | Description |
|------|-------------|
| `stage2_agreement_metrics.json` | All computed statistics |
| `stage2_agreement_report.md` | Human-readable summary |
| `confusion_matrix_L1_OA_AN.csv` | OpenAI vs Anthropic L1 |
| `confusion_matrix_L1_OA_GO.csv` | OpenAI vs Google L1 |
| `confusion_matrix_L1_AN_GO.csv` | Anthropic vs Google L1 |
| `confusion_matrix_L2_pairwise.csv` | Combined L2 matrices |

### 7.2 Report Sections

1. **Executive Summary**
   - Overall agreement (κ, α)
   - Quality gate status
   - Key findings

2. **Methodology**
   - Metric selection rationale
   - Threshold justification (cite McHugh, Krippendorff)
   - Prevalence adjustment approach

3. **Results by Level**
   - L1 agreement (table + interpretation)
   - L2 agreement (table + interpretation)
   - Feasibility agreement

4. **Stratified Results**
   - By survey
   - By category

5. **Disagreement Analysis**
   - Confusion matrix findings
   - Systematic patterns
   - Implications for arbitration

---

## 8. Implementation Notes

### 8.1 Python Libraries

```python
from sklearn.metrics import cohen_kappa_score, confusion_matrix
import krippendorff  # pip install krippendorff
# OR use statsmodels.stats.inter_rater for Fleiss
```

### 8.2 L1 Extraction

```python
df['L1_openai'] = df['primary_barrier_openai'].str.split('.').str[0]
df['L1_anthropic'] = df['primary_barrier_anthropic'].str.split('.').str[0]
df['L1_google'] = df['primary_barrier_google'].str.split('.').str[0]
```

### 8.3 Fleiss' Kappa Format

Requires aggregation to count matrix:
- Rows: Items (pairs)
- Columns: Categories
- Cells: Number of raters assigning that category

---

## 9. Validation Checklist

- [ ] All 1,598 pairs processed
- [ ] Three raters per pair verified
- [ ] L1 extracted correctly from L1.L2 format
- [ ] Metrics computed at all levels (L1, L2, Feasibility)
- [ ] Stratifications computed (survey, category)
- [ ] Confusion matrices generated
- [ ] Report includes % agreement alongside kappa
- [ ] Prevalence noted where relevant
- [ ] **Power verification computed and included in JSON output**
- [ ] **Underpowered strata explicitly flagged**
- [ ] Citations included in methodology

---

## 10. Approval

**Prepared by:** Claude (AI Assistant)  
**Reviewed by:** [Brock Webb]  
**Date:** 2025-01-30  
**Status:** Ready for implementation
