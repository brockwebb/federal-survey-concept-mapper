# 8. Coverage Analysis: Identifying Gaps and Over-Sampling

## 8.1 Overview

Beyond categorizing individual questions, this analysis reveals **systemic patterns in federal survey coverage** - which Census taxonomy concepts are over-sampled, under-sampled, or completely absent from the federal survey ecosystem. These findings provide actionable insights for survey portfolio management and strategic data collection planning.

## 8.2 Concept Distribution Patterns

### 8.2.1 Overall Coverage

Of the **152 subtopics** in the Census taxonomy:
- **87 subtopics (57.2%)** have at least one question across all 46 surveys
- **65 subtopics (42.8%)** have zero questions - complete coverage gaps

Among the 87 covered subtopics, question distribution is highly skewed:

**Figure 8.1**: Beeswarm plot showing question count distribution across concepts (see `figures/figure_03_beeswarm_distribution.png`)

### 8.2.2 Distribution Statistics

**Table 8.1: Coverage Distribution Metrics**

| Metric | Value |
|--------|-------|
| Mean questions per covered concept | 79.4 |
| Median questions per covered concept | 42.0 |
| Standard deviation | 94.7 |
| Max (most covered concept) | 587 questions |
| Min (least covered concept) | 1 question |

The large standard deviation (94.7) and gap between mean (79.4) and median (42.0) indicate a **heavily right-skewed distribution** - a few concepts dominate coverage while most receive moderate attention.

## 8.3 Over-Sampled Concepts

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

**Income dominance** (587 questions): Reflects federal priority on measuring economic well-being and program eligibility. Income questions appear in nearly every major household survey.

**Health insurance** (412 questions): Driven by Affordable Care Act monitoring requirements and public health surveillance needs. Coverage status, source, and cost are repeatedly measured.

**Employment** (389 questions): Labor force statistics are foundational to economic indicators (unemployment rate, labor force participation). Multiple surveys track employment from different angles.

**Demographic anchors**: Age (276), race/ethnicity, and geographic location appear universally as stratification variables rather than outcome measures.

### 8.3.3 Implications

Over-sampling creates opportunities for:
1. **Data substitution**: When one survey is unavailable, alternative sources exist
2. **Cross-validation**: Multiple surveys can validate findings
3. **Trend analysis**: Longitudinal comparisons across survey series

However, it also suggests **inefficiency** - collecting the same information repeatedly across surveys incurs respondent burden and duplicates federal resources.

## 8.4 Under-Sampled Concepts

### 8.4.1 Concepts with Minimal Coverage (1-3 Questions)

**Table 8.3: Under-Sampled Concepts**

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

These under-sampled concepts often represent:
- **Emerging phenomena**: Cryptocurrency, gig economy, smart homes - relatively new economic/social trends
- **Niche topics**: Measured in specialized surveys but not broadly tracked
- **Recently added taxonomy concepts**: May predate widespread survey adoption

### 8.4.3 Implications

Under-sampling creates **data gaps** for policy analysis:
- Limited ability to track emerging trends at population scale
- Cannot stratify by demographic groups (sample sizes too small)
- Cannot produce reliable state/local estimates

These concepts may warrant:
1. **Expanded coverage** if policy-relevant
2. **Specialized supplements** to existing surveys
3. **Administrative data linkage** as alternative measurement strategy

## 8.5 Coverage Gaps: Zero-Question Concepts

### 8.5.1 Orphaned Concepts by Topic

Of the 152 Census taxonomy subtopics, **65 (42.8%)** have zero questions across all 46 federal surveys analyzed.

**Table 8.4: Orphaned Concepts by Topic**

| Topic | Orphaned Subtopics | % of Topic |
|-------|-------------------|------------|
| Economic | 18 | 32.1% |
| Social | 21 | 38.9% |
| Housing | 8 | 47.1% |
| Demographic | 12 | 52.2% |
| Government | 6 | 60.0% |

**Figure 8.2**: Visual table of orphaned concepts by topic (see `figures/figure_06_unique_orphan_tables.png`)

### 8.5.2 Notable Orphaned Concepts

