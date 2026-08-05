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

---

## Addendum 2026-06-11: Stale pre-correction numbers found in report/abstract.md

**What happened.** During v2 report verification the author could not reproduce the abstract's headline claim ("approximately 45% of questions have at least one viable harmonization path... roughly 16%... roughly 29%... roughly 55%"). Tracing showed these are exactly the pre-correction, ID-inflated combined values recorded in `docs/validation/question_counts.json` `known_issues`: (102+68)/(240+140) = 44.7%, F1 (37+23)/380 = 15.8%, F2 (65+45)/380 = 28.9%, F3 210/380 = 55.3%. The 2026-02 dedup correction updated NUMBERS_MAP and the validation JSON but was never propagated to `report/abstract.md`.

**Corrected values (V&V certified, unique-question unit, entered-pairing denominator).** Combined CPS+FoodAPS: 275 unique questions compared; 142 (51.6%) with at least one path; best-tier F1 51 (18.5%); best-tier F2 91 (33.1%); F3 133 (48.4%). Per survey: CPS 86/157 (54.8%), FoodAPS 56/118 (47.5%).

**Scope correction applied at the same time.** The abstract phrase "of questions" concealed the entered-pairing denominator. CPS: 157 of 211 instrument questions entered pairing (74.4%); FoodAPS: 118 of 462 (25.5%). On the full-instrument denominator, questions with a path are 86/211 = 40.8% (CPS) and 56/462 = 12.1% (FoodAPS). The abstract now states both denominators explicitly.

**Not changed, flagged for author review.** (a) "Three independent AI models... reach near-perfect agreement": v1 post-arbitration kappa is 0.84 and the v2 confirmation run measured cross-generation binary candidate agreement at 88 to 91% (kappa 0.70 to 0.72); "near-perfect" overclaims. (b) "Harmonization rates are stable across survey pairs": 54.8% vs 47.5% supports "similar"; note the v2 net-new AHS reaches only 12.4% on its full-instrument denominator, so any stability claim must stay scoped to entered-pairing rates for ACS-adjacent content. (c) Combined three-survey tabulation exists in `v2/report/` context but v1 (validated) and AHS (v2-only, unvalidated) figures must not be pooled into one headline percentage.

**Lesson reinforced (see item 3 above).** The abstract is a canonical surface like NUMBERS_MAP; corrections must enumerate every document carrying a number, and the abstract was missed in the 2026-02 sweep.

**Completion note 2026-08-05.** The three flagged claims are resolved and the repo-wide sweep is done. Task log: `cc_tasks/2026-08-05_report_surfaces_sweep_task_log.md`. (a) "Near-perfect" is gone from every report surface, replaced with κ = 0.84 post-arbitration plus the v2 cross-generation figures 88 to 91% (κ = 0.70 to 0.72); `report/index.qmd` turned out never to have carried that sentence, so item (a) applied to `report/abstract.md` only. Two further uses in `report/chapters/02_classification.qmd` and `04_pairwise_harmonization.qmd` were also replaced, with their kappas unchanged, because the rebuild check requires the phrase's absence from the PDF. (b) The stability claim is now scoped to entered-pairing rates and states 54.8% and 47.5% explicitly; AHS appears in neither abstract surface. (c) No pooled three-survey percentage was introduced anywhere.

**The sweep found one surface the 2026-06-11 review missed entirely.** `fact_sheet/index.qmd` carried all four pre-correction rates, not just the near-perfect claim, because it writes them as LaTeX escapes (`\textasciitilde 45\%`) which a plain `45%` grep does not match. Also corrected: `docs/stages/tevv/TEVV_methodology_document.md` stated 41.7% and 48.6% as current consolidability rates. Add the escaped form to any future sweep pattern. Rebuilt and verified: `45%` and `near-perfect` are both absent from `report/FedSurveyHarmonization.pdf` (35 pages, 112/112 validation checks pass), and absent from `fact_sheet/fact_sheet.pdf`.

**New discrepancy opened, not resolved.** ACS-side participation is stated as 51 of 115 (44.3%) in NUMBERS_MAP and `README.md`, but 48 of 115 (41.7%) in `question_counts.json` and the v2 three-survey summary. The certified code reproduces 48 exactly on current data; NUMBERS_MAP's 51 reproduces from nothing. However 48 is itself an undercount: `stage4_question_level.csv` and `stage4_question_best_matches.csv` hold the same 275 questions but kept different representative `survey_q_id`s for 10 of them when duplicate texts were collapsed, so the q_id join silently drops 5 consolidable questions. This is precisely the breakage `docs/validation/inflation_blast_radius.md` predicted for a dedup applied to one file and not the other. A text join yields 50 (43.5%) but loses 3 CPS questions to the 100-character truncation collision already noted at NUMBERS_MAP line 188. All three published numbers are below the true value. The fix is to regenerate `best_matches` from the deduplicated `question_level` so the q_ids agree; no surface edited in this pass states an ACS-side figure, so nothing here is blocked on it.
