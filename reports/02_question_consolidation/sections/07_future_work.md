# Future Work

## Immediate Extensions

### Additional Survey Pairs

The methodology developed here can be applied to additional Family 2 surveys:

| Survey Pair | Estimated Pairs | Expected Pattern |
|-------------|-----------------|------------------|
| SIPP-ACS | ~1,500-2,000 | Similar ~10-12% (income/program focus) |
| CE-ACS | ~800-1,200 | Lower ~5-8% (expenditure detail) |
| AHS-ACS | ~1,200-1,600 | Variable (housing construct differences) |

**Estimated cost:** ~$2-5 total for all three additional surveys

### Methodological Improvements

1. **Human validation sample**
   - 100-200 pairs with expert adjudication
   - Calibrate LLM accuracy against ground truth
   - Identify systematic bias patterns

2. **Construct mismatch classifier**
   - Train model to specifically detect this barrier type
   - Distinguish from reference_period_mismatch and related_but_distinct

3. **Cross-survey framing analysis**
   - Systematic comparison of reference period conventions
   - Identify coordination opportunities

---

## Research Questions

### Does Consolidation Potential Vary by Survey Domain?

We analyzed economic household surveys. Other domains may show different patterns:

| Domain | Hypothesis |
|--------|------------|
| Health surveys (NHIS, MEPS) | Higher - more demographic content |
| Education surveys (NCES) | Moderate - standardized constructs exist |
| Business surveys | Lower - specialized definitional needs |

### Can Reference Period Coordination Increase Consolidation?

The Hours/Week finding (26-29% consolidation due to habitual framing) suggests deliberate coordination could help. Research questions:

- Which surveys could adopt habitual framing without analytical loss?
- What's the cost-benefit of survey redesign vs. accepting current ceilings?

### What's the Actual Linkage Error Rate?

Our analysis assumes perfect linkage. Real implementation faces:
- Person-matching error
- Temporal misalignment (ACS from different month)
- Consent refusal
- Coverage gaps

A simulation study could model realistic consolidation under imperfect linkage.

---

## Technical Extensions

### Alternative Classification Approaches

- Fine-tuned models on survey question pairs
- Embedding-based similarity (failed for topic classification but might work for direct question comparison)
- Hybrid LLM + rule-based systems

### Visualization and Reporting

- Interactive consolidation explorer
- Survey-specific consolidation reports
- Policy briefing documents

### Integration with Survey Metadata

- Link to question skip logic
- Incorporate temporal collection windows
- Connect to survey purpose documentation

---

## Resource Summary

| Item | Cost |
|------|------|
| Completed analysis (FoodAPS + CPS) | ~$1.50 |
| Future surveys (SIPP + CE + AHS) | ~$3-5 |
| Human validation sample | TBD (analyst time) |
| Total API costs | <$10 |

---

*The question-level analysis framework is ready for extension. The primary constraint is analyst time for interpretation, not computational cost.*