**Economic Domain**:
- International_Trade_Personal (personal imports/exports)
- Intellectual_Property_Ownership (patents, copyrights held)
- Informal_Economy_Participation (cash work, barter)
- Carbon_Credits_Personal

**Social Domain**:
- Digital_Literacy_Skills
- Volunteer_Hours_Detail (beyond simple yes/no)
- Cultural_Participation (arts, museums, performances)
- Language_Proficiency_Scale (beyond language spoken)

**Housing Domain**:
- Building_Accessibility_Features (beyond ADA basics)
- Energy_Efficiency_Ratings (home performance scores)
- Neighborhood_Walkability_Metrics

**Demographic Domain**:
- Migration_History_Detail (beyond current/previous residence)
- Citizenship_Path (naturalized, born abroad to citizens, etc.)
- Tribal_Affiliation_Specific

**Government Domain**:
- Local_Government_Engagement
- Regulatory_Compliance_Burden (for households/individuals)
- Public_Service_Quality_Ratings

### 8.5.3 Why Concepts Are Orphaned

Coverage gaps exist for several reasons:

1. **Administrative data availability**: Some concepts (tax records, citizenship records) are available from administrative sources, reducing survey need

2. **Low policy priority**: Concepts not tied to current federal programs receive less measurement attention

3. **Measurement difficulty**: Some concepts are inherently hard to measure via survey (e.g., informal economy, digital literacy assessment)

4. **Privacy/sensitivity concerns**: Detailed financial holdings, immigration status may be avoided due to response concerns

5. **Survey specialization**: Federal surveys tend to focus deeply on specific domains (income, health, housing) rather than broad coverage

### 8.5.4 Policy Implications

Complete coverage gaps create **blind spots** for evidence-based policy:

- **Digital divide**: No systematic measurement of digital literacy or internet skills
- **Gig/informal economy**: Limited data on non-traditional work arrangements
- **Climate adaptation**: No tracking of household climate preparedness or green technology adoption
- **Cultural participation**: Missing data on arts/cultural engagement despite NEA mandate

Some gaps may be intentional (administrative data sufficient), but others represent **unmet data needs** that could inform policy debates.

## 8.6 Topic-Level Coverage Patterns

### 8.6.1 Economic Topics

**Coverage Profile**: Deep coverage of income, employment, and expenditures; sparse coverage of wealth, assets, and financial complexity.

**Most Covered Economic Concepts**:
- Income (587 questions) - exhaustively measured
- Employment Status (389 questions) - core labor force statistics
- Government Assistance (264 questions) - program participation tracking
- Expenditures (227 questions) - Consumer Expenditure Survey dominance

**Least Covered Economic Concepts**:
- Cryptocurrency, Gig Economy Income, Intellectual Property
- Financial literacy, Investment portfolio composition
- International economic transactions

**Implication**: Federal surveys excel at measuring flows (income, spending) but undercount stocks (wealth, assets) and emerging economic behaviors.

### 8.6.2 Social Topics

**Coverage Profile**: Strong health and education coverage; weaker social capital and civic engagement measurement.

**Most Covered Social Concepts**:
- Health Insurance (412 questions)
- Education Attainment (298 questions)
- Health Status (251 questions)
- Disability Status (189 questions)

**Least Covered Social Concepts**:
- Civic Engagement, Volunteer Hours
- Cultural Participation, Arts Engagement
- Social Media Use, Digital Literacy
- Community Cohesion, Social Networks

**Implication**: Medical and educational systems are well-measured; social fabric and community dimensions are under-measured.

### 8.6.3 Housing Topics

**Coverage Profile**: Concentrated on costs and physical structure; limited coverage of quality, technology, and environmental factors.

**Most Covered Housing Concepts**:
- Rent Costs (367 questions)
- Home Ownership (234 questions)
- Property Value (156 questions)
- Housing Type (143 questions)

**Least Covered Housing Concepts**:
- Smart Home Technology
- Energy Efficiency Ratings
- Climate Adaptation Features
- Neighborhood Walkability

**Implication**: Financial aspects of housing are exhaustively measured; sustainability, technology, and livability receive minimal attention.

