# Complete Number Trace: From Raw Data to Reported Results

**Date:** 2026-02-27  
**Purpose:** Fully explainable end-to-end trace of every number in the analysis, how they transform at each stage, where inflation occurs, and what the corrected values are.  
**Source files:** Listed per layer below.  
**Validation output:** `docs/validation/question_counts.json`, `docs/validation/number_flow.md`

---

## The Five Units People Confuse

Before anything else: this analysis produces numbers in five different units. They look similar but are not interchangeable. Every confusion in this project traces to mixing them up.

| Unit | What It Counts | Example |
|------|---------------|---------|
| **Raw questions** | Rows in `PublicSurveyQuestionsMap.csv` with "X" in a survey column | "CPS has 211 questions" |
| **Question-subtopic assignments** | Questions classified into subtopics; one question can land in multiple subtopics | "240 CPS question-subtopic entries" |
| **Shared subtopic intersections** | Number of (survey A question × subtopic) entries that share a subtopic with survey B | "CPS has 181 shared subtopic intersections with ACS" |
| **Question pairs** | Every source question matched to every ACS question in its subtopic | "1,030 CPS-ACS pairs" |
| **Unique questions with results** | Distinct question texts with a best feasibility score | "157 unique CPS questions evaluated" |

---

## Layer 0: Raw Material

**Source:** `data/raw/PublicSurveyQuestionsMap.csv`  
**Unit:** Rows (deduplicated questions) and columns (survey instruments)

| Metric | Value | How Computed |
|--------|------:|-------------|
| Total rows | 6,987 | Row count of CSV |
| Total instrument columns | 47 | Column count minus "Question" and "Unnamed: 48" |
| Questions on exactly 1 survey | 6,910 | Count rows where exactly 1 column has "X" |
| Questions on 2+ surveys | 1 | Count rows where 2+ columns have "X" |
| Literal sharing ACS-CPS | 0 | Count rows with "X" in both ACS and CPS columns |
| Literal sharing ACS-FoodAPS | 0 | Same logic |
| Literal sharing CPS-FoodAPS | 0 | Same logic |

**Key fact:** ACS, CPS, and FoodAPS share ZERO identical questions. Every harmonization path discovered by this research is concept-level matching, not verbatim question sharing. The report must state this.

---

## Layer 1: Survey Question Counts

**Source:** Same CSV, counting "X" marks per column  
**Unit:** Raw questions per survey

Multi-instrument surveys (FoodAPS = 4 instruments, NSCH = 4, NTPS = 6, etc.) are aggregated: a question appearing on any instrument counts once for the survey program.

### ACS Family (scope of this research)

| Survey | Questions | Instruments | Source |
|--------|----------:|------------:|--------|
| SIPP | 1,218 | 1 | `PublicSurveyQuestionsMap.csv` col count |
| CE | 1,106 | 1 | same |
| AHS | 744 | 1 | same |
| FoodAPS | 462 | 4 (246 + 56 + 74 + 86) | same, union across 4 columns |
| CPS | 211 | 1 | same |
| ACS | 115 | 1 | same |

**Key fact:** ACS has the fewest questions of any survey in its own family. Its value is topical breadth, not depth. It covers the broadest range of Census topics with 115 compact questions.

---

## Layer 2: Topic and Subtopic Classification (Ch 2)

**Source:** `output/report_01/final/master_dataset.csv`, `output/report_01/comparison/`  
**Unit:** Questions classified by Census topic and subtopic

Two LLMs (GPT-5-mini, Claude Haiku 4.5) independently classified each question. Agreement: 89.2% on topics (kappa = 0.839), 69.7% on subtopics (kappa = 0.687).

**Critical mechanism:** A single question CAN be classified into multiple subtopics. This is intentional --- "hours worked last week at your main job" legitimately relates to both "Employment Status" and "Hours/Week, Weeks/Year." But this creates a one-to-many relationship: 1 raw question can become 2+ question-subtopic assignments.

This is where inflation begins.

---

## Layer 3: Concept Overlap and Survey Selection (Ch 3)

**Source:** `output/report_02/data/acs_family2_summary.csv`  
**Unit:** Shared subtopic intersections (NOT unique questions)

| Survey | Shared Subtopic Intersections | Subtopics Covered |
|--------|-----------------------------:|------------------:|
| SIPP | 577 | 38 |
| AHS | 460 | 34 |
| CE | 283 | 30 |
| CPS | 181 | 25 |
| FoodAPS | 123 | 23 |

"181 shared subtopic intersections" means: across all CPS questions and all ACS questions, there are 181 instances where a CPS question shares a subtopic with at least one ACS question. If CPS has 5 questions in "Employment Status" and ACS has 3, that is 5 question-level intersections in that subtopic.

