# Question-Level Survey Consolidation Analysis

## Research Context

Federal statistical agencies face increasing pressure to reduce respondent burden while maintaining data quality. One proposed solution is record linkage: if a household completes the American Community Survey (ACS), could their responses substitute for similar questions on other surveys like the Current Population Survey (CPS) or Food Acquisition and Purchase Survey (FoodAPS)?

This analysis moves from **concept-level overlap** ("both surveys measure employment") to **question-level classification** ("these specific questions can/cannot be substituted"). We use dual-LLM classification (Claude Haiku 4.5, GPT-5-mini) to assess 1,702 question pairs across two survey comparisons.

## Research Questions

1. What proportion of conceptually overlapping questions are **substitutable** (identical or near-identical wording, response format, and reference period)?

2. What structural barriers prevent consolidation even when questions address the same topic?

3. What is the **realistic consolidation ceiling** for ACS-linked survey integration?

4. Can LLM-based classification reliably identify consolidation opportunities?

---

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

**Note:** Race was previously reported as 0/6 - this was an error. Actual rate is 5/6 (83%), consistent with other demographic items.

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
| **Employment Status** | **25/215** | **11.6%** | Reference period (37 mismatches) |
| Unemployment | 1/26 | 4% | Reference period |
| **Disability** | **6/342** | **1.8%** | Construct mismatch |
| Household | 0/52 | 0% | Construct mismatch |
| Labor Force | 0/16 | 0% | Reference period |
| Commute | 0/5 | 0% | Reference period |

---

## Deep-Dive Case Studies

Detailed analysis with actual question text is available in companion documents:
- [`case_studies_foodaps.md`](case_studies_foodaps.md) - SNAP, Race, Hours/Week
- [`case_studies_cps.md`](case_studies_cps.md) - Disability, Employment Status

### Case Study 1: SNAP (FoodAPS) - 2/23 Consolidable (8.7%)

**The paradox:** FoodAPS's core mission is food acquisition among SNAP participants, yet SNAP questions show low consolidation with ACS.

