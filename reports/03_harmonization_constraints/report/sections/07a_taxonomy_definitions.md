# Appendix A: Taxonomy Definitions

<!-- Pull from: docs/taxonomy_v1.md, docs/coding_procedure.md -->

## Harmonization Feasibility Codes

### F1: Direct Recode

**Definition**: Variables are mechanically transformable through simple recoding, collapsing categories, or unit conversion.

**Action Required**: Simple data transformation

**Characteristics**:
- Same underlying construct
- Compatible measurement scale
- Deterministic mapping between responses
- No loss of information (or acceptable minimal loss)

**Examples**:

| Source | Target | Transformation |
|--------|--------|----------------|
| Age in years (continuous) | Age in 5-year brackets | Group into categories |
| Income in dollars | Income in thousands | Divide by 1,000 |
| Hours worked (0-168) | Hours worked (0-168) | Direct copy (identical) |
| Education (8 categories) | Education (4 categories) | Collapse categories |

**Data Quality**: F1 transformations preserve original information or involve only aggregation (no modeling or imputation).

---

### F2: Statistical Adjustment

**Definition**: Variables require modeling, imputation, bridging studies, or statistical harmonization methods to make comparable.

**Action Required**: Statistical harmonization (modeling, imputation, or bridging)

**Characteristics**:
- Related but not identical constructs
- Requires statistical assumptions
- May involve measurement error or information loss
- Transformation is probabilistic, not deterministic

**Examples**:

| Source | Target | Transformation |
|--------|--------|----------------|
| Weekly work hours | Annual work weeks | Model seasonal patterns, impute missing data |
| Hourly wage (excluding tips) | Hourly wage (including tips) | Impute tip proportion based on occupation |
| Food insecurity (12-item battery) | Food insecurity (6-item battery) | Bridging study to map scales |
| Health insurance (current) | Health insurance (annual) | Model coverage transitions |

**Data Quality**: F2 transformations introduce modeling assumptions and potential bias. Users must assess fitness-for-purpose.

---

### F3: Incompatible

**Definition**: Variables measure fundamentally different constructs and cannot be harmonized without re-fielding questions.

**Action Required**: No harmonization possible

**Characteristics**:
- Different underlying constructs
- No statistical transformation can bridge gap
- Conceptual rather than operational barriers
- Would require new data collection to resolve

**Examples**:

| Source | Target | Why Incompatible |
|--------|--------|------------------|
| "Do you want to work full-time?" | "Did you work last week?" | Intention vs. behavior |
| "How many children live with you?" | "How many children have you given birth to?" | Household composition vs. lifetime fertility |
| "Annual household income" | "Hourly wage at main job" | Different income concepts |
| "Food security score" | "SNAP participation" | Outcome measure vs. program participation |

**Barrier Codes**: F3 classifications must include a barrier code explaining why harmonization is impossible.

---

## Barrier Code Taxonomy

When variables are F3 (incompatible), one of the following barrier codes applies:

### Temporal Constraints (TC)

Reference period or timing differences that prevent meaningful comparison.

#### TC.1: Reference Period Length

**Definition**: Different recall windows or time spans.

**Examples**:
- "Hours worked last week" vs. "Hours worked in past 12 months"
- "Income last month" vs. "Income last year"
- "Health status today" vs. "Health status past year"

**Why Incompatible**: Different reference periods capture different phenomena (short-term vs. long-term patterns, seasonal effects, recall bias).

---

#### TC.2: Temporal Framing

**Definition**: Point-in-time vs. habitual vs. retrospective framing.

**Examples**:
- "Did you work last week?" (point-in-time) vs. "Do you usually work?" (habitual)
- "Are you currently enrolled?" (present) vs. "Were you ever enrolled?" (retrospective)
- "Last week's income" vs. "Usual weekly income"

**Why Incompatible**: Habitual measures smooth over variation; point-in-time measures capture specific instances.

---

#### TC.3: Calendar Alignment

**Definition**: Fixed calendar periods vs. rolling reference periods.

**Examples**:
- "Income in calendar year 2025" vs. "Income in past 12 months"
- "Employment status January 1" vs. "Employment status on interview date"
- "Tax year" vs. "Fiscal year"

**Why Incompatible**: Calendar alignment affects comparability across respondents interviewed at different times.

---

