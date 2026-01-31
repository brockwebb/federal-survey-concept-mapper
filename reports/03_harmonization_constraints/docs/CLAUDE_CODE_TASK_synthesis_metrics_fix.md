# Claude Code Task: Fix Synthesis Detection Metrics

**Task ID:** TASK-S3-002  
**Created:** 2026-01-30  
**Priority:** HIGH  
**Spec Reference:** `SPEC_R03_S3_001_AMENDMENT_A_synthesis_metrics.md`

---

## Problem

Current `synthesis_detection` metrics in `04_stage3_arbitration.py` are computing the WRONG thing:

| Current Bug | Correct Definition |
|-------------|-------------------|
| Measures if arbitrator verdict matches rater consensus | Measures if `selected_rater_key == "synthesis"` |
| TP=825 for OpenAI (impossible given 59% synthesis rate) | Should use literal field value |
| Google shows 63.4% synthesis rate | Google position_bias shows 7% synthesis rate |

**The numbers are internally inconsistent.** Position_bias and synthesis_detection must use the same definition of "synthesis" - namely `selected_rater_key == "synthesis"`.

---

## Required Changes

### Location
`reports/03_harmonization_constraints/scripts/04_stage3_arbitration.py`

### Task 1: Replace `compute_synthesis_detection()` function

Delete existing implementation and replace with:

```python
def compute_synthesis_detection(arb_df, rater_df, arbitrator_name):
    """
    Compute synthesis behavior stratified by rater agreement.
    
    Per SPEC_R03_S3_001_AMENDMENT_A:
    - Synthesis = selected_rater_key == "synthesis" (LITERAL, not outcome-based)
    - Stratify by whether raters were unanimous or split
    
    Returns metrics for both conditions plus confusion matrix for precision/recall.
    """
    merged = arb_df.merge(rater_df[['pair_id', 'openai_L1', 'anthropic_L1', 'google_L1']], on='pair_id', how='left')
    
    # Determine rater unanimity on L1
    def is_unanimous(row):
        rater_L1s = []
        for rater in ['openai', 'anthropic', 'google']:
            col = f'{rater}_L1'
            if col in row.index and pd.notna(row[col]):
                rater_L1s.append(row[col])
        if len(rater_L1s) < 2:
            return None
        return len(set(rater_L1s)) == 1
    
    merged['raters_unanimous'] = merged.apply(is_unanimous, axis=1)
    merged['arb_synthesized'] = merged['selected_rater_key'] == 'synthesis'
    
    # Filter to rows with valid unanimity determination
    valid = merged[merged['raters_unanimous'].notna()].copy()
    
    # Split by condition
    unanimous = valid[valid['raters_unanimous'] == True]
    split = valid[valid['raters_unanimous'] == False]
    
    n_unanimous = len(unanimous)
    n_split = len(split)
    
    # Count synthesis in each condition
    synth_when_unanimous = int(unanimous['arb_synthesized'].sum()) if n_unanimous > 0 else 0
    synth_when_split = int(split['arb_synthesized'].sum()) if n_split > 0 else 0
    
    # Rates
    rate_unanimous = round(synth_when_unanimous / n_unanimous * 100, 1) if n_unanimous > 0 else None
    rate_split = round(synth_when_split / n_split * 100, 1) if n_split > 0 else None
    
    # Confusion matrix per spec:
    # TP = raters unanimous AND arbitrator synthesized
    # FN = raters unanimous AND arbitrator did NOT synthesize
    # FP = raters NOT unanimous AND arbitrator synthesized
    # TN = raters NOT unanimous AND arbitrator did NOT synthesize
    TP = synth_when_unanimous
    FN = n_unanimous - synth_when_unanimous
    FP = synth_when_split
    TN = n_split - synth_when_split
    
    # Precision/Recall/F1
    precision = TP / (TP + FP) if (TP + FP) > 0 else 0
    recall = TP / (TP + FN) if (TP + FN) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    
    # Overall synthesis rate (should match position_bias)
    total_synth = TP + FP
    total_n = len(valid)
    synthesis_rate_overall = round(total_synth / total_n * 100, 1) if total_n > 0 else 0
    
    # Classify pattern
    pattern = classify_synthesis_pattern(rate_unanimous, rate_split)
    
    return {
        'n_pairs': total_n,
        'n_raters_unanimous': n_unanimous,
        'n_raters_split': n_split,
        'synthesis_when_unanimous': {
            'n': n_unanimous,
            'synthesis_count': TP,
            'rate_pct': rate_unanimous
        },
        'synthesis_when_split': {
            'n': n_split,
            'synthesis_count': FP,
            'rate_pct': rate_split
        },
        'confusion_matrix': {
            'TP': TP,
            'FN': FN,
            'FP': FP,
            'TN': TN
        },
        'precision': round(precision, 3),
        'recall': round(recall, 3),
        'f1': round(f1, 3),
        'synthesis_rate_overall': synthesis_rate_overall,
        'interpretation': pattern
    }


def classify_synthesis_pattern(unanimous_rate, split_rate):
    """
    Classify synthesis behavior pattern per Amendment A.
    
    Patterns:
    - efficient: Low unanimous (<30%), high split (>50%)
    - always_synthesizes: High unanimous (>70%), high split (>70%)
    - deferential: Low unanimous (<30%), low split (<30%)
    - backwards: Unanimous rate > split rate by >20pp
    - moderate: Everything else
    """
    if unanimous_rate is None or split_rate is None:
        return "insufficient_data"
    
    # Convert to 0-1 scale for comparison
    u = unanimous_rate / 100
    s = split_rate / 100
    
    if u < 0.30 and s > 0.50:
        return "efficient"
    elif u > 0.70 and s > 0.70:
        return "always_synthesizes"
    elif u < 0.30 and s < 0.30:
        return "deferential"
    elif u > s + 0.20:
        return "backwards"
    else:
        return "moderate"
```