CPS and FoodAPS selected for proof-of-concept: fewest pairs = cheapest to run through multi-model evaluation. Cost optimization, not cherry-picking.

---

## Layer 4: Pair Generation (Ch 4)

**Source:** `docs/stages/03_harmonization/data/analysis/stage4_question_level.csv`  
**Unit:** Question pairs (combinatorial)

Every source question is paired with every ACS question sharing its subtopic. This is deliberately broad: most pairs will be unrelated. The purpose is to avoid missing valid matches.

### The Inflation Problem

The pair generation stage assigns a new ID to each question-subtopic-pairing context. A CPS question classified into 2 subtopics gets 2 IDs. The same question text about disability that was classified into multiple subtopics received 25 separate IDs.

**`stage4_question_level.csv` has 380 rows. These are NOT 380 unique questions.**

| Metric | CPS | FoodAPS | How Known |
|--------|----:|--------:|-----------|
| Raw survey questions | 211 | 462 | Layer 1 |
| Rows in `stage4_question_level.csv` | 240 | 140 | Row count filtered by survey |
| Unique question TEXTS in those rows | 157 | 118 | `nunique()` on question_text |
| Inflation factor | 1.53x | 1.19x | 240/157, 140/118 |

**Why 157 < 211:** 54 CPS questions are in subtopics where ACS has zero questions. No ACS counterpart = no pair possible = excluded from pairing.

**Why 118 < 462:** 344 FoodAPS questions are in subtopics ACS does not cover (food shopping frequency, meal preparation, food storage, etc.).

### Pair Counts

| Survey Pair | Pairs Generated | Source |
|-------------|----------------:|--------|
| CPS-ACS | 1,030 | `stage4_question_level.csv` sum of pair_count for CPS |
| FoodAPS-ACS | 568 | same for FOODAPS |
| Total | 1,598 | sum |

---

## Layer 5: Rating and Arbitration (Ch 4-5)

**Source:** `docs/stages/03_harmonization/data/analysis/final_verdicts.csv`  
**Unit:** Pairs rated, then collapsed to question-level

All 1,598 pairs rated by 3 LLMs (rater stage), disagreements resolved by 3 LLM arbitrators.

| Stage | Metric | Value | Source |
|-------|--------|------:|--------|
| Rater | Fleiss' kappa (feasibility) | 0.537 | `stage2_agreement_metrics.json` |
| Rater | Fleiss' kappa (L1 barrier) | 0.611 | same |
| Arbitration | Cohen's kappa (feasibility, 2-way) | 0.843 | `stage3_arbitration_metrics.json` |
| Arbitration | Cohen's kappa (binary consolidability, 2-way) | 0.896 | same |

---

## Layer 6: Question-Level Results (Ch 5)

**Source:** `stage4_question_level.csv` (inflated) and `stage4_question_best_matches.csv`  
**Unit:** Unique questions with best feasibility score

### The NUMBERS_MAP Reported (INFLATED)

These are the numbers currently in the report. They count question-subtopic assignments as if they were unique questions.

| | CPS | FoodAPS |
|--|--:|--:|
| Total questions | 240 | 140 |
| F1 (direct recode) | 37 | 23 |
| F2 (statistical adjustment) | 65 | 45 |
| F3 (incompatible) | 138 | 72 |
| Consolidable (F1+F2) | 102 (42.5%) | 68 (48.6%) |

### Corrected (Unique Question Texts)

Correction method: group by `question_text`, take the best feasibility (F1 > F2 > F3) across all subtopic assignments. Each unique question text counted once.

| | CPS | FoodAPS |
|--|--:|--:|
| Total unique questions | **157** | **118** |
| F1 (direct recode) | **32** | **19** |
| F2 (statistical adjustment) | **54** | **37** |
| F3 (incompatible) | **71** | **62** |
| Consolidable (F1+F2) | **86 (54.8%)** | **56 (47.5%)** |

### Why the CPS Rate Goes UP

The inflated duplicates are disproportionately disability-related questions (25 copies of the same text) that mostly scored F3. Removing duplicates removes more F3s than F1/F2s, raising the consolidation rate from 42.5% to 54.8%.

FoodAPS stays roughly flat (48.6% to 47.5%) because its duplication is milder (max 4 copies).

---

## Layer 7: ACS-Side Participation

**Source:** `docs/stages/03_harmonization/data/analysis/stage4_question_best_matches.csv`  
**Unit:** Unique ACS question texts serving as bridge targets

This is the number everyone forgets to ask: ACS has 115 questions total, but how many actually participate as harmonization targets?

| Metric | CPS | FoodAPS | Combined |
|--------|----:|--------:|---------:|
| Unique ACS targets (F1+F2 pairs) | 36 | 31 | 50 |
| Shared ACS targets (serve both surveys) | -- | -- | 17 |
| ACS participation rate | -- | -- | 43.5% (50/115) |

