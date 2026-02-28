# Federal Survey Concept Mapper — Project Guide

## Critical Reference Documents

- **`docs/NUMBERS_MAP.md`** — Single source of truth for every key number. Traces all metrics to their source files/JSON paths. ALWAYS check this before citing any number in reports or deliverables.
- **`docs/SCRIPT_ARTIFACT_MAP.md`** — Maps every generated figure, table, and analysis output to the script that produces it and its input data.
- **`docs/FIGURE_MAP.md`** — Master report figure traceability: script, input data, output file, chapter reference, and style convention for every figure and architecture diagram.
- **`docs/validation/question_counts.json`** — Validated question counts per instrument and survey program, computed from raw data. All figure scripts read from this file, not hardcoded values.
- **`src/validation/validate_complete.py`** — Complete validation suite (~80 checks). Run after ANY number change. Validates raw data, pairing chain, rating metrics, dedup, ACS-side, round-trip traces, arithmetic, and cross-document consistency. Exit 0=pass, 1=fail, 2=warn.
- **`report/NARRATIVE_CHECKLIST.md`** — Lightweight V&V checklist for the master report. Every claim, its supporting number, and the source. Quick-check version of NUMBERS_MAP.

## Project Scope (DO NOT DEVIATE)

- **47 Census Bureau demographic survey instruments** (not 48, not "federal surveys" broadly)
- **~7,000 questions** (6,987 deduplicated from 7,419 raw)
- **NOT cross-agency** — Census Bureau only
- ACS is the anchor survey for harmonization comparisons
- CPS and FoodAPS are the two source surveys evaluated so far

## Narrative Arc

1. Classify ~7,000 questions by Census topic/subtopic (Ch 2)
2. Identify concept overlap across surveys, select ACS as anchor (Ch 3)
3. Pair overlapping questions, evaluate harmonization feasibility with barrier taxonomy (Ch 4)
4. Collapse pairs to question-level results: source questions with harmonization paths reported per survey (Ch 5). See NUMBERS_MAP for current rates.
5. Expert validation and multi-hop enrichment discovery (Report 04, TBD)

## Deliverables and Working Materials (post-restructure Feb 2026)

**Two deliverables at top level:**
```
├── report/                     # THE master report (Quarto book) — the only Quarto build target
│   ├── _quarto.yml
│   ├── index.qmd
│   ├── NARRATIVE_CHECKLIST.md  # V&V checklist
│   ├── chapters/
│   │   ├── 01_introduction.qmd
│   │   ├── 02_classification.qmd
│   │   ├── 03_survey_overlap.qmd
│   │   ├── 04_pairwise_harmonization.qmd
│   │   ├── 05_results.qmd
│   │   ├── 06_implications.qmd
│   │   └── 07_limitations.qmd
│   └── appendices/
│       ├── A_architecture.qmd
│       ├── B_taxonomy.qmd
│       └── C_tevv.qmd
└── fact_sheet/                 # Executive one-page fact sheet (approved deliverable)

**Working materials under docs/stages/:**
docs/stages/
├── 01_classification/          # Stage 1: Topic classification
│   ├── notes/                  # Lab notebooks
│   └── data/                   # Classification results
├── 02_overlap/                 # Stage 2: Question overlap analysis
│   ├── notes/                  # Lab notebooks
│   └── data/                   # Pair generation results
├── 03_harmonization/           # Stage 3: Harmonization constraints
│   ├── notes/                  # Lab notebooks
│   └── data/                   # Barrier analysis results
├── 04_enrichment/              # Stage 4: Cross-survey enrichment (planned)
└── tevv/                       # TEVV documentation working materials

**Archived content:**
archive/research_notes/         # Historical lab notes from early development
├── 01_llm_concept_mapping/
├── 02_question_consolidation/
└── 03_harmonization_constraints/
```

## Repository Layout

