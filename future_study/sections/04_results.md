# Results

## Executive Summary

### Key Finding: ~11% Consolidation Potential, Structurally Bounded

| Survey Pair | Total Pairs | Both Models Agree Consolidable | Rate |
|-------------|-------------|-------------------------------|------|
| FoodAPS-ACS | 610 | 74 | 12.1% |
| CPS-ACS | 1,092 | 118 | 10.8% |
| **Combined** | **1,702** | **192** | **11.3%** |

Both surveys converge on ~11% regardless of their different missions (food behavior vs labor force). This convergence suggests a **structural ceiling** rather than survey-specific limitations.

### Why Only 11%?

1. **Demographics consolidate well** (60-100%): Sex, age, race are stable characteristics with standardized constructs
2. **Habitual measures partially consolidate** (~26%): "Usually/normally" framing aligns across surveys  
3. **Point-in-time measures rarely consolidate** (~4-12%): Reference period mismatches block substitution
4. **Construct mismatches block consolidation entirely** (0-2%): Same topic, different operationalization

### LLM Validation: High Accuracy on Clear Cases

The CPS Disability analysis provides strong validation:
- **6/6 ACS6 standardized question matches identified** (perfect diagonal)
- **336/336 non-matching pairs correctly rejected**
- Model agreement: 94.7% on Disability subtopic

---

## Detailed Results

### FoodAPS-ACS (610 pairs)

#### Classification Distribution

| Classification | Claude Haiku 4.5 | GPT-5-mini |
|----------------|------------------|------------|
| related_but_distinct | 283 (46%) | 419 (69%) |
| not_comparable | 179 (29%) | 53 (9%) |
| near_duplicate | 44 (7%) | 28 (5%) |
| response_format_mismatch | 38 (6%) | 32 (5%) |
| reference_period_mismatch | 36 (6%) | 39 (6%) |
| exact_duplicate | 30 (5%) | 39 (6%) |

#### Consolidation by Subtopic

| Subtopic | Consolidable/Total | Rate | Pattern |
|----------|-------------------|------|---------|
| Education | 2/2 | 100% | Demographic |
| Tenure (Own/Rent) | 1/1 | 100% | Demographic |
| Sex | 24/27 | 89% | Demographic |
| **Race** | **5/6** | **83%** | Demographic |
| Age | 6/9 | 67% | Demographic |
| Relationship | 3/6 | 50% | Demographic |
| Hours/Week, Weeks/Year | 16/56 | 29% | Habitual framing |
| Marital Status | 2/8 | 25% | Demographic |
| Veterans | 5/36 | 14% | Mixed |
| Employment Status | 6/60 | 10% | Point-in-time |
| **SNAP** | **2/23** | **8.7%** | Screener vs battery |
| Earnings | 3/90 | 3% | Reference period |
| School Enrollment | 2/65 | 3% | Reference period |
| Costs | 1/54 | 2% | Construct mismatch |
| Household | 1/72 | 1% | Construct mismatch |
| Disability | 0/12 | 0% | Construct mismatch |
| Commute | 0/55 | 0% | Reference period |
| Computer/Internet | 0/12 | 0% | Construct mismatch |
| Health Insurance | 0/6 | 0% | Construct mismatch |

---

### CPS-ACS (1,092 pairs)

#### Classification Distribution

| Classification | Claude Haiku 4.5 | GPT-5-mini |
|----------------|------------------|------------|
| related_but_distinct | 693 (63%) | 781 (72%) |
| not_comparable | 141 (13%) | 19 (2%) |
| near_duplicate | 83 (8%) | 54 (5%) |
| reference_period_mismatch | 77 (7%) | 71 (7%) |
| response_format_mismatch | 63 (6%) | 103 (9%) |
| exact_duplicate | 35 (3%) | 64 (6%) |

#### Consolidation by Subtopic

| Subtopic | Consolidable/Total | Rate | Pattern |
|----------|-------------------|------|---------|
| Sex | 3/3 | 100% | Demographic |
| Hispanic Origin | 6/9 | 67% | Demographic |
| Occupation | 10/17 | 59% | Standardized codes |
| Commissions | 1/2 | 50% | Small N |
| Education | 2/5 | 40% | Demographic |
| Age | 3/9 | 33% | Demographic |
| Citizenship | 1/3 | 33% | Demographic |
| Relationship | 8/30 | 27% | Demographic |
| Hours/Week, Weeks/Year | 44/168 | 26% | Habitual framing |
| Veterans | 2/8 | 25% | Demographic |
| Race | 2/9 | 22% | Demographic |
| Foreign Born | 1/6 | 17% | Demographic |
| Earnings | 17/138 | 12% | Reference period |
| Marital Status | 1/8 | 12% | Demographic |
| Population | 1/8 | 12% | Response format |
| School Enrollment | 1/10 | 10% | Reference period |
| **Employment Status** | **25/215** | **11.6%** | Reference period |
| Unemployment | 1/26 | 4% | Reference period |
| **Disability** | **6/342** | **1.8%** | Construct mismatch |
| Household | 0/52 | 0% | Construct mismatch |
| Labor Force | 0/16 | 0% | Reference period |
| Commute | 0/5 | 0% | Reference period |

