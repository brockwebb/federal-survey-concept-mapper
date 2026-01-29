# CPS-ACS Deep Dive: Case Studies in Survey Consolidation

## Executive Summary

This document provides detailed analysis of CPS-ACS question pairs, focusing on two subtopics that reveal fundamental barriers to survey consolidation:

1. **Disability (1.8% consolidable)**: A textbook case of construct mismatch - CPS measures work-limiting disability while ACS measures functional limitations. The 6 consolidable pairs are exactly the ACS6 standardized questions, validating LLM accuracy.

2. **Employment Status (11.6% consolidable)**: Reference period incompatibility - CPS uses multiple temporal windows for labor force dynamics while ACS uses fixed "last week" snapshots.

Key findings:
- LLMs correctly identify ACS6 disability questions with **100% precision** (6/6 diagonal matches)
- Employment Status has **28% model disagreement** - the highest of any subtopic
- CPS's multi-window temporal design is structurally incompatible with ACS consolidation

---

## Case Study 1: Disability - 6/342 Consolidable (1.8%)

### The Structure

The Disability subtopic contains 342 pairs formed from:
- **57 unique CPS disability questions** × **6 unique ACS disability questions**

This combinatorial structure reveals a critical pattern: CPS has two fundamentally different types of disability questions.

### CPS Disability Question Types

**Type A: Work-Limiting Disability (51 questions)**
```
"(Do/Does) (name/you) have a disability that prevents (you/he/she) from 
 accepting any kind of work during the next 6 months?"

"Does (your/his/her) disability prevent (you/he/she) from accepting any 
 kind of work during the next 6 months?"

"Does (your/his/her) disability continue to prevent (you/he/she) from 
 doing any kind of work for the next 6 months?"
```

**Purpose:** Labor force participation measurement for BLS employment statistics

**Type B: Functional Limitations - ACS6 Compatible (6 questions)**
```
CPS_294: "(Are you/Is NAME) deaf or (do you/does NAME) have serious difficulty hearing?"
CPS_295: "(Are you/Is NAME) blind or (do you/does NAME) have serious difficulty seeing?"
CPS_296: "Because of a physical, mental, or emotional condition, (do you/does NAME) 
          have serious difficulty concentrating, remembering, or making decisions?"
CPS_297: "(Do you/Does NAME) have serious difficulty walking or climbing stairs?"
CPS_298: "(Do you/Does NAME) have difficulty dressing or bathing?"
CPS_299: "Because of a physical, mental, or emotional condition, (do you/does NAME) 
          have difficulty doing errands alone such as visiting a doctor's office or shopping?"
```

**Purpose:** ADA compliance, accessibility planning, disability prevalence (matches ACS purpose)

### ACS Disability Questions (The ACS6)

The ACS uses the standardized ACS6 battery mandated for federal surveys:

```
ACS_84: "Is this person deaf or does he/she have serious difficulty hearing?"
ACS_85: "Is this person blind or does he/she have serious difficulty seeing even when wearing glasses?"
ACS_86: "Because of a physical, mental, or emotional condition, does this person have serious 
         difficulty concentrating, remembering, or making decisions?"
ACS_87: "Does this person have serious difficulty walking or climbing stairs?"
ACS_88: "Does this person have difficulty dressing or bathing?"
ACS_89: "Because of a physical, mental, or emotional condition, does this person have difficulty 
         doing errands alone such as visiting a doctor's office or shopping?"
```

### LLM Validation: Perfect Diagonal Match

The 6 consolidable pairs form a **perfect 1:1 diagonal** between CPS Type B and ACS questions:

| CPS Question | ACS Question | Construct | Claude | GPT |
|--------------|--------------|-----------|--------|-----|
| CPS_294 | ACS_84 | Hearing | partial | yes |
| CPS_295 | ACS_85 | Vision | yes | yes |
| CPS_296 | ACS_86 | Cognition | yes | yes |
| CPS_297 | ACS_87 | Walking | yes | yes |
| CPS_298 | ACS_88 | Dressing | yes | partial |
| CPS_299 | ACS_89 | Errands | partial | yes |

**Off-diagonal pairs correctly rejected:**

| Pair | Result | Example |
|------|--------|---------|
| CPS_294 (hearing) ↔ ACS_85 (vision) | NO/NO | Different functional domains |
| CPS_295 (vision) ↔ ACS_86 (cognition) | NO/NO | Different functional domains |
| CPS_296 (cognition) ↔ ACS_87 (walking) | NO/NO | Different functional domains |

**All 30 off-diagonal CPS Type B pairs:** Correctly classified as non-consolidable

**All 306 CPS Type A pairs:** Correctly classified as non-consolidable (work-limiting ≠ functional)

### Why Work-Limiting ≠ Functional Limitations

**CPS Work-Limiting Question:**
```
"Does (your/his/her) disability prevent (you/he/she) from accepting 
 any kind of work during the next 6 months?"
```

