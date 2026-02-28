# Master Report — Figure Map

**Purpose:** Every figure in the master report traced to its producing script, input data, output location, and chapter reference.  
**Convention:** All figure scripts live in `src/figures/`. All outputs go to `report/figures/`. All scripts import style from `assets/census_plot_style.py` (symlink → `central_library/style/census_plot_style.py`).  
**Last updated:** 2026-02-27  

---

## Figures

| Figure ID | Title | Chapter | Script | Input Data | Output |
|-----------|-------|---------|--------|------------|--------|
| Fig 1 | Topic Distribution | Ch 2 (Classification) | `src/figures/fig01_topic_distribution.py` | `docs/stages/01_classification/data/comparison/topic_distribution.csv` | `report/figures/fig01_topic_distribution.pdf` |
| Fig 2 | Total Questions by Survey — ACS Family | Ch 3 (Survey Overlap) | `src/figures/fig02_acs_family_profile.py` | `docs/validation/question_counts.json` (validated from `data/raw/PublicSurveyQuestionsMap.csv`) | `report/figures/fig02_acs_family_profile.pdf` |
| Fig 3 | Topic Composition of Evaluated Question Pairs | Ch 4 or Ch 5 (Method/Results) | `src/figures/fig03_paired_topic_composition.py` | `docs/stages/03_harmonization/data/analysis/stage4_topic_breakdown.csv` | `report/figures/fig03_paired_topic_composition.pdf` | ⚠️ **INPUT DATA HAS INFLATION** — `stage4_topic_breakdown.csv` counts question-subtopic assignments, not unique questions. Fig 3 needs regeneration with deduplicated source or dedup logic in the script. See `docs/validation/number_flow.md`. |

## Architecture Diagrams (D2)

| Figure ID | Title | Chapter | Source | Render Script | Output |
|-----------|-------|---------|--------|---------------|--------|
| Arch 1 | Pipeline Overview | Ch 4 (Method) or Appendix A | `assets/diagrams/pipeline_overview.d2` | TBD | `report/figures/arch01_pipeline_overview.pdf` |

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
- [ ] Arch 1 generated and reviewed
- [ ] All figures wired into chapter `.qmd` files
- [ ] Slides figure variants scoped
