# Stage 3 QC Validation Report

**Generated:** 2026-01-31T06:20:22.433572
**Result:** 11/11 checks passed, 0 failed

## 1. Data Integrity

### Record Counts

- openai: 1,598
- anthropic: 1,598
- google: 751

### Duplicate Check: PASS

### Pair ID Coverage: PASS
- Verdict pairs: 1,598
- Source pairs: 1,702

### Schema Validation: PASS

## 2. Taxonomy Conformance

### l1_valid: PASS

### l2_format_valid: PASS

### feasibility_valid: PASS

### nhb_f1_check: PASS

## 3. Cross-Arbitrator Consistency

### Extreme Divergence (F1 vs F3): 2 pairs

| pair_id | OA feas | OA code | AN feas | AN code |
|---------|---------|---------|---------|---------|
| CPS_0000 | F3 | CC.2 | F1 | RS.1 |
| FOODAPS_0140 | F3 | CC.2 | F1 | RS.1 |

### Synthesis Rates

- openai: 59.4%
- anthropic: 77.2%
- google: 5.9%

## 4. Final Verdicts Validation

### Confidence Distribution

- HIGH: 1,458
- MODERATE: 112
- LOW: 28

### HIGH Confidence Check: PASS
- 0 HIGH-confidence pairs with no agreement

### Orphan Records: 0

### Survey Field: PASS

## 5. Bug Regression

### Google Rater Format: PASS
- Raw selected_rater still contains "Rater X" format; normalize_position() in 04_stage3_arbitration.py handles mapping. selected_rater_key has known upstream mapping issue for these values.

### Google Synthesis Rate: PASS
- Actual: 5.9%, Expected: ~7.0%

---

**Total checks:** 11, **Passed:** 11, **Failed:** 0