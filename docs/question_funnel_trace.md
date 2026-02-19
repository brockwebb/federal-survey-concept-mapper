# Question Funnel Trace: CPS and FoodAPS

**Date:** 2026-02-19
**Purpose:** Trace the complete question funnel from raw survey instruments through to harmonization results

---

## Executive Summary

**Key Findings:**
- ✅ **Raw data counts verified** against source files
- ⚠️ **CPS discrepancy identified**: 211 → 250 → 240 (two unexplained jumps)
- ⚠️ **FoodAPS instrument scope unclear**: 462 total questions → 150 in pairs (32.5% inclusion rate)
- ⚠️ **FoodAPS instrument breakdown unknown**: Cannot determine which of 4 instruments contributed to the 140/150 questions

---

## 1. Raw Survey Instrument Counts

**Source:** `data/raw/PublicSurveyQuestionsMap.csv` (ground truth)

### CPS (Current Population Survey)
- **Total questions:** 211
- **Instruments:** 1 (single CPS column)

### FoodAPS (Food Acquisition and Purchase Survey)
- **Total questions across all instruments:** 462
- **Instrument breakdown:**
  - Initial Interview/Household Survey: 246 questions (53.2%)
  - Food Log: 86 questions (18.6%)
  - Debriefing Questionnaire: 74 questions (16.0%)
  - Profile and Income Questionnaire: 56 questions (12.1%)

### ACS (American Community Survey - anchor)
- **Total questions:** 115

---

## 2. Report 01 Classification Stage

**Source:** `output/report_01/final/master_dataset.csv`

### CPS
- **Questions classified:** 211 ✅ (matches raw data)
- **Status:** All CPS questions from raw data were successfully classified

### FoodAPS
- **Questions classified:** 462 ✅ (matches raw data)
- **All 4 instruments included:** Yes
  - Initial Interview/Household Survey: 246
  - Food Log: 86
  - Debriefing Questionnaire: 74
  - Profile and Income Questionnaire: 56
- **Status:** All FoodAPS questions from all 4 instruments were classified

### ACS
- **Questions classified:** 115 ✅ (matches raw data)

---

## 3. Report 02 Pair Generation Stage

**Source:** `output/report_02/question_matching/{cps,foodaps}/`

### CPS
- **Candidate pairs generated:** 1,092
- **Unique CPS source questions:** 250 ⚠️ (211 → 250 = +39 questions)
- **Unique ACS target questions:** 76
- **Source file:** `cps_comparison_merged.csv`

**Discrepancy #1: Where did the extra 39 CPS questions come from?**
- Raw data: 211 CPS questions
- Report 01: 211 CPS questions
- Report 02 pairs: 250 unique CPS questions
- **Status:** UNEXPLAINED (requires pipeline script inspection)

### FoodAPS
- **Candidate pairs generated:** 610
- **Unique FoodAPS source questions:** 150 ⚠️ (462 → 150 = 67.5% reduction)
- **Unique ACS target questions:** 86
- **Source file:** `foodaps_comparison_merged.csv`

**Question #1: Which FoodAPS instruments contributed to the 150 questions?**
- **Status:** UNKNOWN - attempted text matching to raw data failed (likely due to text normalization differences)
- **Inclusion rate:** 32.5% (150/462)
- **Hypothesis:** Only questions with subtopic overlap with ACS were included in pairing

**Question #2: Breakdown by instrument?**
- **Status:** CANNOT DETERMINE without additional mapping files or pipeline inspection
- **Need:** Script that generated `foodaps_candidate_pairs_all.csv` to see selection logic

---

## 4. Report 03 Barrier Rating Stage

**Source:** `output/report_03/analysis/stage4_survey_summary.json`

### CPS
- **Questions rated:** 240 ⚠️ (250 → 240 = -10 questions)
- **Results:**
  - Direct recode (F1): 37 questions (15.4%)
  - Statistical adjustment (F2): 65 questions (27.1%)
  - Incompatible (F3): 138 questions (57.5%)
- **Harmonization candidates (F1+F2):** 102 questions (42.5%)

**Discrepancy #2: Where did 10 CPS questions go between Report 02 and Report 03?**
- Report 02 pairs: 250 unique CPS questions
- Report 03 rated: 240 questions
- **Status:** UNEXPLAINED (requires pipeline checkpoint inspection)
- **Hypotheses:**
  - Pipeline filtering (e.g., removed questions with data quality issues)
  - Deduplication at different stage
  - Pairs that failed rating process

### FoodAPS
- **Questions rated:** 140 ⚠️ (150 → 140 = -10 questions)
- **Results:**
  - Direct recode (F1): 23 questions (16.4%)
  - Statistical adjustment (F2): 45 questions (32.1%)
  - Incompatible (F3): 72 questions (51.4%)
