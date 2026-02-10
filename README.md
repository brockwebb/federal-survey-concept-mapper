# Federal Survey Harmonization Research

**Thesis**: The federal government already collects an enormous mosaic of survey data across dozens of agencies. AI-assisted harmonization analysis can reveal how to assemble that mosaic into a more complete picture — enabling cross-survey data enrichment without collecting a single additional data point — and can compress what traditionally takes months of expert review into weeks.

📄 **[Executive Fact Sheet](reports/fact_sheet/)** — One-page plain-language overview for leadership ([PDF](reports/fact_sheet/_output/index.pdf))

## Research Overview

This project analyzes ~7,000 questions across 48 federal surveys to identify harmonization opportunities: overlapping questions that can serve as **bridge variables** for cross-survey data integration, increasing analytical power from existing collections. A secondary benefit: the same analysis identifies where instrument consolidation could reduce respondent burden.

The work demonstrates that AI-assisted classification (multi-model ensemble with arbitration) achieves strong inter-rater reliability (κ = 0.53–0.84 depending on classification level) at total API costs under $100, validating AI as a practical accelerant for survey methodology research.

## Research Journey

The project progresses through four reports, each building on the prior:

### Report 01 — LLM Concept Mapping
*Can AI reliably categorize federal survey questions into a unified taxonomy?*

