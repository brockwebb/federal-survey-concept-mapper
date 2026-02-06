# Repo Restructure Migration Plan

**Date:** 2026-02-06
**Goal:** Untangle the rat-nested maze into a clean, navigable structure.

## Principles

1. **Separate source from generated** — build artifacts never committed
2. **One canonical location per thing** — no duplicate figures/data
3. **`reports/` = publishable content ONLY** — no pipeline code, no data, no scripts
4. **`src/` = all code** — organized by report/phase
5. **`output/` = all generated analysis** — organized by report
6. **Preserve git history** — use `git mv` everywhere possible

## Target Structure

```
federal-survey-concept-mapper/
├── CLAUDE.md                       # Updated project-level guidance
├── README.md
├── requirements.txt
├── .gitignore                      # Massively expanded
│
├── config/
│   ├── canonical_format.json
│   ├── census_taxonomy.yaml
│   └── report_03.yaml              # Was reports/03/config.yaml
│
├── data/
│   ├── raw/                        # Original untouched input files
│   ├── processed/                  # Cleaned/derived data
│   └── reference/                  # Taxonomies, lookup tables
│
├── src/
│   ├── report_01/                  # Report 01 pipeline code (minimal)
│   ├── report_02/                  # Report 02 pipeline code
│   │   ├── build_report.py
│   │   ├── generate_treemaps.py
│   │   └── render_mermaid.py
│   ├── report_03/                  # Report 03 pipeline code
│   │   ├── pipelines/              # Main pipeline stages
│   │   │   ├── 01_barrier_pipeline.py
│   │   │   ├── 02_arbitration_pipeline.py
│   │   │   ├── 03_stage2_agreement.py
│   │   │   ├── 03b_stage2_extended.py
│   │   │   ├── 04_findings_pipeline.py
│   │   │   ├── 05_deliverables_pipeline.py
│   │   │   ├── run_pipeline.py
│   │   │   └── run_full_pipeline.py
│   │   ├── scripts/                # Analysis scripts
│   │   │   ├── lib/
│   │   │   └── *.py
│   │   └── CLAUDE.md               # Report 03 session guidance
│   ├── core/                       # Report 01 original pipeline scripts
│   │   ├── categorize_claude.py
│   │   ├── categorize_openai.py
│   │   ├── compare_llm_results.py
│   │   ├── run_pipeline.py
│   │   └── ...
│   └── notebooks/                  # Exploratory notebooks
│       └── *.ipynb
│
├── output/                         # ALL generated analysis outputs
│   ├── report_01/                  # Report 01 outputs
│   ├── report_02/                  # Report 02 outputs
│   │   └── data/                   # Analysis CSVs/JSONs
│   ├── report_03/                  # Report 03 outputs
│   │   ├── analysis/               # All analysis files
│   │   ├── checkpoints/            # API checkpoints
│   │   ├── results/                # Raw API results
│   │   └── visuals/                # Generated figures
│   └── archive/                    # Old runs (gpt4omini_error etc)
│
├── reports/                        # PUBLISHABLE CONTENT ONLY
│   ├── 01_llm_concept_mapping/
│   │   ├── sections/               # Markdown source
│   │   ├── figures/ → ../../output/report_01/figures  (symlink)
│   │   └── _quarto.yml
│   ├── 02_question_consolidation/
│   │   ├── sections/
│   │   ├── diagrams/               # Mermaid source files
│   │   ├── figures/ → ../../output/report_02/figures  (symlink)
│   │   ├── index.qmd
│   │   └── _quarto.yml
│   ├── 03_harmonization_constraints/
│   │   ├── report/
│   │   │   ├── sections/
│   │   │   ├── figures/ → ../../../output/report_03/visuals  (symlink)
│   │   │   ├── index.qmd
│   │   │   └── _quarto.yml
│   │   └── presentation/
│   │       ├── slides.qmd
│   │       ├── slides_3a_findings.qmd
│   │       ├── slides_3b_methodology.qmd
│   │       ├── images/ → ../../../output/report_03/visuals  (symlink)
│   │       └── _quarto.yml
│   └── 04_empirical_validation/    # Future
│
├── docs/
│   ├── project/                    # Top-level project docs
│   │   ├── REPORT_04_VISION_cross_survey_enrichment.md
│   │   ├── STRATEGIC_REFRAME_enrichment_over_consolidation.md
│   │   ├── lessons_learned_embedding_failure.md
│   │   └── pipeline_documentation.md
│   └── report_03/                  # Report 03 methodology docs
│       ├── methodology_log.md
│       ├── ANALYSIS_VV_PLAN.md
│       ├── FINDINGS_*.md
│       ├── SPEC_*.md
│       ├── literature/
│       └── ...
│
└── archive/                        # Clearly dead stuff
    └── output_gpt4omini_error/
```

## What Gets Deleted (not moved)

- `reports/03/presentation/_output/` — Quarto build artifacts (10x duplicate libs!)
- `reports/03/report/_output/` — Quarto HTML build output
- `reports/02/_output/` — Quarto HTML build output  
- `reports/03/presentation/slides_files/libs 2` through `libs 10` — corrupt duplicates
- All `.quarto/` directories — IDE cache
- `*.aux`, `*.log`, `*.toc`, `*.tex` — LaTeX intermediates
- `reports/03/report/index_files/` — empty mediabag dirs
- `reports/03/report/report/` — nested empty report dir
- `reports/03/presentation/*_SUMMARY.md` (8 files) — change tracking docs, superseded

## Migration Phases

### Phase 0: Commit current state
- Ensure clean working tree before restructure

### Phase 1: Delete build artifacts  
- Remove all `_output/` dirs, `.quarto/`, LaTeX intermediates
- Remove duplicate `libs N` directories
- Update `.gitignore` to prevent re-commitment

### Phase 2: Move code → src/
- Report 03 pipelines → `src/report_03/pipelines/`
- Report 03 scripts → `src/report_03/scripts/`
- Report 02 scripts → `src/report_02/`
- Original src/ scripts → `src/core/`
- Notebooks → `src/notebooks/`

### Phase 3: Move data/output → output/
- Report 03 `output/` → `output/report_03/`
- Report 03 `data/` → stays or merges with top-level `data/`
- Report 02 `data/` → `output/report_02/data/`
- Report 03 archive → `output/archive/`
- Top-level `output/` reorganized

### Phase 4: Clean reports/
- Strip everything except publishable markdown, .qmd, _quarto.yml
- Create symlinks for figures
- Remove tracking/summary markdown files from presentation/

### Phase 5: Move docs
- Report 03 `docs/` → `docs/report_03/`
- Top-level `docs/` → `docs/project/`
- Report 03 config → `config/`

### Phase 6: Update references
- Update CLAUDE.md with new paths
- Update any hardcoded paths in pipeline scripts
- Test Quarto renders still work

## Risks

1. **Quarto path references** — slides.qmd references `images/` which will become symlinks
2. **Pipeline imports** — scripts may have relative imports that break
3. **Git submodule-like behavior** — Report 03 has its own CLAUDE.md, may confuse Claude Code
4. **Symlinks on Windows** — if anyone clones on Windows, symlinks may not work

## Rollback

Before migration: `git tag pre-restructure`
If anything breaks: `git reset --hard pre-restructure`
