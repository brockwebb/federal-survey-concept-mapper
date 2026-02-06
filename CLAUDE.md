# Federal Survey Concept Mapper — Project Guide

## Repository Layout (post-restructure)

```
├── data/
│   ├── raw/                    # Input data (untouched)
│   ├── processed/              # Pipeline outputs (CSV, JSONL)
│   └── reference/              # Lookup tables, taxonomies
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
│   │   ├── checkpoints/        # API call checkpoints
│   │   ├── results/            # Raw API results
│   │   ├── visuals/            # Generated figures
│   │   └── pdf/                # Rendered slide PDFs
│   └── report_04/              # Report 04 (empirical validation)
├── reports/                    # ONLY publishable Quarto content
│   ├── 01_llm_concept_mapping/
│   ├── 02_question_consolidation/
│   ├── 03_harmonization_constraints/
│   │   ├── report/             # Quarto report
│   │   └── presentation/       # Quarto slides
│   └── 04_empirical_validation/
├── docs/                       # Project-level docs, methodology logs
├── config/                     # Configuration files
└── archive/                    # Old/superseded artifacts
```

## Key Principles
- **Source vs Generated**: `src/` has code, `output/` has generated artifacts
- **One canonical location**: Each file type lives in exactly one place
- **reports/ = publishable only**: No pipeline code, data, or scripts
- **Figures via symlinks**: reports/ reference output/ figures via relative symlinks

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

## Import Convention
After restructure, imports use:
```python
from src.lib.stats import compute_kappa
from src.lib.io_utils import load_jsonl
```

## Rollback
```bash
git reset --hard pre-restructure
```
