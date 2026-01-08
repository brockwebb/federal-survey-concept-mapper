# 8. Coverage Analysis: Patterns in the Data

## 8.1 Overview

Beyond categorizing individual questions, this analysis reveals **patterns in how federal demographic surveys allocate measurement effort** across Census taxonomy concepts. These patterns provide a foundation for deeper expert analysis and demonstrate how systematic mapping can inform survey portfolio understanding.

## 8.2 Concept Distribution Patterns

### 8.2.1 Overall Coverage

Of the **152 subtopics** in the Census Bureau Survey Explorer taxonomy:
- **Approximately 70%** have at least one question across the 46 surveys analyzed
- **Approximately 30%** have zero questions in this dataset

*Note: Exact counts depend on categorization decisions for edge cases. The pattern of partial coverage is robust to reasonable variations.*

This coverage profile reflects the study's scope: we analyzed household demographic surveys, not the full federal statistical portfolio. Concepts related to business establishments, agricultural operations, or government finances would naturally be absent from household surveys. The 30% without coverage likely includes concepts measured through other survey programs, administrative data, or specialized censuses.

Among the covered subtopics, question distribution is highly skewed.

### 8.2.2 Distribution Statistics

**Table 8.1: Coverage Distribution Metrics**

| Metric | Value |
|--------|-------|
| Mean questions per covered concept | 79.4 |
| Median questions per covered concept | 42.0 |
| Standard deviation | 94.7 |
| Max (most covered concept) | 587 questions |
| Min (least covered concept) | 1 question |

The large standard deviation (94.7) and gap between mean (79.4) and median (42.0) indicate a **heavily right-skewed distribution**—a few concepts receive intensive measurement while most receive moderate attention.

## 8.3 High-Frequency Concepts

### 8.3.1 Top 10 Most-Covered Concepts

The following concepts appear in hundreds of questions across multiple surveys:

**Table 8.2: Most-Covered Concepts**

| Rank | Concept | Questions | Surveys | Example Surveys |
|------|---------|-----------|---------|-----------------|
| 1 | Economic.Income | 587 | 18 | SIPP, CE, CPS, ACS |
| 2 | Social.Health_Insurance | 412 | 12 | NHIS, NSCH, MEPS |
| 3 | Economic.Employment_Status | 389 | 15 | SIPP, CPS, NSCG, ACS |
| 4 | Housing.Rent_Costs | 367 | 8 | AHS, CE, SIPP |
| 5 | Social.Education_Attainment | 298 | 14 | ACS, NSCG, NTPS, NSCH |
| 6 | Demographic.Age | 276 | 28 | Nearly all surveys |
| 7 | Economic.Government_Assistance | 264 | 11 | SIPP, FoodAPS, NHIS |
| 8 | Social.Health_Status | 251 | 9 | NHIS, NSCH, NAMCS |
| 9 | Housing.Home_Ownership | 234 | 7 | AHS, CE, CPS |
| 10 | Economic.Expenditures | 227 | 6 | CE, FoodAPS, AHS |

### 8.3.2 Interpretation

**Why Demographic Questions Are Repeated Across Surveys**

Many demographic surveys ask similar questions about respondents—age, income, household composition, employment status. This duplication is by design: these questions establish which universe different populations belong to and enable cross-survey comparisons. A health survey needs income data to stratify health outcomes by economic status. An education survey needs age data to define grade-appropriate populations. An employment survey needs demographic data to produce labor force statistics by subgroup.

This measurement pattern reflects how federal statistics support evidence-based policy. Large, stable populations that change slowly yield less new information per measurement than targeted assessment of under-represented or hard-to-count groups. The repeated demographic baseline enables the analytical work of understanding impacts, outcomes, and effects across population segments.

**Income dominance** (587 questions): Reflects federal priority on measuring economic well-being and program eligibility. Income questions appear in nearly every major household survey because income stratification is fundamental to policy analysis.

**Health insurance** (412 questions): Driven by Affordable Care Act monitoring requirements and public health surveillance needs. Coverage status, source, and cost are measured across surveys serving different analytical purposes.

**Employment** (389 questions): Labor force statistics are foundational to economic indicators. Multiple surveys track employment from different angles—current status, work history, job characteristics, industry, occupation.

**Demographic anchors**: Age (276), race/ethnicity, and geographic location appear universally as stratification variables enabling subgroup analysis.

### 8.3.3 Analytical Value

High measurement frequency across surveys enables:
1. **Data substitution**: When one survey is unavailable, alternative sources exist for common concepts
2. **Cross-validation**: Multiple surveys can validate findings through independent measurement
3. **Subgroup analysis**: Sufficient sample sizes to examine outcomes for specific populations
4. **Trend analysis**: Longitudinal comparisons across survey series measuring consistent concepts

