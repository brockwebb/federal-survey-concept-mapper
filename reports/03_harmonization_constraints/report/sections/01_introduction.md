# Introduction

<!-- TODO: Refine and expand from existing docs -->
<!-- Pull from: docs/framing_ai_assisted.md, docs/stage4_research_framing.md -->

## Problem Statement

The federal statistical system conducts dozens of surveys annually, many asking overlapping questions about demographics, economics, health, and social conditions. These overlaps represent both analytical opportunities and challenges:

1. **Untapped analytical potential**: Overlapping questions across surveys represent bridge variables that could enable cross-survey statistical linkage, increasing explanatory power without additional data collection. Currently, this potential remains largely unrealized due to the difficulty of systematically identifying harmonizable questions across the ecosystem.

2. **Declining response rates**: As survey participation drops (ACS response rates declined from mid-90s to ~85%, CPS around 70%), extracting more value from existing data becomes critical. Cross-survey enrichment through linkage provides this — using bridge variables to integrate datasets and expand analytical capabilities.

3. **Respondent burden**: Overlaps also represent potential for survey streamlining. Same households answering similar questions across multiple surveys creates unnecessary burden, and consolidation where feasible offers a secondary benefit.

Determining which questions are harmonizable — and characterizing the quality of potential bridge variables — requires deep subject-matter expertise and traditionally involves weeks or months of manual review by survey methodologists.

## Research Questions

This report addresses three core questions:

### RQ1: Harmonization Potential
**What proportion of federal survey questions are harmonizable — serving as potential bridge variables for cross-survey data enrichment?**

- Hypothesis: Significant harmonization potential exists but requires systematic identification
- Approach: Exhaustive pairwise comparison of CPS/FoodAPS questions against ACS
- Outcome: Quantify F1 (direct harmonization), F2 (harmonization with adjustment), F3 (not harmonizable) rates and identify linkage-ready bridge variables

### RQ2: Linkage Quality Constraints
**What barriers prevent survey question harmonization, and how do these constraints define where cross-survey linkage is viable?**

- Hypothesis: Most barriers stem from construct differences, not operational issues; these barriers characterize linkage quality constraints
- Approach: Classify incompatibilities using DataSHaPER/Maelstrom harmonization framework
- Outcome: Identify primary barrier types, their prevalence, and implications for bridge variable quality

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
- Not a claim that all harmonizable pairs should be linked — fitness-for-purpose assessment is required for each enrichment use case
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

1. **Bridge variable catalog** identifying harmonization potential across federal surveys (~44% harmonizable), characterizing 168 linkage-ready questions for cross-survey data enrichment
2. **Linkage quality characterization** showing CC dominance (97% of incompatibilities), defining precisely where cross-survey enrichment is viable and where surveys serve distinct analytical purposes
3. **Operational triage framework** (two-axis: Borda direction × Entropy stability) enabling efficient expert review prioritization
4. **Reproducible methodology** for AI-assisted survey harmonization scalable to the entire federal survey ecosystem

---

**Note**: All data, code, and intermediate outputs are available in `reports/03_harmonization_constraints/` for replication and extension.
