# Example Question Pairs - Usage Guide

**Generated:** 2026-02-02
**Purpose:** Compelling examples for capstone slide deck

---

## Files Generated

### 1. `example_pairs_for_presentation.md`
Formatted examples ready for slides with:
- Full question text (source and ACS match)
- Feasibility verdict (F1/F2/F3)
- Barrier codes (for F3)
- Scoring metrics (Borda, Entropy, Triage quadrant)
- LLM reasoning (concise, 2-3 sentences)

**Usage:** Copy-paste directly into slide notes or text boxes.

### 2. `example_pairs_candidates.csv`
Spreadsheet with top 5 candidates per category for cherry-picking.

**Usage:** Review in Excel/Numbers to select final examples.

---

## Selection Criteria

### High Consolidability (F1)
✅ **Included:**
- Borda > 0.70, Entropy > 0.80
- Employment, education, health, food acquisition content
- Clear direct mapping examples

❌ **Excluded:**
- Demographic questions (age, race, sex) - expected overlap
- Administrative/metadata questions

**Examples:** Hours worked, earnings reporting, work status

### Medium Consolidability (F2)
✅ **Included:**
- Borda 0.40-0.70
- Shows clear transformation needs (temporal, scale, scope)
- Feasible with adjustment

❌ **Excluded:**
- Demographic questions

**Examples:** School enrollment periods, job availability timing, pay components

### Low/No Consolidability (F3)
✅ **Included:**
- Borda < 0.30
- CC (Construct/Concept) barrier preferred
- Illustrates fundamental mismatch

❌ **Excluded:**
- Demographic questions
- Administrative questions (interview readiness, replacement household status)

**Examples:** Work preferences vs. behavior, reasons for part-time vs. work status, paid time off vs. earnings

---

## Quality Notes

All examples are:
- ✅ Non-demographic (avoids "obvious overlap")
- ✅ Substantive content (not administrative)
- ✅ Clear construct illustration
- ✅ High agreement (unanimous or near-unanimous verdicts)

**Reasoning included:** Each example has the arbitrator's explanation to help tell the story.

---

## Recommendation for Slides

Use one example per category (3 total) in main deck:
- **HIGH:** CPS_105 or FOODAPS_184 (clear work/employment mapping)
- **MEDIUM:** CPS_284 (pay components) or FOODAPS_63 (temporal framing)
- **LOW:** CPS_108 (preference vs. behavior) or CPS_109 (reason vs. status)

Keep remaining examples as backup slides or appendix.

---

## Regenerating

To update examples with different criteria:

```bash
python scripts/extract_example_pairs.py
```

Edit threshold constants in script:
- `HIGH_BORDA_MIN = 0.7`
- `MEDIUM_BORDA_MIN = 0.4`
- `LOW_BORDA_MAX = 0.3`

Edit keyword filters:
- `AVOID_KEYWORDS` - demographics to exclude
- `ADMIN_KEYWORDS` - administrative questions to exclude