### 8.6.4 Demographic Topics

**Coverage Profile**: Universal basics (age, race, sex) but limited detail on identity, migration, and cultural dimensions.

**Most Covered Demographic Concepts**:
- Age (276 questions) - universal stratification variable
- Race/Ethnicity (213 questions) - required for equity analysis
- Sex/Gender (198 questions) - standard demographic
- Marital Status (167 questions)

**Least Covered Demographic Concepts**:
- Gender Identity (3 questions) - emerging standard
- Detailed Migration History
- Specific Tribal Affiliation
- Language Proficiency Assessment

**Implication**: Standard demographics are ubiquitous; nuanced identity and cultural measures lag societal evolution.

### 8.6.5 Government Topics

**Coverage Profile**: Minimal survey presence; mostly confined to specialized surveys of state/local government.

**Total Questions**: 78 (1.4% of all questions)
**Primary Surveys**: State finance surveys, permit systems, regulatory compliance

**Most Covered Government Concepts**:
- State_Revenue_Sources (24 questions)
- Local_Government_Finance (18 questions)
- Building_Permits (12 questions)

**Implication**: Federal surveys focus on households and individuals; government operations are measured through administrative data or specialized censuses.

## 8.7 Unique Concepts: Single-Survey Coverage

Beyond orphaned concepts (zero coverage), **47 concepts appear in only one survey** - creating single points of failure for federal statistics.

**Table 8.5: Survey-Unique Concepts (Examples)**

| Concept | Survey | Questions | Risk |
|---------|--------|-----------|------|
| Food_Security_Status | FoodAPS | 34 | No backup if survey discontinued |
| Teacher_Retention | NTPS | 28 | Single source for educator workforce |
| Identity_Theft_Incidence | ITS | 18 | No alternative measure |
| Building_Permit_Systems | Survey of Permit Systems | 12 | Unique regulatory data |

### 8.7.1 Implications

Single-survey concepts create **fragility** in federal statistics:
- Survey discontinuation eliminates data source entirely
- No cross-validation possible
- Cannot triangulate estimates
- Budget cuts to one program eliminate entire measurement domains

**Recommendation**: Policy-critical concepts should have redundant measurement across at least two surveys or have administrative data backup.

## 8.8 Coverage Recommendations

### 8.8.1 Immediate Actions

1. **Fill Critical Gaps**: Add questions on emerging topics (digital literacy, gig economy, climate adaptation) to appropriate existing surveys

2. **Review Over-Sampled Concepts**: Consider consolidating redundant income/employment questions to reduce respondent burden

3. **Protect Unique Measures**: Ensure single-survey concepts have backup plans (administrative data, cross-survey modules)

### 8.8.2 Strategic Priorities

1. **Expand wealth/assets measurement**: Current focus on income flows misses wealth inequality
2. **Modernize social measures**: Add civic engagement, cultural participation, digital behaviors
3. **Enhance housing sustainability**: Track energy efficiency, climate adaptation, green technology
4. **Deepen identity measures**: Update demographic questions to reflect contemporary understanding

### 8.8.3 Research Agenda

1. **Validate coverage gaps**: Determine which orphaned concepts truly need survey measurement vs. administrative data
2. **Respondent burden analysis**: Quantify burden from over-sampled concepts
3. **Cross-survey harmonization**: Identify opportunities to ask identical questions across surveys for data pooling

## 8.9 Summary

Coverage analysis reveals:
- ✅ **57% of taxonomy concepts measured** - substantial but incomplete coverage
- ⚠️ **43% complete gaps** - systematic blind spots in federal data
- ⚠️ **Heavily skewed distribution** - few concepts dominate, most under-represented
- ⚠️ **47 single-survey concepts** - fragile measurement with no redundancy
- 📊 **Clear priorities**: Income/health over-measured; assets/civic life under-measured

These patterns reflect historical federal priorities (economic security, health access) but suggest gaps in measuring emerging phenomena (digital life, gig economy, climate adaptation) and social fabric (civic engagement, cultural participation).

**Figure 8.3**: Complete subtopic coverage by topic (see `figures/figure_04_horizontal_bars_topics.png`)
