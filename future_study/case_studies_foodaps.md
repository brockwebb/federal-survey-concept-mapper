# FoodAPS-ACS Deep Dive: Case Studies in Survey Consolidation

## Executive Summary

This document provides detailed analysis of specific FoodAPS-ACS question pairs to illustrate the structural barriers to survey consolidation. Through examination of actual question text and LLM reasoning, we demonstrate that low consolidation rates in specialized content areas are not analytical failures but **expected outcomes of survey design differences**.

Key findings:
- **SNAP (8.7% consolidable)**: ACS screener vs. FoodAPS program battery - fundamentally different analytical purposes
- **Race (83-100% consolidable)**: Demographics work well - stable characteristics with no temporal scope issues
- **Reference periods drive consolidation**: Habitual framing ("usually/normally") enables consolidation; point-in-time framing blocks it

---

## Case Study 1: SNAP (Food Stamps) - 2/23 Consolidable (8.7%)

### The Paradox

FoodAPS is explicitly designed to study food acquisition behavior among SNAP participants. Yet only 2 of 23 SNAP-related question pairs show consolidation potential with ACS. This appears anomalous - shouldn't the survey's core mission area show *more* overlap with ACS, not less?

### The Data

| Metric | Value |
|--------|-------|
| Total SNAP pairs | 23 |
| Claude consolidable | 6 (26%) |
| GPT consolidable | 5 (22%) |
| **Both agree consolidable** | **2 (8.7%)** |
| Model agreement rate | 48% |

### What Consolidates: Identical Constructs

**Pair FOODAPS_0594** (Both models: YES)
```
FoodAPS: "Did (you/anyone at this address) receive benefits from SNAP in the last 12 months?"
ACS:     "IN THE PAST 12 MONTHS, did you or any member of this household receive benefits 
          from the Food Stamp Program or SNAP (the Supplemental Nutrition Assistance Program)?"
```

**Why it works:**
- Identical reference period (12 months)
- Same unit of analysis (household-level)
- Same construct (binary SNAP receipt)
- Only difference: ACS explicitly names both "Food Stamp Program" and "SNAP"

**Pair FOODAPS_0589** (Both models: PARTIAL)
```
FoodAPS: "On what date did [you/names] last receive [STATE SNAP NAME] benefits?"
ACS:     "IN THE PAST 12 MONTHS, did you or any member of this household receive benefits 
          from the Food Stamp Program or SNAP?"
```

**Why partial:**
- Both measure SNAP receipt
- FoodAPS asks for recency (date of last receipt)
- ACS asks binary yes/no over 12 months
- Partial overlap: "last received within 12 months" → ACS answer derivable

### What Doesn't Consolidate: Screener vs. Battery

**Problem Type 1: Reference Period Mismatch**

**Pair FOODAPS_0583** (Claude: NO, GPT: PARTIAL)
```
FoodAPS: "Have you received benefits from the Supplemental Nutrition Assistance Program 
          in the past 30 days? This program is also known as [STATE SNAP NAME] or food 
          stamps and it puts money on an EBT card..."
ACS:     "IN THE PAST 12 MONTHS, did you or any member of this household receive benefits 
          from the Food Stamp Program or SNAP?"
```

**Claude's reasoning:**
> "Both questions ask about the same core concept (SNAP/Food Stamp receipt) and use the same response format (yes/no), but they differ fundamentally in their time frames. Question A measures current/recent SNAP participation (30 days), while Question B captures any participation within a broader annual period. These time frames serve different analytical purposes and cannot be substituted."

**Why this matters for FoodAPS:**
- FoodAPS needs **current participation status** to interpret food acquisition diaries
- A household that received SNAP 10 months ago but not currently has different purchasing behavior
- 30-day window captures active program participation
- 12-month window captures annual prevalence (different statistic)

**Problem Type 2: Response Format Mismatch**

