# SPEC-R03-S3-001 Amendment A: Synthesis Behavior Metrics

**Amendment ID:** SPEC-R03-S3-001-A  
**Version:** 1.0  
**Created:** 2026-01-30  
**Status:** DRAFT  
**Amends:** Section 3.3 (Synthesis Detection Accuracy)

---

## 1. Purpose

Replace single synthesis detection metric with paired metrics that characterize arbitrator synthesis *behavior* across both agreement conditions. This provides a complete picture of how each arbitrator approaches the synthesis vs. selection decision.

---

## 2. Rationale

### 2.1 Problem with Original Metric

The original Section 3.3 defined synthesis detection only for unanimous cases. This answers one question but leaves behavior in split cases unmeasured. Additionally, implementation ambiguity arose between:

- **Behavioral definition:** Did arbitrator select `selected_rater_key == "synthesis"`?
- **Outcome definition:** Did arbitrator's verdict match rater consensus?

The outcome definition is redundant with existing concordance metrics. The behavioral definition reveals arbitrator decision-making patterns.

### 2.2 Value of Paired Metrics

| Metric | Condition | Question Answered |
|--------|-----------|-------------------|
| Synthesis-when-unanimous | Raters agree | Does arbitrator synthesize even when unnecessary? |
| Synthesis-when-split | Raters disagree | Does arbitrator do the hard work of reconciling conflict? |

**Interpretation Matrix:**

| Unanimous | Split | Pattern | Interpretation |
|-----------|-------|---------|----------------|
| High | High | Always synthesizes | Verbose/thorough - synthesizes regardless of need |
| Low | High | Efficient | Synthesizes only when value-add (ideal?) |
| Low | Low | Deferential | Always picks a rater, never synthesizes |
| High | Low | Backwards | Synthesizes easy cases, punts on hard ones |

---

## 3. Amended Section 3.3

*This section replaces the original Section 3.3 in its entirety.*

### 3.3 Synthesis Behavior Analysis

**Definition:** Measure how often the arbitrator chooses to synthesize (create a combined verdict) vs. defer to a single rater, stratified by whether raters agreed or disagreed.

**Critical implementation note:** Synthesis is determined by `selected_rater_key == "synthesis"`, NOT by whether the arbitrator's verdict matches rater consensus. The latter is already captured in concordance metrics.

#### 3.3.1 Synthesis-When-Unanimous

**Condition:** All available raters agreed on L1 classification.

| Metric | Formula |
|--------|---------|
| Denominator | N pairs where raters are unanimous on L1 |
| Numerator (TP) | Pairs where `selected_rater_key == "synthesis"` |
| Rate | TP / Denominator |

**Complementary counts:**
- TP: Raters unanimous AND arbitrator synthesized
- FN: Raters unanimous AND arbitrator selected single rater

**Derived metrics:**
- Precision: TP / (all synthesis selections) = TP / (TP + FP)
- Recall: TP / (all unanimous cases) = TP / (TP + FN)  
- F1: 2 * (Precision * Recall) / (Precision + Recall)

Where FP = raters NOT unanimous AND arbitrator synthesized.

#### 3.3.2 Synthesis-When-Split

**Condition:** Raters disagreed on L1 classification (2-1 split or 3-way split).

| Metric | Formula |
|--------|---------|
| Denominator | N pairs where raters are NOT unanimous on L1 |
| Numerator | Pairs where `selected_rater_key == "synthesis"` |
| Rate | Numerator / Denominator |

**Split subcategories (optional refinement):**
- 2-1 split synthesis rate: When exactly 2 raters agreed
- 3-way split synthesis rate: When all 3 raters disagreed

#### 3.3.3 Interpretation Framework

**Expected healthy pattern:** Low synthesis-when-unanimous, high synthesis-when-split. This indicates the arbitrator:
1. Recognizes when raters agree and efficiently defers
2. Does genuine reconciliation work when raters disagree

**Warning patterns:**
- Very high synthesis-when-unanimous (>80%): Arbitrator may be ignoring rater agreement, doing unnecessary work
- Very low synthesis-when-split (<20%): Arbitrator may be avoiding reconciliation, just picking favorites
- Higher synthesis-when-unanimous than synthesis-when-split: Backwards behavior, investigate prompt interpretation

#### 3.3.4 Consistency Check

**Validation:** Synthesis rates from this section must match synthesis rates from position_bias analysis (Section 3.4.1). Both use `selected_rater_key == "synthesis"`. If they diverge, there is an implementation error.

---

## 4. Amended JSON Schema

Add to `synthesis_detection` section:

```json
"synthesis_detection": {
  "openai": {
    "n_pairs": 1598,
    "n_raters_unanimous": 1289,
    "n_raters_split": 309,
    "synthesis_when_unanimous": {
      "n": 1289,
      "synthesis_count": 0,
      "rate": 0.0
    },
    "synthesis_when_split": {
      "n": 309,
      "synthesis_count": 0,
      "rate": 0.0
    },
    "confusion_matrix": {
      "TP": 0,
      "FN": 0,
      "FP": 0,
      "TN": 0
    },
    "precision": 0.0,
    "recall": 0.0,
    "f1": 0.0,
    "synthesis_rate_overall": 0.0,
    "interpretation": ""
  }
}
```

**Interpretation field values:**
- `"efficient"`: Low unanimous (<30%), high split (>50%)
- `"always_synthesizes"`: High unanimous (>70%), high split (>70%)
- `"deferential"`: Low unanimous (<30%), low split (<30%)
- `"backwards"`: Unanimous rate > split rate by >20 percentage points
- `"moderate"`: All other patterns

