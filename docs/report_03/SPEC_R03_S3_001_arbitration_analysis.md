# Stage 3: Arbitration Analysis Specification

**Document ID:** `SPEC-R03-S3-001`  
**Version:** 1.0  
**Created:** 2026-01-30  
**Status:** DRAFT  
**Cross-References:** 
- `ANALYSIS_VV_PLAN.md` (parent V&V framework)
- `SPEC-R03-S2-001` (upstream Stage 2 spec)
- `FINDINGS_R03_S2_agreement_analysis.md` (upstream findings)

---

## 1. Purpose

Analyze arbitration results to:
1. Quantify inter-arbitrator agreement (do arbitrators reach consistent verdicts?)
2. Measure arbitration concordance with rater consensus
3. Detect position and family biases in arbitrator selection
4. Produce final barrier verdicts with confidence levels
5. Generate by-survey breakdown of harmonization barriers

---

## 2. Data Sources

### 2.1 Primary Inputs

| File | Description | Records |
|------|-------------|---------|
| `arbitration_deduped_openai.jsonl` | OpenAI arbitrator verdicts | 1,598 |
| `arbitration_deduped_anthropic.jsonl` | Anthropic arbitrator verdicts | 1,598 |
| `arbitration_deduped_google.jsonl` | Google arbitrator verdicts | ~500* |
| `barrier_coding_merged_3rater.csv` | Original rater classifications | 1,598 |

*Google data is incomplete due to rate limits. Three-way analysis limited to available pairs.

### 2.2 Arbitration Record Schema

| Field | Description |
|-------|-------------|
| `pair_id` | Unique pair identifier |
| `final_barrier_code` | Arbitrator's verdict (L1.L2 format) |
| `final_feasibility` | Arbitrator's feasibility verdict (F1/F2/F3) |
| `selected_rater` | Which rater's view was chosen (A/B/C/Synthesis) |
| `selected_rater_key` | Actual rater identity (openai/anthropic/google/synthesis) |
| `reasoning` | Arbitrator's explanation |
| `order_type` | fixed or randomized |
| `rater_order` | Presentation order [rater1, rater2, rater3] |
| `{rater}_barrier` | Original rater L1.L2 code |
| `{rater}_feasibility` | Original rater feasibility |

### 2.3 Coverage Summary

| Analysis Type | Arbitrators | N | Survey Coverage |
|---------------|-------------|---|-----------------|
| Two-way | OpenAI + Anthropic | 1,598 | CPS + FoodAPS |
| Three-way | All three | ~500 | CPS only |

---

## 3. Metrics

### 3.1 Inter-Arbitrator Agreement

**Rationale:** Do different arbitrators reach the same final verdict when given identical rater inputs?

| Metric | Scope | Purpose |
|--------|-------|---------|
| Cohen's κ (L1) | Pairwise | Arbitrator concordance on barrier type |
| Cohen's κ (Feasibility) | Pairwise | Arbitrator concordance on consolidability |
| Cohen's κ (Binary) | Pairwise | Consolidable (F1+F2) vs Not (F3) |
| Fleiss' κ | Three-way | Multi-arbitrator agreement (subset) |
| Raw % Agreement | All | Transparency; kappa paradox check |

**Pairwise Comparisons:**
1. OpenAI-arb vs Anthropic-arb (n=1,598)
2. OpenAI-arb vs Google-arb (n=~500)
3. Anthropic-arb vs Google-arb (n=~500)

### 3.2 Arbitrator-Rater Concordance

**Rationale:** How often does the arbitrator's verdict match what the raters said?

| Metric | Definition |
|--------|------------|
| Majority Confirmation Rate | % where arbitrator verdict = rater majority vote |
| Synthesis Detection Rate | % where arbitrator correctly identified unanimous rater agreement |
| Override Rate | % where arbitrator chose minority rater or novel verdict |

**Compute separately for:**
- L1 barrier classification
- Feasibility classification
- By arbitrator (OA, AN, GO)

### 3.3 Synthesis Detection Accuracy

**Definition:** When all 3 raters agreed (unanimous), did the arbitrator detect this and select "Synthesis"?