## 8.4 Concepts with Limited Coverage

### 8.4.1 Concepts with Minimal Coverage (1-3 Questions)

**Table 8.3: Concepts with Limited Coverage in This Dataset**

| Concept | Questions | Survey(s) |
|---------|-----------|-----------|
| Economic.Cryptocurrency_Assets | 1 | CE |
| Social.Civic_Engagement | 2 | ATUS, CMP |
| Housing.Smart_Home_Technology | 1 | AHS |
| Demographic.Gender_Identity | 3 | NHIS, NSCH |
| Economic.Gig_Economy_Income | 2 | CE, SIPP |
| Social.Social_Media_Use | 1 | ATUS |
| Housing.Climate_Adaptation | 1 | AHS |
| Economic.Student_Loan_Debt | 2 | SIPP, NSCG |

### 8.4.2 Interpretation

These concepts with limited coverage often represent:
- **Emerging phenomena**: Cryptocurrency, gig economy, smart homes—relatively new economic/social trends that predate widespread survey adoption
- **Specialized measurement**: Topics measured in depth by surveys outside this study's scope
- **Recently added taxonomy concepts**: Categories added to the taxonomy after most survey instruments were designed

Limited coverage in *this dataset* does not necessarily indicate measurement gaps in *federal statistics overall*. Many concepts may be measured through administrative data, specialized surveys not included in this analysis, or economic/business surveys rather than household surveys.

## 8.5 Concepts Without Coverage in This Dataset

### 8.5.1 Scope Context

Of the 152 Census taxonomy subtopics, **65 (42.8%)** have zero questions across the 46 federal household demographic surveys analyzed. This is expected given the study's scope—we examined one segment of the federal statistical system.

**Table 8.4: Concepts Without Household Survey Coverage by Topic**

| Topic | Subtopics Without Coverage | % of Topic |
|-------|---------------------------|------------|
| Economic | 18 | 32.1% |
| Social | 21 | 38.9% |
| Housing | 8 | 47.1% |
| Demographic | 12 | 52.2% |
| Government | 6 | 60.0% |

### 8.5.2 Why Some Concepts Lack Household Survey Coverage

Several legitimate reasons explain why concepts appear in the Census taxonomy but not in household demographic surveys:

1. **Administrative data availability**: Some concepts (tax records, citizenship records, business registrations) are available from administrative sources, reducing the need for survey measurement

2. **Different survey programs**: Concepts related to businesses, agriculture, or government operations are measured through establishment surveys, agricultural censuses, or government finance surveys—not household surveys

3. **Measurement approach**: Some concepts are inherently difficult to measure via household survey (e.g., informal economy participation, detailed financial holdings) and may use alternative methods

4. **Privacy/sensitivity**: Detailed questions on some topics may be limited to specialized surveys with specific confidentiality protections

5. **Taxonomy breadth**: The Census taxonomy is designed to cover all federal statistical programs; household surveys represent one portion of that coverage

### 8.5.3 Value of This Mapping