- **Harmonization candidates (F1+F2):** 68 questions (48.6%)

**Discrepancy #3: Where did 10 FoodAPS questions go between Report 02 and Report 03?**
- Report 02 pairs: 150 unique FoodAPS questions
- Report 03 rated: 140 questions
- **Status:** UNEXPLAINED (same hypotheses as CPS)

---

## 5. Complete Funnel (Best Available)

### CPS Funnel (CORRECTED)

```
211 total CPS questions (PublicSurveyQuestionsMap.csv)
  ↓
211 questions classified (Report 01)
  ↓
~164 unique CPS questions entered pairing
  → Some questions paired in multiple subtopics → 250 question-subtopic IDs
  → 1,092 total question pairs generated
  ↓ [Filtered out: 10 IDs = 8 unique questions rated 'yes' by both models]
240 question-subtopic IDs assessed = 157 unique CPS question texts
  → 1,030 pairs rated (per stage2_agreement_metrics.json)
  ↓
  ├─ 37 IDs (15.4%) → F1 (direct recode viable)
  ├─ 65 IDs (27.1%) → F2 (statistical adjustment needed)
  └─ 138 IDs (57.5%) → F3 (incompatible)

RESULT: 102/240 IDs (42.5%) OR ~102/157 unique questions (~65%) have harmonization paths
```

**Key insight:** The 240/250 are question-subtopic combination IDs. The actual unique question count assessed is **157 CPS questions** (of 211 total = 74.4% assessed).

### FoodAPS Funnel (CORRECTED)

```
462 total FoodAPS questions (all 4 instruments)
  ├─ Initial Interview/Household Survey: 246
  ├─ Food Log: 86
  ├─ Debriefing Questionnaire: 74
  └─ Profile and Income Questionnaire: 56
  ↓
462 questions classified (Report 01)
  ↓ [Selection based on subtopic overlap with ACS — exact logic unknown]
~123 unique FoodAPS questions entered pairing (26.6% of total)
  → Some questions paired in multiple subtopics → 150 question-subtopic IDs
  → 610 total question pairs generated
  → INSTRUMENT BREAKDOWN: UNKNOWN (text matching failed)
  ↓ [Filtered out: 10 IDs rated 'yes' by both models]
140 question-subtopic IDs assessed = 118 unique FoodAPS question texts
  → 568 pairs rated (per stage2_agreement_metrics.json)
  ↓
  ├─ 23 IDs (16.4%) → F1 (direct recode viable)
  ├─ 45 IDs (32.1%) → F2 (statistical adjustment needed)
  └─ 72 IDs (51.4%) → F3 (incompatible)

RESULT: 68/140 IDs (48.6%) OR ~68/118 unique questions (~58%) have harmonization paths
```

**Key insight:** The 140/150 are question-subtopic combination IDs. The actual unique question count assessed is **118 FoodAPS questions** (of 462 total = 25.5% assessed).

**Still unknown:** Breakdown by instrument (which of the 4 FoodAPS instruments contributed to the 118 questions).

### ACS (Anchor Survey)

```
115 total ACS questions (PublicSurveyQuestionsMap.csv)
  ↓
115 questions classified (Report 01)
  ↓
CPS matching: 76 ACS questions participated (66.1% of ACS)
FoodAPS matching: 86 ACS questions participated (74.8% of ACS)
Combined: [UNKNOWN - need to count unique ACS questions across both]
```

---

## 6. Discrepancies and Gaps

### Critical Discrepancies

| Stage | Survey | Expected | Actual | Diff | Status |
|-------|--------|----------|--------|------|--------|
| Report 01 → Report 02 | CPS | 211 | 250 | +39 | ⚠️ UNEXPLAINED |
| Report 02 → Report 03 | CPS | 250 | 240 | -10 | ⚠️ UNEXPLAINED |
| Report 01 → Report 02 | FoodAPS | 462 | 150 | -312 | ⚠️ SELECTION LOGIC UNKNOWN |
| Report 02 → Report 03 | FoodAPS | 150 | 140 | -10 | ⚠️ UNEXPLAINED |

### Information Gaps

1. **FoodAPS Instrument Scope**
   - Which of the 4 instruments contributed to the 140/150 questions?
   - Were all 4 instruments eligible, or were some excluded by design?
   - Breakdown of results by instrument

2. **CPS Question Growth**
   - Why did CPS grow from 211 to 250 questions?
   - Are these duplicates? Different phrasings? Data artifacts?

3. **Report 02 → Report 03 Filtering**
   - Why did both CPS and FoodAPS lose exactly 10 questions?
   - Was this intentional filtering or data quality cleanup?

4. **Subtopic Overlap Selection Logic**
   - What criteria determined which questions entered pairing?
   - FoodAPS: 312 questions (67.5%) were excluded - why?

