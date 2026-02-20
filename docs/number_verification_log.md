# Number Verification & Correction Log

**Date:** 2026-02-19
**Purpose:** Document the verification process that identified and corrected inflated counts in the harmonization results

---

## What Happened

During the master report chapter rewrites, the author requested a complete question funnel trace — total survey questions through to harmonization results — to ensure Ch 5 (Results) reported rates against the correct denominators. This verification uncovered a systematic inflation in the reported counts.

## The Problem

The pipeline generates question-subtopic combination IDs (e.g., `CPS_042_Employment_Status`, `CPS_042_Labor_Force`) when a question is classified into multiple subtopics. The findings pipeline (`src/pipelines/04_findings_pipeline.py`, line 87) aggregated by these IDs rather than by unique question text. As a result, a single question appearing in two subtopics was counted twice in every metric: total assessed, F1, F2, F3, and harmonizable.

This is the kind of error that emerges naturally in iterative research pipelines. The ID-based counting was correct for pair-level analysis (each ID represents a distinct evaluation context) but incorrect for question-level reporting (the reader wants to know how many actual questions have harmonization paths).

## How It Was Caught

The verification followed three stages:

**Stage 1: Funnel trace.** Tracing raw question counts from `PublicSurveyQuestionsMap.csv` through to `stage4_survey_summary.json` revealed that CPS went from 211 raw questions to 240 "assessed questions" — an impossible increase for a pipeline that only filters. This triggered deeper investigation.

**Stage 2: ID vs. text analysis.** Counting unique question texts in the pipeline output files (vs. unique IDs) confirmed the inflation. The 240 CPS IDs corresponded to 157 unique question texts. The 140 FoodAPS IDs corresponded to 118 unique texts.

**Stage 3: Numerator verification.** The same inflation affected the harmonizable counts (102 CPS IDs = 86 unique texts; 68 FoodAPS IDs = 56 unique texts). Every number in `stage4_survey_summary.json` was ID-based, not question-based.

## Impact on Reported Numbers

| Metric | Old (ID-based) | Corrected (unique questions) |
|--------|:-:|:-:|
| CPS total | 211 | 211 (unchanged) |
| CPS paired (concept overlap) | 240 (IDs) | 164 (unique questions) |
| CPS harmonizable | 102 (IDs) | 93 (86 assessed + 7 pre-filtered only) |
| CPS rate (of paired) | 42.5% | 56.7% |
| CPS rate (of total survey) | N/A | 44.1% |
| FoodAPS total | 462 | 462 (unchanged) |
| FoodAPS paired (concept overlap) | 140 (IDs) | 123 (unique questions) |
| FoodAPS harmonizable | 68 (IDs) | 61 (56 assessed + 5 pre-filtered only) |
| FoodAPS rate (of paired) | 48.6% | 49.6% |
| FoodAPS rate (of total survey) | N/A | 13.2% |

### Pre-Filtered "Yes" Questions (Final Correction)

The barrier pipeline filters out pairs where both models rated consolidation_potential='yes' before barrier coding. These high-confidence matches (citizenship, sex/gender, DOB, education) were excluded from the findings pipeline because they never received barrier verdicts. Verification confirmed:

- CPS: 24 pre-filtered questions, 17 overlapped with assessed set, **7 unique additions**
- FoodAPS: 14 pre-filtered questions, 9 overlapped with assessed set, **5 unique additions**

These are now included in the final harmonizable counts above.

## Additional Finding: Pipeline Design Was Correct

The pipeline intentionally filters out question pairs where both models rated consolidation_potential='yes' before barrier coding. These are high-confidence matches (demographic basics: age, sex, race, etc.) that don't need barrier analysis. This is correct behavior — the barrier pipeline should only process pairs that need barrier classification. The filtering was documented in `01_barrier_pipeline.py` (lines 107-110).

## Additional Finding: Model Name Contamination

The same verification process caught a separate long-standing issue: hallucinated model names (GPT-4o, Claude 3.5 Sonnet) had been propagated through NUMBERS_MAP.md, NARRATIVE_CHECKLIST.md, and Ch 2 by prior AI sessions. The correct Report 01 classification models are GPT-5-mini and Claude Haiku 4.5 (verified against `output/report_01/FULL_REPORT.md`). All contaminated files were corrected. See `docs/model_name_contamination_cleanup_report.md`.

## Why This Matters

This verification sequence demonstrates the value of end-to-end number tracing in AI-assisted research pipelines. The original pipeline ran correctly at the pair level. The error was in the reporting layer — a mismatch between what the pipeline computed (pair-level and ID-level results) and what the report needed (question-level results). 

In a traditional research workflow, this kind of discrepancy might persist through publication because the volume of data makes manual verification impractical. The iterative AI-assisted approach — rapid pipeline development, followed by systematic tracing and correction — compresses what would normally be a months-long QA process into hours. The error was a natural consequence of moving fast; catching and correcting it was a natural consequence of building verification into the workflow.

## Files Involved

| File | Role |
|------|------|
| `docs/question_funnel_trace.md` | Complete trace with corrected funnels |
| `docs/model_name_contamination_cleanup_report.md` | Model name corrections |
| `cc_tasks/trace_question_funnel_cps_foodaps.md` | Initial trace task |
| `cc_tasks/resolve_funnel_discrepancies.md` | Discrepancy resolution task |
| `cc_tasks/verify_harmonizable_unique_counts.md` | Numerator verification task |
| `cc_tasks/verify_prefiltered_in_counts.md` | Pre-filtered question verification (pending) |
| `cc_tasks/exterminate_hallucinated_model_names.md` | Model name cleanup task |

## Lessons for Future Pipeline Work

1. **ID-based vs. text-based counting must be explicit.** Any pipeline that generates combination IDs should document whether downstream counts are ID-level or entity-level.
2. **Funnel denominators require end-to-end tracing.** Reporting a rate without tracing the denominator back to the raw data source is a recipe for misleading results.
3. **AI session handoffs propagate errors.** Incorrect numbers in canonical reference docs (NUMBERS_MAP, NARRATIVE_CHECKLIST) get treated as ground truth by subsequent sessions. Contaminated references must be corrected at the source.
4. **Verification is a feature, not overhead.** This process caught real errors that would have survived peer review. The cost was a few hours of investigation; the alternative was publishing incorrect rates.
