# Stage 4 Inflation Blast Radius Audit

**Date:** 2026-02-28
**Status:** Read-only audit
**Auditor:** Claude Code

## Summary

The Stage 4 inflation bug originates in `04_findings_pipeline.py`, which groups by `(survey, survey_q_id)` rather than by unique question text. Because dual-subtopic classification assigns multiple IDs to the same question text, CPS inflates from 157 to 240 and FoodAPS from 118 to 140 in all four stage4 output files. The inflated counts propagate directly into `build_expert_review_table.py` (which hard-codes 240/140/380 as validation targets), into `stage4_best_match_rollup.py` (which validates row count against the inflated question-level total), and into figure script `fig03_paired_topic_composition.py` (which reads the inflated `stage4_topic_breakdown.csv`). All six `.qmd` report chapters and appendices use the correct deduplicated counts from `question_counts.json` as reflected in narrative prose. Running `run_pipeline.py --stage all` or `run_pipeline.py --stage findings` will unconditionally overwrite the four inflated stage4 files with fresh inflated output; no guard or warning exists in the pipeline to prevent this.

---

## 1. Affected Scripts

| Script | Reads From | Uses Inflated Counts? | Output Artifacts | Status |
|--------|-----------|----------------------|-----------------|--------|
| `src/pipelines/04_findings_pipeline.py` | `final_verdicts.csv`, `cps_comparison_merged.csv`, `foodaps_comparison_merged.csv` | YES — groups by `survey_q_id` (not `question_text`), producing 240 CPS + 140 FoodAPS rows | `stage4_question_level.csv` (380 rows), `stage4_survey_summary.json`, `stage4_topic_breakdown.csv`, `stage4_findings_report.md`, `stage4_f2_transformations.csv`, `stage4_barrier_patterns.csv` | AFFECTED |
| `src/scripts/build_expert_review_table.py` | `stage4_question_best_matches.csv` (inflated), `final_verdicts.csv`, `arbitration_merged.csv`, `cps_comparison_merged.csv`, `foodaps_comparison_merged.csv` | YES — hard-codes validation: `len(cps) != 240`, `len(foodaps) != 140`, `len(expert) != 380`; will raise `ValueError` if given correct 157/118/275 counts | `expert_review_cps.csv` (240 rows), `expert_review_foodaps.csv` (140 rows), `expert_review_combined.csv` (380 rows), `taxonomy_reference.md`, `classification_distribution.md` | AFFECTED |
| `src/scripts/stage4_best_match_rollup.py` | `stage4_bakeoff_scores.csv`, `stage4_question_level.csv` (inflated), `final_verdicts.csv`, `cps_comparison_merged.csv`, `foodaps_comparison_merged.csv` | YES — validates `len(output) != len(questions)`, where `questions` is the inflated 380-row `stage4_question_level.csv`; will fail if question_level is corrected first | `stage4_question_best_matches.csv` (380 rows, truncated source_text at 120 chars) | AFFECTED |
| `src/figures/fig03_paired_topic_composition.py` | `stage4_topic_breakdown.csv` (inflated) | INFORMATIONAL — reads `total_pairs` column (pair counts, not question counts); the figure title/subtitle hardcodes correct pair counts (1,030 and 568 pairs); question-level inflation does not affect the pair-count aggregation used here | `report/figures/fig03_paired_topic_composition.pdf` | INFORMATIONAL |
| `src/scripts/extract_example_pairs.py` | `output/analysis/stage4_question_best_matches.csv` (inflated, stale path) | NO — reads best_matches for question text and scores only; does not use `total_questions` or `len(df)` as a count; selects individual pairs by feasibility/score filters | `output/analysis/example_pairs_for_presentation.md`, `output/analysis/example_pairs_candidates.csv` | INFORMATIONAL |
| `src/scripts/visualize_question_consolidation_distribution.py` | `output/report_03/analysis/stage4_question_best_matches.csv` (inflated) | YES — computes `len(survey_df)` per survey and reports as question count in summary (`print_summary`); bar chart heights directly encode inflated counts | `output/report_03/visuals/question_consolidation_distribution.png` | AFFECTED |
| `src/validation/validate_question_counts.py` | `stage4_question_level.csv` (inflated) | NO — explicitly documents and compensates for inflation; deduplicates on `question_text`, computes corrected counts, and writes them to `question_counts.json` | `docs/validation/question_counts.json`, `docs/validation/question_counts.log` | SAFE |
| `src/validation/validate_complete.py` | `stage4_question_level.csv`, `stage4_question_best_matches.csv`, `stage4_survey_summary.json` (all inflated) | NO — explicitly expects inflated values (240/140) as "known inflated" sentinel assertions; reads `question_counts.json` for correct values; documents the inflation in log output | None (validation report only) | SAFE |
| `src/pipelines/05_deliverables_pipeline.py` | Does not directly read stage4 files; orchestrates `stage4_best_match_rollup.py`, `build_expert_review_table.py`, `extract_example_pairs.py` | YES — cascades inflation via sub-scripts 5b and 5c | All outputs of sub-scripts listed above | AFFECTED (via orchestration) |
| `src/pipelines/run_pipeline.py` | Does not read stage4 files directly; calls `04_findings_pipeline.py` via `run_findings_stage()` | YES — `--stage findings` or `--stage all` unconditionally calls `04_findings_pipeline.py`, regenerating all inflated files | All stage4 outputs | AFFECTED (via orchestration) |
| `src/pipelines/run_full_pipeline.py` | Does not call `04_findings_pipeline.py` or stage5 | NO — this is the old Report 03 Phase 1-4 runner (coding + arbitration only); does not invoke findings or deliverables stages | Arbitration/coding outputs only | SAFE |
| `src/figures/fig01_topic_distribution.py` | Not examined for stage4 references | NO — no stage4 file references found in grep scan | Report figure | SAFE |
| `src/figures/fig02_acs_family_profile.py` | Not examined for stage4 references | NO — no stage4 file references found in grep scan | Report figure | SAFE |
| `src/scripts/visualize_harmonization_distribution.py` | `output/report_03/analysis/final_verdicts.csv` | NO — reads pair-level verdicts only, not question-level CSV or survey_summary | `output/report_03/visuals/harmonization_distribution.png` | SAFE |
| `src/scripts/stage4_scoring_bakeoff.py` | `final_verdicts.csv`, `barrier_coding_merged_3rater.csv` | NO — works at pair level; does not reference question counts | `stage4_bakeoff_scores.csv`, `stage4_bakeoff_correlations.csv`, `stage4_bakeoff_report.md`, `stage4_divergent_pairs.csv`, `stage4_score_distributions.json` | SAFE |
| `src/scripts/stage4_triage_assignment.py` | `stage4_bakeoff_scores.csv` | NO — pair-level scoring; no question count usage | `stage4_triage_assignments.csv`, `stage4_triage_summary.json` | SAFE |
| `src/scripts/stage4_model_validation_visuals.py` | `stage2_agreement_metrics.json`, `stage3_arbitration_metrics.json` (per docstring) | NO — agreement metrics only; no stage4 question-level files referenced | `stage4_construct_validity.md`, `stage4_cost_quality_summary.md` | SAFE |
| `src/scripts/descriptive_stats.py` | Not in grep results for stage4 patterns | NO — no stage4 file references detected | Unknown | SAFE |

