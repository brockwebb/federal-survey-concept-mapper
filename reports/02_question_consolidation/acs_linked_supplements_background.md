# ACS-Linked Supplements: A Path to Survey Consolidation

## Background

### The Redundancy Problem

Federal statistical agencies operate dozens of household surveys that independently collect similar demographic, economic, and housing information. Each survey re-asks questions about age, race, income, household composition, and other core concepts—not because agencies are unaware of overlap, but because surveys operate as independent data collection efforts without person-level linkage.

This project's concept mapping analysis identified 1,624 questions where the American Community Survey (ACS) shares conceptual overlap with five "Economic Household Surveys" (SIPP, CE, AHS, CPS, FoodAPS). But conceptual overlap alone doesn't justify consolidation. The critical question is: **can we link records at the person/household level?**

Without linkage, apparent "duplication" serves a purpose—it defines comparable demographic universes for each survey. With linkage, duplication becomes eliminable redundancy.

### The Ecological Fallacy Problem

When surveys cannot be linked at the individual level, analysts face the **ecological fallacy**: inferring individual-level relationships from aggregate data. 

Consider studying how food acquisition behavior relates to housing cost burden:
- **Unlinked surveys**: Compare average food spending in "low-income households" from FoodAPS to average housing costs in "low-income households" from AHS. But these are different households—the Johnnys and Susies in one sample versus the Clarks and Rhondas in another. Any relationship found is population-level correlation, not individual causation.
- **Linked surveys**: Track the same household across both domains. Household A spends 45% of income on housing AND relies heavily on food pantries. This is actionable insight.

The value of survey consolidation is not merely cost savings—it's analytical power through linkage.

---

## Case Study: FoodAPS

### What FoodAPS Measures

The National Household Food Acquisition and Purchase Survey (FoodAPS), sponsored by USDA's Economic Research Service, collects comprehensive data on household food acquisition behavior over a 7-day period:

- Where households acquire food (grocery stores, restaurants, food pantries, SNAP retailers, own production, gifts from family)
- What foods are acquired (item-level detail with UPC scanning)
- Prices paid and nutrient content
- Local food environment characteristics

This is unique, policy-relevant data that no other survey collects.

### Current Sample Design

FoodAPS-1 (2012-2013) surveyed 4,826 households using stratified sampling:
- SNAP participants (oversampled)
- Low-income non-SNAP households
- Higher-income households

Weighted to be nationally representative of all non-institutionalized households in the contiguous United States.

### The Overlap Problem

Our analysis found **123 questions** where FoodAPS overlaps conceptually with ACS:

| Domain | Shared Questions | Top Subtopics |
|--------|------------------|---------------|
| Economic | 59 | Food Stamps/SNAP (22), Earnings (10), Employment Status (9) |
| Social | 42 | Household composition (18), School Enrollment (11) |
| Demographic | 12 | Relationship (2), Age (3), Race (2), Sex (3) |
| Housing | 10 | Costs (6), Vehicles (2), Tenure (1) |

These 123 questions represent data that ACS already collects from ~3.5 million households annually. FoodAPS re-collects this information from its 4,826 households because there is no linkage mechanism to pull existing ACS responses.

### Critique: Income-Based Stratification Limitations

FoodAPS stratifies by income and SNAP participation. This approach assumes income brackets cleanly predict food security risk. The COVID-19 pandemic exposed limitations:

- **Asset-rich, cash-poor households**: Home equity but no liquidity
- **Temporary hardship**: Job loss, medical crisis, divorce—not captured by annual income
- **ALICE population**: Asset Limited, Income Constrained, Employed—working households one paycheck from crisis
- **Geographic cost mismatch**: $75,000 in San Francisco ≠ $75,000 in rural Ohio
- **Supply chain disruption**: 2020-2021 showed even "comfortable" households facing empty shelves

Food insecurity is more fluid and contextual than income strata suggest. Linked longitudinal data would capture these dynamics; cross-sectional income brackets cannot.

---

## Proposed Model: ACS-Linked Supplements

### Concept

Instead of independent surveys that re-collect demographic baselines, design topic-specific supplements that:

1. **Sample from ACS respondents** rather than independent frames
2. **Link to existing ACS records** for demographic, economic, and housing data
3. **Collect only supplement-specific content** (e.g., food diaries, shopping behavior)
4. **Oversample target populations** from the ACS frame (e.g., low-income, SNAP-eligible)

### Applied to FoodAPS

**Current FoodAPS workflow:**
```
Independent sample → Screener interview (income, household size, SNAP status)
→ Full demographic battery (123 overlapping questions)
→ Food acquisition diary (7 days)
→ Final interview
```