| Metric | Formula |
|--------|---------|
| True Positive | Raters unanimous AND arbitrator selected "synthesis" |
| False Negative | Raters unanimous BUT arbitrator selected single rater |
| Synthesis Precision | TP / (TP + FP) |
| Synthesis Recall | TP / (TP + FN) |

**Known Issue from Stage 2:** Google arbitrator shows 6% synthesis rate vs Anthropic's 77%. Investigate whether this reflects:
- Different synthesis detection thresholds
- Prompt interpretation differences
- Actual disagreement on what constitutes "agreement"

### 3.4 Bias Detection

#### 3.4.1 Position Bias

**Hypothesis:** Arbitrators may favor raters presented in certain positions (primacy/recency effects).

| Test | Method |
|------|--------|
| Position Selection Rate | % selected by position (A, B, C) |
| Expected (null) | 33.3% each under random selection |
| Chi-square test | Observed vs expected distribution |
| Fixed vs Random comparison | Compare selection patterns |

**Stratify by:**
- Arbitrator (OA, AN, GO)
- Order type (fixed vs randomized)

#### 3.4.2 Family Bias

**Hypothesis:** Arbitrators may favor raters from the same vendor family.

| Test | Method |
|------|--------|
| Same-Family Selection Rate | % where arbitrator selected same-vendor rater |
| Expected (null) | 33.3% (1 of 3 raters is same family) |
| Chi-square test | Observed vs expected |

**Family definitions:**
- OpenAI arbitrator selecting OpenAI rater = same family
- Anthropic arbitrator selecting Anthropic rater = same family
- Google arbitrator selecting Google rater = same family

---

## 4. Stratifications

### 4.1 By Survey

**Primary deliverable:** What barriers prevent harmonization for each survey?

| Stratum | N | Purpose |
|---------|---|---------|
| CPS→ACS | 1,030 | Labor/demographic barriers |
| FoodAPS→ACS | 568 | Food security barriers |

**Report for each survey:**
- L1 barrier distribution (final arbitrated verdicts)
- Feasibility distribution
- Top 5 specific barrier subcategories (L2)
- Example question pairs for each major barrier type

### 4.2 By Rater Agreement Level

| Stratum | Definition | Expected Pattern |
|---------|------------|------------------|
| Unanimous | All 3 raters agreed on L1 | Arbitrator should confirm |
| 2-1 Split | Two raters agreed, one dissented | Arbitrator breaks tie |
| Three-way | All three disagreed | Arbitrator makes judgment call |

**Compute:**
- Arbitrator concordance with majority (for 2-1 splits)
- Arbitrator reasoning patterns (for three-way splits)

### 4.3 By Feasibility Transition

**Focus on F2↔F3 boundary** (identified in Stage 2 as primary confusion):

| Transition | Interpretation |
|------------|----------------|
| Raters split F2/F3 → Arbitrator F2 | Optimistic resolution |
| Raters split F2/F3 → Arbitrator F3 | Conservative resolution |
| Raters unanimous F3 → Arbitrator F3 | Confirmation |
| Raters unanimous F2 → Arbitrator F2 | Confirmation |

---

## 5. Final Verdict Construction

### 5.1 Two-Way Verdict Rule

For pairs with only OpenAI + Anthropic arbitration:

| OA Verdict | AN Verdict | Final Verdict | Confidence |
|------------|------------|---------------|------------|
| Match | Match | Unanimous | HIGH |
| Differ | Differ | OA verdict* | MODERATE |

*Tiebreaker: Use OpenAI as reference (arbitrary but documented). Flag for review.

### 5.2 Three-Way Verdict Rule

For pairs with all three arbitrators:

| Pattern | Final Verdict | Confidence |
|---------|---------------|------------|
| 3-0 unanimous | Unanimous verdict | HIGH |
| 2-1 majority | Majority verdict | MODERATE |
| 3-way split | [Resolution rule TBD] | LOW |

### 5.3 Confidence Levels

| Level | Definition | Action |
|-------|------------|--------|
| HIGH | All available arbitrators agree | Report as definitive |
| MODERATE | Majority agreement or 2-way match | Report with caveat |
| LOW | Disagreement requiring manual review | Flag for discussion |

---

## 6. Outputs

### 6.1 Data Files