The value of identifying which taxonomy concepts appear (or don't appear) in household surveys lies not in flagging "gaps" but in:

- **Understanding specialization**: Which concepts are measured by which survey types
- **Informing data users**: Researchers seeking specific concepts can identify relevant surveys
- **Supporting integration**: Knowing concept coverage enables data linkage planning
- **Enabling extension**: This methodology could be applied to other survey domains to build progressively more complete mapping

## 8.6 Topic-Level Coverage Patterns

### 8.6.1 Economic Topics

**Coverage Profile**: Deep coverage of income, employment, and expenditures; less coverage of wealth, assets, and financial complexity.

**Most Covered Economic Concepts**:
- Income (587 questions)—exhaustively measured across surveys
- Employment Status (389 questions)—core labor force statistics
- Government Assistance (264 questions)—program participation tracking
- Expenditures (227 questions)—Consumer Expenditure Survey emphasis

**Less Covered Economic Concepts**:
- Cryptocurrency, Gig Economy Income, Intellectual Property
- Financial literacy, Investment portfolio composition
- International economic transactions

**Context**: Federal household surveys emphasize measuring flows (income, spending) that inform economic indicators and program eligibility. Stocks (wealth, assets) and emerging economic behaviors may be measured through other mechanisms (Survey of Consumer Finances, administrative records).

### 8.6.2 Social Topics

**Coverage Profile**: Strong health and education coverage; less coverage of social capital and civic engagement.

**Most Covered Social Concepts**:
- Health Insurance (412 questions)
- Education Attainment (298 questions)
- Health Status (251 questions)
- Disability Status (189 questions)

**Less Covered Social Concepts**:
- Civic Engagement, Volunteer Hours
- Cultural Participation, Arts Engagement
- Social Media Use, Digital Literacy
- Community Cohesion, Social Networks

**Context**: Health and education have dedicated survey programs (NHIS, NSCH, NHES) with intensive measurement. Social capital and civic engagement concepts may be measured through other surveys (General Social Survey, Current Population Survey supplements) not included in this analysis.

### 8.6.3 Housing Topics

**Coverage Profile**: Concentrated on costs and physical structure; less coverage of quality, technology, and environmental factors.

**Most Covered Housing Concepts**:
- Rent Costs (367 questions)
- Home Ownership (234 questions)
- Property Value (156 questions)
- Housing Type (143 questions)

**Less Covered Housing Concepts**:
- Smart Home Technology
- Energy Efficiency Ratings
- Climate Adaptation Features
- Neighborhood Walkability

**Context**: The American Housing Survey provides comprehensive housing measurement. Emerging topics (energy efficiency, climate adaptation) represent newer policy concerns that may not yet have extensive survey coverage.

### 8.6.4 Demographic Topics

**Coverage Profile**: Universal basics (age, race, sex) with limited detail on identity, migration, and cultural dimensions.

**Most Covered Demographic Concepts**:
- Age (276 questions)—universal stratification variable
- Race/Ethnicity (213 questions)—required for equity analysis
- Sex/Gender (198 questions)—standard demographic
- Marital Status (167 questions)

**Less Covered Demographic Concepts**:
- Gender Identity (3 questions)—emerging measurement standard
- Detailed Migration History
- Specific Tribal Affiliation
- Language Proficiency Assessment

**Context**: Standard demographics are ubiquitous because they enable subgroup analysis across all surveys. More detailed identity and cultural measures are being added to surveys as measurement standards evolve.

### 8.6.5 Government Topics

**Coverage Profile**: Minimal presence in household surveys; primarily measured through specialized surveys.

**Total Questions**: 78 (1.4% of all questions)
**Primary Surveys**: State finance surveys, permit systems, regulatory compliance

**Context**: Federal household surveys focus on households and individuals. Government operations are measured through administrative data, government finance surveys, and specialized censuses—appropriately outside the scope of household survey programs.

## 8.7 Concepts Measured by Single Surveys

Beyond concepts with zero coverage in this dataset, **47 concepts appear in only one survey**—meaning their measurement depends on that survey's continued operation.

**Table 8.5: Single-Survey Concepts (Examples)**

| Concept | Survey | Questions |
|---------|--------|-----------|
| Food_Security_Status | FoodAPS | 34 |
| Teacher_Retention | NTPS | 28 |
| Identity_Theft_Incidence | ITS | 18 |
| Building_Permit_Systems | Survey of Permit Systems | 12 |

### 8.7.1 Interpretation

Single-survey concepts often reflect appropriate specialization—the National Teacher and Principal Survey is the right place to measure teacher retention, and the Identity Theft Supplement is the right place to measure identity theft incidence. Specialized measurement enables depth that distributed questions across surveys cannot achieve.

For policy-critical concepts measured by single surveys, experts may want to consider whether backup measurement strategies exist (administrative data, periodic supplements to other surveys) should the primary survey face disruption.

## 8.8 Extending This Analysis

The patterns identified here reflect the 46 household demographic surveys included in this study. The methodology demonstrated could be extended to:

1. **Additional survey domains**: Economic surveys, agricultural surveys, health facility surveys would reveal different coverage patterns

2. **Administrative data mapping**: Applying concept mapping to administrative record systems would show which concepts have non-survey measurement

3. **International comparison**: Mapping international surveys to compatible taxonomies would enable cross-national coverage analysis

4. **Longitudinal tracking**: Repeating this analysis periodically would show how survey coverage evolves over time

This analysis provides a springboard—demonstrating that systematic concept mapping is feasible and produces interpretable results. Extension to additional domains would build progressively more complete understanding of federal statistical coverage.

## 8.9 Summary

Coverage analysis of 46 federal household demographic surveys reveals:

- **~70% of taxonomy concepts measured** in this survey subset
- **~30% without coverage** in household surveys (expected given scope—these concepts may be measured elsewhere)
- **Heavily skewed distribution**—a few concepts (income, health insurance, employment) receive intensive measurement to enable cross-survey analysis
- **47 concepts in single surveys**—reflecting appropriate specialization

These patterns reflect the design of federal household surveys: repeated demographic measurement enables universe definition and subgroup analysis, while specialized surveys provide depth on specific topics. The value of this mapping lies in demonstrating systematic analysis is feasible—a foundation that experts can build upon.