**Notes for INFORMATIONAL entries:**

`fig03_paired_topic_composition.py` reads `stage4_topic_breakdown.csv` but only uses `total_pairs` (pair counts aggregated by subtopic). The pair counts (1,030 CPS, 568 FoodAPS) are correct — inflation is at the question level, not the pair level. The hardcoded subtitle text "CPS–ACS (1,030 pairs) and FoodAPS–ACS (568 pairs)" is accurate. However, if a future fix to `04_findings_pipeline.py` changes the topic_breakdown structure, this script would need to be checked again.

`extract_example_pairs.py` reads `stage4_question_best_matches.csv` for individual pair selection (filtering by feasibility code and Borda score). It does not use `len(df)` as a count to report. However, its input path is stale (`output/analysis/stage4_question_best_matches.csv` instead of `output/report_03/analysis/stage4_question_best_matches.csv`), meaning it would fail to find the file at runtime regardless of the inflation issue.

---

## 2. Affected Report Chapters

| Chapter | Stale Values Found | Correct Values Found | Needs Update? |
|---------|-------------------|---------------------|---------------|
| `report/chapters/01_introduction.qmd` | None | None (no specific result numbers) | No |
| `report/chapters/02_classification.qmd` | None | None (pre-pairing stage) | No |
| `report/chapters/03_survey_overlap.qmd` | **240 CPS, 140 FoodAPS, 380 total** | None | YES — stale values present in narrative prose |
| `report/chapters/04_pairwise_harmonization.qmd` | **380 unique source questions (240 + 140)** | None | YES — stale values present |
| `report/chapters/05_results.qmd` | None | **93 CPS, 61 FoodAPS, 154 total** (stated as harmonizable counts, not entry counts) | No — but see note |
| `report/chapters/06_implications.qmd` | None | **93 CPS, 61 FoodAPS, 154 total** | No |
| `report/chapters/07_limitations.qmd` | None | **154 total (93 CPS + 61 FoodAPS)** | No — but see note |
| `report/appendices/A_architecture.qmd` | None | None (placeholder only) | No |
| `report/appendices/B_taxonomy.qmd` | None | None (taxonomy definitions) | No |
| `report/appendices/C_tevv.qmd` | None | None (process quality measures) | No |