**Pair FOODAPS_0585** (Claude: NO, GPT: PARTIAL)
```
FoodAPS: "How many [STATE SNAP NAME] EBT cards are issued to people at this address?"
ACS:     "IN THE PAST 12 MONTHS, did you or any member of this household receive benefits 
          from the Food Stamp Program or SNAP?"
```

**Claude's reasoning:**
> "Both questions address SNAP participation at the household level, but they fundamentally differ in what they measure. Question A asks for a COUNT of EBT cards issued (a quantitative measure of program enrollment intensity), while Question B asks for a YES/NO indicator of whether any household member received benefits. Even if the ACS answer is 'yes,' it provides no information about the number of cards or within-household benefit allocation."

**Problem Type 3: Administrative Detail vs. Prevalence**

**Pair FOODAPS_0586** (Both models: NO)
```
FoodAPS: "You said there is one [STATE SNAP NAME] card in this household. Now we will ask 
          about who in the household is assigned to the EBT card. Select the names of the 
          people below that receive [STATE SNAP NAME] benefits on this card."
ACS:     "IN THE PAST 12 MONTHS, did you or any member of this household receive benefits 
          from the Food Stamp Program or SNAP?"
```

**Claude's reasoning:**
> "While both questions address SNAP benefits, they measure fundamentally different constructs. Question A identifies which household members are currently assigned to a specific EBT card (roster/administrative identification), whereas Question B asks about receipt of SNAP benefits at any point in the past year. These serve entirely different analytical purposes - one maps benefit allocation within households, the other measures program reach."

### The Structural Pattern

| FoodAPS Question Type | Count | Purpose | ACS Substitutable? |
|-----------------------|-------|---------|-------------------|
| 12-month receipt screener | 1 | Same as ACS | ✓ Yes |
| Last receipt date | 1 | Recency measure | ∼ Partial |
| 30-day receipt | 2 | Current status | ✗ No |
| Number of EBT cards | 1 | Enrollment intensity | ✗ No |
| Card assignment roster | ~15 | Within-HH allocation | ✗ No |
| Benefit amount/timing | ~3 | Program economics | ✗ No |

**Conclusion:** The 8.7% consolidation rate is structurally determined. FoodAPS needs program *mechanics* (who has cards, how many, when received) while ACS measures program *reach* (did anyone participate). These are complementary, not redundant, data collection strategies.

---

## Case Study 2: Race/Ethnicity - 5-6/6 Consolidable (83-100%)

### Initial Confusion

The session handoff noted "Race: 0/6 - unexpected, needs review." This was incorrect. Actual analysis shows Race performs as expected for demographic items.

### The Data

| Metric | Value |
|--------|-------|
| Total Race pairs | 6 |
| Claude consolidable (partial+yes) | 6 (100%) |
| GPT consolidable (partial+yes) | 5 (83%) |
| **Both agree consolidable** | **5 (83%)** |

### Why Race Works

**All 6 pairs show the same pattern:**
```
FoodAPS: "What is your race and/or ethnicity? Select all that apply."
         "What is NAME's race and/or ethnicity? Select all that apply."
         
ACS:     "What is Person 1's race?"
         "What is Person 2's race?"
         "What is Person 3's race?"
```

**Why consolidation works:**
1. **No temporal scope** - Race is a stable characteristic, not a time-bounded event
2. **Same construct** - Both measure racial/ethnic self-identification
3. **Similar response format** - Both allow multiple selections

**Why "partial" instead of "yes":**
- FoodAPS combines race AND ethnicity in one question
- ACS asks race and Hispanic origin separately (standard federal practice)
- Operationally similar but not identical

### The One Disagreement

**Pair FOODAPS_0173** (Claude: PARTIAL, GPT: NO)
```
FoodAPS: "What is NAME's race and/or ethnicity? Select all that apply."
ACS:     "What is Person 1's race?"
```

GPT's more conservative assessment likely reflects the race/ethnicity bundling difference. Both models correctly identify the substantive overlap.

### Demographics: The Reliable Consolidation Target