---

## 7. Required Follow-Up Investigation

### To Resolve CPS Discrepancies

**Check these files/scripts:**
1. `src/pipelines/` - pair generation scripts
2. `output/report_02/question_matching/cps/` - inspect how 250 unique questions were identified
3. Report 03 pipeline checkpoints - trace the 240 questions to their provenance
4. Deduplication logs (if any)

**Specific questions:**
- Are there duplicate question IDs in `cps_comparison_merged.csv`?
- Did Report 01 classification create multiple entries per question (e.g., dual-modal classifications)?
- Did Report 03 filter out low-confidence pairs?

### To Resolve FoodAPS Questions

**Check these files/scripts:**
1. Pair generation script for FoodAPS - how were the 150/462 questions selected?
2. `output/report_02/question_matching/foodaps/foodaps_candidate_pairs_all.csv` - trace survey_q_id back to instruments
3. Report 01 classification - map the 150 question texts back to original instrument columns
4. Look for a question ID mapping file (e.g., `FOODAPS_130` → original instrument)

**Specific questions:**
- Is there a `question_id_mapping.csv` or similar file?
- Do the pair generation scripts log which instruments were included?
- Was there an intentional decision to exclude certain FoodAPS instruments?

### To Complete the Funnel

**Generate these missing numbers:**
1. CPS: % of original 211 questions with subtopic overlap
2. CPS: % of original 211 questions with harmonization paths (resolve 211→240 first)
3. FoodAPS: breakdown of 140 questions by instrument
4. FoodAPS: % of each instrument with harmonization paths
5. ACS: unique questions participating across both CPS and FoodAPS matching

---

## 8. Recommendations for Master Report Ch 5

### Current Limitation

The master report cannot accurately present the complete funnel due to unresolved discrepancies. Reporting "48.6% (68/140)" is technically correct but misleading without context:

- Is 140 questions the right denominator? (FoodAPS has 462 questions total)
- Should we report against all FoodAPS questions (68/462 = 14.7%)?
- Or report against the subset with concept overlap (need to know which 150/462 were selected)?

### Immediate Actions

1. **Resolve the 211→250→240 CPS discrepancy** (highest priority)
   - Inspect pair generation script
   - Check for deduplication differences
   - Verify Report 03 input data

2. **Determine FoodAPS instrument scope**
   - Map the 140/150 questions back to source instruments
   - Document inclusion/exclusion criteria
   - Report breakdown by instrument if possible

3. **Document what we DON'T know**
   - Be transparent about gaps in the funnel
   - Note that percentages are relative to questions with concept overlap, not total survey questions
   - Acknowledge the 312 excluded FoodAPS questions

### Suggested Narrative for Ch 5

**Option A (Conservative):** Report only what we can verify

> "Of the [240/140] source survey questions that had subtopic overlap with ACS and entered the harmonization assessment, [42.5%/48.6%] were classified as having viable harmonization paths (F1 or F2). This represents a subset of the full survey instruments; complete funnel statistics require additional investigation."

**Option B (Transparent):** Acknowledge the gaps

> "The CPS and FoodAPS surveys contain [211/462] questions respectively. Of these, [240/140] questions with Census topic overlap with ACS were assessed for harmonization potential. Among these assessed questions, [42.5%/48.6%] have viable harmonization paths. The selection criteria and complete funnel from total survey questions to assessed questions requires further investigation to report accurately."

**Option C (Best-effort with caveats):** Use available data with clear disclaimers

> "Among CPS questions with concept overlap with ACS (N=240, representing [UNKNOWN%] of the 211-question survey), 42.5% have viable harmonization paths. Among FoodAPS questions assessed (N=140, drawn from 4 survey instruments totaling 462 questions), 48.6% have viable harmonization paths. Full instrument-level breakdowns and selection criteria are documented in [methodology companion doc]."

---

## 9. Files Examined

| File | Purpose | Status |
|------|---------|--------|
| `data/raw/PublicSurveyQuestionsMap.csv` | Ground truth question counts | ✅ Verified |
| `output/report_01/final/master_dataset.csv` | Classification results | ✅ Verified |
| `output/report_02/question_matching/cps/cps_comparison_merged.csv` | CPS pairs | ✅ Counted |
| `output/report_02/question_matching/foodaps/foodaps_comparison_merged.csv` | FoodAPS pairs | ✅ Counted |
| `output/report_03/analysis/stage4_survey_summary.json` | Final results | ✅ Verified |
| `data/processed/melted_survey_data.csv` | Processed questions | ⚠️ No survey mapping |
| `data/processed/question_metadata.csv` | Question metadata | ⚠️ No survey mapping |