**Construct:** Binary assessment of labor force participation barrier
**Use case:** BLS unemployment statistics, labor force attachment
**Reference period:** Forward-looking (next 6 months)

**ACS Functional Limitation Question:**
```
"Does this person have serious difficulty walking or climbing stairs?"
```

**Construct:** Specific functional capacity in daily living
**Use case:** ADA compliance, accessibility planning, disability prevalence
**Reference period:** Current/ongoing

**Why they can't substitute:**

1. **Different constructs:** "Can you work?" vs "Can you walk?" are different questions even for the same person
2. **Different analytical purposes:** Labor economics vs civil rights compliance
3. **Not derivable:** Knowing someone has difficulty walking doesn't tell you if they can work
4. **Policy implications differ:** One informs unemployment insurance, the other informs accessibility requirements

### Classification Accuracy

| Metric | Value |
|--------|-------|
| True positives (ACS6 diagonal) | 6/6 (100%) |
| True negatives (off-diagonal + Type A) | 336/336 (100%) |
| Model agreement on consolidable | 6/6 (100%) |
| Model agreement overall | 324/342 (94.7%) |

**This is the strongest validation of LLM classification accuracy in the dataset.**

---

## Case Study 2: Employment Status - 25/215 Consolidable (11.6%)

### The Reference Period Problem

Employment Status shows the clearest example of temporal incompatibility between surveys.

### The Data

| Metric | Value |
|--------|-------|
| Total pairs | 215 |
| Claude consolidable | 38 (17.7%) |
| GPT consolidable | 52 (24.2%) |
| **Both agree consolidable** | **25 (11.6%)** |
| Reference period mismatches | 37 (17.2%) |
| **Model disagreements** | **60 (27.9%)** |

The 28% disagreement rate is the **highest of any subtopic** - reflecting genuine ambiguity in borderline cases.

### Reference Period Distribution

**CPS Employment Questions:**

| Reference Period | Count | % |
|------------------|-------|---|
| Not specified | 27 | 12.6% |
| Last 4 weeks | 20 | 9.3% |
| Week before last / last week | 21 | 9.8% |
| Last month | 7 | 3.3% |
| Last 12 months | 10 | 4.7% |
| Currently/ongoing | 9 | 4.2% |
| Other | 121 | 56.3% |

**ACS Employment Questions:**

| Reference Period | Count | % |
|------------------|-------|---|
| Last week | 160 | 74.4% |
| Lifetime/historical | 10 | 4.7% |
| Not specified | 45 | 20.9% |

**The mismatch is structural:** CPS uses multiple temporal windows; ACS standardizes on "last week."

### What Consolidates: Overlapping Windows

**Pair CPS_0273** (Both: PARTIAL)
```
CPS: "(THE WEEK BEFORE LAST/LAST WEEK), did (name/you) do ANY work for (pay/either pay or profit)?"
ACS: "LAST WEEK, did this person work for pay at a job (or business)?"
```

**Why partial consolidation:**
- CPS asks about "week before last OR last week" (two-week window)
- ACS asks about "last week" only (one-week window)
- If ACS is collected during CPS's reference period, answers overlap
- But CPS's broader window means some CPS "yes" answers won't match ACS

**Pair CPS_0274** (Both: PARTIAL)
```
CPS: "(THE WEEK BEFORE LAST/LAST WEEK), did (name/you) do ANY work for (pay/either pay or profit)?"
ACS: "LAST WEEK, did this person do ANY work for pay, even for as little as one hour?"
```

**Same pattern** - overlapping but not identical reference periods.

### What Doesn't Consolidate: Incompatible Windows

**Pair CPS_0288** (Claude: PARTIAL, GPT: NO) - Model Disagreement
```
CPS: "(THE WEEK BEFORE LAST/LAST WEEK), (in addition to the business) (name/you) have a job 
      either full or part time? Include any job from which (you were/name was) temporarily 
      absent."
ACS: "LAST WEEK, did this person work for pay at a job (or business)?"
```

**Claude's reasoning:**
> "Both questions ask about employment/work during a recent period, with overlapping reference frames (CPS includes 'last week'). The core concept of having a job is the same. However, CPS explicitly includes temporary absences while ACS focuses on actual work performed."

**GPT's reasoning:**
> "Question A asks about having a job (employment relationship) including temporary absence, while Question B asks about working for pay (actual labor performed). Having a job but being on vacation would yield different answers."

**This disagreement is legitimate** - it reflects genuine ambiguity about whether "having a job" and "working at a job" are the same construct.

**Pair CPS_0285** (Both: NO) - Clear Incompatibility
```
CPS: "(Do/Does) (name/you) currently want a job, either full or part time?"
ACS: "LAST WEEK, was this person on layoff from a job?"
```

**Why no consolidation:**
- CPS asks about job-seeking intention (labor force attachment)
- ACS asks about layoff status (employment disruption)
- Different constructs despite both being "employment related"

### Why CPS Needs Multiple Windows

