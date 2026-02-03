# Question-Level Consolidation Distribution Visualization

**Date:** 2026-02-02
**Added:** Question-level consolidation showing CPS vs FoodAPS breakdown

---

## Overview

Created question-level visualization showing:
1. **Survey comparison**: F1/F2/F3 distribution for CPS vs FOODAPS (380 questions)
2. **F3 breakdown**: Top 10 barrier sub-codes for non-consolidable questions

---

## Key Difference from Pair-Level Visualization

| Aspect | Pair-Level | Question-Level |
|--------|------------|----------------|
| **Unit of analysis** | 1,598 question pairs | 380 unique questions |
| **What it shows** | All comparison attempts | Best match per question |
| **F3 interpretation** | Pair cannot be harmonized | Question has no consolidable match |
| **Use case** | Research rigor (exhaustive) | Practical triage (what to review) |

---

## Data Summary

### Overall Question Distribution

| Survey | Total | F1 | F2 | F3 | Consolidable | Rate |
|--------|-------|----|----|----|--------------|----|
| **CPS** | 240 | 37 | 63 | 140 | 100 | 41.7% |
| **FOODAPS** | 140 | 23 | 45 | 72 | 68 | 48.6% |
| **Combined** | 380 | 60 | 108 | 212 | 168 | 44.2% |

**Key Finding:** FoodAPS has slightly higher consolidation potential (48.6%) than CPS (41.7%).

### F3 Barrier Sub-Code Breakdown (Question-Level)

**Top 10 barriers** (out of 212 F3 questions):

| Rank | Code | Count | % of F3 | Description |
|------|------|-------|---------|-------------|
| 1 | CC.1 | 163 | 76.9% | Concept definition differences |
| 2 | CC.2 | 38 | 17.9% | Operationalization differences |
| 3 | CC.4 | 4 | 1.9% | Scope inclusion differences |
| 4 | RS.1 | 3 | 1.4% | Scale type differences |
| 5 | TC.2 | 2 | 0.9% | Temporal framing differences |
| 6 | PC.1 | 1 | 0.5% | Universe definition differences |
| 7 | CC.3 | 1 | 0.5% | Boundary condition differences |

**Key Finding:** CC.1 (concept definition) accounts for **76.9%** of non-consolidable questions - even higher concentration than at pair level (70.1%).

---

## Comparison with Pair-Level Results

### F3 Barrier Distribution

| Barrier | Pair-Level (1,598) | Question-Level (380) |
|---------|-------------------|---------------------|
| **CC.1** | 900 (70.1%) | 163 (76.9%) |
| **CC.2** | 250 (19.5%) | 38 (17.9%) |
| **CC.4** | 88 (6.9%) | 4 (1.9%) |
| **Other** | 45 (3.5%) | 7 (3.3%) |

**Interpretation:** Question-level shows even stronger CC.1 dominance because:
- Questions with no consolidable path tend to have fundamental concept mismatches
- Pairs with minor barriers (CC.4, TC, RS) can sometimes find consolidable alternatives
- Best-match selection filters out edge cases

---

## Visualization Details

### Script Created
**File:** `scripts/visualize_question_consolidation_distribution.py`

**Function:**
- Loads stage4_question_best_matches.csv (380 questions)
- Joins with final_verdicts.csv to get barrier codes
- Creates 2-panel matplotlib figure
- Left panel: Grouped bar chart showing F1/F2/F3 by survey
- Right panel: Horizontal bar chart of top 10 F3 barrier codes

**Features:**
- Survey comparison (CPS vs FOODAPS)
- Color-coded by feasibility (F1=green, F2=yellow, F3=red)
- Barrier codes color-coded by category (CC=red, TC=blue, RS=green, etc.)
- Value labels showing counts and percentages
- Legends explaining codes
- Professional styling with grid and clean layout

### Output Image
**File:** `presentation/images/question_consolidation_distribution.png`

**Specifications:**
- Size: 309KB
- Dimensions: ~4200×1800 pixels (300 DPI)
- Format: PNG with white background
- Layout: 2 panels side-by-side

---

## Slide Integration

### New Slide Added
**Position:** After "Harmonization Code Distribution" in appendix

**Title:** "Question-Level Consolidation Distribution"

**Content:**
- Full-width visualization (95%)
- Speaker notes explaining survey comparison
- Highlights FoodAPS higher consolidability (48.6% vs 41.7%)
- Shows CC.1 dominance at question level (76.9%)