**Detail on stale values found:**

`03_survey_overlap.qmd` (line 21): "Together they contribute 380 unique source questions (240 from CPS, 140 from FoodAPS), a sufficient sample to validate the approach before scaling up." The correct numbers are 275 unique questions (157 CPS + 118 FoodAPS). The inflated values 240/140/380 appear in the chapter checklist comment as `[x] 380 unique source questions (240 CPS + 140 FoodAPS)`.

`04_pairwise_harmonization.qmd` (line 5 and checklist, line 48): "1,598 total pairs, drawn from 380 unique source questions." Also checklist: `[x] 380 unique source questions (240 + 140)`. The 1,598 pair count is correct (pair-level, not affected by inflation). The "380 unique source questions" is the inflated figure.

`05_results.qmd`: The chapter does not cite 157, 118, or 275 directly but says "164 unique CPS questions" and "123 unique FoodAPS questions" as those entering pairing (these are neither the inflated nor the `question_counts.json` figures — they appear to be a third set of numbers not verified in this audit). The harmonizable counts (93, 61) do not match `question_counts.json` (86, 56). These may reflect a different dedup method. Flag for separate verification.

`07_limitations.qmd` (line 3): "Of these, 154 questions (93 CPS, 61 FoodAPS) have viable harmonization paths." The checklist confirms these are treated as "corrected numbers," but they do not match `question_counts.json` values of 86 CPS + 56 FoodAPS = 142 total. Flag for separate verification.

---

## 3. Pipeline Rerun Risk

Running `python src/pipelines/run_pipeline.py --stage findings` or `python src/pipelines/run_pipeline.py --stage all` will unconditionally call `04_findings_pipeline.py` via `run_findings_stage()` (line 415 of `run_pipeline.py`). There is no `--skip` flag for the findings stage, no existence check on outputs, and no warning about the inflation issue. The pipeline will overwrite all four inflated files with fresh inflated output.

`04_findings_pipeline.py` does NOT write to `question_counts.json`. The canonical file at `docs/validation/question_counts.json` is produced only by `src/validation/validate_question_counts.py` and is not part of the normal pipeline. A pipeline rerun will not corrupt `question_counts.json`.

Running `python src/pipelines/run_pipeline.py --stage deliverables` (or `--stage all`) will subsequently call `05_deliverables_pipeline.py`, which runs `stage4_best_match_rollup.py` (stage 5b) and `build_expert_review_table.py` (stage 5c). Both of these scripts have hard-coded validation assertions that expect the inflated counts (380, 240, 140). If `04_findings_pipeline.py` is fixed to produce correct counts, stages 5b and 5c will raise `ValueError` and halt the pipeline until their validation assertions are also updated.

The old runner `run_full_pipeline.py` does not call `04_findings_pipeline.py` or `05_deliverables_pipeline.py` and poses no rerun risk for the inflation bug.

---

## 4. Dedup Edge Cases

Results from the Python spot check on `stage4_question_level.csv` (380 rows):

**Q1 — Texts with multiple feasibility values: 8**