---

## 5. Amended Report Section

Add to Section 4b (Synthesis Detection Accuracy):

### Synthesis Behavior by Condition

| Arbitrator | Unanimous N | Unanimous Synth Rate | Split N | Split Synth Rate | Pattern |
|------------|-------------|----------------------|---------|------------------|---------|
| openai | 1,289 | X% | 309 | Y% | [pattern] |
| anthropic | 1,289 | X% | 309 | Y% | [pattern] |
| google | 383 | X% | 120 | Y% | [pattern] |

**Interpretation:**
- [Narrative interpretation of patterns observed]

---

## 6. Implementation Notes

### 6.1 Determining Rater Unanimity

```python
def is_unanimous(row):
    """Check if all available raters agreed on L1."""
    rater_L1s = []
    for rater in ['openai', 'anthropic', 'google']:
        col = f'{rater}_L1'
        if col in row and pd.notna(row[col]):
            rater_L1s.append(row[col])
    
    if len(rater_L1s) < 2:
        return None  # Not enough raters
    
    return len(set(rater_L1s)) == 1
```

### 6.2 Computing Paired Metrics

```python
def compute_synthesis_behavior(arb_df, rater_df, arbitrator_name):
    """Compute synthesis rates stratified by rater agreement."""
    
    merged = arb_df.merge(rater_df, on='pair_id')
    merged['raters_unanimous'] = merged.apply(is_unanimous, axis=1)
    merged['arb_synthesized'] = merged['selected_rater_key'] == 'synthesis'
    
    # Split by condition
    unanimous = merged[merged['raters_unanimous'] == True]
    split = merged[merged['raters_unanimous'] == False]
    
    # Compute rates
    synth_when_unanimous = unanimous['arb_synthesized'].mean() if len(unanimous) > 0 else None
    synth_when_split = split['arb_synthesized'].mean() if len(split) > 0 else None
    
    # Confusion matrix (for precision/recall)
    TP = unanimous['arb_synthesized'].sum()
    FN = (~unanimous['arb_synthesized']).sum()
    FP = split['arb_synthesized'].sum()
    TN = (~split['arb_synthesized']).sum()
    
    precision = TP / (TP + FP) if (TP + FP) > 0 else 0
    recall = TP / (TP + FN) if (TP + FN) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    
    # Determine pattern
    pattern = classify_synthesis_pattern(synth_when_unanimous, synth_when_split)
    
    return {
        'n_pairs': len(merged),
        'n_raters_unanimous': len(unanimous),
        'n_raters_split': len(split),
        'synthesis_when_unanimous': {
            'n': len(unanimous),
            'synthesis_count': int(TP),
            'rate': round(synth_when_unanimous * 100, 1) if synth_when_unanimous else None
        },
        'synthesis_when_split': {
            'n': len(split),
            'synthesis_count': int(FP),
            'rate': round(synth_when_split * 100, 1) if synth_when_split else None
        },
        'confusion_matrix': {'TP': int(TP), 'FN': int(FN), 'FP': int(FP), 'TN': int(TN)},
        'precision': round(precision, 3),
        'recall': round(recall, 3),
        'f1': round(f1, 3),
        'synthesis_rate_overall': round((TP + FP) / len(merged) * 100, 1),
        'interpretation': pattern
    }


def classify_synthesis_pattern(unanimous_rate, split_rate):
    """Classify synthesis behavior pattern."""
    if unanimous_rate is None or split_rate is None:
        return "insufficient_data"
    
    high_unanimous = unanimous_rate > 0.70
    low_unanimous = unanimous_rate < 0.30
    high_split = split_rate > 0.50
    low_split = split_rate < 0.30
    
    if low_unanimous and high_split:
        return "efficient"
    elif high_unanimous and high_split:
        return "always_synthesizes"
    elif low_unanimous and low_split:
        return "deferential"
    elif unanimous_rate > split_rate + 0.20:
        return "backwards"
    else:
        return "moderate"
```

### 6.3 Validation Check

```python
def validate_synthesis_consistency(synthesis_metrics, position_bias_metrics):
    """Ensure synthesis rates match between sections."""
    for arb in ['openai', 'anthropic', 'google']:
        synth_rate_3_3 = synthesis_metrics[arb]['synthesis_rate_overall']
        synth_rate_3_4 = position_bias_metrics[arb]['synthesis_rate']
        
        if abs(synth_rate_3_3 - synth_rate_3_4) > 0.1:
            raise ValueError(
                f"Synthesis rate mismatch for {arb}: "
                f"Section 3.3 says {synth_rate_3_3}%, "
                f"Section 3.4 says {synth_rate_3_4}%"
            )
```

---

## 7. Expected Findings

Based on preliminary position_bias data showing synthesis rates of:
- OpenAI: 59.4%
- Anthropic: 77.2%
- Google: 7.0%

**Predicted patterns:**

| Arbitrator | Predicted Pattern | Reasoning |
|------------|-------------------|-----------|
| Google | Deferential | 7% overall synthesis suggests low in both conditions |
| Anthropic | Always synthesizes | 77% overall suggests high regardless of condition |
| OpenAI | Moderate or Efficient | 59% is intermediate; split stratification will reveal |

These predictions should be tested against actual stratified data.

---

## 8. Approval

**Prepared by:** Claude (AI Assistant)  
**Reviewed by:** [Pending]  
**Date:** 2026-01-30  
**Status:** DRAFT - Awaiting review

---

## 9. Changelog

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-01-30 | Initial amendment creating paired synthesis metrics |
