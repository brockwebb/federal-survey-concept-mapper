# Master Report — Figure Map

**Purpose:** Every figure in the master report traced to its producing script, input data, output location, and chapter reference.  
**Convention:** All figure scripts live in `src/figures/`. All outputs go to `report/figures/`. All scripts import style from `assets/census_plot_style.py` (symlink → `central_library/style/census_plot_style.py`).  
**Last updated:** 2026-03-01

---

## Figures

| Figure ID | Title | Chapter | Script | Input Data | Output |
|-----------|-------|---------|--------|------------|--------|
| Fig 1 | Topic Distribution | Ch 2 (Classification) | `src/figures/fig01_topic_distribution.py` | NUMBERS_MAP Step 2 (validated from `docs/stages/01_classification/data/comparison/topic_distribution.csv`) | `report/figures/fig01_topic_distribution.pdf` + `.png` | ✅ Generated 2026-03-01. Horizontal bar chart, sorted descending. xdgov qualitative palette via `src/figures/topic_colors.py`. |
| Fig 2 | Total Questions by Survey — ACS Family | Ch 3 (Survey Overlap) | `src/figures/fig02_acs_family_profile.py` | `docs/validation/question_counts.json` (validated from `data/raw/PublicSurveyQuestionsMap.csv`) | `report/figures/fig02_acs_family_profile.pdf` |
| Fig 3 | Topic Composition of Evaluated Question Pairs | Ch 4 or Ch 5 (Method/Results) | `src/figures/fig03_paired_topic_composition.py` | `docs/stages/03_harmonization/data/analysis/stage4_topic_breakdown.csv` | `report/figures/fig03_paired_topic_composition.pdf` | ⚠️ **INPUT DATA HAS INFLATION** — `stage4_topic_breakdown.csv` counts question-subtopic assignments, not unique questions. Fig 3 needs regeneration with deduplicated source or dedup logic in the script. See `docs/validation/number_flow.md`. |

## Architecture Diagrams (PaperBanana + D2)

PaperBanana diagrams: method spec → `paperbanana generate` → PNG. See CLAUDE.md "Diagrams Are Built From Source" for full workflow.

**⚠️ ALL PRIOR RUNS PRODUCED UNUSABLE OUTPUT** (gibberish text, hallucinated labels). Method specs corrected 2026-03-01 with V&V-verified numbers. All architecture diagrams require regeneration. See `assets/diagrams/paperbanana/HANDOFF_next_thread.md` for root cause analysis.

| Figure ID | Title | Chapter | Method Spec | Deployed Output | Provenance Run | Status |
|-----------|-------|---------|-------------|-----------------|----------------|--------|
| Arch 1 | Pipeline Overview | Appendix A | `assets/diagrams/paperbanana/pipeline_overview_method.txt` | `assets/diagrams/fig_pipeline_overview.png` | — | **needs regeneration** — spec corrected 2026-03-01 (cost junk removed, routing % fixed) |
| Arch 2 | Stage 1: Classification | Appendix A | `assets/diagrams/paperbanana/stage1_classification_method.txt` | `assets/diagrams/fig_stage1_classification.png` | — | **needs regeneration** — spec corrected 2026-03-01 (routing 68.5%, arb count 1,368, output 6,954/6,987, cost junk removed) |
| Arch 3 | Stage 2: Overlap and Pairing | Appendix A | `assets/diagrams/paperbanana/stage2_overlap_method.txt` | `assets/diagrams/fig_stage2_overlap.png` | — | **needs regeneration** — spec verified correct, prior output was garbage |
| Arch 4 | Stage 3: Barrier Rating | Appendix A | `assets/diagrams/paperbanana/stage3_rating_method.txt` | `assets/diagrams/fig_stage3_rating.png` | — | **needs regeneration** — spec verified correct, prior output was garbage |
| Arch 5 | Stage 4: Arbitration | Appendix A | `assets/diagrams/paperbanana/stage4_arbitration_method.txt` | `assets/diagrams/fig_stage4_arbitration.png` | — | **needs regeneration** — spec verified correct, prior output was garbage |
| Arch 6 | Stage 5: Results | Appendix A | `assets/diagrams/paperbanana/stage5_results_method.txt.HOLD` | — | — | ON HOLD — pending design discussion |

**D2 diagrams (if any):**

| Figure ID | Title | Chapter | Source | Output |
|-----------|-------|---------|--------|--------|
| (none yet) | | | `assets/diagrams/*.d2` | `report/figures/*.pdf` |

## Style

- **Palette:** U.S. Census Bureau xdgov Data Design Standards (Section 508 compliant)
- **Topic color mapping:** `src/figures/topic_colors.py` — canonical topic→hex color assignment for all report figures. Every figure script imports from here to ensure consistent colors across the report. Five topics: Economic (#112E51 navy), Social (#0095A8 teal), Housing (#FF7043 orange), Demographic (#2E78D2 blue), Government (#78909C grey).
- **Pragmatics style module:** `assets/census_plot_style.py` → plotnine-based, used by pragmatics/census-mcp figures. Not used by report figures (which use matplotlib).
- **Output format:** PDF + PNG, 300 DPI, 6.5in max width
- **D2 diagrams:** `.d2` source in `assets/diagrams/`, rendered to PDF/SVG in `report/figures/`

## Slides

Slide figures will be derived from the same scripts with adjusted dimensions. Mapping TBD when slides are scoped.

---

## Checklist

- [ ] Symlink created: `assets/census_plot_style.py`
- [x] Fig 1 generated and reviewed (2026-03-01)
- [ ] Fig 2 generated and reviewed
- [ ] Fig 3 generated and reviewed — ⚠️ BLOCKED: input data inflated, needs corrected source
- [ ] D2 installed (`brew install d2`)
- [ ] Arch 1–5 specs corrected with V&V-verified numbers (2026-03-01) — need regeneration
- [ ] Arch 6 on hold
- [ ] All figures wired into chapter `.qmd` files
- [ ] Slides figure variants scoped