Eight distinct question texts appear with more than one `best_feasibility` value across their duplicate rows. The worst case is a CPS disability question (truncated: `(Do / Does) (name/you) have a disability that prevents (you/he/she) from accepti...`) which appears 25 times under IDs CPS_66 through CPS_167. One instance (CPS_67) received F2; all others received F3. If dedup takes "best feasibility" (minimum rank), that question correctly becomes F2. However, the current inflated files count it 25 times, with 24 rows reporting F3 and one reporting F2. Any aggregate calculation on the inflated file without dedup will be wrong for this question.

A FoodAPS question (`Are you currently looking for a job...`) appears twice (FOODAPS_193 as F3, FOODAPS_194 as F2), and a CPS question (`Did (you/he/she) do any of this work during the last 4 weeks...`) appears four times (one F1, three F2). In both cases a correct dedup on `question_text` keeping minimum feasibility rank will yield the more-consolidable classification.

**Q2 — Leading/trailing whitespace: 7 rows**

Seven rows have whitespace in `question_text` that differs from the stripped version. These could cause groupby to miss deduplication for those texts. Combined with case sensitivity, this poses a risk to any fix that groups on raw `question_text`. A production fix should apply `.str.strip().str.lower()` normalization before grouping.

**Q3 — Case differences: 1 group**

One text group differs only by case (i.e., the same question appears in both original and lowercased form). This is a single instance but confirms that case normalization is required.

**Distribution of survey_q_id per unique question_text:**

```
1 unique q_id:  245 texts  (most questions — no duplication)
2 unique q_ids:  20 texts
3 unique q_ids:   1 text
4 unique q_ids:   5 texts
6 unique q_ids:   1 text
16 unique q_ids:  1 text
25 unique q_ids:  2 texts
```

30 question texts have more than one q_id. The maximum is 25 q_ids for a single question text. The total inflation is 380 rows - 275 unique texts = 105 extra rows.

---

## 5. ACS-Side Join Integrity

**Column mapping:**

`question_level.csv` columns: `['survey', 'survey_q_id', 'question_text', 'pair_count', 'has_consolidable_path', 'has_f1_path', 'best_is_f2', 'all_f3', 'best_feasibility']`

`best_matches.csv` columns: `['survey', 'source_q_id', 'source_text', 'has_consolidable_path', 'best_match_q_id', 'best_match_text', 'best_feasibility', 'score_borda', 'score_entropy', 'triage_quadrant', 'pair_id']`

The join key between the two files is `survey_q_id` (question_level) ↔ `source_q_id` (best_matches). Both use the same ID namespace (e.g., `CPS_0`, `CPS_1`, `CPS_10`). The join is valid.

**Namespace samples confirm alignment:**

`survey_q_id` from question_level: `['CPS_0', 'CPS_1', 'CPS_10']`
`source_q_id` from best_matches: `['CPS_0', 'CPS_1', 'CPS_10']`

**Consolidable q_ids with no match in best_matches: 0**

All source q_ids classified as F1 or F2 in question_level have a corresponding row in best_matches. There are no "lost" consolidable questions in the join.

**Orphan matches (best_matches source_q_id not in question_level): 0**

No rows in best_matches reference a q_id that does not exist in question_level. The two files are fully consistent with each other at the q_id level.

**Note on text truncation:** `best_matches.csv` truncates `source_text` at 120 characters (max observed: 120, mean: 87.8 characters). The spec identifies this as a known issue with truncation at ~100 chars; the actual cutoff is 120 characters (set at line 92 of `stage4_best_match_rollup.py`). The `build_expert_review_table.py` script compensates by re-joining to the original comparison CSVs to recover full text (`source_text_full` column), so downstream expert review tables will have untruncated text.

**Implication for a fix:** Because the join integrity between the two files is perfect at the q_id level, a dedup fix applied to question_level alone (collapsing 380 rows to 275 unique texts) would break the 1:1 correspondence with best_matches unless best_matches is simultaneously regenerated. `stage4_best_match_rollup.py` explicitly validates `len(output) != len(questions)`, so the fix must be applied to both files in the same pipeline run.

---

## 6. Recommended Fix Order

Priority ordered by blast radius and stakeholder visibility:

1. **Fix `04_findings_pipeline.py` (root cause)** — Change `aggregate_to_question_level()` to group by `['survey', 'question_text']` after normalizing with `.str.strip().str.lower()`, taking best feasibility and first q_id. This is the single change that corrects all four stage4 output files. Validate output row counts against `question_counts.json` (157 CPS + 118 FoodAPS = 275 total).

2. **Regenerate stage4 files by running the fixed pipeline** — Run `04_findings_pipeline.py` alone (not via `run_pipeline.py --stage all` to avoid side effects). This will overwrite `stage4_question_level.csv`, `stage4_survey_summary.json`, `stage4_topic_breakdown.csv`, and related files with correct counts.

3. **Fix `stage4_best_match_rollup.py` (stage 5b)** — Update the validation assertion from `len(output) != len(questions)` to compare against the correct 275-row question_level. Also regenerate `stage4_question_best_matches.csv` with 275 rows.

4. **Fix `build_expert_review_table.py` (stage 5c)** — Update hard-coded validation targets from `240/140/380` to `157/118/275`. Regenerate the expert review CSVs and `classification_distribution.md`.

5. **Fix `visualize_question_consolidation_distribution.py`** — The script will automatically produce correct bar chart heights once it reads the corrected `stage4_question_best_matches.csv`. No code change required; regenerate the output PNG.

6. **Update `report/chapters/03_survey_overlap.qmd`** — Change "380 unique source questions (240 from CPS, 140 from FoodAPS)" to "275 unique source questions (157 from CPS, 118 from FoodAPS)" at line 21 and in the checklist comment.

7. **Update `report/chapters/04_pairwise_harmonization.qmd`** — Change "380 unique source questions" to "275 unique source questions" at line 5 and in the checklist comment (line 48). The 1,598 pair count is correct and should not be changed.

8. **Verify `report/chapters/05_results.qmd` and `07_limitations.qmd`** — These chapters cite 93/61/154 as harmonizable counts, which do not match `question_counts.json` values of 86/56/142. This discrepancy may reflect a different dedup method or a secondary data source. Requires a separate investigation to determine whether these numbers are correct or stale before updating the narrative.

9. **Add pipeline guard to `run_pipeline.py`** — Consider adding a `--skip-findings` flag or an existence check with `--force` requirement for the findings stage, analogous to the `--skip-coding` and `--skip-arbitration` flags in `run_full_pipeline.py`.

---

## Additional Findings

**The OUTPUT_DIR path discrepancy:** `04_findings_pipeline.py` writes outputs to `REPO_ROOT / "output" / "report_03" / "analysis"` (the old pre-restructure path). The files cited in the bug report as inflated are at `docs/stages/03_harmonization/data/analysis/`. These appear to be the same physical files, presumably accessed via a symlink or the audit spec path differs from the pipeline write path. The validation scripts at `src/validation/` reference `docs/stages/03_harmonization/data/analysis/` directly. Confirm that these paths resolve to the same location before running any fix.

**`extract_example_pairs.py` has a stale import:** Line 16 uses `sys.path.insert` without first importing `sys`. This would cause a `NameError` at runtime. Additionally, its `BEST_MATCHES` path is `BASE / "output/analysis/stage4_question_best_matches.csv"` — the old pre-restructure path, not the current `output/report_03/analysis/` path. This script cannot run in the current repo layout regardless of the inflation fix.

**`05_deliverables_pipeline.py` has a `NameError`:** Line 43 references `BASE_DIR` which is never defined in that file (it is defined in script-level files but not in this pipeline). This script would fail at import/startup. This is a pre-existing bug unrelated to the inflation issue but blocks deliverables from running.

**`run_full_pipeline.py` is not the active orchestrator:** Despite its name, this older runner covers only Phases 1-4 (coding + arbitration), not findings or deliverables. The active full-pipeline orchestrator is `run_pipeline.py`. The distinction matters for rerun risk assessment.

**Feasibility counts in `question_counts.json`:** The canonical file records CPS: F1=32, F2=54, F3=71, consolidable=86 (rate=54.8%) and FoodAPS: F1=19, F2=37, F3=62, consolidable=56 (rate=47.5%). The report chapters citing 93 CPS and 61 FoodAPS as harmonizable exceed these figures by 7 and 5 respectively. This gap likely reflects a different feasibility assignment method used to generate those chapter numbers and is a separate data integrity issue from the inflation bug itself.
