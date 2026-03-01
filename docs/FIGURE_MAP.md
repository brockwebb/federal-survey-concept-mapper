# Master Report — Figure Map

**Purpose:** Every figure in the master report traced to its producing script, input data, output location, and chapter reference.  
**Convention:** All figure scripts live in `src/figures/`. All outputs go to `report/figures/`. All scripts import style from `assets/census_plot_style.py` (symlink → `central_library/style/census_plot_style.py`).  
**Last updated:** 2026-03-01

---

## Figures

| Figure ID | Title | Chapter | Script | Input Data | Output |
|-----------|-------|---------|--------|------------|--------|
| Fig 1 | Topic Distribution | Ch 2 (Classification) | `src/figures/fig01_topic_distribution.py` | `docs/stages/01_classification/data/comparison/topic_distribution.csv` | `report/figures/fig01_topic_distribution.pdf` |
| Fig 2 | Total Questions by Survey — ACS Family | Ch 3 (Survey Overlap) | `src/figures/fig02_acs_family_profile.py` | `docs/validation/question_counts.json` (validated from `data/raw/PublicSurveyQuestionsMap.csv`) | `report/figures/fig02_acs_family_profile.pdf` |
| Fig 3 | Topic Composition of Evaluated Question Pairs | Ch 4 or Ch 5 (Method/Results) | `src/figures/fig03_paired_topic_composition.py` | `docs/stages/03_harmonization/data/analysis/stage4_topic_breakdown.csv` | `report/figures/fig03_paired_topic_composition.pdf` | ⚠️ **INPUT DATA HAS INFLATION** — `stage4_topic_breakdown.csv` counts question-subtopic assignments, not unique questions. Fig 3 needs regeneration with deduplicated source or dedup logic in the script. See `docs/validation/number_flow.md`. |

## Architecture Diagrams (PaperBanana + D2)

PaperBanana diagrams: method spec → `paperbanana generate` → PNG. See CLAUDE.md "Diagrams Are Built From Source" for full workflow.

Models used: VLM `gemini-2.5-flash` (config specifies `gemini-3.1-pro` — NOT FOUND in API); Image `gemini-3.1-flash-image-preview` (matches config). Generated 2026-03-01.

| Figure ID | Title | Chapter | Method Spec | Deployed Output | Provenance Run | Status |
|-----------|-------|---------|-------------|-----------------|----------------|--------|
| Arch 1 | Pipeline Overview | Appendix A | `assets/diagrams/paperbanana/pipeline_overview_method.txt` | `assets/diagrams/fig_pipeline_overview.png` | `run_20260301_182906_fe0aa1` | generated — awaiting review |
| Arch 2 | Stage 1: Topic and Subtopic Classification | Appendix A | `assets/diagrams/paperbanana/stage1_classification_method.txt` | `assets/diagrams/fig_stage1_classification.png` | `run_20260301_183032_263c19` | generated — awaiting review |
| Arch 3 | Stage 2: Concept Overlap and Pair Generation | Appendix A | `assets/diagrams/paperbanana/stage2_overlap_method.txt` | `assets/diagrams/fig_stage2_overlap.png` | `run_20260301_183156_f0d033` | generated — awaiting review |
| Arch 4 | Stage 3: Multi-Model Barrier Rating | Appendix A | `assets/diagrams/paperbanana/stage3_rating_method.txt` | `assets/diagrams/fig_stage3_rating.png` | `run_20260301_183327_d0fdff` | generated — awaiting review |
| Arch 5 | Stage 4: Structured Arbitration Protocol | Appendix A | `assets/diagrams/paperbanana/stage4_arbitration_method.txt` | `assets/diagrams/fig_stage4_arbitration.png` | `run_20260301_183455_fb490d` | generated — awaiting review |
| Arch 6 | Stage 5: Question-Level Results | Appendix A | `assets/diagrams/paperbanana/stage5_results_method.txt` | `assets/diagrams/fig_stage5_results.png` | `run_20260301_181411_72c0da` | ON HOLD — pending design discussion |

**D2 diagrams (if any):**

| Figure ID | Title | Chapter | Source | Output |
|-----------|-------|---------|--------|--------|
| (none yet) | | | `assets/diagrams/*.d2` | `report/figures/*.pdf` |

## Style

- **Palette:** U.S. Census Bureau xdgov Data Design Standards (Section 508 compliant)
- **Style module:** `assets/census_plot_style.py` → `from census_plot_style import COLORS, paper_theme, save_figure`
- **Output format:** PDF, 300 DPI, 6.5in max width
- **D2 diagrams:** `.d2` source in `assets/diagrams/`, rendered to PDF/SVG in `report/figures/`

## Slides

Slide figures will be derived from the same scripts with adjusted dimensions. Mapping TBD when slides are scoped.

---

## Checklist

- [ ] Symlink created: `assets/census_plot_style.py`
- [ ] Fig 1 generated and reviewed
- [ ] Fig 2 generated and reviewed
- [ ] Fig 3 generated and reviewed — ⚠️ BLOCKED: input data inflated, needs corrected source
- [ ] D2 installed (`brew install d2`)
- [ ] Arch 1–6 generated (2026-03-01) — awaiting Brock review before wiring into report
- [ ] All figures wired into chapter `.qmd` files
- [ ] Slides figure variants scoped
