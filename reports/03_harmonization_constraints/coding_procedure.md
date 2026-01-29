# Coding Procedure: Harmonization Constraints

## Overview

This document operationalizes the taxonomy for systematic coding of non-consolidatable question pairs.

---

## Input Data

**Source files:**
- `output/question_matching/cps_comparison_merged.csv`
- `output/question_matching/foodaps_comparison_merged.csv`

**Filter criteria:**
- `classification` IN ('different_construct', 'related_not_equivalent', 'not_consolidatable')
- OR `consolidation_feasible` = False
- OR LLM reasoning indicates consolidation barriers

**Expected N:** ~500-800 pairs across both survey comparisons

---

## Sampling Strategy

### Phase 1: Taxonomy Development (Saturation-Based)

1. Random sample of 30 pairs from each survey comparison (60 total)
2. Code iteratively, refining taxonomy as new patterns emerge
3. **Saturation criterion:** Stop adding categories when 10 consecutive pairs fit existing taxonomy
4. Document all taxonomy revisions with rationale

### Phase 2: Full Coding

1. Apply finalized taxonomy to all non-consolidatable pairs
2. Use batch processing with spot-checks
3. Flag ambiguous cases for review

### Phase 3: Reliability Check

1. Randomly select 10% of coded pairs
2. Independent second coding (blind to first)
3. Compute Cohen's Kappa for:
   - Level 1 (constraint type)
   - Level 2 (subtype)
   - Feasibility
4. Resolve disagreements through discussion

---

## Coding Rules

### Rule 1: Primary Constraint

When multiple constraints apply, code the **primary** constraint that would need to be resolved first.

Example: A pair has both reference period mismatch (TC.1) and different response scales (RS.2).
- If harmonizing reference periods would still leave incompatible scales → code RS.2 as primary
- If fixing reference periods would make scales comparable → code TC.1 as primary

### Rule 2: Hierarchy for Ambiguous Cases

When constraint type is ambiguous, use this hierarchy:
1. CC (Construct) > TC (Temporal) - if the temporal difference implies a construct difference
2. CC (Construct) > RS (Response Scale) - if scale difference reflects construct difference
3. PC (Population) > MC (Mode) - if population difference is the binding constraint

### Rule 3: Specificity in Level 3

Level 3 (specific_conflict) should be concrete enough to inform remediation.

**Good:** "30-day recall vs 12-month recall for food expenditures"
**Bad:** "Different reference periods"

**Good:** "Employment includes unpaid family farm workers in CPS but not ACS"
**Bad:** "Different employment definitions"

### Rule 4: Feasibility Assessment

Base feasibility on what's achievable with **existing data**, not hypothetical redesign:

- **F1 (Direct recode):** Can transform Survey A responses to match Survey B categories through simple mapping
- **F2 (Statistical adjustment):** Requires modeling, bridging studies, or assumptions, but data exists
- **F3 (Incompatible):** No statistical fix; would require re-fielding or accepting non-comparability

### Rule 5: Document Reasoning

Every coded pair must have a `reasoning` field explaining the classification decision. This supports:
- Quality control
- Disambiguation of edge cases
- Training of future coders (human or LLM)

---

## Coding Template

```csv
pair_id,survey_a,survey_b,question_a,question_b,constraint_type,constraint_subtype,specific_conflict,feasibility,reasoning,additional_constraints,coder,timestamp
```

### Field Definitions

| Field | Type | Values | Required |
|-------|------|--------|----------|
| pair_id | str | From source merged CSV | Yes |
| survey_a | str | Survey name | Yes |
| survey_b | str | Survey name (typically ACS) | Yes |
| question_a | str | Full question text | Yes |
| question_b | str | Full question text | Yes |
| constraint_type | str | TC, CC, PC, RS, MC, PM | Yes |
| constraint_subtype | str | e.g., TC.1, CC.2 | Yes |
| specific_conflict | str | Free text, concrete | Yes |
| feasibility | str | F1, F2, F3 | Yes |
| reasoning | str | Explanation of coding decision | Yes |
| additional_constraints | str | Comma-separated codes if multiple apply | No |
| coder | str | Coder identifier | Yes |
| timestamp | datetime | ISO format | Yes |

---

## Quality Control Checkpoints

### After 20 pairs:
- [ ] Review taxonomy - any missing categories?
- [ ] Check distribution - is one category dominating? (may indicate over-broad definition)
- [ ] Review reasoning quality - specific enough?

### After 50 pairs:
- [ ] Saturation check - new categories emerging?
- [ ] Spot-check 10 pairs against taxonomy definitions
- [ ] Identify any systematic ambiguities

### After full coding:
- [ ] Distribution analysis by constraint type
- [ ] Cross-tabulate constraint type × feasibility
- [ ] Flag outliers for review

---

## Decision Log

Document all non-obvious coding decisions here for consistency:

| Date | Pair ID | Decision | Rationale |
|------|---------|----------|-----------|
| | | | |

---

## Edge Case Examples

### Example 1: Temporal vs Construct

**CPS:** "Did you work last week?"
**ACS:** "Did you work in the past 12 months?"

**Coding:** TC.1 (Reference period length), not CC.1
**Reasoning:** Both measure employment; the difference is recall window, not what "employment" means.
**Feasibility:** F2 - could model point-in-time from annual with assumptions about employment volatility.

### Example 2: Construct vs Response Scale

**Survey A:** "How many hours did you work?" (open numeric)
**Survey B:** "Did you work full-time or part-time?" (binary)

**Coding:** CC.2 (Operationalization), not RS.1
**Reasoning:** The issue isn't the response format per se - it's that one measures continuous hours while other measures a categorical classification. Even if Survey B had numeric response, they'd measure different things (hours vs employment status).
**Feasibility:** F3 - can't recover hours from full-time/part-time binary.

### Example 3: Multiple Constraints

**Survey A:** "In the past 30 days, how many times did you eat at a restaurant?" (adults 18+)
**Survey B:** "In the past 12 months, how often did your household eat meals away from home?" (all ages)

**Primary coding:** TC.1 (30-day vs 12-month)
**Additional:** PC.3 (18+ vs all ages), CC.2 (individual vs household)
**Feasibility:** F3 - too many differences to bridge
**Reasoning:** Even resolving temporal mismatch wouldn't help because unit of analysis differs (individual vs household).
