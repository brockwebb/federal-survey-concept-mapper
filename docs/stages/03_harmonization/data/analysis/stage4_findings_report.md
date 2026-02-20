# Stage 4: Question-Level Consolidability Findings

**Generated:** 2026-02-04T13:54:50.320926

## Executive Summary

This analysis answers the core research question: **What proportion of source survey questions can be consolidated with ACS?**

Consolidability is determined at the *question* level — a source question is consolidable if it has **at least one** ACS pair rated F1 (direct recode) or F2 (statistical adjustment).

### CPS
- **102/240 (42.5%) questions have at least one consolidable path to ACS**
  - Direct recode (F1): 37 (15.4%)
  - Statistical adjustment (F2): 65 (27.1%)
  - Not consolidable (F3): 138 (57.5%)

### FOODAPS
- **68/140 (48.6%) questions have at least one consolidable path to ACS**
  - Direct recode (F1): 23 (16.4%)
  - Statistical adjustment (F2): 45 (32.1%)
  - Not consolidable (F3): 72 (51.4%)

## Pair-Level vs Question-Level Rates

Pair-level consolidability rates understate the true consolidation potential because each source question is paired with multiple ACS questions, most of which are unrelated.

| Survey | Pair-Level Rate | Question-Level Rate | Unique Questions | Total Pairs |
|--------|----------------|--------------------|-----------------:|------------:|
| CPS | 19.5% | 42.5% | 240 | 1030 |
| FOODAPS | 20.6% | 48.6% | 140 | 568 |

## Barriers to Consolidation (F3 Pairs)

Among pairs rated not consolidable (F3), the dominant barrier types are:

### CPS

| Barrier | Description | Count | % of F3 |
|---------|-------------|------:|--------:|
| CC | Construct/Concept | 797 | 96.1% |
| TC | Temporal/Chronological | 20 | 2.4% |
| RS | Response Scale | 8 | 1.0% |
| PC | Population/Coverage | 4 | 0.5% |

### FOODAPS

| Barrier | Description | Count | % of F3 |
|---------|-------------|------:|--------:|
| CC | Construct/Concept | 439 | 97.3% |
| RS | Response Scale | 5 | 1.1% |
| TC | Temporal/Chronological | 4 | 0.9% |
| PC | Population/Coverage | 2 | 0.4% |
| MC | Mode/Context | 1 | 0.2% |

## Topic Analysis

Consolidation rates by subtopic (pair-level):

### CPS — Top subtopics by consolidation rate

| Subtopic | Total Pairs | Consolidable | Rate |
|----------|------------:|-------------:|-----:|
| Commissions | 1 | 1 | 100.0% |
| Race | 9 | 9 | 100.0% |
| Age | 6 | 5 | 83.3% |
| Relationship | 27 | 20 | 74.1% |
| Occupation | 13 | 7 | 53.8% |
| Education | 4 | 2 | 50.0% |
| Hispanic Origin | 4 | 2 | 50.0% |
| Population | 8 | 3 | 37.5% |
| Veterans | 8 | 3 | 37.5% |
| Earnings | 135 | 43 | 31.9% |
| Hours/Week, Weeks/Year | 136 | 43 | 31.6% |
| Marital Status | 7 | 2 | 28.6% |
| Employment Status | 215 | 49 | 22.8% |
| School Enrollment | 9 | 2 | 22.2% |
| Commute/Commuting | 5 | 1 | 20.0% |

### FOODAPS — Top subtopics by consolidation rate

| Subtopic | Total Pairs | Consolidable | Rate |
|----------|------------:|-------------:|-----:|
| Age | 5 | 5 | 100.0% |
| Labor Force | 1 | 1 | 100.0% |
| Race | 6 | 6 | 100.0% |
| Relationship | 5 | 5 | 100.0% |
| Tenure (Own/Rent) | 1 | 1 | 100.0% |
| Vehicles | 2 | 2 | 100.0% |
| Unemployment | 2 | 1 | 50.0% |
| Food Stamps (SNAP) | 22 | 10 | 45.5% |
| Sex | 5 | 2 | 40.0% |
| School Enrollment | 65 | 25 | 38.5% |
| Health Insurance | 6 | 2 | 33.3% |
| Hours/Week, Weeks/Year | 56 | 18 | 32.1% |
| Employment Status | 55 | 12 | 21.8% |
| Veterans | 31 | 5 | 16.1% |
| Marital Status | 7 | 1 | 14.3% |

## F2 Transformation Requirements

There are **244 pairs** rated F2 (statistical adjustment needed).
Barrier types requiring transformation:

| Survey | Barrier | Count |
|--------|---------|------:|
| CPS | CC (Construct/Concept) | 74 |
| CPS | MC (Mode/Context) | 4 |
| CPS | PC (Population/Coverage) | 3 |
| CPS | RS (Response Scale) | 16 |
| CPS | TC (Temporal/Chronological) | 57 |
| FOODAPS | CC (Construct/Concept) | 61 |
| FOODAPS | MC (Mode/Context) | 2 |
| FOODAPS | PM (Policy/Market) | 1 |
| FOODAPS | RS (Response Scale) | 2 |
| FOODAPS | TC (Temporal/Chronological) | 24 |

## Burden Reduction Potential

If consolidable questions could be replaced by ACS equivalents:

- **CPS:** 102 of 240 questions could potentially be eliminated (42.5%)
- **FOODAPS:** 68 of 140 questions could potentially be eliminated (48.6%)

*Caveat: This is an upper bound. Practical consolidation depends on use case, statistical precision requirements, and institutional constraints.*

---

**Methodology:** Pair-level feasibility verdicts from Stage 3 arbitration (3 LLM arbitrators with majority-rule consolidation). Question-level consolidability = at least one pair rated F1 or F2.