### Task 2: Add validation check after synthesis_detection computation

After computing synthesis_detection for each arbitrator, add:

```python
def validate_synthesis_consistency(synthesis_metrics, position_bias_metrics):
    """Ensure synthesis rates match between sections (per Amendment A Section 6.3)."""
    errors = []
    for arb in ['openai', 'anthropic', 'google']:
        if arb not in synthesis_metrics or arb not in position_bias_metrics:
            continue
        synth_rate_detection = synthesis_metrics[arb]['synthesis_rate_overall']
        synth_rate_position = position_bias_metrics[arb]['synthesis_rate']
        
        if abs(synth_rate_detection - synth_rate_position) > 0.5:  # Allow 0.5% tolerance for rounding
            errors.append(
                f"{arb}: synthesis_detection says {synth_rate_detection}%, "
                f"position_bias says {synth_rate_position}%"
            )
    
    if errors:
        raise ValueError("Synthesis rate mismatch!\n" + "\n".join(errors))
    
    print("✓ Synthesis rate consistency validated")
```

Call this after both metrics are computed:

```python
# After computing both synthesis_detection and position_bias
validate_synthesis_consistency(metrics['synthesis_detection'], metrics['position_bias'])
```

### Task 3: Update report generation

In the report generation section, update the synthesis detection table:

```python
# Section 4b: Synthesis Behavior Analysis
report_lines.append("## 4b. Synthesis Behavior Analysis\n")
report_lines.append("**Question:** How does each arbitrator approach synthesis vs. single-rater selection?\n")
report_lines.append("| Arbitrator | n | Unanimous N | Unan Synth % | Split N | Split Synth % | Pattern | F1 |")
report_lines.append("|------------|---|-------------|--------------|---------|---------------|---------|-----|")

for arb in ['openai', 'anthropic', 'google']:
    if arb in metrics['synthesis_detection']:
        m = metrics['synthesis_detection'][arb]
        unan = m['synthesis_when_unanimous']
        split = m['synthesis_when_split']
        report_lines.append(
            f"| {arb} | {m['n_pairs']:,} | {unan['n']:,} | "
            f"{unan['rate_pct'] if unan['rate_pct'] is not None else 'N/A'}% | "
            f"{split['n']:,} | {split['rate_pct'] if split['rate_pct'] is not None else 'N/A'}% | "
            f"{m['interpretation']} | {m['f1']:.3f} |"
        )

report_lines.append("")
report_lines.append("**Pattern Interpretation:**")
report_lines.append("- *efficient*: Synthesizes only when raters disagree (ideal)")
report_lines.append("- *always_synthesizes*: Synthesizes regardless of rater agreement")
report_lines.append("- *deferential*: Rarely synthesizes, prefers to pick a rater")
report_lines.append("- *backwards*: Synthesizes more when raters agree than disagree (problematic)")
report_lines.append("- *moderate*: No strong pattern")
report_lines.append("")
```

