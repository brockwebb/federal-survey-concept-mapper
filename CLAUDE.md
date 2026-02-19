# Federal Survey Concept Mapper — Project Guide

## Critical Reference Documents

- **`docs/NUMBERS_MAP.md`** — Single source of truth for every key number. Traces all metrics to their source files/JSON paths. ALWAYS check this before citing any number in reports or deliverables.
- **`docs/SCRIPT_ARTIFACT_MAP.md`** — Maps every generated figure, table, and analysis output to the script that produces it and its input data.
- **`reports/master/NARRATIVE_CHECKLIST.md`** — Lightweight V&V checklist for the master report. Every claim, its supporting number, and the source. Quick-check version of NUMBERS_MAP.

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

## Report Structure (post-restructure Feb 2026)

```
reports/
├── master/                     # THE master report (Quarto book)
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
├── tevv/                       # TEVV companion doc (skeleton)
├── methodology/                # Methodology companion doc (skeleton)
├── fact_sheet/                 # Approved fact sheet (stays as-is)
└── 04_empirical_validation/    # Report 04 (TBD)

archive/research_notes/         # Former Reports 01, 02, 03
├── 01_llm_concept_mapping/
├── 02_question_consolidation/
└── 03_harmonization_constraints/
```

## Repository Layout

```
├── data/
│   ├── raw/                    # Input data (untouched)
│   └── processed/              # Pipeline outputs (CSV, JSONL, embeddings)
├── src/
│   ├── core/                   # Report 01/02 era scripts
│   ├── pipelines/              # Report 03+ pipeline stages (01-05)
│   ├── scripts/                # One-off analysis scripts
│   ├── lib/                    # Shared utilities (io_utils, stats, taxonomy)
│   ├── notebooks/              # Jupyter exploration notebooks
│   └── report_02/              # Report 02 build scripts
├── output/
│   ├── report_01/              # Report 01 analysis artifacts
│   ├── report_02/              # Report 02 analysis artifacts
│   ├── report_03/              # Report 03 analysis artifacts
│   │   ├── analysis/           # JSON, CSV analysis files
│   │   ├── visuals/            # Generated figures
│   │   └── ...
│   └── report_04/              # Report 04 (TBD)
├── reports/                    # ONLY publishable Quarto content
├── config/                     # Configuration files (report_03.yaml)
├── docs/                       # NUMBERS_MAP, SCRIPT_ARTIFACT_MAP
├── archive/                    # Old/superseded artifacts + research notes
├── handoffs/                   # Session handoff documentation
└── cc_tasks/                   # Claude Code task planning files
```

## Active Task Roadmap

**File:** `reports/master/TASK_ROADMAP.md` — 31 tasks across 7 blocks, risk-prioritized.

Check TASK_ROADMAP.md for current status. Do NOT duplicate status here — that's how stale data happens.

**Critical distinction:** Barrier taxonomy (classification scheme for results) ≠ TEVV (evidence the methodology is trustworthy). They connect at ONE point: SME review validates classification accuracy. Do not conflate.

## Key Principles
- **Source vs Generated**: `src/` has code, `output/` has generated artifacts
- **One canonical location**: Each file type lives in exactly one place
- **reports/ = publishable only**: No pipeline code, data, or scripts
- **Figures via symlinks**: reports/ reference output/ figures via relative symlinks
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
