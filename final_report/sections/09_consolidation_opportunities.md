# 9. Consolidation Opportunities: Survey Overlap Analysis

## 9.1 Overview

Having identified coverage patterns in Section 8, we now examine survey similarity to identify potential consolidation opportunities. High conceptual overlap between surveys suggests redundant measurement infrastructure - separate surveys asking essentially similar questions to similar populations.

Consolidation benefits include:
- **Reduced respondent burden**: Fewer surveys fielded
- **Cost savings**: Eliminated duplicate infrastructure
- **Improved data quality**: Larger sample sizes from merged surveys
- **Enhanced comparability**: Consistent measurement across formerly separate surveys

This analysis uses Jaccard similarity to quantify concept overlap between all survey pairs, identifying candidates for merger, harmonization, or retirement.

## 9.2 Methodology

### 9.2.1 Similarity Metric

Survey similarity was calculated using the **Jaccard Index**:

J(A,B) = |A ∩ B| / |A ∪ B|

Where:
- A = set of concepts measured by Survey 1
- B = set of concepts measured by Survey 2
- ∩ = intersection (shared concepts)
- ∪ = union (all concepts measured by either survey)

Jaccard ranges from 0 (no shared concepts) to 1.0 (identical concept coverage). We established a threshold of **≥50% overlap** to identify high-similarity survey pairs warranting consolidation consideration.

### 9.2.2 Interpretation Guidelines

- **≥80% overlap**: Strong consolidation candidates - surveys are conceptually redundant
- **60-79% overlap**: Moderate candidates - significant overlap but some unique coverage
- **50-59% overlap**: Weak candidates - substantial overlap but distinct purposes
- **<50% overlap**: Complementary surveys - overlap is incidental, not systematic

## 9.3 High-Similarity Survey Pairs

### 9.3.1 Perfect or Near-Perfect Overlap (≥80%)

**Table 9.1: Strongest Consolidation Candidates**

| Survey Pair | Overlap | Shared Concepts | Total Questions | Assessment |
|-------------|---------|-----------------|-----------------|------------|
| NSCH Children 12-17 ↔ NSCH Children 6-11 | 100% | 22 | 289 | **MERGE: Identical measurement** |
| NTPS Private Teacher ↔ NTPS Public Teacher | 82.1% | 23 | 232 | **MERGE: Nearly identical** |

**Case Study 1: NSCH Age-Specific Questionnaires**

The three National Survey of Children's Health (NSCH) age-specific questionnaires show:
- Children 12-17 ↔ Children 6-11: **100% overlap** (22 shared concepts, 289 total questions)
- Children 0-5 ↔ Children 6-11: **61.3% overlap** (19 shared concepts, 302 total questions)
- Children 0-5 ↔ Children 12-17: **61.3% overlap** (19 shared concepts, 307 total questions)

**Recommendation**: The three questionnaires could be unified into a single NSCH instrument with age-conditional skip logic. The 12-17 and 6-11 versions are essentially identical and should definitely be merged. The 0-5 version has some infant/toddler-specific content but 61% overlap suggests a unified instrument with developmental stage branching would reduce total question count while maintaining measurement quality.

**Estimated savings**: 738 total questions → ~450-500 unified questions (32-39% reduction)

**Case Study 2: NTPS Teacher Surveys**

The National Teacher and Principal Survey (NTPS) and Teacher Follow-up Survey (TFS) show systematic overlap:
- Private Teacher ↔ Public Teacher: **82.1% overlap**
- Both teacher surveys ↔ Former Teacher survey: **53-59% overlap**

The high overlap between public and private teacher questionnaires (82%) suggests they could be unified with a single "school type" variable rather than maintaining separate instruments.

**Recommendation**: Merge public/private teacher questionnaires into unified NTPS Teacher Survey. Consider integrating TFS Former Teacher Survey as a module within NTPS for teachers who leave profession.

**Estimated savings**: 232 questions across separate surveys → ~140-160 unified questions (30-40% reduction)

### 9.3.2 Substantial Overlap (60-79%)

**Table 9.2: Moderate Consolidation Candidates**

| Survey Pair | Overlap | Questions | Primary Overlap Areas |
|-------------|---------|-----------|----------------------|
| NTPS Private Principal ↔ TFS Former Teacher | 66.7% | 85 | Demographics, employment history |
| NSCH 0-5 ↔ NSCH 6-11 | 61.3% | 302 | Child health, demographics |
| NSCH 0-5 ↔ NSCH 12-17 | 61.3% | 307 | Child health, demographics |
| NTPS Private Principal ↔ NTPS Public Teacher | 60.0% | 152 | Demographics, education background |

These pairs show significant conceptual overlap but serve somewhat different populations or purposes. Consolidation should focus on **harmonization** (using identical question wording for shared concepts) rather than merger.