```
├── report/                     # Master report (Quarto book) — the only Quarto build target
├── fact_sheet/                 # Executive one-page fact sheet
├── docs/
│   ├── stages/                 # Pipeline working materials (see "Deliverables and Working Materials" above)
│   │   ├── 01_classification/  # notes/ + data/ for Stage 1
│   │   ├── 02_overlap/         # notes/ + data/ for Stage 2
│   │   ├── 03_harmonization/   # notes/ + data/ for Stage 3
│   │   ├── 04_enrichment/      # Stage 4 planning
│   │   └── tevv/               # TEVV working materials
│   ├── NUMBERS_MAP.md
│   ├── SCRIPT_ARTIFACT_MAP.md
│   └── ...other project docs...
├── data/
│   ├── raw/                    # Input data (untouched)
│   └── processed/              # Pipeline outputs (CSV, JSONL, embeddings)
├── src/
│   ├── core/                   # Report 01/02 era scripts
│   ├── pipelines/              # Pipeline stages (01-05)
│   ├── scripts/                # One-off analysis scripts
│   ├── lib/                    # Shared utilities (io_utils, stats, taxonomy)
│   ├── notebooks/              # Jupyter exploration notebooks
│   └── report_02/              # Report 02 build scripts
├── config/                     # Configuration files (report_03.yaml)
├── docs/                       # NUMBERS_MAP, SCRIPT_ARTIFACT_MAP
├── archive/                    # Old/superseded artifacts + historical research notes
├── handoffs/                   # Session handoff documentation
└── cc_tasks/                   # Claude Code task planning files
```

## Active Task Roadmap

**File:** `report/TASK_ROADMAP.md` — 31 tasks across 7 blocks, risk-prioritized.

Check TASK_ROADMAP.md for current status. Do NOT duplicate status here — that's how stale data happens.

**Critical distinction:** Barrier taxonomy (classification scheme for results) ≠ TEVV (evidence the methodology is trustworthy). They connect at ONE point: SME review validates classification accuracy. Do not conflate.

## Key Principles
- **Source vs Generated**: `src/` has code, `docs/stages/0X_*/data/` has generated artifacts
- **One canonical location**: Each file type lives in exactly one place
- **report/ = the only Quarto build target**: Build: `cd report && quarto render`
- **Data lives with its stage**: Pipeline data under `docs/stages/01_classification/data/`, `docs/stages/02_overlap/data/`, `docs/stages/03_harmonization/data/`
- **Figures via symlinks**: report/ references stage data figures via relative symlinks
- **All model names from config**: `config/report_03.yaml` — NEVER hardcode
- **Numbers from NUMBERS_MAP**: Every metric traces to a source file

## Pipeline Stages (Report 03)
1. `src/pipelines/01_barrier_pipeline.py` — Barrier classification (3 LLM raters)
2. `src/pipelines/02_arbitration_pipeline.py` — Disagreement arbitration (3 LLM arbitrators)
3. `src/pipelines/03_analysis_pipeline.py` — Agreement analysis & metrics
4. `src/pipelines/04_findings_pipeline.py` — Question-level findings & rollup
5. `src/pipelines/05_deliverables_pipeline.py` — Report generation

## Shared Library
- `src/lib/io_utils.py` — File I/O helpers
- `src/lib/stats.py` — Statistical functions (kappa, agreement)
- `src/lib/taxonomy.py` — Barrier taxonomy definitions

## Figure Style Convention
- **Style source**: `assets/census_plot_style.py` (symlink → `central_library/style/census_plot_style.py`)
- **Import**: `from census_plot_style import COLORS, paper_theme, save_figure`
- **Palette**: U.S. Census Bureau xdgov Data Design Standards, Section 508 compliant
- **Output**: PDF at 300 DPI, 6.5in max width (letter paper with 1in margins)
- **Theme**: `paper_theme()` — serif font, minimal grid, bottom legend
- **Writing conventions**: Follow `central_library/crosswalks/fcsm_nist/WRITING_CONVENTIONS.md`
- **No bold in prose, no em dashes, no "novel," no throat-clearing, no self-congratulation**
- Figure scripts go in `src/figures/`, outputs go in `report/figures/`