| File | Description |
|------|-------------|
| `stage3_arbitration_metrics.json` | All computed statistics |
| `stage3_arbitration_report.md` | Human-readable summary |
| `final_verdicts.csv` | Pair-level final classifications |
| `barrier_summary_by_survey.csv` | Survey-level barrier distributions |
| `arbitrator_confusion_matrix_L1.csv` | Inter-arbitrator disagreements |
| `position_bias_analysis.csv` | Position selection patterns |
| `family_bias_analysis.csv` | Same-family selection patterns |

### 6.2 JSON Schema for `stage3_arbitration_metrics.json`

```json
{
  "metadata": {
    "generated_at": "ISO timestamp",
    "spec_version": "SPEC-R03-S3-001 v1.0",
    "two_way_n": 1598,
    "three_way_n": 500
  },
  
  "inter_arbitrator_agreement": {
    "two_way": {
      "OA_vs_AN": {
        "L1": {"percent_agreement": 0.0, "cohens_kappa": 0.0, "interpretation": ""},
        "feasibility": {"percent_agreement": 0.0, "cohens_kappa": 0.0},
        "binary": {"percent_agreement": 0.0, "cohens_kappa": 0.0}
      }
    },
    "three_way": {
      "n_pairs": 500,
      "L1": {"fleiss_kappa": 0.0, "krippendorff_alpha": 0.0},
      "feasibility": {"fleiss_kappa": 0.0, "krippendorff_alpha": 0.0},
      "coverage_note": "CPS only due to Google rate limits"
    }
  },
  
  "arbitrator_concordance": {
    "by_arbitrator": {
      "openai": {
        "majority_confirmation_rate_L1": 0.0,
        "majority_confirmation_rate_feas": 0.0,
        "synthesis_detection_rate": 0.0,
        "override_rate": 0.0
      }
    }
  },
  
  "synthesis_detection": {
    "by_arbitrator": {
      "openai": {"precision": 0.0, "recall": 0.0, "f1": 0.0},
      "anthropic": {"precision": 0.0, "recall": 0.0, "f1": 0.0},
      "google": {"precision": 0.0, "recall": 0.0, "f1": 0.0}
    }
  },
  
  "bias_detection": {
    "position_bias": {
      "by_arbitrator": {
        "openai": {
          "position_A_rate": 0.0,
          "position_B_rate": 0.0,
          "position_C_rate": 0.0,
          "synthesis_rate": 0.0,
          "chi_square_p": 0.0,
          "significant": false
        }
      }
    },
    "family_bias": {
      "by_arbitrator": {
        "openai": {
          "same_family_rate": 0.0,
          "expected_rate": 0.333,
          "chi_square_p": 0.0,
          "significant": false
        }
      }
    }
  },
  
  "barrier_summary_by_survey": {
    "CPS": {
      "n_pairs": 1030,
      "L1_distribution": {"CC": 0, "TC": 0, "RS": 0},
      "feasibility_distribution": {"F1": 0, "F2": 0, "F3": 0},
      "top_L2_barriers": []
    },
    "FoodAPS": {
      "n_pairs": 568,
      "L1_distribution": {},
      "feasibility_distribution": {},
      "top_L2_barriers": []
    }
  },
  
  "final_verdict_summary": {
    "confidence_distribution": {"HIGH": 0, "MODERATE": 0, "LOW": 0},
    "unanimous_rate": 0.0,
    "majority_rate": 0.0,
    "split_rate": 0.0
  }
}
```

### 6.3 Report Sections

1. **Executive Summary**
   - Inter-arbitrator agreement metrics
   - Key bias findings
   - Final verdict confidence distribution

2. **Inter-Arbitrator Agreement**
   - Two-way results (full coverage)
   - Three-way results (CPS subset)
   - Comparison with Stage 2 rater agreement

3. **Arbitration Quality**
   - Concordance with rater majority
   - Synthesis detection accuracy
   - Override patterns and rationale

4. **Bias Analysis**
   - Position bias results
   - Family bias results
   - Implications for methodology

5. **Barriers by Survey**
   - CPS→ACS: What prevents harmonization?
   - FoodAPS→ACS: What prevents harmonization?
   - Comparison and patterns

6. **Final Verdicts**
   - Confidence distribution
   - Flagged pairs requiring review
   - Verdict construction methodology