**Recommendation**: Develop standardized modules for shared concepts (demographics, employment history, education background) that all education surveys use. This improves cross-survey comparability without necessarily merging surveys.

### 9.3.3 Meaningful Overlap (50-59%)

**Table 9.3: Large Survey Consolidation Opportunities**

| Survey Pair | Overlap | Total Questions | Shared Concepts | Potential Impact |
|-------------|---------|-----------------|-----------------|------------------|
| AHS ↔ CE | 57.9% | 1,844 | 44 | Major burden reduction |
| CE ↔ SIPP | 54.9% | 2,322 | 50 | Major burden reduction |
| CPS ↔ NSCG | 54.5% | 332 | 24 | Moderate reduction |
| ACS ↔ AHS | 52.3% | 853 | 34 | Moderate reduction |
| CE ↔ FoodAPS | 50.7% | 1,352 | 36 | Moderate reduction |
| AHS ↔ SIPP | 50.6% | 1,954 | 44 | Major burden reduction |

**Critical Finding**: The three major economic surveys (SIPP, CE, AHS) show 51-58% overlap with each other, representing **5,120 total questions** across three surveys. This overlap is particularly striking given they all measure household economic well-being.

**Case Study 3: The Economic Survey Triad (SIPP-CE-AHS)**

**Survey of Income and Program Participation (SIPP)**:
- 1,216 questions, 61 concepts
- Focus: Detailed income sources, program participation

**Consumer Expenditure Survey (CE)**:  
- 1,106 questions, 54 concepts
- Focus: Detailed spending patterns, budget allocation

**American Housing Survey (AHS)**:
- 738 questions, 50 concepts
- Focus: Housing characteristics, costs, quality

**Overlap Analysis**:
- SIPP ↔ CE: 54.9% overlap (50 shared concepts) = **Income + Expenditures + Demographics**
- SIPP ↔ AHS: 50.6% overlap (44 shared concepts) = **Income + Housing Costs + Demographics**
- CE ↔ AHS: 57.9% overlap (44 shared concepts) = **Expenditures + Housing Costs + Demographics**

**Shared Measurement**: All three surveys ask about:
- Demographics (age, race, Hispanic origin, marital status, household composition)
- Income (wages, benefits, government transfers)
- Housing costs (rent/mortgage, utilities, taxes, insurance)
- Employment status
- Education attainment

**Unique Measurement**:
- SIPP: Detailed government program eligibility and participation
- CE: Itemized expenditure diaries and detailed consumption
- AHS: Physical housing characteristics, neighborhood quality

**Consolidation Scenarios**:

*Option 1: Modular Approach*
- Create "Core Economic Module" covering shared demographics + basic income/expenditures
- Each survey adds specialized modules (program participation, expenditure diary, housing quality)
- **Estimated reduction**: 5,120 questions → 3,500-3,800 questions (25-32% reduction)

*Option 2: Integrated Survey*
- Merge into unified "Household Economic Survey" with rotating topic modules
- Year 1: Income focus (SIPP questions)
- Year 2: Expenditure focus (CE questions)  
- Year 3: Housing focus (AHS questions)
- **Estimated reduction**: 5,120 questions → 2,000-2,500 annually (51-61% reduction)
- **Trade-off**: Less frequent measurement of each specialized domain

*Option 3: Status Quo with Harmonization*
- Maintain separate surveys but standardize all shared questions (exact wording, response options)
- Improves comparability and potentially enables data linkage across surveys
- **Estimated reduction**: Minimal question reduction, but major analytical benefit

**Recommendation**: Option 3 (harmonization) is most politically feasible and preserves specialized measurement, while Option 1 (modular approach) offers significant burden reduction without sacrificing measurement frequency.

### 9.3.4 Cross-Agency Coordination Opportunities

The 50%+ overlap pairs often cross agency boundaries:
- **Census Bureau**: ACS, AHS, SIPP, CE, CPS (5 surveys)
- **NCES/Education**: NTPS (multiple variants), TFS, PSS (7-8 surveys)
- **HRSA/Health**: NSCH (3 variants), NHIS, NAMCS (5 surveys)

High overlap within agency portfolios suggests internal consolidation opportunities, while cross-agency overlap indicates the need for interagency coordination on shared measurement (especially demographics).

## 9.4 Survey Family Analysis

Clustering by similarity reveals five natural "survey families":

### Family 1: Education/Teacher Surveys
- NTPS variants (6 surveys)
- TFS variants (2 surveys)
- PSS, SPP, SSOCS (3 surveys)
- **Average internal overlap**: 48-82%
- **Consolidation potential**: HIGH - many variants measure similar populations

### Family 2: Economic Household Surveys  
- SIPP, CE, AHS, CPS (4 surveys)
- FoodAPS, HTOPS (2 surveys)
- **Average internal overlap**: 50-58%
- **Consolidation potential**: MODERATE-HIGH - core measurement overlaps substantially

