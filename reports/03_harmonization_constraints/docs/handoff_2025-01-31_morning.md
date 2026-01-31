# Handoff Document: Stage 3 Arbitration Validation
**Date:** 2025-01-31 Morning Session  
**Previous Session:** 2025-01-30 Evening (Bug Fix & Validation)

---

## Executive Summary

Identified and fixed a parsing bug that was corrupting Google arbitrator metrics. After correction, discovered a **significant architectural finding**: the three LLM arbitrators exhibit fundamentally different decision-making behaviors that should be documented in Report 03.

---

## Bug Fix Completed

### Root Cause
Pipeline function `process_single_pair()` in `02_arbitration_pipeline.py` only matched exact `'A'`, `'B'`, `'C'` in `selected_rater` field. Google outputs `"Rater A"` format inconsistently, which fell through to `else` branch and was incorrectly mapped to `'synthesis'`.

### Fix Applied
1. **Pipeline fix** (lines ~380-387 in `02_arbitration_pipeline.py`): Added normalization to extract letter from "Rater X" format
2. **Data fix**: Applied inline Python to `output/analysis/arbitration_deduped_google.jsonl` — 284 records corrected
3. **Documentation**: Added Decision 015 to `docs/methodology_log.md`

### Lesson Learned
Stage 2 deduplication would have propagated the pipeline fix automatically. Tomorrow, after collecting more Google data, re-run Stage 2 then Stage 3.

---

## Key Finding: Arbitrator Behavioral Differences

**This should be emphasized in Report 03.**

### Synthesis Rates
| Arbitrator | Synthesis Rate | Interpretation |
|------------|----------------|----------------|
| Anthropic  | 77.2%          | High synthesis — creates own verdict |
| OpenAI     | 59.4%          | Middle ground |
| Google     | 7.0%           | Deferential — selects existing rater |

### Family Bias (Same-Vendor Selection)
| Arbitrator | Same-Family Rate | Expected | Direction | Significant |
|------------|------------------|----------|-----------|-------------|
| OpenAI     | 51.8%            | 33.3%    | **Pro-self** | Yes (p<.001) |
| Anthropic  | 36.8%            | 33.3%    | Neutral | No (p=.159) |
| Google     | 16.2%            | 33.3%    | **Anti-self** | Yes (p<.001) |

### Interpretation
- **Google** almost never synthesizes; when selecting, actively avoids own-family raters
- **OpenAI** moderately synthesizes; when selecting, favors own-family raters  
- **Anthropic** synthesizes most often; when selecting, shows no family preference

This represents genuine architectural/behavioral differences between models as arbitrators — methodologically interesting and should be documented.

---

## Validation Status

### Issues Closed
| Issue | Status | Resolution |
|-------|--------|------------|
| 8.2 Google Behavior | ✅ RESOLVED | 7% synthesis is real behavior, not labeling artifact |
| 8.3 L1 Quality Gate | ✅ ACCEPT | κ=0.796 accepted with kappa paradox context; three-way κ=0.833 confirms reliability |

### Issue Deferred
| Issue | Status | Notes |
|-------|--------|-------|
| 8.1 Synthesis Interpretation | ⏳ DEFERRED | Revisit with complete Google data; sample 10-20 synthesis cases from final_verdicts.csv |

---

## Current Metrics (Post-Fix)

### Agreement Statistics
- **Two-way L1 Cohen's κ:** 0.796 (Substantial)
- **Three-way L1 Fleiss' κ:** 0.833 (Almost Perfect) — CPS subset only
- **Binary consolidability κ:** 0.896 two-way / 0.903 three-way (Almost Perfect)
- **Feasibility κ:** 0.843 two-way / 0.871 three-way (Almost Perfect)

### Coverage
- OpenAI: 1,598 pairs (complete)
- Anthropic: 1,598 pairs (complete)
- Google: 503 pairs (CPS only, ~31%)

### Final Verdicts
- HIGH confidence: 1,458 (91.2%)
- MODERATE: 112 (7.0%)
- LOW: 28 (1.8%)

---

## Morning Action Items

### 1. Collect Google Data (~250 pairs)
```bash
cd /Users/brock/Documents/GitHub/federal-survey-concept-mapper/reports/03_harmonization_constraints
python 02_arbitration_pipeline.py --arbitrator google
```
Rate limit resets overnight. Target: ~750 total Google pairs.

### 2. Re-run Stage 2 (Deduplication)
This propagates any pipeline fixes to deduped analysis files:
```bash
python scripts/03_stage2_deduplication.py
```

### 3. Re-run Stage 3 (Analysis)
```bash
python scripts/04_stage3_arbitration.py
```

### 4. Revalidate
- Check if three-way agreement improves with more Google data
- Revisit Issue 8.1 (synthesis interpretation) with larger sample
- Verify family bias patterns hold with expanded data

### 5. Stage 4 Sign-off
Once Stage 3 is validated with complete data, proceed to Stage 4 question-level consolidability analysis.

---

## Critical Reminder: Pair-Level ≠ Question-Level

Stage 4 must compute **per-question consolidability rates**, not just pair-level.

Example: FoodAPS has 52 food security questions, ACS has 6 → 312 pairs. Even 100% ACS coverage = 6/312 = 1.9% pair-level, but stakeholders need "X of 52 FoodAPS questions are consolidable."

---

## Files Modified This Session

### Code
- `02_arbitration_pipeline.py` — Pipeline fix for "Rater X" parsing
- `scripts/fix_google_selected_rater_key.py` — One-time cleanup script (created)

### Documentation  
- `docs/methodology_log.md` — Decision 015 added

### Data (Fixed)
- `output/results/arbitration_v3_results_google_gemini-3-pro-preview.jsonl`
- `output/analysis/arbitration_deduped_google.jsonl`

### Outputs (Regenerated)
- `output/analysis/stage3_arbitration_metrics.json`
- `output/analysis/stage3_arbitration_report.md`
- `output/analysis/final_verdicts.csv`
- `output/analysis/barrier_summary_by_survey.csv`

---

## Transcript Reference

Full session transcript: `/mnt/transcripts/2026-01-31-03-11-42-stage3-synthesis-labeling-bug-fix.txt`
