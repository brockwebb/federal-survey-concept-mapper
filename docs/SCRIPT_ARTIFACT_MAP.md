# Script → Artifact Map

**Purpose:** Every generated figure, table, and analysis output traced to the script that produces it.  
**Last audited:** 2026-02-27  

---

## Report 01 Artifacts

### Figures

| Output File | Location | Producing Script | Input Data |
|-------------|----------|-----------------|------------|
| `figure_02_model_agreement.png` | `output/report_01/` and `output/report_01/visualizations/` | `src/core/create_figure_02_agreement.py` | `output/report_01/comparison/agreement_summary.csv` |
| `figure_04_topic_distribution.png` | `output/report_01/` | **UNKNOWN** — not traced to a script | `output/report_01/comparison/topic_distribution.csv` likely |
| `beeswarm_coverage_distribution.png` | `output/report_01/visualizations/` | `src/core/generate_coverage_analysis.py` | `output/report_01/final/master_dataset.csv` |
| `diverging_bars_by_topic.png` | `output/report_01/visualizations/` | `src/core/generate_coverage_analysis.py` | same |
| `horizontal_bars_all_subtopics.png` | `output/report_01/visualizations/` | `src/core/generate_coverage_analysis.py` | same |
| `unique_orphan_tables.png` | `output/report_01/visualizations/` | `src/core/generate_coverage_analysis.py` | same |
| `2_clustered_heatmap.png` | `output/report_01/visualizations/` | `src/core/generate_visualizations_1_2_3.py` | `output/report_01/final/survey_concept_matrix.csv` |
| `acs_overlap_heatmap.png` | `output/report_01/visualizations/` | `src/core/build_acs_survey_families.py` (likely) | `output/report_01/visualizations/acs_overlap_matrix.csv` |
| `comparison_overview.png` | `output/report_01/comparison/` | `src/core/compare_llm_results.py` (likely) | Raw LLM results |
| `agreement_by_confidence.png` | `output/report_01/comparison/` | `src/core/compare_llm_results.py` (likely) | same |

### Interactive HTML (not in reports, exploratory)

| Output File | Location | Producing Script |
|-------------|----------|-----------------|
| `1_coverage_treemap.html` | `output/report_01/visualizations/` | `src/core/generate_visualizations_1_2_3.py` |
| `3_sankey_flow.html` | `output/report_01/visualizations/` | same |
| `acs_overlap_network.html` | `output/report_01/visualizations/` | same or `build_acs_survey_families.py` |
| `acs_overlap_network_bipartite.html` | `output/report_01/visualizations/` | same |
| `treemap_cps_acs.html` | `output/report_01/visualizations/` | same |
| `treemap_foodaps_acs.html` | `output/report_01/visualizations/` | same |

### Key Data Files

| File | Location | Producing Script |
|------|----------|-----------------|
| `master_dataset.csv` | `output/report_01/final/` | `src/core/create_final_outputs.py` |
| `survey_concept_matrix.csv` | `output/report_01/` and `/final/` | same |
| `agreement_summary.csv` | `output/report_01/comparison/` | `src/core/compare_llm_results.py` |
| `topic_distribution.csv` | `output/report_01/comparison/` | same |
| `full_comparison.csv` | `output/report_01/comparison/` | same |
| `disagreements.csv` | `output/report_01/comparison/` | same |

---

## Report 02 Artifacts

### Figures

| Output File | Location | Producing Script | Input Data |
|-------------|----------|-----------------|------------|
| `treemap_cps.png` | `output/report_02/figures/` | `src/report_02/generate_treemaps.py` | `output/report_02/data/treemap_data_cps.json` |
| `treemap_foodaps.png` | `output/report_02/figures/` | `src/report_02/generate_treemaps.py` | `output/report_02/data/treemap_data_foodaps.json` |
| `classification_workflow.png` | `output/report_02/figures/` | `src/report_02/render_mermaid.py` | Mermaid source in script or .mmd file |
| `decision_tree.png` | `output/report_02/figures/` | `src/report_02/render_mermaid.py` | same |
| `pair_matching.png` | `output/report_02/figures/` | `src/report_02/render_mermaid.py` | same |
| `process_flow.png` | `output/report_02/figures/` | `src/report_02/render_mermaid.py` | same |