### Task 4: Update executive summary

Add synthesis patterns to executive summary:

```python
# In executive summary section, add:
for arb in ['openai', 'anthropic', 'google']:
    if arb in metrics['synthesis_detection']:
        m = metrics['synthesis_detection'][arb]
        report_lines.append(f"- **{arb.capitalize()} synthesis pattern:** {m['interpretation']} "
                          f"(unanimous: {m['synthesis_when_unanimous']['rate_pct']}%, "
                          f"split: {m['synthesis_when_split']['rate_pct']}%)")
```

---

## Verification Commands

After running the updated script:

```bash
cd /Users/brock/Documents/GitHub/federal-survey-concept-mapper/reports/03_harmonization_constraints

# 1. Run the script
python scripts/04_stage3_arbitration.py

# 2. Check synthesis rates match position_bias
python -c "
import json
with open('output/analysis/stage3_arbitration_metrics.json') as f:
    m = json.load(f)

print('=== CONSISTENCY CHECK ===')
for arb in ['openai', 'anthropic', 'google']:
    if arb in m['synthesis_detection'] and arb in m['position_bias']:
        sd = m['synthesis_detection'][arb]['synthesis_rate_overall']
        pb = m['position_bias'][arb]['synthesis_rate']
        match = '✓' if abs(sd - pb) < 0.5 else '✗ MISMATCH'
        print(f'{arb}: synthesis_detection={sd}%, position_bias={pb}% {match}')
"

# 3. Check new stratified metrics exist
python -c "
import json
with open('output/analysis/stage3_arbitration_metrics.json') as f:
    m = json.load(f)

print('=== STRATIFIED SYNTHESIS METRICS ===')
for arb in ['openai', 'anthropic', 'google']:
    if arb in m['synthesis_detection']:
        sd = m['synthesis_detection'][arb]
        print(f\"\n{arb}:\")
        print(f\"  Unanimous: {sd['synthesis_when_unanimous']['rate_pct']}% ({sd['synthesis_when_unanimous']['synthesis_count']}/{sd['synthesis_when_unanimous']['n']})\")
        print(f\"  Split: {sd['synthesis_when_split']['rate_pct']}% ({sd['synthesis_when_split']['synthesis_count']}/{sd['synthesis_when_split']['n']})\")
        print(f\"  Pattern: {sd['interpretation']}\")
"

# 4. Verify report has new section
grep -A 20 "Synthesis Behavior Analysis" output/analysis/stage3_arbitration_report.md
```

---

## Expected Results

Based on position_bias showing:
- OpenAI: 59.4% overall synthesis (949/1598)
- Anthropic: 77.2% overall synthesis (1234/1598)
- Google: 7.0% overall synthesis (35/503)

**Predicted patterns:**

| Arbitrator | Overall | Predicted Unanimous | Predicted Split | Predicted Pattern |
|------------|---------|---------------------|-----------------|-------------------|
| Google | 7% | ~5-10% | ~5-10% | deferential |
| OpenAI | 59% | ~50-60%? | ~60-70%? | moderate or always_synthesizes |
| Anthropic | 77% | ~75-80% | ~75-80% | always_synthesizes |

The key insight will be whether OpenAI/Anthropic synthesize MORE when raters disagree (efficient) or the same regardless (always_synthesizes).

---

## Files Modified

- `scripts/04_stage3_arbitration.py` - Main changes
- `output/analysis/stage3_arbitration_metrics.json` - Updated output
- `output/analysis/stage3_arbitration_report.md` - Updated report

---

## Success Criteria

1. ✓ `synthesis_rate_overall` matches `position_bias.synthesis_rate` for each arbitrator (within 0.5%)
2. ✓ New stratified metrics (`synthesis_when_unanimous`, `synthesis_when_split`) present
3. ✓ Pattern interpretation assigned to each arbitrator
4. ✓ Report includes updated synthesis behavior section
5. ✓ No runtime errors

---

## Notes

- The rater_df needs columns `openai_L1`, `anthropic_L1`, `google_L1` for unanimity check
- For Google arbitrator (CPS only), unanimity is determined using all three raters where available
- The confusion matrix TP/FN/FP/TN definitions follow Amendment A exactly