---

## 7. Implementation Notes

### 7.1 Data Loading

```python
import pandas as pd
import json

# Load arbitration results
arb_oa = pd.read_json('arbitration_deduped_openai.jsonl', lines=True)
arb_an = pd.read_json('arbitration_deduped_anthropic.jsonl', lines=True)
arb_go = pd.read_json('arbitration_deduped_google.jsonl', lines=True)

# Load original rater data for concordance analysis
raters = pd.read_csv('barrier_coding_merged_3rater.csv')

# Merge on pair_id
merged = arb_oa.merge(arb_an, on='pair_id', suffixes=('_oa', '_an'))
```

### 7.2 Survey Extraction

```python
df['survey'] = df['pair_id'].apply(lambda x: 'CPS' if x.startswith('CPS') else 'FoodAPS')
```

### 7.3 L1 Extraction

```python
df['L1'] = df['final_barrier_code'].str.split('.').str[0]
```

### 7.4 Three-Way Subset

```python
# Get pairs where all three arbitrators have verdicts
three_way_pairs = set(arb_oa['pair_id']) & set(arb_an['pair_id']) & set(arb_go['pair_id'])
```

### 7.5 Rater Majority Vote

```python
from collections import Counter

def get_majority(row, field='L1'):
    votes = [row[f'{field}_openai'], row[f'{field}_anthropic'], row[f'{field}_google']]
    counts = Counter(votes)
    most_common = counts.most_common(1)[0]
    if most_common[1] >= 2:
        return most_common[0]
    return None  # Three-way split
```

### 7.6 Position Bias Chi-Square

```python
from scipy.stats import chisquare

def test_position_bias(selection_counts, n_total):
    """Test if position selection deviates from uniform."""
    observed = [selection_counts.get(pos, 0) for pos in ['A', 'B', 'C']]
    expected = [n_total / 3] * 3
    chi2, p = chisquare(observed, expected)
    return chi2, p, p < 0.05
```

---

## 8. Statistical Power

### 8.1 Two-Way Analysis

| Analysis | N | Required | Status |
|----------|---|----------|--------|
| Overall | 1,598 | 200 | ✅ ADEQUATE |
| CPS | 1,030 | 200 | ✅ ADEQUATE |
| FoodAPS | 568 | 200 | ✅ ADEQUATE |

### 8.2 Three-Way Analysis

| Analysis | N | Required | Status |
|----------|---|----------|--------|
| Overall | ~500 | 200 | ✅ ADEQUATE |
| CPS only | ~500 | 200 | ✅ ADEQUATE |
| FoodAPS | 0 | 200 | ❌ NOT AVAILABLE |

**Limitation:** Three-way arbitrator agreement cannot be computed for FoodAPS due to incomplete Google data. Document this limitation in findings.

---

## 9. Validation Checklist

- [ ] Arbitration data loaded for all three arbitrators
- [ ] Two-way merge verified (n=1,598)
- [ ] Three-way subset identified and counted
- [ ] L1 extracted correctly from L1.L2 format
- [ ] Survey field derived from pair_id
- [ ] Inter-arbitrator agreement computed (two-way full, three-way subset)
- [ ] Concordance with rater majority computed
- [ ] Synthesis detection accuracy computed per arbitrator
- [ ] Position bias chi-square tests run
- [ ] Family bias chi-square tests run
- [ ] By-survey barrier distributions computed
- [ ] Final verdicts constructed with confidence levels
- [ ] Three-way limitation documented (CPS only)
- [ ] Report generated with all sections

---

## 10. Open Questions

1. **Tiebreaker for two-way disagreement:** Currently defaults to OpenAI. Should we use different logic (e.g., more conservative, or flag for manual review)?

2. **Google data completion:** Continue collecting overnight? Current ~500 provides adequate power for three-way analysis on CPS.

3. **Three-way split resolution:** For pairs where all 3 arbitrators disagree, what's the final verdict rule? Options:
   - Flag as LOW confidence, no verdict
   - Use rater majority vote as fallback
   - Manual review required

---

## 11. Approval

**Prepared by:** Claude (AI Assistant)  
**Reviewed by:** [Pending]  
**Date:** 2026-01-30  
**Status:** DRAFT - Awaiting review