### Key Data Files

| File | Location | Producing Script |
|------|----------|-----------------|
| `acs_family2_summary.csv` | `output/report_02/data/` | `src/core/build_acs_survey_families.py` or `src/report_02/build_report.py` |
| `acs_family2_overlap.csv` | `output/report_02/data/` | same |
| `cps_comparison_merged.csv` | `output/report_02/data/` | `src/core/cps_acs_analysis.py` or merge script |
| `foodaps_comparison_merged.csv` | `output/report_02/data/` | `src/core/survey_question_matching.py` or merge script |

---

## Report 03 Artifacts

### Figures (in `output/report_03/visuals/`)

| Output File | Producing Script | Input Data |
|-------------|-----------------|------------|
| `consolidation_rates.png` | `src/scripts/generate_visuals.py` | `stage4_survey_summary.json` |
| `expert_review_load.png` | `src/scripts/generate_visuals.py` | `stage4_survey_summary.json` |
| `barrier_distribution.png` | `src/scripts/generate_visuals.py` | `barrier_summary_by_survey.csv` |
| `triage_quadrant.png` | `src/scripts/generate_visuals.py` | `stage4_bakeoff_scores.csv` |
| `process_flow.png` | `src/scripts/generate_visuals.py` | Mermaid diagram (generated inline) |
| `rater_agreement_heatmap.png` | `src/scripts/stage4_model_validation_visuals.py` | `stage2_agreement_metrics.json` |
| `arbitrator_agreement_heatmap.png` | `src/scripts/stage4_model_validation_visuals.py` | `stage3_arbitration_metrics.json` |
| `arbitrator_synthesis_rates.png` | `src/scripts/stage4_model_validation_visuals.py` | `stage3_arbitration_metrics.json` |
| `single_model_risk.png` | `src/scripts/stage4_model_validation_visuals.py` | `stage2_agreement_metrics.json` |
| `family_bias_analysis.png` | `src/scripts/stage4_model_validation_visuals.py` | `stage3_arbitration_metrics.json` |
| `architecture_pipeline.png` | `src/scripts/stage4_model_validation_visuals.py` | Mermaid diagram (generated inline) |
| `harmonization_distribution.png` | `src/scripts/visualize_harmonization_distribution.py` | `final_verdicts.csv` |
| `question_consolidation_distribution.png` | `src/scripts/visualize_question_consolidation_distribution.py` | `stage4_question_best_matches.csv`, `final_verdicts.csv` |

### Analysis Outputs (in `output/report_03/analysis/`)

| File | Producing Script | Pipeline Stage |
|------|-----------------|----------------|
| `barrier_deduped_*.jsonl` (×3) | `src/scripts/clean_rater_data.py` | Stage 1 (cleaning) |
| `barrier_coding_merged_3rater.csv` | `src/pipelines/03_analysis_pipeline.py` or merge step | Stage 1→2 |
| `stage2_agreement_metrics.json` | `src/pipelines/03_stage2_agreement.py` | Stage 2 |
| `stage2_agreement_report.md` | same | Stage 2 |
| `stage2_extended_report.md` | `src/pipelines/03b_stage2_extended.py` | Stage 2 |
| `arbitration_deduped_*.jsonl` (×3) | `src/scripts/clean_arbitration_data.py` | Stage 3 (cleaning) |
| `stage3_arbitration_metrics.json` | `src/scripts/04_stage3_arbitration.py` | Stage 3 |
| `stage3_arbitration_report.md` | same | Stage 3 |
| `final_verdicts.csv` | `src/scripts/04_stage3_arbitration.py` | Stage 3 |
| `barrier_summary_by_survey.csv` | same or `analyze_barrier_results.py` | Stage 3 |
| `confusion_matrices/*.csv` | `src/scripts/confusion_matrix_analysis.py` | Stage 2/3 |
| `stage4_findings_report.md` | `src/pipelines/04_findings_pipeline.py` | Stage 4 |
| `stage4_survey_summary.json` | same | Stage 4 | ⚠️ **INFLATED** — use `question_counts.json` |
| `stage4_question_level.csv` | same | Stage 4 | ⚠️ **INFLATED** — dedup by question_text or use `question_counts.json` |
| `stage4_question_best_matches.csv` | `src/scripts/stage4_best_match_rollup.py` | Stage 4 |
| `stage4_topic_breakdown.csv` | `src/pipelines/04_findings_pipeline.py` | Stage 4 |
| `stage4_bakeoff_scores.csv` | `src/scripts/stage4_scoring_bakeoff.py` | Stage 4 |
| `stage4_construct_validity.md` | `src/scripts/stage4_model_validation_visuals.py` | Stage 4 |
| `stage4_cost_quality_summary.md` | same | Stage 4 |
| `expert_review_*.csv` | `src/scripts/build_expert_review_table.py` | Stage 5 |