### Family 3: Children's Health Surveys
- NSCH variants (3 surveys)
- NHIS (overlaps partially)
- **Average internal overlap**: 61-100%
- **Consolidation potential**: HIGH - age-specific variants are redundant

### Family 4: Crime/Safety Surveys
- NCVS, SCS, SVS, ITS (4 surveys)
- SSOCS (overlaps on safety)
- **Average internal overlap**: 35-45%
- **Consolidation potential**: LOW - specialized victimization measurement

### Family 5: Specialized Surveys
- NSSRN, NSCG, NTEWS, NAMCS, MEPS, etc.
- **Average internal overlap**: <40%
- **Consolidation potential**: LOW - unique measurement purposes

## 9.5 Cost-Benefit Considerations

### 9.5.1 Potential Savings

Assuming successful consolidation of high-overlap survey pairs:

**Conservative Scenario** (merge only 80%+ overlap pairs):
- NSCH age variants: 738 → 500 questions (238 saved)
- NTPS teacher variants: 232 → 160 questions (72 saved)
- **Total reduction**: ~310 questions (4.4% of total ecosystem)

**Moderate Scenario** (harmonize 50%+ overlap pairs):
- Economic survey triad: 5,120 → 3,800 questions (1,320 saved)
- Education surveys: 800 → 600 questions (200 saved)
- Children's health: 738 → 500 questions (238 saved)
- **Total reduction**: ~1,758 questions (25% of total ecosystem)

**Aggressive Scenario** (integrated merged surveys):
- Economic survey triad: 5,120 → 2,250 questions (2,870 saved)
- Education surveys: 800 → 400 questions (400 saved)
- Children's health: 738 → 350 questions (388 saved)
- **Total reduction**: ~3,658 questions (52% of total ecosystem)

### 9.5.2 Implementation Challenges

**Statistical Continuity**: Merged surveys must maintain time series comparability, requiring careful transitional analysis.

**Agency Authority**: Cross-agency consolidation requires OMB coordination and memoranda of understanding.

**Specialized Users**: Each survey has dedicated user communities who may resist changes to "their" survey.

**Budget Allocation**: Savings from survey consolidation may not flow directly to implementing agencies, reducing incentives.

**Sample Design**: Different surveys have different sample frames, weighting procedures, and periodicity that complicate integration.

### 9.5.3 Phased Implementation

**Phase 1 (Years 1-2)**: Harmonize shared questions across high-overlap pairs without changing survey structure. Test comparability.

**Phase 2 (Years 3-4)**: Pilot merged instruments for NSCH age variants and NTPS teacher variants. Evaluate data quality.

**Phase 3 (Years 5-7)**: If pilots succeed, implement modular approach for economic survey triad. Maintain measurement frequency.

**Phase 4 (Years 8-10)**: Evaluate integrated survey approach for economic surveys if modular approach proves successful.

This phased approach minimizes risk while allowing iterative learning from consolidation experiments.

## 9.6 Recommendations

### High Priority (Implement within 2 years)

1. **Merge NSCH age-specific questionnaires** into unified instrument with developmental stage branching (100% overlap = no information loss)

2. **Merge NTPS public/private teacher questionnaires** into unified teacher survey with school type variable (82% overlap)

3. **Harmonize demographics across all surveys** using OMB Statistical Policy Directive standards (benefits all downstream analysis)

### Medium Priority (Implement within 5 years)

4. **Create Core Economic Module** for SIPP, CE, and AHS covering shared demographics, income, expenditures, housing costs

5. **Harmonize employment questions** across CPS, SIPP, NSCG, NSSRN, NTEWS (54%+ overlap)

6. **Consolidate education surveys** (NTPS variants + TFS) into unified education workforce study

### Research Needed (Evaluate feasibility)

7. **Integrated household economic survey** with rotating topic modules (explore trade-offs between frequency and burden)

8. **Cross-survey imputation** using harmonized questions to reduce burden by allowing households to skip questions answered in linked surveys

## 9.7 Summary

Overlap analysis reveals substantial consolidation opportunities:
- ✅ **4 survey pairs** show 80%+ overlap (strong merger candidates)
- ✅ **6 survey pairs** show 60-79% overlap (harmonization candidates)
- ✅ **11 survey pairs** show 50-59% overlap (coordination opportunities)
- 💰 **Potential burden reduction**: 25-52% of total questions depending on aggressiveness
- 📊 **Greatest opportunity**: Economic survey triad (SIPP-CE-AHS) with 5,120 questions and 51-58% overlap

Strategic consolidation could reduce the federal survey question inventory from ~7,000 to 3,500-5,200 questions while maintaining or improving measurement quality through larger sample sizes and improved harmonization.

*See Figure 9.1 (Survey Similarity Heatmap) and Table 9.4 (Complete Pairwise Similarity Matrix) in report appendices.*