Race confirms the broader pattern: **demographic items consolidate well** because:
- No reference period issues (characteristics don't have "last week" vs "last year" problems)
- Standardized constructs (OMB race/ethnicity categories are federally mandated)
- Same analytical purpose (population classification)

| Demographic Item | FoodAPS Rate | CPS Rate | Explanation |
|------------------|--------------|----------|-------------|
| Sex | 89% (24/27) | 100% (3/3) | Binary, stable |
| Age | 67% (6/9) | 33% (3/9) | Date/year variations |
| Race | 83% (5/6) | 22% (2/9) | Construct bundling |
| Relationship | 50% (3/6) | 27% (8/30) | HH definition variance |

---

## Case Study 3: Hours/Week, Weeks/Year - 16/56 Consolidable (29%)

### Why This Works Better Than Employment Status

Hours/Week shows the highest consolidation rate among labor content. The key is **habitual framing**.

### The Pattern

**Consolidable pairs use habitual language:**
```
FoodAPS: "How many hours do you NORMALLY work for pay?"
CPS:     "How many hours per week do you USUALLY work at your main job?"
ACS:     "How many hours do you USUALLY work per week?"
```

All three surveys ask about typical/habitual hours - no specific reference period. This enables direct comparison.

**Non-consolidable pairs use point-in-time language:**
```
FoodAPS: "How many hours did you work LAST WEEK?"
ACS:     "LAST WEEK, how many hours did this person work?"
         vs.
         "During the PAST 12 MONTHS, did this person usually work 35 hours or more per week?"
```

The weekly snapshot (for specific week tracking) cannot substitute for annual typical hours.

### Reference Period Alignment Drives Consolidation

| Framing Type | Consolidation Rate | Explanation |
|--------------|-------------------|-------------|
| Habitual ("usually/normally") | ~40-50% | No temporal anchor, comparable across surveys |
| Point-in-time ("last week") | ~10% | Specific window, not substitutable |
| Annual retrospective ("past 12 months") | ~15% | Different analytical purpose |

---

## Methodological Note: Model Generation Effects

### Observation: Newer Models Are More Discerning

During development, we tested multiple LLM configurations. Newer models (Claude Haiku 4.5, GPT-5-mini) showed **lower consolidation rates** than earlier models.

| Model Generation | Approximate Pass Rate | Interpretation |
|------------------|----------------------|----------------|
| Earlier models | Higher | Less sensitive to construct/reference period nuance |
| Current models | Lower | Better discrimination of subtle incompatibilities |

### Hypothesis

This pattern is consistent with improved nuance handling in more capable models. Newer models:
- Catch reference period mismatches that earlier models missed
- Distinguish construct differences (work-limiting vs functional disability)
- Recognize response format incompatibilities

**Implication:** The ~11-12% consolidation rates from current models may be more accurate than higher rates from earlier systems. This is an observation, not a validated finding - it would require systematic comparison to confirm.

---

## Summary: What FoodAPS-ACS Teaches Us

### 1. Specialized Surveys Have Specialized Needs

FoodAPS can't use ACS SNAP data because ACS doesn't collect what FoodAPS needs:
- Current vs. annual participation (30-day vs 12-month)
- Benefit allocation mechanics (who's on which card)
- Benefit amounts and timing

### 2. Demographics Are the Only Reliable Target

Race, sex, age work because they're:
- Time-invariant characteristics
- Federally standardized constructs
- Collected for the same purpose (population classification)

### 3. Habitual Framing Enables Cross-Survey Comparison

"How many hours do you usually work?" is answerable from any survey.
"How many hours did you work last week?" is survey-specific.

### 4. Low Consolidation Rates Are Features, Not Bugs

The 8.7% SNAP consolidation rate reflects **correct survey design** - FoodAPS and ACS serve complementary purposes. Consolidation would destroy analytical value.

---

*Analysis completed: January 27, 2026*
*Data sources: foodaps_comparison_merged.csv (610 pairs)*
