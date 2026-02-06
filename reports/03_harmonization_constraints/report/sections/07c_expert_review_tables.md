# Appendix C: Expert Review Tables

This appendix describes the expert review deliverables generated from the analysis.

---

## Overview

Three CSV files provide complete question-level results for expert review and validation:

| File | Rows | Description |
|------|------|-------------|
| `expert_review_cps.csv` | 240 | CPS questions with ACS matches |
| `expert_review_foodaps.csv` | 140 | FoodAPS questions with ACS matches |
| `expert_review_combined.csv` | 380 | All questions combined |

**Location**: `reports/03_harmonization_constraints/output/analysis/`

---

## Table Schema

Each file contains 17 columns:

### Identification

| Column | Type | Description |
|--------|------|-------------|
| `survey` | string | Source survey (CPS or FOODAPS) |
| `source_q_id` | string | Source question identifier |
| `source_text` | string | Full source question text |
| `best_match_q_id` | string | Best matching ACS question identifier |
| `best_match_text` | string | Full ACS question text |
| `pair_id` | string | Unique pair identifier (source_target) |

### Classification

| Column | Type | Description |
|--------|------|-------------|
| `best_feasibility` | string | F1, F2, or F3 |
| `has_harmonizable_path` | boolean | True if F1 or F2 |
| `barrier_code` | string | CC.1, TC.2, etc. (if F3) |
| `confidence` | string | HIGH, MODERATE, or LOW |

### Scoring

| Column | Type | Description |
|--------|------|-------------|
| `score_borda` | float | Borda count [0, 1] - direction |
| `score_entropy` | float | Normalized entropy [0, 1] - stability |
| `score_composite` | float | Baseline composite score |
| `score_bayesian` | float | Bayesian score with priors |

### Triage

| Column | Type | Description |
|--------|------|-------------|
| `triage_quadrant` | string | Q1, Q2, Q3, or Q4 |

### Reasoning

| Column | Type | Description |
|--------|------|-------------|
| `reasoning_summary` | string | Explanation of classification |
| `arbitration_notes` | string | Additional notes from arbitration (if applicable) |

---

## Triage Quadrants

Questions are assigned to quadrants for prioritization:

### Q1: Confident Harmonizable (151 questions)

- **Borda**: High (≥0.167)
- **Entropy**: High (≥0.330)
- **Interpretation**: Models agree it's harmonizable
- **Action**: Auto-accept, spot-check recommended
- **Expert Review Priority**: Low

**Example**:
```
Source (CPS): "How many hours per week do you USUALLY work?"
Target (ACS): "What is your best estimate of hours per week you usually work?"
Feasibility: F1
Borda: 1.0, Entropy: 1.0
```

---

### Q2: Confident Non-Harmonizable (136 questions)

- **Borda**: Low (<0.167)
- **Entropy**: High (≥0.330)
- **Interpretation**: Models agree it's not consolidable
- **Action**: Auto-reject, low priority for review
- **Expert Review Priority**: Low

**Example**:
```
Source (CPS): "Do you WANT to work full-time (35+ hours)?"
Target (ACS): "Did you work for pay last week?"
Feasibility: F3 (CC.1)
Borda: 0.0, Entropy: 0.33
```

---

### Q3: Uncertain Accept (40 questions) ⚠️ PRIORITY

- **Borda**: High (≥0.167)
- **Entropy**: Low (<0.330)
- **Interpretation**: Leaning consolidable but unstable (models argued)
- **Action**: **EXPERT REVIEW REQUIRED** - highest priority
- **Expert Review Priority**: **HIGH**

**Why Priority?**
- High Borda suggests consolidation potential
- Low Entropy indicates disagreement or uncertainty
- These are "edge cases" that need human judgment

**Review Question**: Is consolidation truly feasible despite model disagreement?

---

### Q4: Uncertain Reject (53 questions)

- **Borda**: Low (<0.167)
- **Entropy**: Low (<0.330)
- **Interpretation**: Genuinely ambiguous (no clear direction, low agreement)
- **Action**: Expert review - secondary priority
- **Expert Review Priority**: Medium

**Why Secondary?**
- Low Borda suggests non-consolidable lean
- Low Entropy indicates genuine ambiguity
- Less actionable than Q3 (less clear consolidation potential)

**Review Question**: Can expert domain knowledge resolve ambiguity?

---

## Usage Guide

### For Expert Reviewers

**Step 1: Prioritize Q3 Questions (40 questions)**

Focus first on Q3 - these have consolidation potential but model uncertainty:

```bash
# Filter Q3 questions
grep ",Q3," expert_review_combined.csv > q3_priority_review.csv
```

**Review Criteria**:
- Does source question measure same construct as target?
- Are differences fixable (F2) or fundamental (F3)?
- Is consolidation desirable from policy/research perspective?

**Actions**:
- **Confirm F1/F2**: Validate consolidation is appropriate
- **Reclassify to F3**: If models missed fundamental barrier
- **Add notes**: Document reasoning for stakeholders