**Files NOT examined (need to check):**
- Pair generation scripts in `src/pipelines/` or `src/scripts/`
- Report 03 pipeline checkpoints
- Question ID mapping files (if they exist)
- Deduplication logs

---

## 10. RESOLUTION UPDATE (2026-02-19)

### Discrepancy 1: CPS 211 → 250 → 240 **✅ RESOLVED**

**Finding:** The 250 and 240 are **question-subtopic combination IDs**, not unique question counts.

**Evidence:**
- Report 02 (`cps_comparison_merged.csv`): 250 unique IDs, but only **164 unique question texts**
- Report 03 (`expert_review_cps.csv`): 240 unique IDs, but only **157 unique question texts**
- Questions can appear in multiple subtopics (e.g., "Do you want a job?" appears in both "Labor Force" and "Employment Status")

**The 250 → 240 drop:**
- **All 10 dropped IDs were rated "yes" (easily consolidatable) by BOTH models** (Claude and GPT)
- The barrier coding pipeline (01_barrier_pipeline.py, lines 107-110) **intentionally filters** pairs rated 'yes' by both models
- These were demographic basics: sex, age, Hispanic origin, citizenship, education, occupation, commissions
- **This is correct behavior** — the pipeline only codes barriers for pairs that need it

**Corrected funnel:**
```
211 CPS questions (raw data)
  ↓
~164 unique CPS questions entered pairing (some questions paired in multiple subtopics → 250 IDs)
  ↓ [Filtered: -10 IDs (8 unique questions) rated 'yes' by both models]
240 question-subtopic IDs assessed = ~157 unique CPS question texts
  → 1,030 pairs rated
  ↓
102 IDs (42.5%) have harmonization paths (F1 or F2)
```

**Correct denominator for Ch 5:** Use **157 unique CPS questions** assessed, NOT 240 IDs.

---

### Discrepancy 2: FoodAPS 150 → 140 **✅ PARTIALLY RESOLVED**

**Finding:** Same pattern as CPS.

**Evidence:**
- Report 02: 150 unique IDs, but only **123 unique question texts**
- Report 03: 140 unique IDs, but only **118 unique question texts**
- **All 10 dropped IDs were rated "yes" by both models** (same filter as CPS)

**Corrected funnel:**
```
462 FoodAPS questions (raw data, all 4 instruments)
  ↓ [Selection logic unknown — 67.5% excluded]
~123 unique FoodAPS questions entered pairing (some questions paired in multiple subtopics → 150 IDs)
  ↓ [Filtered: -10 IDs rated 'yes' by both models]
140 question-subtopic IDs assessed = ~118 unique FoodAPS question texts
  → 568 pairs rated
  ↓
68 IDs (48.6%) have harmonization paths (F1 or F2)
```

**Correct denominator for Ch 5:** Use **118 unique FoodAPS questions** assessed, NOT 140 IDs.

**Still unresolved:** Which of the 4 FoodAPS instruments contributed to the 118/123 questions? Text matching to raw data failed (questions were transformed during pair generation).

---

### Discrepancy 3: Why Both Lost Exactly 10 **✅ RESOLVED**

**Finding:** Pure coincidence. Both had exactly 10 question-subtopic IDs rated 'yes' by both models.

**Evidence:** Pipeline filter (01_barrier_pipeline.py) removes ALL pairs where both models rated consolidation_potential='yes'. CPS had 10 such IDs, FoodAPS had 10 such IDs — coincidence, not a hardcoded limit.

---

## 11. Conclusion

We have **mostly resolved the funnel discrepancies**:

✅ **Fully Resolved:**
- CPS: 211 → 250 → 240 transitions explained (question-subtopic IDs + intentional filtering)
- FoodAPS: 150 → 140 transition explained (same pattern)
- Both surveys losing 10: explained (coincidence in filtering)
- Correct unique question counts identified (157 CPS, 118 FoodAPS)

⚠️ **Remaining Gap:**
- FoodAPS instrument breakdown: Cannot determine which of 4 instruments contributed to the 118 questions
  - Attempted text matching to raw data failed (questions transformed during pair generation)
  - Would require either: (a) original pair generation script inspection, (b) ID mapping file, or (c) manual review

**Recommendations for Ch 5:**
1. **Use unique question counts, not IDs:** Report against 157 CPS and 118 FoodAPS questions
2. **Be transparent about IDs vs questions:** Note that 240/140 are question-subtopic combinations
3. **Acknowledge FoodAPS gap:** State that the 118 questions are drawn from 4 FoodAPS instruments (totaling 462 questions) but specific instrument breakdown is not available
4. **Report both rates:**
   - Of assessed questions: 42.5% CPS, 48.6% FoodAPS
   - Of total survey (if assuming 462→118 is accurate): ~14.7% FoodAPS (68/462)
