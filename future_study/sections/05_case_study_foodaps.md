# Case Study: FoodAPS-ACS

## Overview

This case study provides detailed analysis of specific FoodAPS-ACS question pairs to illustrate the structural barriers to survey consolidation. Through examination of actual question text and LLM reasoning, we demonstrate that low consolidation rates in specialized content areas are not analytical failures but **expected outcomes of survey design differences**.

Key findings:
- **SNAP (8.7% consolidable)**: ACS screener vs. FoodAPS program battery - fundamentally different analytical purposes
- **Race (83-100% consolidable)**: Demographics work well - stable characteristics with no temporal scope issues
- **Reference periods drive consolidation**: Habitual framing ("usually/normally") enables consolidation; point-in-time framing blocks it

---

## SNAP (Food Stamps) - 2/23 Consolidable (8.7%)

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

### What Doesn't Consolidate: Screener vs. Battery

**Problem Type 1: Reference Period Mismatch**

```
FoodAPS: "Have you received benefits from SNAP in the past 30 days?"
ACS:     "IN THE PAST 12 MONTHS, did you receive SNAP benefits?"
```

30 days ≠ 12 months. FoodAPS needs **current participation status** to interpret food acquisition diaries.

**Problem Type 2: Response Format Mismatch**

```
FoodAPS: "How many EBT cards are issued to people at this address?"
ACS:     "Did you receive SNAP benefits?" (yes/no)
```

Count vs binary - ACS provides no information about enrollment intensity.

**Problem Type 3: Administrative Detail vs. Prevalence**

```
FoodAPS: "Select the names of the people that receive SNAP benefits on this card."
ACS:     "Did you receive SNAP benefits?" (yes/no)
```

Roster identification vs prevalence - entirely different analytical purposes.

### The Structural Pattern

| FoodAPS Question Type | Count | ACS Substitutable? |
|-----------------------|-------|-------------------|
| 12-month receipt screener | 1 | ✓ Yes |
| Last receipt date | 1 | ∼ Partial |
| 30-day receipt | 2 | ✗ No |
| Number of EBT cards | 1 | ✗ No |
| Card assignment roster | ~15 | ✗ No |
| Benefit amount/timing | ~3 | ✗ No |

**Conclusion:** The 8.7% consolidation rate is structurally determined. FoodAPS needs program *mechanics*; ACS measures program *reach*. These are complementary, not redundant.

---

## Race/Ethnicity - 5/6 Consolidable (83%)

### Why Race Works

**The pattern:**
```
FoodAPS: "What is your race and/or ethnicity? Select all that apply."
ACS:     "What is Person 1's race?"
```

**Why consolidation works:**
1. **No temporal scope** - Race is a stable characteristic
2. **Same construct** - Both measure racial/ethnic self-identification
3. **Similar response format** - Both allow multiple selections

**Why "partial" instead of "yes":**
- FoodAPS combines race AND ethnicity in one question
- ACS asks race and Hispanic origin separately (standard federal practice)

### Demographics: The Reliable Consolidation Target

| Demographic Item | FoodAPS Rate | CPS Rate |
|------------------|--------------|----------|
| Sex | 89% (24/27) | 100% (3/3) |
| Age | 67% (6/9) | 33% (3/9) |
| Race | 83% (5/6) | 22% (2/9) |
| Relationship | 50% (3/6) | 27% (8/30) |

---

## Hours/Week - 16/56 Consolidable (29%)

### Why This Works Better Than Employment Status

The key is **habitual framing**.

**Consolidable pairs use habitual language:**
```
FoodAPS: "How many hours do you NORMALLY work for pay?"
ACS:     "How many hours do you USUALLY work per week?"
```

No specific reference period → direct comparison possible.

**Non-consolidable pairs use point-in-time language:**
```
FoodAPS: "How many hours did you work LAST WEEK?"
ACS:     "During the PAST 12 MONTHS, did this person usually work 35+ hours?"
```

Weekly snapshot ≠ annual typical hours.

### Reference Period Alignment Drives Consolidation

| Framing Type | Consolidation Rate |
|--------------|-------------------|
| Habitual ("usually/normally") | ~40-50% |
| Point-in-time ("last week") | ~10% |
| Annual retrospective ("past 12 months") | ~15% |

---

## Summary: What FoodAPS-ACS Teaches Us

1. **Specialized Surveys Have Specialized Needs** - FoodAPS can't use ACS SNAP data because ACS doesn't collect program mechanics

2. **Demographics Are the Reliable Target** - Race, sex, age work because they're time-invariant and federally standardized

3. **Habitual Framing Enables Cross-Survey Comparison** - "Usually work" is comparable; "worked last week" is not

4. **Low Consolidation Rates Are Features, Not Bugs** - The 8.7% SNAP rate reflects correct survey design