---

**Step 2: Review Q4 Questions (53 questions)**

After Q3, review Q4 - genuinely ambiguous cases:

```bash
# Filter Q4 questions
grep ",Q4," expert_review_combined.csv > q4_secondary_review.csv
```

**Review Criteria**:
- Why did models disagree?
- Is additional context needed?
- Does domain expertise resolve ambiguity?

---

**Step 3: Spot-Check Q1/Q2 (287 questions)**

Sample Q1 and Q2 to validate auto-processing quality:

```bash
# Sample 10% of Q1 questions
grep ",Q1," expert_review_combined.csv | shuf -n 15 > q1_spot_check.csv

# Sample 10% of Q2 questions
grep ",Q2," expert_review_combined.csv | shuf -n 14 > q2_spot_check.csv
```

**Review Criteria**:
- Are high-confidence consolidable (Q1) classifications correct?
- Are high-confidence non-consolidable (Q2) classifications correct?
- Any systematic errors that suggest prompt refinement?

---

### For Data Users

**Finding Consolidable Questions**:

```bash
# All consolidable questions (F1 + F2)
grep ",True," expert_review_combined.csv > consolidable_questions.csv

# Direct recode only (F1)
grep ",F1," expert_review_combined.csv > f1_direct_recode.csv

# Statistical adjustment (F2)
grep ",F2," expert_review_combined.csv > f2_statistical_adjustment.csv
```

**Finding Specific Topics**:

```bash
# Employment questions (example)
grep -i "work\|employ\|job\|hour" expert_review_combined.csv > employment_questions.csv

# Income questions (example)
grep -i "income\|earn\|wage\|salary" expert_review_combined.csv > income_questions.csv
```

---

### For Survey Designers

**Identifying Patterns**:

```bash
# Group by barrier code to see common failure modes
cut -d',' -f9 expert_review_combined.csv | sort | uniq -c | sort -rn

# Group by feasibility
cut -d',' -f7 expert_review_combined.csv | sort | uniq -c
```

**Use Cases**:
- **Questionnaire design**: Identify wording patterns that enable/prevent harmonization
- **New question development**: Check if similar questions already harmonized
- **Cross-survey integration**: Plan data linkage based on consolidable variables

---

## Summary Statistics

### Overall Distribution

| Category | CPS | FoodAPS | Combined |
|----------|-----|---------|----------|
| **Total** | 240 | 140 | 380 |
| **F1** | 37 (15.4%) | 23 (16.4%) | 60 (15.8%) |
| **F2** | 63 (26.3%) | 45 (32.1%) | 108 (28.4%) |
| **F3** | 140 (58.3%) | 72 (51.4%) | 212 (55.8%) |
| **Harmonizable** | 100 (41.7%) | 68 (48.6%) | 168 (44.2%) |

### Triage Distribution

| Quadrant | CPS | FoodAPS | Combined |
|----------|-----|---------|----------|
| **Q1** (Auto-accept) | 94 (39.2%) | 57 (40.7%) | 151 (39.7%) |
| **Q2** (Auto-reject) | 84 (35.0%) | 52 (37.1%) | 136 (35.8%) |
| **Q3** (Priority review) | 26 (10.8%) | 14 (10.0%) | 40 (10.5%) |
| **Q4** (Secondary review) | 36 (15.0%) | 17 (12.1%) | 53 (13.9%) |

### Expert Review Load

| Category | Questions | % of Total |
|----------|-----------|------------|
| **Auto-processed** (Q1 + Q2) | 287 | 75.5% |
| **Expert review** (Q3 + Q4) | 93 | 24.5% |
| **Priority review** (Q3) | 40 | 10.5% |

---

## Validation Checklist

When validating results, check:

- [ ] All 380 questions have exactly one best match
- [ ] F1/F2 questions have `has_harmonizable_path = True`
- [ ] F3 questions have valid barrier code (CC.*, TC.*, RS.*, PC.*, MC.*, PM.*)
- [ ] Borda scores in [0, 1]
- [ ] Entropy scores in [0, 1]
- [ ] Triage quadrant matches Borda-Entropy rules
- [ ] Reasoning summary provided for all questions
- [ ] No missing data in required fields

---

## Contact Information

For questions about expert review tables:
- **Technical issues**: See `docs/SOFTWARE.md` for script documentation
- **Methodology questions**: See this report's Methodology section
- **Data corrections**: Submit corrections via project repository

---

## Next Steps

1. **Expert validation**: Complete Q3/Q4 review
2. **Quality assessment**: Evaluate classification accuracy
3. **Feedback integration**: Refine classifications based on expert input
4. **Consolidation pilots**: Test F1 recommendations in practice
5. **Documentation updates**: Incorporate lessons learned

---

**Files Ready for Review**:
- `output/analysis/expert_review_cps.csv` (240 rows)
- `output/analysis/expert_review_foodaps.csv` (140 rows)
- `output/analysis/expert_review_combined.csv` (380 rows)

**Status**: ✅ Ready for expert validation
