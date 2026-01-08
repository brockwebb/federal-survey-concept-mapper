# 5. Data Collection and Preparation

## 5.1 Source Data

Survey question data were obtained and compiled from published federal demographic surveys that the US Census Bureau conducts. The dataset was consolidated in wide-format CSV:
- **Rows**: 6,987 unique questions
- **Columns**: 49 survey identifiers (46 actual surveys + metadata columns)
- **Values**: Binary indicators (1 = question appears in survey, 0/blank = does not appear)

### 5.1.1 Survey Coverage

The dataset includes questions from:
- **12 Census Bureau surveys**: ACS, AHS, SIPP, CE, CPS, HTOPS, CMP, SOMA, FoodAPS (4 variants), Building Permits (2 variants)
- **11 NCES education surveys**: NTPS (6 variants), TFS (2 surveys), PSS, SPP, SSOCS
- **7 NCHS health surveys**: NHIS, NHAMCS, NAMCS, NSCH (4 variants)
- **4 BJS crime surveys**: NCVS, SCS, SVS, ITS
- **4 HRSA surveys**: NSCH variants, NSSRN
- **8 other surveys**: NSCG, NTEWS, MEPS-IC, Business R&D, Business Classification

**Temporal Coverage**: Questions reflect survey instruments fielded between 2019-2024, representing current federal measurement practices.

## 5.2 Data Quality Issues

Manual data collection introduced several quality issues requiring remediation:

### 5.2.1 Missing Survey Context

**Problem**: Questions were extracted without associated skip logic, routing information, or response options. This removes critical context for understanding measurement intent.

Example: 
- Question text: "Amount?"
- Without context: Ambiguous (income? expenditure? time? quantity?)
- With skip logic: "If yes to Q47 (received Social Security), Amount?" → Clearly income

**Impact**: ~3-5% of questions (200-350) were too ambiguous to categorize without full survey context. These were flagged for human review.

**Mitigation**: We provided survey name to LLMs as context. This partially compensates - knowing a question appears in NHIS (health survey) vs. CE (expenditure survey) helps disambiguate.

### 5.2.2 Duplicate Entries

**Problem**: Some questions appeared multiple times due to data entry errors or legitimate cross-survey use.

Example: "What is your age?" appears in 24 surveys, creating 24 dataset rows with identical text but different survey indicators.

**Remediation**: 
- Exact duplicates within same survey: Removed (14 cases)
- Identical text across surveys: Retained, as these represent genuine cross-survey concept replication (important for redundancy analysis)

### 5.2.3 Administrative Text

**Problem**: Some entries were not substantive questions:
- Administrative markers: "END OF SURVEY", "INTERVIEWER NOTE"
- Skip instructions: "IF Q12 = 1, SKIP TO Q19"  
- Response codes: "98 = DON'T KNOW, 99 = REFUSED"

These represent ~1-2% of entries (70-140 rows).

**Remediation**: Attempted categorization; if both models returned low confidence (<0.30), flagged as `categorization_failed` and excluded from analysis.

### 5.2.4 Extremely Short Questions

**Problem**: Some entries were fragments lacking context:
- Single words: "Other"
- Yes/No prompts: "Yes?"
- Amounts without units: "Number"

**Remediation**: Same as administrative text - flagged if both models showed low confidence.

## 5.3 Data Transformation

### 5.3.1 Wide-to-Long Conversion

The source data were in wide format (one row per question, columns for surveys). For analysis, we converted to long format:

**Original structure**:
```
Question                          | SIPP | CE | AHS | ...
What is your age?                 |  1   | 1  |  1  | ...
How much did you spend on food?   |  0   | 1  |  0  | ...
```

**Transformed structure**:
```
question_id | question_text              | survey | present
Q001       | What is your age?           | SIPP   | 1
Q001       | What is your age?           | CE     | 1
Q001       | What is your age?           | AHS    | 1
Q002       | How much did you spend...   | CE     | 1
```

This long format enabled:
- Assignment of unique question IDs
- Tracking of primary survey (first survey where question appears)
- Analysis of cross-survey question replication

### 5.3.2 Text Cleaning

Questions underwent minimal cleaning to preserve original wording:
- **Whitespace normalization**: Multiple spaces → single space
- **Character encoding**: Fixed UTF-8 encoding errors (em dashes, smart quotes)
- **No stemming/lemmatization**: Preserved exact question language for accurate categorization

