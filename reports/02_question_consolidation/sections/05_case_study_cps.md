# Case Study: CPS-ACS

## Overview

This case study analyzes CPS-ACS question pairs, focusing on two subtopics that reveal fundamental barriers to survey consolidation:

1. **Disability (1.8% consolidable)**: A textbook case of construct mismatch - CPS measures work-limiting disability while ACS measures functional limitations. The 6 consolidable pairs are exactly the ACS6 standardized questions, validating LLM accuracy.

2. **Employment Status (11.6% consolidable)**: Reference period incompatibility - CPS uses multiple temporal windows for labor force dynamics while ACS uses fixed "last week" snapshots.

---

## Disability - 6/342 Consolidable (1.8%)

### The Structure

The Disability subtopic contains 342 pairs formed from:
- **57 unique CPS disability questions** × **6 unique ACS disability questions**

CPS has two fundamentally different types of disability questions.

### CPS Disability Question Types

**Type A: Work-Limiting Disability (51 questions)**
```
"Does your disability prevent you from accepting any kind of work 
 during the next 6 months?"
```
**Purpose:** Labor force participation measurement for BLS employment statistics

**Type B: Functional Limitations - ACS6 Compatible (6 questions)**
```
CPS_294: "Are you deaf or do you have serious difficulty hearing?"
CPS_295: "Are you blind or do you have serious difficulty seeing?"
CPS_296: "Do you have serious difficulty concentrating, remembering, or making decisions?"
CPS_297: "Do you have serious difficulty walking or climbing stairs?"
CPS_298: "Do you have difficulty dressing or bathing?"
CPS_299: "Do you have difficulty doing errands alone?"
```
**Purpose:** ADA compliance, accessibility planning (matches ACS purpose)

### LLM Validation: Perfect Diagonal Match

The 6 consolidable pairs form a **perfect 1:1 diagonal** between CPS Type B and ACS questions:

| CPS Question | ACS Question | Construct | Result |
|--------------|--------------|-----------|--------|
| CPS_294 | ACS_84 | Hearing | ✓ CONSOLIDABLE |
| CPS_295 | ACS_85 | Vision | ✓ CONSOLIDABLE |
| CPS_296 | ACS_86 | Cognition | ✓ CONSOLIDABLE |
| CPS_297 | ACS_87 | Walking | ✓ CONSOLIDABLE |
| CPS_298 | ACS_88 | Dressing | ✓ CONSOLIDABLE |
| CPS_299 | ACS_89 | Errands | ✓ CONSOLIDABLE |

**Accuracy:**
- 6/6 true positive diagonal matches (100%)
- 336/336 true negatives - off-diagonal and Type A correctly rejected
- Model agreement: 94.7%

**This is the strongest validation of LLM classification accuracy in the dataset.**

### Why Work-Limiting ≠ Functional Limitations

| Dimension | Work-Limiting | Functional |
|-----------|---------------|------------|
| Question | "Can you work?" | "Can you walk?" |
| Use case | BLS unemployment stats | ADA compliance |
| Reference | Forward (next 6 months) | Current/ongoing |
| Derivability | Not related | Not related |

---

## Employment Status - 25/215 Consolidable (11.6%)

### The Reference Period Problem

| Metric | Value |
|--------|-------|
| Total pairs | 215 |
| Both agree consolidable | 25 (11.6%) |
| Reference period mismatches | 37 (17.2%) |
| **Model disagreements** | **60 (27.9%)** |

The 28% disagreement rate is the **highest of any subtopic**.

### Reference Period Distribution

**CPS uses multiple windows:**
- Last week / week before last
- Last 4 weeks
- Last month
- Last 12 months
- Currently/ongoing

**ACS uses one window:**
- Last week (74%)

**The mismatch is structural:** CPS needs multiple temporal windows for labor force dynamics.

### What Consolidates: Overlapping Windows

```
CPS: "LAST WEEK, did you do ANY work for pay?"
ACS: "LAST WEEK, did this person work for pay at a job?"
```

Same reference period → consolidable.

### What Doesn't Consolidate: Incompatible Windows

```
CPS: "Did you do any work for pay in the LAST 4 WEEKS?"
ACS: "LAST WEEK, did this person work for pay?"
```

Different time periods, different statistics → not consolidable.

### Model Disagreement Analysis

| Disagreement Type | Count | Pattern |
|-------------------|-------|---------|
| Claude YES, GPT NO | 13 | Claude more lenient on overlapping windows |
| Claude NO, GPT YES | 27 | GPT more lenient on construct similarity |
| Same consolidation, different reasoning | 20 | Agree on bottom line |

**Example of legitimate disagreement:**

```
CPS: "Do you currently want a job, either full or part time?"
ACS: "LAST WEEK, was this person on layoff from a job?"
```

Job-seeking intention vs layoff status - both models defensible.

---

## Consolidation Rate by Content Type

| Content Type | CPS Rate | Driver |
|--------------|----------|--------|
| Demographics (sex, age, race) | 40-100% | Stable, standardized |
| Habitual measures (hours/week) | 26% | "Usually" framing aligns |
| Point-in-time status (employment) | 11.6% | Reference period mismatch |
| Construct-specific (disability) | 1.8% | Different definitions |

---

## Summary: What CPS-ACS Teaches Us

1. **LLMs Correctly Identify Standardized Matches** - Perfect ACS6 diagonal validates methodology

2. **Multi-Purpose Surveys Resist Consolidation** - CPS's multi-window design serves BLS needs incompatible with ACS's single window

3. **Construct Mismatch Is Invisible at Topic Level** - "Disability" appears in both surveys but measures different things

4. **High Model Disagreement = Genuine Ambiguity** - 28% disagreement in Employment reflects real uncertainty, not model failure

5. **Consolidation Is Structurally Bounded** - 10.8% is an accurate measurement of design-constrained overlap