---

## Build System Entry Points

| Command | What it does |
|---------|-------------|
| `python report_builder.py all` | Everything |
| `python report_builder.py r03-visuals` | Runs all 4 visual scripts for Report 03 |
| `python report_builder.py r03` | Visuals + Quarto render (report + slides) |
| `python report_builder.py fact_sheet` | Quarto render fact sheet |
| `python report_builder.py status` | Show what exists / what's missing |

### Visual generation order (Report 03)

```
1. src/scripts/generate_visuals.py
   → consolidation_rates.png, expert_review_load.png, 
     barrier_distribution.png, triage_quadrant.png, process_flow.png

2. src/scripts/stage4_model_validation_visuals.py
   → rater_agreement_heatmap.png, arbitrator_agreement_heatmap.png,
     arbitrator_synthesis_rates.png, single_model_risk.png,
     family_bias_analysis.png, architecture_pipeline.png

3. src/scripts/visualize_harmonization_distribution.py
   → harmonization_distribution.png

4. src/scripts/visualize_question_consolidation_distribution.py
   → question_consolidation_distribution.png
```

---

## Master Report Figures

See **`docs/FIGURE_MAP.md`** — dedicated figure traceability document covering scripts, input data, output files, chapter references, and style conventions.

---

## Validation Infrastructure (added 2026-02-27)

| File | Purpose | Run Command |
|------|---------|-------------|
| `src/validation/validate_question_counts.py` | Computes all corrected counts from raw sources (3-level: instrument, survey, question-level with dedup + ACS-side) | `python src/validation/validate_question_counts.py` |
| `src/validation/validate_complete.py` | **Complete validation suite**: raw data integrity, pairing chain, rating metrics, dedup correctness, ACS-side, round-trip spot checks, cross-document consistency, arithmetic invariants. ~80 checks. | `python src/validation/validate_complete.py` |
| `src/validation/validate_stage1_classification.py` | **Stage 1 classification V&V**: routing path verification (consensus/auto_dual_modal/arbitrated counts), routing equation, agreement metrics recomputed from raw labels, input→output gap reconciliation, kappa applicability check. | `python src/validation/validate_stage1_classification.py` |
| `docs/validation/question_counts.json` | Machine-readable validated output — canonical source for all corrected counts | Generated by `validate_question_counts.py` |
| `docs/validation/question_counts.log` | Human-readable summary | Generated by above |
| `docs/validation/validation_report.json` | Machine-readable complete validation output — all checks with PASS/FAIL/WARN | Generated by `validate_complete.py` |
| `docs/validation/validation_report.log` | Human-readable validation summary | Generated by above |
| `docs/validation/stage1_classification_report.json` | Machine-readable Stage 1 routing verification — includes routing ledger | Generated by `validate_stage1_classification.py` |
| `docs/validation/stage1_classification_report.log` | Human-readable Stage 1 routing summary | Generated by above |
| `docs/validation/number_flow.md` | Complete narrative trace: Five Units table, full funnel, correction summary, files-to-update list | Manual |