**Fan-in ratio:** 142 consolidable source questions (86 CPS + 56 FoodAPS) bridge to 50 ACS questions = 2.84 source questions per ACS target.

**17 three-way bridges:** These ACS questions link CPS, FoodAPS, and ACS data simultaneously. They are the highest-value variables. Examples: employment status (worked last week, temporarily absent, on layoff), hours worked, race, age, marital status, military service, relationship to household reference person.

---

## The Complete Funnel

```
Layer 0:  6,987 deduplicated questions across 47 instruments
              |
Layer 1:  ACS: 115 | CPS: 211 | FoodAPS: 462
              |
Layer 2:  Classification into topics/subtopics
              |  (dual-subtopic assignments begin here)
              |
Layer 3:  Concept overlap identifies ACS family
              |  CPS: 181 shared subtopic intersections
              |  FoodAPS: 123 shared subtopic intersections
              |
Layer 4:  Pair generation (source × ACS per shared subtopic)
              |  CPS: 157 unique questions → 1,030 pairs
              |  FoodAPS: 118 unique questions → 568 pairs
              |  (54 CPS questions + 344 FoodAPS questions excluded: no ACS subtopic coverage)
              |
Layer 5:  3-model rating + 3-model arbitration
              |  rater κ = 0.537 → arbitrated κ = 0.843
              |
Layer 6:  Question-level results (best feasibility per unique text)
              |  CPS: 86 of 157 consolidable (54.8%)
              |  FoodAPS: 56 of 118 consolidable (47.5%)
              |
Layer 7:  ACS hub analysis
              50 of 115 ACS questions serve as bridge targets (43.5%)
              17 serve BOTH CPS and FoodAPS
              Fan-in: 2.84 source questions per ACS target
```

---

## Correction Summary

| What | NUMBERS_MAP (old) | Corrected | Root Cause |
|------|------------------:|----------:|------------|
| CPS unique source questions | 240 | **157** | Dual-subtopic IDs counted as separate questions |
| FoodAPS unique source questions | 140 | **118** | Same |
| Total unique source questions | 380 | **275** | Same |
| CPS F1 | 37 | **32** | Duplicates collapsed |
| CPS F2 | 65 | **54** | Same |
| CPS consolidable | 102 (42.5%) | **86 (54.8%)** | Same; rate UP because inflated duplicates were mostly F3 |
| FoodAPS F1 | 23 | **19** | Same |
| FoodAPS F2 | 45 | **37** | Same |
| FoodAPS consolidable | 68 (48.6%) | **56 (47.5%)** | Same; rate roughly flat |
| ACS questions participating | (not reported) | **50 of 115 (43.5%)** | New analysis |
| Three-way bridge variables | (not reported) | **17** | New analysis |

---

## What Stays the Same

These numbers are NOT affected by the inflation correction:

- Total surveys: 47 instruments
- Total questions: 6,987 deduplicated
- Total pairs evaluated: 1,598
- All pair-level metrics (kappa, agreement rates, barrier distributions)
- The barrier distribution (CC dominates at ~87%)
- The kappa improvement narrative (0.537 → 0.843)
- ACS family overlap table (577, 460, 283, 181, 123)

The correction changes the *question-level rollup* and the *denominators for consolidation rates*. The pair-level analysis is unaffected.

---

## Files That Need Updating

| File | What Changes |
|------|-------------|
| `docs/NUMBERS_MAP.md` | Steps 4, 7: replace all inflated counts. Add ACS-side findings. |
| `report/chapters/03_survey_overlap.qmd` | "380 unique source questions (240 CPS + 140 FoodAPS)" → "275 unique source questions (157 CPS + 118 FoodAPS)" |
| `report/chapters/05_results.qmd` | All results tables and inline numbers |
| `report/chapters/06_implications.qmd` | Rates, subtopic breakdowns |
| `report/NARRATIVE_CHECKLIST.md` | Update checked claims |
| `src/figures/fig03_paired_topic_composition.py` | Input data has inflation; needs corrected source or dedup logic |
| `docs/stages/03_harmonization/data/analysis/stage4_topic_breakdown.csv` | Pair-level topic breakdown may have inflation |
| `fact_sheet/` | If it cites any of these numbers |

---

## Validation Infrastructure

| File | Purpose | Run Command |
|------|---------|-------------|
| `src/validation/validate_question_counts.py` | Computes all corrected counts from raw sources | `python src/validation/validate_question_counts.py` |
| `docs/validation/question_counts.json` | Machine-readable validated output | Generated by above |
| `docs/validation/question_counts.log` | Human-readable summary | Generated by above |
| `docs/validation/number_flow.md` | This document (narrative version) | Manual |