**ACS-linked FoodAPS workflow:**
```
ACS completes annual survey → Identify target strata (low-income, SNAP, etc.)
→ Recruit subset for FoodAPS supplement
→ Link ACS record (skip 123 questions)
→ Food acquisition diary (7 days)
→ Final interview
```

### Quantified Benefits

| Metric | Current Model | ACS-Linked Model |
|--------|---------------|------------------|
| Questions per respondent | ~300+ | ~175 (est. 40% reduction) |
| Respondent burden | High (multiple interviews) | Lower (skip demographics) |
| Data consistency | Self-reported each time | Anchored to ACS record |
| Analytical power | Population-level only | Individual-level linkage |
| Sample frame quality | Address-based, requires screening | Pre-identified from ACS |
| Longitudinal potential | None (cross-sectional) | Link to ACS panel design |

### Practical Considerations

**Legal/consent requirements:**
- ACS respondents would need to consent to recontact for supplements
- Statistical confidentiality protections (Title 13, CIPSEA) apply
- May require OMB clearance for modified design

**Technical requirements:**
- Secure linkage infrastructure (Census Bureau has this)
- Timing coordination (FoodAPS fielding aligned with ACS response windows)
- Variable harmonization (ensure ACS variables meet FoodAPS analytical needs)

**What would NOT transfer:**
- Reference period differences (ACS asks about "past 12 months"; FoodAPS needs current-week context)
- Domain-specific detail (ACS income ≠ FoodAPS food-specific income allocation)
- Some questions may need retention despite apparent overlap

---

## Research Questions for Question-Level Analysis

The concept-level overlap (123 questions) provides the upper bound on consolidation potential. Question-level analysis would determine the actual achievable reduction:

1. **Exact duplicates**: Identical question wording, response options, reference period
   - These are directly droppable with linkage

2. **Near duplicates**: Same concept, minor wording differences
   - May require crosswalk validation before dropping

3. **Reference period mismatches**: "Past 12 months" vs. "past 7 days" vs. "current"
   - May not be substitutable; retention likely needed

4. **Response scale differences**: Continuous vs. categorical, different bins
   - May require retention or recoding validation

5. **Domain-specific precision**: General income vs. food-allocated income
   - Supplement may need finer granularity than ACS provides

### Proposed Methodology

For each overlapping subtopic:
1. Extract actual question text from both ACS and FoodAPS instruments
2. Classify each pair as: exact match, near match, different reference period, different scale, conceptually related but distinct
3. Estimate "droppable" percentage by category
4. Calculate realistic respondent burden reduction

---

## Broader Implications

FoodAPS is one case study. The same model applies across the federal survey ecosystem:

| Survey | ACS Overlap | Linkage Feasibility | Consolidation Potential |
|--------|-------------|---------------------|------------------------|
| SIPP | 577 questions | High (Census-run) | Significant |
| CPS | 181 questions | High (Census-run) | Moderate (already supplements) |
| AHS | 460 questions | High (Census-run) | Significant |
| CE | 283 questions | Medium (BLS-run, Census-collected) | Moderate |
| NHIS | 430 questions | Medium (CDC-run) | Requires interagency agreement |

The CPS model is instructive: it already operates as a core labor force survey with rotating supplements (Food Security, Voting, Internet Use, etc.). ACS could serve a similar backbone function for household economic surveys.

---

## Conclusion

Concept mapping identifies where surveys measure the same things. But "so what?" requires answering whether records can be linked. 

**Without linkage**: Overlap is unavoidable—each survey needs its own demographic baseline to define comparable universes. Apparent duplication is actually methodological necessity.

**With linkage**: Overlap becomes eliminable redundancy. Supplements can reference backbone surveys, reducing respondent burden, improving data consistency, and enabling individual-level analysis that aggregate comparisons cannot support.

The path forward requires:
1. Question-level analysis to quantify realistic consolidation potential
2. Legal/policy review of consent and confidentiality requirements  
3. Interagency coordination for non-Census surveys
4. Pilot testing with a tractable case (FoodAPS or similar)

The value proposition is not just efficiency—it's analytical power. Linked data answers questions that parallel surveys cannot.

---

## References

- USDA Economic Research Service. FoodAPS National Household Food Acquisition and Purchase Survey. https://www.ers.usda.gov/data-products/foodaps-national-household-food-acquisition-and-purchase-survey/
- Census Bureau. American Community Survey. https://www.census.gov/programs-surveys/acs
- Federal survey concept mapping analysis (this project), 2024-2025.

---

*Document created: January 2025*
*Project: Federal Survey Concept Mapper*
