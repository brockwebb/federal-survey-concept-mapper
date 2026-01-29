# Survey Selection: Family 2 Economic Household Surveys

## The ACS as a Linkage Backbone

The American Community Survey (ACS) is the largest household survey in the federal statistical system, collecting data continuously from approximately 3.5 million households annually. Its comprehensive coverage of demographics, economics, housing, and social characteristics makes it a natural candidate for record linkage with specialized surveys.

The key insight: rather than each survey independently collecting the same demographic information, surveys could potentially sample from ACS respondents and link records, collecting only the specialized content unique to their mission.

## Family 2: Economic Household Surveys

From the broader concept mapping analysis (Phase 1), we identified "Family 2" as surveys sharing substantial conceptual overlap with ACS in economic and household domains:

| Survey | Full Name | Total Shared Questions | Subtopics Covered | Dominant Domain |
|--------|-----------|------------------------|-------------------|-----------------|
| SIPP | Survey of Income and Program Participation | 577 | 38 | Economic (304) |
| AHS | American Housing Survey | 460 | 34 | Housing (343) |
| CE | Consumer Expenditure Survey | 283 | 30 | Housing/Economic |
| CPS | Current Population Survey | 181 | 25 | Economic (110) |
| FoodAPS | Food Acquisition and Purchase Survey | 123 | 23 | Economic (59) |

**Total across Family 2: 1,624 shared questions with ACS**

## Why FoodAPS and CPS?

We selected FoodAPS and CPS as pilot cases for question-level analysis:

**Practical considerations:**
- Lowest question counts (123 and 181) → tractable for methodology development
- Combined: 1,702 question pairs to classify
- Estimated API cost: ~$1.50 total

**Analytical considerations:**
- Different overlap profiles: FoodAPS is SNAP-heavy, CPS is employment-heavy
- Different survey designs: FoodAPS is a specialized supplement, CPS is a core labor force survey
- Testing generalizability across survey types

**What we deferred:**
- SIPP (577 questions) - largest, save for scaled analysis
- AHS (460 questions) - housing-dominated, different domain
- CE (283 questions) - moderate size, future candidate

## Domain Distribution

### FoodAPS (123 questions)

| Domain | Count | Top Subtopics |
|--------|-------|---------------|
| Economic | 59 | Food Stamps/SNAP (22), Earnings (10), Employment (9) |
| Social | 42 | Household (18), School Enrollment (11), Veterans (5) |
| Demographic | 12 | Age (3), Sex (3), Race (2), Relationship (2) |
| Housing | 10 | Costs (6), Vehicles (2), Tenure (1) |

### CPS (181 questions)

| Domain | Count | Top Subtopics |
|--------|-------|---------------|
| Economic | 110 | Employment Status (36), Earnings (23), Hours/Week (19) |
| Social | 41 | Disability (17), Household (10), Education (5) |
| Demographic | 29 | Relationship (10), Age (3), Race (3), Hispanic (3) |
| Housing | 1 | Tenure (1) |

## Implications for Pair Generation

Questions are paired **within shared subtopics only**. This means:
- FoodAPS's 22 SNAP questions pair with ACS's 1 SNAP question → 22 pairs
- CPS's 36 Employment Status questions pair with ACS's 6 Employment questions → 216 pairs
- Cross-subtopic comparisons are excluded (reduces noise)

The total pair counts:
- **FoodAPS × ACS**: 610 pairs
- **CPS × ACS**: 1,092 pairs
- **Combined**: 1,702 pairs

This many-to-many pairing within subtopics is why pair counts exceed question counts.
