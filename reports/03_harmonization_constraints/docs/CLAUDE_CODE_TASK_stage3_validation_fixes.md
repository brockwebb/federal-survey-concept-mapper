# Claude Code Task: Stage 3 Validation Fixes

**Priority:** HIGH  
**Estimated effort:** 30-45 min  
**Context:** Stage 3 arbitration analysis is ~90% complete but fails spec validation on synthesis detection metrics and has minor structural gaps.

---

## Files to Modify

- **Script:** `reports/03_harmonization_constraints/scripts/04_stage3_arbitration.py`
- **Spec:** `reports/03_harmonization_constraints/docs/SPEC_R03_S3_001_arbitration_analysis.md` (reference only)
- **Output:** `reports/03_harmonization_constraints/output/analysis/stage3_arbitration_metrics.json`

---

## Task 1: Add Synthesis Detection Metrics

The spec (Section 3.3) requires precision/recall/F1 for synthesis detection per arbitrator. Currently missing.

### Definition

**Synthesis detection = When raters were unanimous, did arbitrator select "synthesis"?**

- **True Positive (TP):** Raters unanimous AND arbitrator `selected_rater_key == 'synthesis'`
- **False Negative (FN):** Raters unanimous AND arbitrator selected single rater (not synthesis)
- **False Positive (FP):** Raters NOT unanimous AND arbitrator selected synthesis
- **True Negative (TN):** Raters NOT unanimous AND arbitrator selected single rater

Metrics:
```
Precision = TP / (TP + FP)
Recall = TP / (TP + FN)  
F1 = 2 * (Precision * Recall) / (Precision + Recall)
```

### Implementation

Add new function after `compute_arbitrator_rater_concordance()`:

```python
def compute_synthesis_detection(arb, raters):
    """Compute synthesis detection precision/recall/F1 per arbitrator.
    
    Synthesis detection: Did arbitrator correctly identify when all 3 raters agreed?
    - TP: Raters unanimous AND arbitrator chose synthesis
    - FN: Raters unanimous AND arbitrator chose single rater
    - FP: Raters NOT unanimous AND arbitrator chose synthesis
    - TN: Raters NOT unanimous AND arbitrator chose single rater
    """
    # Prep rater data - check unanimity on L1
    raters = raters.copy()
    for r in ['openai', 'anthropic', 'google']:
        raters[f'L1_{r}'] = raters[f'primary_barrier_{r}'].apply(extract_l1)
    
    def is_unanimous_l1(row):
        votes = [row['L1_openai'], row['L1_anthropic'], row['L1_google']]
        return len(set(votes)) == 1
    
    raters['raters_unanimous'] = raters.apply(is_unanimous_l1, axis=1)
    
    results = {}
    
    for arb_name, arb_df in arb.items():
        # Merge arbitrator decisions with rater unanimity
        merged = arb_df[['pair_id', 'selected_rater_key']].merge(
            raters[['pair_id', 'raters_unanimous']],
            on='pair_id',
            how='inner'
        )
        
        merged['arb_chose_synthesis'] = merged['selected_rater_key'] == 'synthesis'
        
        # Confusion matrix
        tp = ((merged['raters_unanimous']) & (merged['arb_chose_synthesis'])).sum()
        fn = ((merged['raters_unanimous']) & (~merged['arb_chose_synthesis'])).sum()
        fp = ((~merged['raters_unanimous']) & (merged['arb_chose_synthesis'])).sum()
        tn = ((~merged['raters_unanimous']) & (~merged['arb_chose_synthesis'])).sum()
        
        # Metrics
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        results[arb_name] = {
            "n_pairs": len(merged),
            "n_raters_unanimous": int(merged['raters_unanimous'].sum()),
            "n_raters_split": int((~merged['raters_unanimous']).sum()),
            "confusion_matrix": {
                "TP": int(tp),
                "FN": int(fn),
                "FP": int(fp),
                "TN": int(tn)
            },
            "precision": round(float(precision), 3),
            "recall": round(float(recall), 3),
            "f1": round(float(f1), 3),
            "synthesis_rate_overall": round(float(merged['arb_chose_synthesis'].mean() * 100), 1)
        }
    
    return results
```