**⚠️ INFLATION NOTE:** `stage4_question_level.csv`, `stage4_survey_summary.json`, and `stage4_topic_breakdown.csv` all contain inflated question counts (question-subtopic assignments counted as unique questions). Any script or report citing these files must either deduplicate by question text or use `question_counts.json` as the authoritative source.

---

## Master Report Figures

| Output File | Location | Producing Script | Input Data |
|-------------|----------|-----------------|------------|
| `fig01_topic_distribution.pdf` + `.png` | `report/figures/` | `src/figures/fig01_topic_distribution.py` | NUMBERS_MAP Step 2 (validated from `topic_distribution.csv`) |

### Shared Style

| File | Location | Purpose |
|------|----------|---------|
| `topic_colors.py` | `src/figures/` | Canonical topic→color mapping (xdgov palette). All report figure scripts import from here. |

---

## v2 TEVV Artifacts

### Prompt-Equivalence Gate (v1-vs-v2 prompt fidelity)

| Output File | Location | Producing Script | Input Data |
|-------------|----------|-----------------|------------|
| `prompt_equivalence_report.md` | `docs/stages/tevv/` | `v2/src/tevv/prompt_equivalence.py` | rendered v1/v2 stage3 builders + `v2/config/prompt_divergences.yaml` (allowlist) |
| `prompt_equivalence_evidence.json` | `docs/stages/tevv/` | `v2/src/tevv/prompt_equivalence.py` | same |

**What it is:** A static-text gate (no model calls) that mechanically diffs the
rendered v1 vs v2 prompts across four dimensions (taxonomy block, available
codes, output schema, task framing) and fails unless every divergence is
acknowledged with a written justification in the allowlist. Run from `v2/`:
`python src/tevv/prompt_equivalence.py --stage stage3 --report`. Exit 0 =
equivalent or all-acknowledged; 2 = unacknowledged divergence; 1 = config/IO
fatal; 4 = nothing verified. The allowlist `v2/config/prompt_divergences.yaml`
is its config input; both ship to WORK via git.

**Coverage:** stage3 is VERIFIED (21 acknowledged divergences). stage1 and
stage2 are UNVERIFIED with documented reasons (stage1 v1 module is
import-unsafe; stage2 needs classification-aware extractors). See the report.

**Wired into:** `v2/src/core/stage3_barrier_classify.py` calls
`evaluate("stage3")` in-process on the initial-run path (second precondition
after the smoke gate); blocks unless acknowledged, `--skip-prompt-gate` to
override.

---

## Known Issues

1. **Report 01 scripts use relative paths** (`../output/comparison`). They must be run from `src/` directory. Post-restructure, these paths may be broken since scripts moved to `src/core/`.

2. **Duplicate outputs.** `figure_02_model_agreement.png` exists in both `output/report_01/` (root) and `output/report_01/visualizations/`. Which is canonical?

3. **Report 02 data provenance unclear.** The `acs_family2_summary.csv` and `cps_comparison_merged.csv` files could come from multiple scripts. Need to verify which script actually produced the current versions.

4. **Report 03 presentation images.** Slides reference `presentation/images/` which should be symlinked to `output/report_03/visuals/`. If the symlink is broken, slides render with missing images.

5. **`figure_04_topic_distribution.png`** in Report 01 — no script found that produces this. May have been manually created or produced by a since-deleted script.

6. **Model names in `stage4_model_validation_visuals.py`** — FIXED 2026-02-13. Was hardcoding model names instead of reading from `config/report_03.yaml`. Now reads from config. **Must rerun script to regenerate visuals with correct names.** All 6 PNGs and 2 markdown files in output currently have stale/wrong model names.

7. **RULE: No script may hardcode model names.** All model identifiers must come from `config/report_03.yaml`. This config exists specifically to prevent LLM sessions from hallucinating model names into scripts.