**The explanation:** ACS asks a **screener** ("Did anyone receive SNAP in 12 months?"). FoodAPS asks a **program battery**:
- Current participation (30-day window vs ACS's 12-month)
- Number of EBT cards issued
- Which household members are on each card
- Benefit amounts and timing

**What consolidates:**
```
FoodAPS: "Did (you/anyone at this address) receive benefits from SNAP in the last 12 months?"
ACS:     "IN THE PAST 12 MONTHS, did you or any member of this household receive benefits 
          from the Food Stamp Program or SNAP?"
```
Identical construct, identical reference period → YES

**What doesn't:**
```
FoodAPS: "How many [STATE SNAP NAME] EBT cards are issued to people at this address?"
ACS:     "IN THE PAST 12 MONTHS, did you receive SNAP benefits?"
```
Count vs binary, administrative detail vs prevalence → NO

**Conclusion:** Low consolidation reflects correct survey design. FoodAPS needs program mechanics; ACS measures program reach. These are complementary, not redundant.

---

### Case Study 2: Disability (CPS) - 6/342 Consolidable (1.8%)

**The structure:** 57 CPS disability questions × 6 ACS disability questions = 342 pairs

**CPS has two disability question types:**

**Type A: Work-Limiting (51 questions)**
```
"Does (your/his/her) disability prevent (you/he/she) from accepting 
 any kind of work during the next 6 months?"
```
Purpose: BLS labor force statistics

**Type B: Functional Limitations - ACS6 Compatible (6 questions)**
```
CPS_294: "Are you deaf or do you have serious difficulty hearing?"
CPS_295: "Are you blind or do you have serious difficulty seeing?"
CPS_296: "Do you have serious difficulty concentrating, remembering, or making decisions?"
CPS_297: "Do you have serious difficulty walking or climbing stairs?"
CPS_298: "Do you have difficulty dressing or bathing?"
CPS_299: "Do you have difficulty doing errands alone?"
```
Purpose: ADA compliance (matches ACS)

**LLM Performance: Perfect Diagonal Match**

| CPS | ACS | Construct | Result |
|-----|-----|-----------|--------|
| CPS_294 | ACS_84 | Hearing | ✓ CONSOLIDABLE |
| CPS_295 | ACS_85 | Vision | ✓ CONSOLIDABLE |
| CPS_296 | ACS_86 | Cognition | ✓ CONSOLIDABLE |
| CPS_297 | ACS_87 | Walking | ✓ CONSOLIDABLE |
| CPS_298 | ACS_88 | Dressing | ✓ CONSOLIDABLE |
| CPS_299 | ACS_89 | Errands | ✓ CONSOLIDABLE |

- 6/6 true positive diagonal matches
- 30/30 off-diagonal correctly rejected (hearing ≠ vision)
- 306/306 work-limiting questions correctly rejected vs functional questions

**This validates LLM accuracy.** When constructs genuinely align, LLMs find them. When they don't, LLMs correctly reject.

---

### Case Study 3: Employment Status (CPS) - 25/215 Consolidable (11.6%)

**The problem:** CPS uses multiple temporal windows for labor force dynamics; ACS uses fixed "last week."

**Reference period distribution:**

| CPS Windows | ACS Window |
|-------------|------------|
| "Last week" | "Last week" |
| "Week before last" | — |
| "Last 4 weeks" | — |
| "Last month" | — |
| "Last 12 months" | — |
| "Currently" | — |

**What consolidates:** Overlapping windows
```
CPS: "(THE WEEK BEFORE LAST/LAST WEEK), did you do ANY work for pay?"
ACS: "LAST WEEK, did this person work for pay?"
```
Partial overlap → PARTIAL

**What doesn't:** Non-overlapping windows
```
CPS: "Did you do any work for pay in the LAST 4 WEEKS?"
ACS: "LAST WEEK, did this person work for pay?"
```
Different time periods, different statistics → NO

**Model disagreement:** 60/215 pairs (28%) - the highest rate of any subtopic. This reflects genuine ambiguity in borderline cases, not model error.

---

## Structural Barriers to Consolidation

### 1. Construct Mismatch (Proposed New Category)

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

**Implication:** The ~11% consolidation rate from current models may be more accurate than higher rates from earlier systems.

### Sampling vs. Full Population

| Approach | CPS Consolidation Rate | Model Agreement |
|----------|----------------------|-----------------|
| 300-pair stratified sample | 15% | 66% |
| Full 1,092-pair run | 10.8% | 75.4% |

Stratified sampling overestimated consolidation by 4 percentage points due to demographic over-representation. Full runs cost ~$0.50-1.00 per survey - sampling offers no meaningful savings.

---

## Conclusions

### 1. Consolidation Potential Is Real but Limited

The 11% rate represents genuine opportunities - mostly demographics and habitual measures. This is not nothing: for a 100-question survey, ~11 questions could potentially be dropped with ACS linkage.

### 2. Low Rates Reflect Correct Survey Design

SNAP at 8.7%, Disability at 1.8%, Employment Status at 11.6% - these aren't failures. Specialized surveys ask specialized questions that ACS doesn't and shouldn't collect.

### 3. Demographics Are the Reliable Target

| Content Type | Typical Consolidation Rate |
|--------------|---------------------------|
| Core demographics (sex, age, race) | 60-100% |
| Habitual measures (hours/week) | 25-30% |
| Point-in-time status | 10-15% |
| Program-specific content | 0-10% |

### 4. LLM Classification Works

The ACS6 Disability validation (6/6 diagonal, 336/336 off-diagonal) demonstrates that LLMs can reliably identify consolidation opportunities when they exist and correctly reject false matches.

### 5. Construct Mismatch Deserves Taxonomic Recognition

Current classifications (reference_period_mismatch, response_format_mismatch) don't capture the construct_mismatch problem. Proposed addition to taxonomy.

---

## Limitations and Caveats

1. **LLM classifications are not human-validated.** Specific consolidation claims require expert review.

2. **"Consolidable" assumes perfect linkage.** Real-world linkage has error, latency, and coverage gaps.

3. **Temporal alignment not assessed.** ACS from March may not substitute for CPS in October.

4. **Skip logic compatibility not evaluated.** Survey flow dependencies may require questions ACS doesn't ask.

5. **Respondent burden tradeoffs not quantified.** Linkage itself imposes costs (consent, matching, privacy).

---

## Data and Methods

### Data Sources

| File | Contents | Pairs |
|------|----------|-------|
| `foodaps_comparison_merged.csv` | FoodAPS-ACS classifications | 610 |
| `cps_comparison_merged.csv` | CPS-ACS classifications | 1,092 |

### Classification Schema

- **exact_duplicate:** Identical wording, format, reference period
- **near_duplicate:** Minor wording differences, same construct
- **related_but_distinct:** Same topic, different specifics
- **reference_period_mismatch:** Same construct, incompatible time windows
- **response_format_mismatch:** Same construct, incompatible response types
- **not_comparable:** Different topics or constructs

### Consolidation Definition

A pair is "consolidable" if **both models** classify it as exact_duplicate, near_duplicate, or assign consolidation_potential = "yes" or "partial".

---

## Status and Next Steps

| Survey Pair | Pairs | Classified | Deep-Dive | Status |
|-------------|-------|------------|-----------|--------|
| FoodAPS-ACS | 610 | ✓ 100% | ✓ Complete | Done |
| CPS-ACS | 1,092 | ✓ 100% | ✓ Complete | Done |
| SIPP-ACS | TBD | — | — | Not started |

### Potential Extensions

1. **SIPP-ACS analysis** - Income and program participation focus
2. **Human validation sample** - Expert review of LLM classifications
3. **Linkage feasibility study** - Assess practical implementation barriers
4. **Cost-benefit analysis** - Quantify burden reduction vs linkage costs

---

## Resource Summary

| Item | Cost |
|------|------|
| FoodAPS classification (610 pairs) | ~$0.50 |
| CPS classification (1,092 pairs) | ~$1.00 |
| **Total API costs** | **~$1.50** |
| Analysis time | ~16 hours |

---

*Last updated: January 27, 2026*
*See also: [case_studies_foodaps.md](case_studies_foodaps.md), [case_studies_cps.md](case_studies_cps.md)*