CPS serves the Bureau of Labor Statistics' monthly employment estimates. This requires:

1. **Point-in-time employment status** ("last week" for current month's report)
2. **Labor force transitions** ("week before last" to track flows in/out)
3. **Job search activity** ("last 4 weeks" for unemployment definition)
4. **Longer-term patterns** ("last 12 months" for discouraged workers)

Each window serves a specific statistical purpose. ACS's single "last week" reference cannot substitute for this multi-window design.

### Model Disagreement Analysis

The 60 disagreements (28%) cluster around borderline cases:

| Disagreement Type | Count | Pattern |
|-------------------|-------|---------|
| Claude YES, GPT NO | 13 | Claude more lenient on overlapping windows |
| Claude NO, GPT YES | 27 | GPT more lenient on construct similarity |
| Classification differs, consolidation same | 20 | Agree on bottom line, differ on reasoning |

**Example of legitimate disagreement:**

**Pair CPS_0292** (Claude: NO, GPT: PARTIAL)
```
CPS: "(THE WEEK BEFORE LAST/LAST WEEK), (in addition to the business) (name/you) have a job?"
ACS: "When did this person last work, even for a few days?"
```

**Claude:** "CPS asks about having a job in a specific recent window; ACS asks about lifetime work history. These are different temporal scopes - one is bounded, one is unbounded."

**GPT:** "Both questions identify whether the person has worked. If someone worked last week (CPS), they definitely have a 'last work' date (ACS). Partial overlap exists."

**Both models are defensible.** The questions relate but serve different purposes.

---

## Cross-Subtopic Patterns

### Consolidation Rate by Content Type

| Content Type | CPS Rate | Driver |
|--------------|----------|--------|
| Demographics (sex, age, race) | 40-100% | Stable characteristics, standardized |
| Habitual measures (hours/week) | 26% | "Usually/normally" framing aligns |
| Point-in-time status (employment) | 11.6% | Reference period mismatch |
| Construct-specific (disability) | 1.8% | Different operational definitions |

### Model Agreement by Subtopic

| Subtopic | Agreement Rate | Interpretation |
|----------|----------------|----------------|
| Disability | 94.7% | Clear construct boundaries |
| Sex | 100% | Unambiguous |
| Employment Status | 72.1% | Genuine borderline cases |
| Earnings | 78.3% | Reference period ambiguity |

**Higher disagreement = more genuine ambiguity**, not model error.

---

## Methodological Implications

### 1. Construct Mismatch Requires New Taxonomy Category

Current classification categories:
- exact_duplicate
- near_duplicate
- related_but_distinct
- reference_period_mismatch
- response_format_mismatch
- not_comparable

**Proposed addition: construct_mismatch**

Definition: Questions address the same topic domain but operationalize different constructs that serve different analytical purposes and cannot be substituted regardless of linkage.

Examples:
- Work-limiting disability vs functional disability
- Job-seeking intention vs layoff status
- SNAP card count vs SNAP receipt (yes/no)

### 2. Model Disagreement as Signal, Not Noise

High disagreement rates indicate **genuine ambiguity** in question comparability. These cases warrant human review, not automated resolution.

Recommendation: Flag pairs with model disagreement for expert adjudication rather than defaulting to either model's judgment.

### 3. Reference Period Taxonomy

Consolidation potential correlates with reference period type:

| Reference Period Type | Consolidation Potential |
|----------------------|------------------------|
| Habitual ("usually") | High - no temporal anchor |
| Same specific window | High - direct comparison |
| Overlapping windows | Partial - subset relationship |
| Non-overlapping windows | Low - different time points |
| Different temporal scope | None - incompatible constructs |

---

## Summary: What CPS-ACS Teaches Us

### 1. LLMs Correctly Identify Standardized Question Matches

The perfect ACS6 diagonal (6/6) demonstrates that LLMs can reliably identify question pairs that are genuinely substitutable when construct, reference period, and response format align.

### 2. Multi-Purpose Surveys Resist Consolidation

CPS serves BLS monthly employment statistics with a multi-window temporal design. This architectural requirement makes consolidation with ACS structurally limited - not because questions are poorly written, but because they serve different statistical purposes.

### 3. Construct Mismatch Is Invisible at Topic Level

"Disability" appears in both surveys, suggesting overlap. But CPS disability (work limitation) and ACS disability (functional limitation) measure different things. Topic-level analysis misses this; question-level analysis catches it.

### 4. High Model Disagreement Indicates Genuine Ambiguity

The 28% disagreement rate in Employment Status reflects real uncertainty about comparability, not model failure. These borderline cases require human judgment.

### 5. Consolidation Potential Is Structurally Bounded

The 10.8% CPS-ACS consolidation rate is not a failure to find overlap - it's an accurate measurement of how much overlap exists given survey design constraints.

---

*Analysis completed: January 27, 2026*
*Data sources: cps_comparison_merged.csv (1,092 pairs)*