Dual-LLM classification (Claude Haiku 4.5, GPT-5-mini) of 6,987 questions across 48 surveys into a hierarchical Census-derived taxonomy. Established that LLMs achieve high agreement (Cohen's κ = 0.84) on concept categorization, producing a master cross-survey concept map. Also documented that embedding-based clustering fails for this domain due to extreme baseline similarity (99.16%) in standardized government language.

- **Report**: [`reports/01_llm_concept_mapping/`](reports/01_llm_concept_mapping/)
- **Output data**: [`output/report_01/`](output/report_01/)

### Report 02 — Question-Level Consolidation Analysis
*Where do specific survey questions overlap, and can AI identify consolidation candidates at the question level?*

Developed pairwise question matching for CPS-ACS and FoodAPS-ACS survey pairs. Multi-model comparison across rater generations, fuzzy matching baselines, and LLM classification. Produced 1,598 candidate pairs for detailed harmonization analysis.

- **Report**: [`reports/02_question_consolidation/`](reports/02_question_consolidation/)
- **Output data**: [`output/report_02/`](output/report_02/)

### Report 03 — Harmonization Constraints Analysis
*What specific barriers prevent harmonization, and what does that tell us about cross-survey data enrichment potential?*

Three-rater ensemble (OpenAI, Anthropic, Google) with multi-model arbitration to classify harmonization barriers across 1,598 pairs. Key findings: ~44% of questions are harmonizable (bridge-variable quality), with ~11% directly consolidable. Barrier taxonomy (Construct/Concept, Temporal/Collection, Reference/Scope, Practical/Cost) characterizes precisely where linkage works and where it doesn't. Discovered significant behavioral differences between LLM arbitrators (synthesis rates: Google 7%, OpenAI 59%, Anthropic 77%).

- **Report**: [`reports/03_harmonization_constraints/`](reports/03_harmonization_constraints/)
  - Full Quarto report: [`reports/03_harmonization_constraints/report/`](reports/03_harmonization_constraints/report/)
  - Slide decks: [`reports/03_harmonization_constraints/presentation/`](reports/03_harmonization_constraints/presentation/)
- **Output data**: [`output/report_03/`](output/report_03/)
- **Pipeline code**: [`src/pipelines/`](src/pipelines/) (Stages 1–5)
- **Analysis scripts**: [`src/scripts/`](src/scripts/)

### Report 04 — Cross-Survey Enrichment Discovery *(Planned)*
*Can AI discover multi-hop enrichment pathways across the full federal survey topology?*

Will extend analysis to the full survey network, using AI to identify connection patterns (multi-hop bridge variables) that exceed human working memory limitations. Validates AI classifications empirically using public microdata from CPS and ACS (IPUMS) to test whether "harmonizable" pairs show comparable response distributions.

- **Report**: [`reports/04_empirical_validation/`](reports/04_empirical_validation/)
- **Vision doc**: [`docs/project/REPORT_04_VISION_cross_survey_enrichment.md`](docs/project/REPORT_04_VISION_cross_survey_enrichment.md)

## Repository Structure

```
├── reports/                  # Report source files (Quarto/Markdown)
│   ├── fact_sheet/           # Executive one-pager (Quarto → PDF)
│   ├── 01_llm_concept_mapping/
│   ├── 02_question_consolidation/
│   ├── 03_harmonization_constraints/
│   └── 04_empirical_validation/
├── output/                   # Generated outputs per report
│   ├── report_01/            # Master dataset, visualizations, comparisons
│   ├── report_02/            # Question matching results, treemaps
│   ├── report_03/            # Barrier analysis, arbitration, stage 1-4 outputs
│   └── report_04/            # (empty, planned)
├── src/
│   ├── core/                 # Report 01-02 scripts
│   ├── pipelines/            # Report 03 modular pipeline (stages 1-5)
│   ├── scripts/              # Report 03 analysis scripts
│   ├── lib/                  # Shared utilities (IO, stats, taxonomy)
│   ├── notebooks/            # Exploratory Jupyter notebooks
│   └── report_02/            # Report 02 build tools
├── data/
│   ├── raw/                  # Original survey question CSVs
│   └── processed/            # Cleaned, melted, embedded data
├── config/                   # Taxonomy, pipeline configs
├── docs/
│   ├── project/              # Strategic docs, handoffs, vision
│   ├── report_01/            # Report 01 planning docs
│   ├── report_02/            # Report 02 methodology docs
│   └── report_03/            # Report 03 specs, findings, literature
├── handoffs/                 # Session continuity documents
├── cc_tasks/                 # Claude Code task files
└── archive/                  # Superseded outputs and stale figures
```

## Data

Source data: ~7,000 questions from 48 publicly available federal survey instruments. See [`data/raw/`](data/raw/).

## Setup

```bash
conda create -n survey-mapper python=3.10
conda activate survey-mapper
pip install -r requirements.txt
```

API keys required in `.env` for OpenAI, Anthropic, and Google (Report 03 pipeline only).

## Key Strategic Documents

- [Strategic Reframe: Enrichment over Consolidation](docs/project/STRATEGIC_REFRAME_enrichment_over_consolidation.md) — Why data enrichment, not consolidation, is the primary value proposition
- [Report 04 Vision](docs/project/REPORT_04_VISION_cross_survey_enrichment.md) — Next phase design
- [Pipeline Documentation](docs/project/pipeline_documentation.md) — Report 03 technical architecture
- [Embedding Failure Lessons](docs/project/lessons_learned_embedding_failure.md) — Why embeddings don't work for standardized government language

## Building Reports

All reports are compiled from **section source files** using [Quarto](https://quarto.org/). Do not edit rendered outputs directly — edit the section files under each report's `sections/` directory, then re-render.

| Deliverable | Source Directory | Render Command |
|:---|:---|:---|
| **Fact Sheet** (PDF) | `reports/fact_sheet/` | `cd reports/fact_sheet && quarto render` |
| **Report 02** (PDF + HTML) | `reports/02_question_consolidation/` | `cd reports/02_question_consolidation && quarto render` |
| **Report 03 — Report** (PDF + HTML) | `reports/03_harmonization_constraints/report/` | `cd reports/03_harmonization_constraints/report && quarto render` |
| **Report 03 — Slides** (RevealJS) | `reports/03_harmonization_constraints/presentation/` | `cd reports/03_harmonization_constraints/presentation && quarto render` |

Report 01 (`reports/01_llm_concept_mapping/`) does not yet have a Quarto build — it is structured as standalone markdown sections.

Outputs land in each directory's `_output/` folder. The `_quarto.yml` in each directory defines the chapter order, format options, and bibliography. If you add or reorder sections, update `_quarto.yml` to match.

## License

Analysis code and methodology are original work. Source data is from publicly available federal survey instruments.
