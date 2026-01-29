# 9. Survey Overlap Patterns: Areas for Expert Investigation

## 9.1 Overview

This section presents survey overlap patterns identified through automated concept mapping. **These patterns are descriptive findings, not recommendations.**

As discussed in Section 8, many demographic surveys ask similar questions about respondents because these establish which universe different populations belong to and enable cross-survey comparisons. High conceptual overlap at the taxonomy level typically reflects this intentional design. Where overlap exists, it may serve important purposes:

- Establishing population universes for different analytical contexts
- Enabling cross-survey comparability and data validation
- Different sampling frames targeting distinct populations
- Statutory requirements mandating separate surveys
- Methodological differences (mode, frequency, depth) serving different analytical needs
- Historical data continuity requirements
- Specialized agency expertise and stakeholder relationships

**Expert judgment is required to interpret these patterns.** This analysis identifies *where* overlap exists; domain experts can determine whether any patterns warrant closer examination.

## 9.2 Methodology

### 9.2.1 Similarity Metric

Survey similarity was calculated using the **Jaccard Index**:

J(A,B) = |A ∩ B| / |A ∪ B|

Where:
- A = set of taxonomy concepts measured by Survey 1
- B = set of taxonomy concepts measured by Survey 2
- ∩ = intersection (shared concepts)
- ∪ = union (all concepts measured by either survey)

Jaccard ranges from 0 (no shared concepts) to 1.0 (identical concept coverage).

**Important Limitation**: This metric measures conceptual overlap at the taxonomy level, not question-level similarity. Two surveys may both measure "Income" but ask very different questions targeting different income components, populations, or reference periods.

### 9.2.2 Interpretation Guidance

These thresholds provide rough guidance, not decision rules:

- **≥80% overlap**: High conceptual similarity - warrants expert review
- **60-79% overlap**: Moderate similarity - may warrant investigation
- **50-59% overlap**: Some shared coverage - context-dependent significance
- **<50% overlap**: Limited overlap - likely serving distinct purposes

## 9.3 High-Similarity Survey Pairs

### 9.3.1 Highest Overlap Patterns (≥80%)

**Table 9.1: Survey Pairs with Highest Conceptual Overlap**

| Survey Pair | Overlap | Shared Concepts | Notes |
|-------------|---------|-----------------|-------|
| NSCH Children 12-17 ↔ NSCH Children 6-11 | ~100% | 22 | Same survey family, age variants |
| NTPS Private Teacher ↔ NTPS Public Teacher | ~82% | 23 | Same survey family, sector variants |

**Observations (not recommendations)**:

The NSCH age-specific questionnaires show very high overlap at the taxonomy level. This could indicate:
- Potential for instrument consolidation with age-conditional branching
- OR intentional parallel structure to enable cross-age comparison
- OR historical development that experts may wish to reconsider

The NTPS public/private variants similarly show high overlap, which could reflect:
- Opportunity for unified instrument with school-type variable
- OR meaningful differences in question wording/context not captured at taxonomy level
- OR regulatory/administrative reasons for separate instruments

**Expert review needed** to determine significance.

### 9.3.2 Substantial Overlap Patterns (60-79%)

| Survey Pair | Overlap | Primary Overlap Areas |
|-------------|---------|----------------------|
| NSCH 0-5 ↔ NSCH 6-11 | ~61% | Child health, demographics |
| NSCH 0-5 ↔ NSCH 12-17 | ~61% | Child health, demographics |
| Various NTPS/TFS pairs | 53-67% | Education workforce demographics |

These patterns suggest shared measurement domains across survey variants, which may warrant harmonization review or may reflect appropriate design.

### 9.3.3 Major Survey Overlap Patterns (50-59%)

Several pairs of major federal surveys show moderate conceptual overlap:

| Survey Pair | Overlap | Total Questions | Notes |
|-------------|---------|-----------------|-------|
| AHS ↔ CE | ~58% | 1,844 | Housing + expenditure surveys |
| CE ↔ SIPP | ~55% | 2,322 | Economic household surveys |
| AHS ↔ SIPP | ~51% | 1,954 | Housing + income surveys |

**Observation**: The major economic surveys (SIPP, CE, AHS) show 51-58% conceptual overlap with each other. All three measure aspects of household economic well-being. This pattern could indicate:

- Opportunities for harmonized core modules
- OR appropriate specialization (income depth in SIPP, expenditure detail in CE, housing focus in AHS)
- OR cross-validation benefits from multiple measurement approaches
- OR historical evolution that experts may wish to evaluate

**We cannot determine which interpretation is correct.** Domain experts familiar with these surveys' distinct purposes, user communities, and methodological requirements should evaluate whether this overlap represents inefficiency or appropriate design.

## 9.4 Survey Family Patterns

Clustering by similarity reveals natural groupings:

### Family 1: Education/Teacher Surveys
- NTPS variants, TFS variants, PSS, SPP, SSOCS
- Internal overlap: 48-82%
- Pattern: High overlap within family suggests potential for coordination

### Family 2: Economic Household Surveys  
- SIPP, CE, AHS, CPS, FoodAPS
- Internal overlap: 50-58%
- Pattern: Substantial shared economic measurement

### Family 3: Children's Health Surveys
- NSCH variants, partial NHIS overlap
- Internal overlap: 61-100%
- Pattern: Age variants show very high similarity

### Family 4: Crime/Safety Surveys
- NCVS, SCS, SVS, ITS, SSOCS
- Internal overlap: 35-45%
- Pattern: More specialized, less redundancy apparent

## 9.5 Limitations of This Analysis

This overlap analysis has important limitations:

**Taxonomy-Level Only**: Similarity is measured at the concept level, not the question level. Two surveys may both cover "Income" but ask fundamentally different questions.

**No Population Consideration**: Different surveys may target different populations (e.g., all households vs. families with children). Overlap in *concepts* does not mean overlap in *measurement coverage*.

**No Mode/Frequency Consideration**: Surveys differ in collection mode, frequency, and depth. Annual surveys and monthly surveys measuring the same concept serve different purposes.

**No Statutory/Mandate Analysis**: Some surveys exist due to legislative requirements that mandate specific measurement regardless of overlap with other surveys.

**No User Community Analysis**: Each survey serves distinct analytical communities. Consolidation might improve efficiency but disrupt established data products and time series.

## 9.6 Questions for Expert Review

Based on these patterns, experts may wish to consider:

1. **For high-overlap survey pairs (≥80%)**: Is there justification for separate instruments, or would consolidation improve efficiency without sacrificing measurement quality?

2. **For moderate-overlap pairs (50-79%)**: Are there opportunities for harmonized question modules that would improve cross-survey comparability while maintaining specialized content?

3. **For survey families with shared content**: Could standardized demographic or core economic modules reduce development burden and improve data integration?

4. **For individual surveys**: Are there concepts being measured that other surveys already cover adequately? Are there concepts being under-measured that warrant expanded coverage?

## 9.7 Summary

Overlap analysis reveals patterns in the federal survey ecosystem:

- Several survey pairs show high conceptual overlap (≥80%) at the taxonomy level
- Major economic surveys show 51-58% shared concept coverage
- Survey "families" (education, economic, children's health) show internal clustering

**These patterns describe what exists; they do not prescribe what should change.**

Whether overlap represents inefficiency, appropriate redundancy, or necessary cross-validation is a judgment that requires domain expertise, understanding of statutory requirements, and consideration of user community needs. This analysis provides structured data to support such expert evaluation - it does not substitute for it.