### Call in main()

After concordance computation (~line 520), add:

```python
    # Step 4b: Synthesis detection
    print("\nStep 4b: Synthesis detection accuracy...")
    synthesis_detection = compute_synthesis_detection(arb, raters)
    for name, data in synthesis_detection.items():
        print(f"  {name}: precision={data['precision']}, recall={data['recall']}, F1={data['f1']}")
```

### Add to metrics dict

In the `metrics = {...}` assembly (~line 560), add:

```python
        "synthesis_detection": synthesis_detection,
```

### Add to report

In `generate_report()`, after the Concordance section, add:

```python
    # --- Synthesis Detection ---
    lines.append("## 4b. Synthesis Detection Accuracy")
    lines.append("")
    lines.append("**Question:** When raters were unanimous, did the arbitrator correctly select 'synthesis'?")
    lines.append("")
    sd = metrics.get('synthesis_detection', {})
    lines.append("| Arbitrator | n | Unanimous | Precision | Recall | F1 | Synthesis Rate |")
    lines.append("|------------|---|-----------|-----------|--------|-------|----------------|")
    for arb_name in ARBITRATORS:
        d = sd.get(arb_name, {})
        if not d:
            continue
        lines.append(
            f"| {arb_name} | {d.get('n_pairs', '?'):,} | "
            f"{d.get('n_raters_unanimous', '?'):,} | "
            f"{d.get('precision', '?')} | "
            f"{d.get('recall', '?')} | "
            f"{d.get('f1', '?')} | "
            f"{d.get('synthesis_rate_overall', '?')}% |"
        )
    lines.append("")
    lines.append("*Precision = correctly chose synthesis when unanimous / all synthesis selections*")
    lines.append("*Recall = correctly chose synthesis when unanimous / all unanimous cases*")
    lines.append("")
```

---

## Task 2: Fix Metadata Structure

Update metadata to match spec schema.

In `main()`, update the metadata dict (~line 545):

```python
    metrics = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "spec_version": "SPEC-R03-S3-001 v1.0",
            "script": "scripts/04_stage3_arbitration.py",
            "two_way_n": len(arb.get('openai', [])),
            "three_way_n": len(arb.get('google', [])),
            "openai_count": len(arb.get('openai', [])),
            "anthropic_count": len(arb.get('anthropic', [])),
            "google_count": len(arb.get('google', [])),
            "google_limitation": "CPS only, rate-limited at 250/day",
            "tiebreaker": "OpenAI arbitrator used for two-way disagreements"
        },
        ...
    }
```

---

## Task 3: Add Verdict Rate Metrics

The spec requires `unanimous_rate`, `majority_rate`, `split_rate` in addition to counts.

After constructing `verdicts_df` in main(), compute rates:

```python
    # Compute verdict rates
    total_verdicts = len(verdicts_df)
    
    # Unanimous = both OA and AN agree on L1 AND feasibility
    unanimous_count = (verdicts_df['L1_agree_oa_an'] & verdicts_df['feas_agree_oa_an']).sum()
    
    # For three-way subset, check if Google also agrees
    if 'L1_go' in verdicts_df.columns:
        three_way_mask = verdicts_df['has_google']
        three_way_unanimous = (
            verdicts_df.loc[three_way_mask, 'L1_agree_oa_an'] & 
            verdicts_df.loc[three_way_mask, 'feas_agree_oa_an'] &
            (verdicts_df.loc[three_way_mask, 'L1_oa'] == verdicts_df.loc[three_way_mask, 'L1_go']) &
            (verdicts_df.loc[three_way_mask, 'final_feasibility_oa'] == verdicts_df.loc[three_way_mask, 'final_feasibility_go'])
        ).sum()
    else:
        three_way_unanimous = 0
```

Update the verdict_confidence section in metrics:

```python
        "final_verdict_summary": {
            "total": total_verdicts,
            "confidence_distribution": {k: int(v) for k, v in confidence_dist.items()},
            "unanimous_rate": round(float(unanimous_count / total_verdicts * 100), 1),
            "two_way_agreement_rate": round(float(
                (verdicts_df['L1_agree_oa_an'] | verdicts_df['feas_agree_oa_an']).sum() / total_verdicts * 100
            ), 1),
            "three_way_coverage": round(float(verdicts_df['has_google'].sum() / total_verdicts * 100), 1)
        }
```

Replace:
```python
        "verdict_confidence": {k: int(v) for k, v in confidence_dist.items()}
```

With:
```python
        "final_verdict_summary": { ... }  # as above
```

---

## Task 4: Update Report Executive Summary

Add synthesis detection highlight to executive summary in `generate_report()`:

After the existing summary bullets, add:

```python
    sd = metrics.get('synthesis_detection', {})
    if sd:
        # Find lowest F1
        f1_scores = [(name, d.get('f1', 0)) for name, d in sd.items()]
        min_f1 = min(f1_scores, key=lambda x: x[1])
        max_f1 = max(f1_scores, key=lambda x: x[1])
        lines.append(f"- **Synthesis detection F1:** {min_f1[0]}={min_f1[1]}, {max_f1[0]}={max_f1[1]}")
```

---

## Verification Steps

After making changes:

1. **Run the script:**
   ```bash
   cd /Users/brock/Documents/GitHub/federal-survey-concept-mapper/reports/03_harmonization_constraints
   python scripts/04_stage3_arbitration.py
   ```

2. **Verify synthesis_detection in JSON:**
   ```bash
   python3 -c "
   import json
   with open('output/analysis/stage3_arbitration_metrics.json') as f:
       m = json.load(f)
   print('synthesis_detection present:', 'synthesis_detection' in m)
   if 'synthesis_detection' in m:
       for name, data in m['synthesis_detection'].items():
           print(f'  {name}: P={data[\"precision\"]}, R={data[\"recall\"]}, F1={data[\"f1\"]}')
   "
   ```

3. **Verify metadata structure:**
   ```bash
   python3 -c "
   import json
   with open('output/analysis/stage3_arbitration_metrics.json') as f:
       m = json.load(f)
   meta = m['metadata']
   print('spec_version:', meta.get('spec_version'))
   print('two_way_n:', meta.get('two_way_n'))
   print('three_way_n:', meta.get('three_way_n'))
   "
   ```

4. **Verify final_verdict_summary:**
   ```bash
   python3 -c "
   import json
   with open('output/analysis/stage3_arbitration_metrics.json') as f:
       m = json.load(f)
   print('final_verdict_summary:', json.dumps(m.get('final_verdict_summary'), indent=2))
   "
   ```

5. **Check report has new section:**
   ```bash
   grep -A10 "Synthesis Detection" output/analysis/stage3_arbitration_report.md
   ```

---

## Expected Outcomes

After fixes, the metrics JSON should have:

```json
{
  "metadata": {
    "spec_version": "SPEC-R03-S3-001 v1.0",
    "two_way_n": 1598,
    "three_way_n": 503,
    ...
  },
  "synthesis_detection": {
    "openai": {"precision": 0.xx, "recall": 0.xx, "f1": 0.xx, ...},
    "anthropic": {"precision": 0.xx, "recall": 0.xx, "f1": 0.xx, ...},
    "google": {"precision": 0.xx, "recall": 0.xx, "f1": 0.xx, ...}
  },
  "final_verdict_summary": {
    "total": 1598,
    "confidence_distribution": {"HIGH": 1458, "MODERATE": 112, "LOW": 28},
    "unanimous_rate": xx.x,
    ...
  }
}
```

---

## Notes

- The synthesis detection metrics will likely show Google has very low recall (7% synthesis rate observed in position_bias)
- This is a known finding, not a bug - document in report interpretation
- Anthropic should have highest recall (~77% synthesis rate)
- OpenAI intermediate (~59% synthesis rate)
