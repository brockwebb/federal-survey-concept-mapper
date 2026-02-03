# Harmonization Distribution Visualization

**Date:** 2026-02-02
**Added:** New visualization showing F1/F2/F3 distribution and F3 barrier breakdown

---

## Overview

Created comprehensive visualization showing:
1. **Overall distribution**: F1/F2/F3 counts across all 1,598 pairs
2. **F3 breakdown**: Top 10 barrier sub-codes for incompatible pairs

---

## Data Summary

### Overall Feasibility Distribution

| Code | Count | Percentage | Meaning |
|------|-------|------------|---------|
| **F1** | 74 | 4.6% | Direct recode (mechanically transformable) |
| **F2** | 241 | 15.1% | Statistical adjustment (requires modeling) |
| **F3** | 1,283 | 80.3% | Incompatible (fundamental barriers) |

**Total:** 1,598 question pairs

### F3 Barrier Sub-Code Breakdown

**Top 10 barriers** (out of 1,283 F3 pairs):

| Rank | Code | Count | % of F3 | Description |
|------|------|-------|---------|-------------|
| 1 | CC.1 | 900 | 70.1% | Concept definition differences |
| 2 | CC.2 | 250 | 19.5% | Operationalization differences |
| 3 | CC.4 | 88 | 6.9% | Scope inclusion differences |
| 4 | TC.2 | 20 | 1.6% | Temporal framing differences |
| 5 | RS.1 | 11 | 0.9% | Scale type differences |
| 6 | PC.1 | 6 | 0.5% | Universe definition differences |
| 7 | TC.1 | 4 | 0.3% | Reference period length differences |
| 8 | RS.2 | 2 | 0.2% | Category structure differences |
| 9 | CC.3 | 1 | 0.1% | Boundary condition differences |
| 10 | MC.2 | 1 | 0.1% | Question routing differences |

**Key Finding:** CC.1 (concept definition) accounts for 70% of all F3 pairs - fundamentally different constructs that cannot be harmonized.

---

## Visualization Details

### Script Created
**File:** `scripts/visualize_harmonization_distribution.py`

**Function:**
- Loads final_verdicts.csv data
- Creates 2-panel matplotlib figure
- Left panel: Bar chart of F1/F2/F3 distribution
- Right panel: Horizontal bar chart of top 10 F3 barrier codes

**Features:**
- Color-coded by feasibility (F1=green, F2=yellow, F3=red)
- Barrier codes color-coded by category (CC=red, TC=blue, RS=green, etc.)
- Value labels showing counts and percentages
- Legends explaining codes
- Professional styling with grid and clean layout

### Output Image
**File:** `presentation/images/harmonization_distribution.png`

**Specifications:**
- Size: 323KB
- Dimensions: ~4200×1800 pixels (300 DPI)
- Format: PNG with white background
- Layout: 2 panels side-by-side

---

## Slide Integration

### New Slide Added
**Position:** After "Question-Level Rollup" in appendix (slide 4 of appendix)

**Title:** "Harmonization Code Distribution"

**Content:**
- Full-width visualization (95%)
- Speaker notes explaining the two panels
- Highlights CC.1 dominance (70% of F3 pairs)

**Slide count:** 32 → 33 slides total

---

## Files Created/Modified

### New Files
1. **`scripts/visualize_harmonization_distribution.py`** (Python script)
   - 185 lines
   - Generates visualization from final_verdicts.csv
   - Reusable for updates

2. **`presentation/images/harmonization_distribution.png`** (Visualization)
   - 323KB
   - 2-panel chart
   - Ready for slides

### Modified Files
1. **`presentation/slides.qmd`**
   - Added 1 new slide after "Question-Level Rollup"
   - Image reference: `![](images/harmonization_distribution.png){width=95%}`
   - Speaker notes added

---

## Key Insights Visualized

### 1. Majority Are Incompatible (80%)
Only 20% of pairs can be harmonized (F1 + F2 combined), confirming that naive exhaustive comparison yields mostly negative results.

### 2. CC.1 Dominates F3 Barriers (70%)
Concept definition differences are the primary reason pairs can't consolidate - fundamentally different constructs, not just operational differences.

### 3. Long Tail of Barriers
Top 3 CC codes account for 96.5% of F3 pairs, with other barrier types (TC, RS, PC, MC) being relatively rare.

### 4. Validates "97% CC" Finding
Previous slide states "97% of F3 = CC barriers" - this detailed breakdown shows CC.1 + CC.2 + CC.4 = 96.5%, confirming the finding.

---

## Usage in Presentation

### During Main Narrative
This slide appears in the appendix, providing detailed empirical support for the barrier taxonomy definitions that follow.

**Flow:**
1. Architecture diagrams (pipeline, ensemble, rollup)
2. **Harmonization Code Distribution** ← NEW empirical view
3. Harmonization Taxonomy (definitions)
4. Barrier Code Taxonomy (detailed codes)

### In Appendix
Serves as transition between:
- **Architecture** (how we did it)
- **Empirical results** (what we found)
- **Taxonomy** (how we define it)

---

## Regeneration

If data updates, regenerate visualization:

```bash
# Regenerate visualization
python scripts/visualize_harmonization_distribution.py

# Re-render slides
cd presentation
quarto render slides.qmd
```

**Note:** Script reads from `output/analysis/final_verdicts.csv` automatically.

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

---

## Status: Complete ✅

**Created:**
- ✅ Python visualization script
- ✅ PNG image (323KB)
- ✅ New slide in deck

**Integration:**
- ✅ Added to presentation/images/
- ✅ Referenced in slides.qmd
- ✅ Slides render successfully
- ✅ 33 slides total (22 main + 11 appendix)

**Result:** Presentation now has detailed harmonization code breakdown showing F1/F2/F3 distribution and F3 barrier sub-codes! 🎉
