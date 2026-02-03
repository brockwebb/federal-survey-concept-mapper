# Introduction

<!-- TODO: Refine and expand from existing docs -->
<!-- Pull from: docs/framing_ai_assisted.md, docs/stage4_research_framing.md -->

## Problem Statement

The federal statistical system conducts dozens of surveys annually, many asking overlapping questions about demographics, economics, health, and social conditions. This redundancy creates:

1. **Respondent burden**: Same households answering similar questions across multiple surveys
2. **Data integration challenges**: Incompatible question wording prevents cross-survey analysis
3. **Resource inefficiency**: Agencies duplicating effort in questionnaire design and data collection

Determining which questions can be consolidated or harmonized requires deep subject-matter expertise and traditionally involves weeks or months of manual review by survey methodologists.

## Research Questions

This report addresses three core questions:

### RQ1: Consolidation Potential
**What proportion of federal survey questions can be consolidated with existing ACS questions?**

- Hypothesis: Significant consolidation potential exists but requires systematic identification
- Approach: Exhaustive pairwise comparison of CPS/FoodAPS questions against ACS
- Outcome: Quantify F1 (direct), F2 (with adjustment), F3 (incompatible) rates

### RQ2: Barrier Taxonomy
**What barriers prevent survey question consolidation?**

- Hypothesis: Most barriers stem from construct differences, not operational issues
- Approach: Classify failures using DataSHaPER/Maelstrom harmonization framework
- Outcome: Identify primary barrier types and their prevalence

### RQ3: AI-Assisted Methods
**Can AI-assisted methods accelerate this traditionally labor-intensive analysis?**

- Hypothesis: LLM ensemble can handle routine classifications, reserving expert judgment for edge cases
- Approach: Multi-model rating + arbitration + two-axis triage
- Outcome: Measure agreement rates, expert review load reduction

## Scope

### Surveys Analyzed
- **American Community Survey (ACS)**: Target survey with comprehensive demographic/economic questions
- **Current Population Survey (CPS)**: Employment-focused survey (240 questions)
- **FoodAPS**: Food security survey (140 questions)

Total: **380 unique source questions** compared against ACS, yielding **1,598 question pairs**.

### Framework Applied
We adopt the DataSHaPER/Maelstrom retrospective harmonization framework:
- **F1**: Direct recode (mechanically transformable)
- **F2**: Statistical adjustment (requires modeling/bridging)
- **F3**: Incompatible (fundamental barriers prevent harmonization)

### What This Report Is NOT
- Not a recommendation to eliminate any surveys (policy decision)
- Not a claim that all F1/F2 pairs should be consolidated (requires stakeholder input)
- Not a replacement for expert judgment (AI assists, experts decide)

## Prior Work

This is **Report 03** of a multi-phase project:

- **Report 01**: Concept classification of 7,400+ questions using LLM ensemble
- **Report 02**: Pairwise comparison setup and sampling strategy
- **Report 03** (this report): Harmonization constraints and consolidation analysis

Each report builds on the previous, with validated outputs feeding forward.

## Report Structure

The remainder of this report is organized as:

- **Chapter 2 (Background)**: Survey harmonization frameworks and prior work
- **Chapter 3 (Methodology)**: 5-stage pipeline from rating to deliverables
- **Chapter 4 (Results)**: Consolidation rates, barrier analysis, agreement statistics
- **Chapter 5 (Discussion)**: Interpretation, limitations, implications
- **Chapter 6 (Conclusion)**: Summary and future directions
- **Appendices**: Taxonomy definitions, methodology decisions, expert review tables

## Key Contributions

This work contributes:

1. **Empirical findings** on federal survey consolidation potential (~44%)
2. **Barrier taxonomy application** showing CC dominance (97% of failures)
3. **Operational triage framework** (two-axis: Borda direction × Entropy stability)
4. **Reproducible methodology** for AI-assisted survey harmonization

---

**Note**: All data, code, and intermediate outputs are available in `reports/03_harmonization_constraints/` for replication and extension.