### Construct/Concept Constraints (CC)

Concept definition or operationalization differences - the most common barrier type.

#### CC.1: Concept Definition

**Definition**: Different meaning of core term or different construct entirely.

**Examples**:
- "Employment" including vs. excluding unpaid work
- "Income" including vs. excluding government transfers
- "Household" including vs. excluding non-relatives
- "Disability" based on self-report vs. functional limitations

**Why Incompatible**: Measuring fundamentally different things, even if using similar terminology.

**This is the dominant barrier** (70% of F3 pairs).

---

#### CC.2: Operationalization

**Definition**: Different behavioral indicators or measurement approaches for nominally the same concept.

**Examples**:
- "Food insecurity" measured by 12-item battery vs. single question
- "Health status" measured by self-rating vs. diagnosed conditions
- "Job search" measured by specific activities vs. general question
- "Poverty" based on income thresholds vs. consumption measures

**Why Incompatible**: Different operationalizations capture different dimensions of the construct.

---

#### CC.3: Boundary Conditions

**Definition**: Different thresholds, cutoffs, or qualifying conditions.

**Examples**:
- "Full-time work" defined as 35+ hours vs. 40+ hours
- "Low income" using different poverty thresholds
- "Recent immigrant" defined as <5 years vs. <10 years
- "Elderly" defined as 65+ vs. 60+

**Why Incompatible**: Boundary differences create non-overlapping populations or classifications.

---

#### CC.4: Scope Inclusions

**Definition**: Different components counted or included in measurement.

**Examples**:
- "Income" including vs. excluding capital gains
- "Household members" including vs. excluding temporary residents
- "Work hours" including vs. excluding overtime
- "Educational attainment" including vs. excluding vocational training

**Why Incompatible**: Different scope creates systematically different measures.

---

### Population/Coverage Constraints (PC)

Universe, frame, or sample design differences.

#### PC.1: Universe Definition

**Definition**: Target population differs between surveys.

**Examples**:
- Civilian population vs. all residents
- Adults 18+ vs. all household members
- US citizens vs. all residents
- Employed persons vs. labor force participants

**Why Incompatible**: Questions asked of different populations cannot be directly compared.

---

#### PC.2: Frame Exclusions

**Definition**: Different sampling frame exclusions.

**Examples**:
- Excluding vs. including group quarters (prisons, dorms, nursing homes)
- Excluding vs. including US territories
- Excluding vs. including institutionalized population
- Excluding vs. including military bases

**Why Incompatible**: Systematic exclusions create non-comparable samples.

---

#### PC.3: Age Bounds

**Definition**: Different age eligibility criteria.

**Examples**:
- Labor force questions for 15+ vs. 16+ vs. 18+
- Health insurance questions for all ages vs. non-elderly only
- Education questions for school-age vs. all adults

**Why Incompatible**: Age restrictions prevent full population comparison.

---

#### PC.4: Geographic Scope

**Definition**: Different geographic coverage.

**Examples**:
- 50 states vs. 50 states + DC + territories
- Metropolitan areas only vs. all areas
- Border regions vs. national sample
- State-specific vs. national questions

**Why Incompatible**: Geographic restrictions limit comparability.

---

### Response Scale Constraints (RS)

Scale type, categories, or format differences.

#### RS.1: Scale Type

**Definition**: Fundamentally different response formats.

**Examples**:
- Binary (yes/no) vs. 5-point Likert scale
- Continuous numeric vs. categorical
- Frequency scale vs. intensity scale
- Open numeric vs. bracketed ranges

**Why Incompatible**: Different scale types capture different levels of information and are not directly comparable.

---

#### RS.2: Category Structure

**Definition**: Different number of categories or category boundaries within same scale type.

**Examples**:
- 5-point vs. 7-point Likert scale
- Income brackets with different boundaries
- Age categories with different groupings
- "Often/Sometimes/Rarely" vs. "Always/Often/Sometimes/Rarely/Never"

**Why Incompatible**: Category differences prevent direct mapping without information loss or assumptions.

---

#### RS.3: Anchoring/Labels

**Definition**: Different verbal anchors or category labels.

**Examples**:
- "Strongly agree" interpreted differently across surveys
- "Good health" vs. "Excellent health" as top category
- "Frequently" without numeric anchors
- Cultural/linguistic differences in label interpretation