---

## Structural Barriers to Consolidation

### 1. Construct Mismatch

**Definition:** Questions address the same topic but operationalize different constructs serving different analytical purposes.

| Topic | Survey A Construct | Survey B Construct | Substitutable? |
|-------|-------------------|-------------------|----------------|
| Disability | Work-limiting | Functional limitation | No |
| SNAP | Program mechanics | Program prevalence | No |
| Employment | Labor force flows | Point-in-time status | Partial |

**Implication:** Topic-level overlap analysis dramatically overestimates consolidation potential.

### 2. Reference Period Incompatibility

| Reference Type | Consolidation Potential |
|----------------|------------------------|
| Habitual ("usually/normally") | High - no temporal anchor |
| Same specific window | High - direct comparison |
| Overlapping windows | Partial - subset relationship |
| Non-overlapping windows | Low - different statistics |

### 3. Screener vs. Battery Design

Surveys collect the "same thing" at different depths:
- **Screener:** "Did anyone receive SNAP?" (yes/no)
- **Battery:** "How much? When? Which cards? Who's covered?"

ACS optimizes for breadth (many topics, shallow). Specialized surveys optimize for depth (few topics, detailed). These are complementary designs.

### 4. Response Format Differences

Even identical constructs may use incompatible formats:
- Count vs binary ("How many?" vs "Any?")
- Roster vs aggregate ("Who specifically?" vs "Anyone?")
- Continuous vs categorical ("Exact amount?" vs "Range?")

---

## Methodological Findings

### LLM Classification Performance

| Metric | FoodAPS-ACS | CPS-ACS |
|--------|-------------|---------|
| Model agreement | 68.2% | 75.4% |
| Agreement on consolidable | 74/74 (100%) | 118/118 (100%) |
| Disability diagonal accuracy | N/A | 6/6 (100%) |

**Interpretation:** When both models agree on consolidation, confidence is high. Disagreements indicate genuine ambiguity warranting human review.

### Model Generation Effects

Newer models (Claude Haiku 4.5, GPT-5-mini) showed **lower consolidation rates** than earlier models tested during development. This pattern is consistent with improved nuance handling:
- Better detection of reference period mismatches
- Better discrimination of construct differences
- More conservative on borderline cases

### Sampling vs. Full Population

| Approach | CPS Consolidation Rate | Model Agreement |
|----------|----------------------|-----------------|
| 300-pair stratified sample | 15% | 66% |
| Full 1,092-pair run | 10.8% | 75.4% |

Stratified sampling overestimated consolidation by 4 percentage points due to demographic over-representation. Full runs cost ~$0.50-1.00 per survey - sampling offers no meaningful savings.

---

## Consolidation Patterns by Content Type

| Content Type | Typical Consolidation Rate | Rationale |
|--------------|---------------------------|-----------|
| Core demographics (sex, age, race) | 60-100% | Stable characteristics, standardized constructs |
| Habitual measures (hours/week) | 25-30% | "Usually/normally" framing aligns |
| Point-in-time status | 10-15% | Reference period mismatches |
| Program-specific content | 0-10% | Specialized needs require specialized questions |

---

## Data Sources

| File | Contents | Pairs |
|------|----------|-------|
| `data/foodaps_comparison_merged.csv` | FoodAPS-ACS classifications | 610 |
| `data/cps_comparison_merged.csv` | CPS-ACS classifications | 1,092 |

### Classification Schema

- **exact_duplicate:** Identical wording, format, reference period
- **near_duplicate:** Minor wording differences, same construct
- **related_but_distinct:** Same topic, different specifics
- **reference_period_mismatch:** Same construct, incompatible time windows
- **response_format_mismatch:** Same construct, incompatible response types
- **not_comparable:** Different topics or constructs

### Consolidation Definition

A pair is "consolidable" if **both models** classify it as exact_duplicate, near_duplicate, or assign consolidation_potential = "yes" or "partial".
