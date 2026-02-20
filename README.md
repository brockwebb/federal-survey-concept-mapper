# Federal Survey Harmonization Research

The federal government already collects an enormous mosaic of survey data across the Census Bureau's demographic survey programs. AI-assisted harmonization analysis can reveal how to assemble that mosaic into a more complete picture — enabling cross-survey data enrichment without collecting a single additional data point — and can compress what traditionally takes months of expert review into weeks.

## Read This

📄 **[Master Report (PDF)](report/AI-Assisted-Federal-Survey-Harmonization.pdf)** — Classification of ~7,000 questions across 47 Census Bureau demographic surveys, overlap analysis, and harmonization results for CPS–ACS and FoodAPS–ACS pairs.

📄 **[Executive Fact Sheet (PDF)](fact_sheet/fact_sheet.pdf)** — One-page overview.

Report source: [`report/`](report/). Build: `cd report && quarto render`

## Key Results

The analysis identified 154 harmonizable questions (93 from CPS, 61 from FoodAPS) as candidate bridge variables for cross-survey data enrichment with ACS. Topic-level classification achieved Cohen's κ = 0.84; post-arbitration harmonization agreement reached κ = 0.843. A barrier taxonomy characterizes why the remaining questions cannot harmonize, creating a diagnostic tool for future survey design. Total API cost across all analysis stages was under $100.

## Companion Documents

- **TEVV Report** *(planned)* — Test, Evaluation, Verification & Validation documentation mapping pipeline measures to NIST AI RMF 1.0 trustworthiness characteristics. Includes a novel crosswalk between FCSM 20-04 and NIST AI RMF 1.0 — no published crosswalk between these frameworks currently exists. Working materials: [`docs/stages/tevv/`](docs/stages/tevv/)
- **Barrier Taxonomy** — [`report/appendices/B_taxonomy.qmd`](report/appendices/B_taxonomy.qmd) — Barrier codes (CC, TC, RS, PC, MC, PM) and feasibility tiers (F1/F2/F3)

## Pipeline Working Directories

The analysis progressed through three completed stages. The directories below contain lab notebooks and intermediate artifacts — not finished documents. The master report synthesizes these into a coherent narrative.

| Directory | Contents |
|-----------|----------|
| `docs/stages/01_classification/notes/` | Topic classification lab notes |
| `docs/stages/01_classification/data/` | Classification data artifacts (CSV, JSON) |
| `docs/stages/02_overlap/notes/` | Overlap analysis lab notes |
| `docs/stages/02_overlap/data/` | Pair generation data artifacts |
| `docs/stages/03_harmonization/notes/` | Barrier analysis lab notes |
| `docs/stages/03_harmonization/data/` | Barrier results, arbitration, analysis JSONs |
| `docs/stages/04_enrichment/` | Stage 4 planning (cross-survey enrichment discovery) |
| `docs/stages/tevv/` | TEVV working materials |
| `src/pipelines/` | Pipeline code |

## Repository Structure

```
├── report/                   # Master report (Quarto book)
├── fact_sheet/               # Executive one-page fact sheet
├── docs/
│   └── stages/               # Pipeline working materials
│       ├── 01_classification/
│       ├── 02_overlap/
│       ├── 03_harmonization/
│       ├── 04_enrichment/
│       └── tevv/
├── src/                      # Analysis code
├── data/                     # Source data
├── config/                   # Configuration files
└── archive/                  # Historical artifacts
```

## Data

Source data: ~7,000 questions from 47 publicly available Census Bureau demographic survey instruments. See [`data/raw/`](data/raw/).

## Setup

```bash
conda create -n survey-mapper python=3.10
conda activate survey-mapper
pip install -r requirements.txt
```

API keys required in `.env` for OpenAI, Anthropic, and Google (pipeline only).

## Building

```bash
cd report && quarto render
```

## License

Analysis code and methodology are original work. Source data is from publicly available federal survey instruments.