**Why Incompatible**: Verbal anchors are subjective and survey-specific.

---

#### RS.4: Numeric vs. Verbal

**Definition**: Numeric scales vs. labeled categories.

**Examples**:
- 0-10 slider vs. "Excellent/Very Good/Good/Fair/Poor"
- Days per week (numeric) vs. "Daily/Weekly/Monthly" (verbal)
- Exact count vs. frequency categories

**Why Incompatible**: Numeric precision differs from categorical judgment.

---

### Mode/Context Constraints (MC)

Interview mode or questionnaire context differences.

#### MC.1: Interview Mode

**Definition**: Different data collection modes.

**Examples**:
- CATI (phone) vs. Web self-administered
- In-person interview vs. mail survey
- Interviewer-administered vs. self-administered
- Video vs. audio interview

**Why Incompatible**: Mode effects (social desirability, interviewer effects, visual cues) create systematic differences.

---

#### MC.2: Question Routing

**Definition**: Different skip patterns or conditional questions.

**Examples**:
- Asked of all respondents vs. subset
- Follow-up question vs. standalone question
- Conditional on prior response vs. unconditional

**Why Incompatible**: Routing affects who answers and question interpretation context.

---

#### MC.3: Contextual Priming

**Definition**: Preceding questions affect interpretation.

**Examples**:
- Question order effects
- Section context (health questions in health module vs. employment module)
- Priming from related questions
- Survey frame (government survey vs. academic survey)

**Why Incompatible**: Context shapes interpretation and response patterns.

---

#### MC.4: Proxy Response

**Definition**: Proxy vs. self-report rules differ.

**Examples**:
- Self-report only vs. household head can report for all
- Proxy allowed with restrictions vs. always allowed
- Age threshold for self-report differs

**Why Incompatible**: Proxy responses differ systematically from self-reports.

---

### Processing/Metadata Constraints (PM)

Coding, weighting, or documentation differences.

#### PM.1: Coding Schemes

**Definition**: Different classification systems.

**Examples**:
- Occupation coding differences (SOC 2010 vs. SOC 2018)
- Industry coding (NAICS 2012 vs. NAICS 2017)
- Geographic coding (FIPS vs. other systems)
- Race/ethnicity categories (different standards)

**Why Incompatible**: Different coding prevents direct comparison without crosswalks.

---

#### PM.2: Derived Variables

**Definition**: Different construction algorithms.

**Examples**:
- Poverty calculation methods (official vs. supplemental)
- Composite scores with different formulas
- Imputed variables with different models
- Weighted vs. unweighted aggregates

**Why Incompatible**: Different construction creates systematically different measures.

---

#### PM.3: Documentation Gaps

**Definition**: Insufficient metadata to assess comparability.

**Examples**:
- Missing questionnaire context
- Unclear skip patterns
- Ambiguous variable definitions
- Undocumented changes across survey years

**Why Incompatible**: Cannot determine compatibility without adequate documentation.

---

## Application Notes

### Selecting Primary Barrier Code

When multiple barriers apply, select based on hierarchy:
1. **CC** (Construct) - most fundamental
2. **TC** (Temporal) - affects interpretation
3. **RS** (Response Scale) - limits comparability
4. **PC** (Population) - affects universe
5. **MC** (Mode/Context) - measurement effects
6. **PM** (Processing) - technical issues

**Example**: If a question has both CC.1 (different concept) and RS.1 (different scale), classify as CC.1 because construct differences are more fundamental.

### Edge Cases

**Borderline F2/F3**: When uncertain whether statistical adjustment can bridge gap:
- **F2** if adjustment is feasible with reasonable assumptions
- **F3** if adjustment requires untenable assumptions or would destroy information

**Multiple sub-codes**: Document all applicable codes in reasoning field, but select single primary code for classification.

---

## Citation

This taxonomy is adapted from:

- **Fortier, I., et al. (2011)**. Is rigorous retrospective harmonization possible? Application of the DataSHaPER approach across 53 large studies. *International Journal of Epidemiology*, 40(5), 1314-1328.

- **Fortier, I., et al. (2017)**. Maelstrom Research guidelines for rigorous retrospective data harmonization. *International Journal of Epidemiology*, 46(1), 103-115.

Extensions and examples specific to federal surveys developed for this analysis.