Example corrections:
- `"whatâ\x80\x99s"` → `"what's"` (smart apostrophe encoding error)
- `"in  the   past"` → `"in the past"` (extra whitespace)

### 5.3.3 Survey Name Standardization

Survey names were standardized to official acronyms and full names for LLM context:
- `SIPP` → `Survey of Income and Program Participation (SIPP)`
- `NSCH_0-5` → `National Survey of Children's Health Topical Questionnaire (Children, 0-5 years)`

This provided LLMs with richer context about survey domain and purpose.

## 5.4 Final Dataset Characteristics

After preparation, the analysis dataset contained:
- **6,987 unique questions**
- **46 federal surveys**
- **Mean question length**: 87 characters (SD = 52)
- **Range**: 4 characters ("Age?") to 487 characters (complex skip logic question)

**Distribution by Survey Size**:
- **Large surveys** (>500 questions): SIPP, CE, NHIS, AHS (4 surveys)
- **Medium surveys** (100-499 questions): FoodAPS, CPS, NSCG, NSCH variants, MEPS-IC, ATUS, HTOPS (9 surveys)
- **Small surveys** (<100 questions): All other surveys (33 surveys)

The dataset represents a comprehensive cross-section of federal demographic measurement, though with acknowledged limitations around missing skip logic and context.

## 5.5 Recommendations for Future Data Collection

This analysis revealed several data quality issues stemming from manual question extraction. Future iterations should:

### 5.5.1 Automated Question Extraction

**Current Limitation**: Questions were manually copied from PDFs and web documents, introducing transcription errors and losing context.

**Recommendation**: Develop automated extraction from structured survey metadata:
- DDI (Data Documentation Initiative) XML files contain full question text, skip logic, and response options
- Many federal surveys publish DDI metadata; extraction tools exist (e.g., PyDDI)
- Automated extraction preserves full context and reduces errors

**Related Work**: Automated question extraction systems for survey instruments exist that would substantially improve data quality for this analysis. Future applications of this methodology should prioritize automated extraction over manual collection.

### 5.5.2 Skip Logic Preservation

**Current Limitation**: Questions were decontextualized from their survey flow.

**Recommendation**: Include skip logic as metadata:
```json
{
  "question_id": "Q047",
  "text": "Amount?",
  "previous_question": "Did you receive Social Security?",
  "condition": "IF Q046 = YES",
  "response_type": "currency"
}
```

This context dramatically improves categorization accuracy for ambiguous questions.

### 5.5.3 Response Option Documentation

**Current Limitation**: Response categories were not captured.

**Recommendation**: Include response options as they provide context:
- "How many people live here?" with responses "1, 2, 3-4, 5+" → Household size (ordinal)
- "How many people live here?" with responses "0-999 [numeric]" → Housing unit count (different concept)

Response options help disambiguate question intent.

### 5.5.4 Version Control

**Current Limitation**: No tracking of question changes over time.

**Recommendation**: Maintain version history to enable longitudinal analysis of how federal measurement priorities evolve:
- Which concepts are added/dropped?
- How do question wordings change?
- What drives survey evolution?

## 5.6 Implications for Results

The data quality issues have several implications:

**1. Categorization Success Rate**: The 99.5% success rate (Section 7.1) is remarkable given the challenges. With better source data (skip logic, response options), success rate would likely approach 99.9%.

**2. Unresolved Disagreements**: The 1,538 unresolved disagreements (22% of dataset, Section 7.3) primarily stem from data quality issues, not methodology failures. Most are administrative text or fragments lacking context.

**3. Conservative Gap Analysis**: Coverage gaps identified in Section 8 are conservative - some uncovered concepts may actually be measured but their questions were too ambiguous to categorize successfully.

**4. Replication Opportunity**: With improved source data, this analysis could be replicated periodically (e.g., every 3-5 years) to track federal survey evolution at minimal cost (~$15 in API fees, 2 hours processing time).

## 5.7 Summary

The source dataset of 6,987 questions from 46 federal surveys provided comprehensive coverage of federal demographic measurement but suffered from data quality issues inherent to manual extraction. These issues - missing skip logic, administrative text, fragmented questions - primarily affected the tail of difficult-to-categorize cases while the bulk of substantive questions categorized successfully. Future applications of this methodology would benefit substantially from automated question extraction preserving full survey context.