**Slide count:** 33 → 34 slides total

---

## Files Created/Modified

### New Files
1. **`scripts/visualize_question_consolidation_distribution.py`** (Python script)
   - 193 lines
   - Generates visualization from stage4_question_best_matches.csv
   - Joins with final_verdicts.csv for barrier codes
   - Reusable for updates

2. **`presentation/images/question_consolidation_distribution.png`** (Visualization)
   - 309KB
   - 2-panel chart
   - Ready for slides

### Modified Files
1. **`presentation/slides.qmd`**
   - Added 1 new slide after "Harmonization Code Distribution"
   - Image reference: `![](images/question_consolidation_distribution.png){width=95%}`
   - Speaker notes added

---

## Key Insights Visualized

### 1. FoodAPS More Consolidable (48.6% vs 41.7%)
FoodAPS questions have slightly better overlap with ACS than CPS questions, possibly because:
- More demographic questions (age, income, household composition)
- Fewer specialized employment questions (CPS focus)
- Shorter questionnaire overall (140 vs 240 questions)

### 2. Question-Level Shows Stronger CC.1 Dominance (76.9%)
At the question level, concept definition differences are even more dominant:
- Questions without any consolidable path have fundamental concept mismatches
- Best-match selection filters to the most viable option per question
- Minor barriers appear less frequently because alternatives exist

### 3. Combined Consolidation Rate: 44.2%
Overall, 168 of 380 questions (44.2%) have at least one consolidable ACS match:
- 60 questions (15.8%) are F1 - directly consolidable
- 108 questions (28.4%) are F2 - need statistical adjustment
- 212 questions (55.8%) are F3 - no viable match

### 4. Validates Two-Survey Strategy
CPS and FoodAPS were selected to represent different survey types:
- CPS: Employment-focused, high question count
- FoodAPS: Food security-focused, moderate question count
- Both show ~40-50% consolidation potential, validating that approach works across survey types

---

## Usage in Presentation

### During Main Narrative
This slide appears in the appendix immediately after the pair-level harmonization distribution, showing the complementary question-level view.

**Flow:**
1. Harmonization Code Distribution (pair-level, 1,598 pairs)
2. **Question-Level Consolidation Distribution** (question-level, 380 questions) ← NEW
3. Harmonization Taxonomy (definitions)
4. Barrier Code Taxonomy (detailed codes)

### Interpretation Guidance

**For stakeholders:**
- Pair-level = "How many comparison attempts succeeded?"
- Question-level = "How many questions have consolidable matches?"

**For researchers:**
- Pair-level shows exhaustive comparison rigor
- Question-level shows practical triage output
- Both perspectives validate each other

---

## Regeneration

If data updates, regenerate visualization:

```bash
# Regenerate visualization
python scripts/visualize_question_consolidation_distribution.py

# Re-render slides
cd presentation
quarto render slides.qmd
```

**Note:** Script reads from:
- `output/analysis/stage4_question_best_matches.csv` (380 questions)
- `output/analysis/final_verdicts.csv` (1,598 pairs, for barrier codes)

---

## Technical Details

### Color Coding

**Feasibility (left panel):**
- F1: Green (#4CAF50) - Direct recode
- F2: Yellow (#FFC107) - Statistical adjustment
- F3: Red (#F44336) - Incompatible

**Barrier Categories (right panel):**
- CC: Red (#E57373) - Construct/Concept
- TC: Blue (#64B5F6) - Temporal
- RS: Green (#81C784) - Response Scale
- PC: Yellow (#FFD54F) - Population
- MC: Purple (#BA68C8) - Mode/Context
- PM: Orange (#FF8A65) - Processing/Metadata

### Layout
- Figure: 14" × 6" (2 subplots)
- DPI: 300 (high resolution)
- Font sizes: 11-14pt
- Style: Seaborn whitegrid
- Left panel: Grouped bar chart (2 surveys × 3 feasibility codes)
- Right panel: Horizontal bar chart (top 10 barriers)

---

## Status: Complete ✅

**Created:**
- ✅ Python visualization script
- ✅ PNG image (309KB)
- ✅ New slide in deck

**Integration:**
- ✅ Added to presentation/images/
- ✅ Referenced in slides.qmd
- ✅ Slides render successfully
- ✅ 34 slides total (22 main + 12 appendix)

**Result:** Presentation now has both pair-level and question-level consolidation visualizations, showing complementary perspectives on harmonization outcomes! 🎉
