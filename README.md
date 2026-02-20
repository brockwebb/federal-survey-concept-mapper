# Federal Survey Harmonization Research

**Thesis**: The federal government already collects an enormous mosaic of survey data across the Census Bureau's demographic survey programs. AI-assisted harmonization analysis can reveal how to assemble that mosaic into a more complete picture — enabling cross-survey data enrichment without collecting a single additional data point — and can compress what traditionally takes months of expert review into weeks.

📄 **[Executive Fact Sheet](output/fact_sheet/fact_sheet.pdf)** — One-page plain-language overview for leadership

## Primary Deliverable

📄 **Master Report**: [`reports/master/`](reports/master/) — Consolidated narrative covering classification, overlap analysis, and harmonization results across CPS-ACS and FoodAPS-ACS pairs. Build: `cd reports/master && quarto render`

## Key Results

Analyzed ~7,000 questions across 47 Census Bureau demographic surveys. Assessed harmonization potential for 164 CPS questions and 123 FoodAPS questions that share Census topic overlap with ACS. Found 154 questions (93 CPS, 61 FoodAPS) with viable harmonization paths — enabling cross-survey data enrichment through bridge variables. Multi-model AI rating achieved high post-arbitration agreement (κ = 0.843 on feasibility ratings). Total API cost under $100, demonstrating AI feasibility assessment can scale across the full federal survey topology at costs infeasible for manual expert review.

## Research Journey

The project progresses through four reports, each building on the prior:

### Report 01 — LLM Concept Mapping

*Can AI reliably categorize federal survey questions into a unified taxonomy?*

Dual-LLM classification (Claude Haiku 4.5, GPT-5-mini) of 6,987 questions across 47 Census Bureau demographic surveys into a hierarchical Census-derived taxonomy. Established that LLMs achieve high topic-level agreement (Cohen's κ = 0.84) on concept categorization, producing a master cross-survey concept map. Also documented that embedding-based clustering fails for this domain due to extreme baseline similarity (99.16%) in standardized government language.

- **Research notes**: [`archive/research_notes/01_llm_concept_mapping/`](archive/research_notes/01_llm_concept_mapping/)
- **Output data**: [`output/report_01/`](output/report_01/)

### Report 02 — Question-Level Consolidation Analysis

*Where do specific survey questions overlap, and can AI identify consolidation candidates at the question level?*

Developed pairwise question matching for CPS-ACS and FoodAPS-ACS survey pairs. Multi-model comparison across rater generations, fuzzy matching baselines, and LLM classification. Produced 1,598 candidate pairs for detailed harmonization analysis.

- **Research notes**: [`archive/research_notes/02_question_consolidation/`](archive/research_notes/02_question_consolidation/)
- **Rendered report**: [`output/report_02/FULL_REPORT.pdf`](output/report_02/FULL_REPORT.pdf)
- **Output data**: [`output/report_02/`](output/report_02/)

### Report 03 — Harmonization Constraints Analysis

*What specific barriers prevent harmonization, and what does that tell us about cross-survey data enrichment potential?*

Three-rater ensemble (OpenAI gpt-5-mini, Anthropic claude-haiku-4.5, Google gemini-3-flash) with three-arbitrator ensemble for disagreements. Classified 1,598 question pairs using a six-category barrier taxonomy (TC: Temporal/Collection, CC: Concept/Construct, RS: Reference/Scope, PC: Practical/Cost, MC: Measurement Constraints, PM: Pathway Mismatch) with three-tier feasibility ratings (F1: direct recode, F2: statistical adjustment, F3: incompatible). Found 154 harmonizable questions across 287 unique source questions assessed. Discovered significant behavioral differences between LLM arbitrators (synthesis rates: Google 7%, OpenAI 59%, Anthropic 77%).

- **Research notes**: [`archive/research_notes/03_harmonization_constraints/`](archive/research_notes/03_harmonization_constraints/)
- **Rendered slides**: [`output/report_03/pdf/`](output/report_03/pdf/) (findings, methodology, combined)
- **Output data**: [`output/report_03/`](output/report_03/)
- **Pipeline code**: [`src/pipelines/`](src/pipelines/) (Stages 1–5)
- **Analysis scripts**: [`src/scripts/`](src/scripts/)

### Report 04 — Cross-Survey Enrichment Discovery *(Planned)*

*Can AI discover multi-hop enrichment pathways across the full federal survey topology?*

Will extend analysis to the full 47-survey network, discovering multi-hop integration paths (Survey A → B → C) where direct harmonization is not possible but indirect linkage through intermediate surveys enables cross-survey enrichment. Focuses on identifying connection patterns that exceed human working memory limitations in multi-survey network analysis.

- **Report source**: [`reports/04_empirical_validation/`](reports/04_empirical_validation/)
- **Vision doc**: [`docs/project/REPORT_04_VISION_cross_survey_enrichment.md`](docs/project/REPORT_04_VISION_cross_survey_enrichment.md)

## Repository Structure

```
├── report_builder.py         # Build individual reports (python report_builder.py)
├── reports/
│   ├── master/                # PRIMARY: Consolidated narrative report (Quarto book)
│   ├── tevv/                  # TEVV methodology + FCSM × NIST crosswalk
│   ├── fact_sheet/            # Executive one-pager (Quarto → PDF)
│   └── 04_empirical_validation/
├── archive/
│   └── research_notes/        # Reports 01-03 research notes (superseded by master)
│       ├── 01_llm_concept_mapping/
│       ├── 02_question_consolidation/
│       └── 03_harmonization_constraints/
├── output/                    # Committed deliverables and data per report
│   ├── fact_sheet/            # Rendered fact sheet PDF
│   ├── report_01/             # Master dataset, visualizations, comparisons
│   ├── report_02/             # Full report PDF, question matching results
│   ├── report_03/             # Slide PDFs, barrier analysis, stage outputs
│   └── report_04/             # (planned)
├── src/
│   ├── core/                  # Report 01-02 scripts
│   ├── pipelines/             # Report 03 modular pipeline (stages 1-5)
│   ├── scripts/               # Report 03 analysis scripts
│   ├── lib/                   # Shared utilities (IO, stats, taxonomy)
│   ├── notebooks/             # Exploratory Jupyter notebooks
│   └── report_02/             # Report 02 build tools
├── data/
│   ├── raw/                   # Original survey question CSVs
│   └── processed/             # Cleaned, melted, paired data
├── config/                    # Taxonomy, pipeline configs (report_03.yaml)
├── docs/
│   ├── project/               # Strategic docs, vision, pipeline documentation
│   ├── literature/            # FCSM, NIST framework PDFs
│   ├── report_01/             # Report 01 planning docs
│   ├── report_02/             # Report 02 methodology docs
│   └── report_03/             # Report 03 specs, findings, validation
├── handoffs/                  # Session continuity documents
├── cc_tasks/                  # Claude Code task files
└── archive/                   # Superseded outputs and stale figures
```

## Companion Documents

- **Master Report**: [`reports/master/`](reports/master/) — Consolidated narrative (Quarto book)
- **TEVV Methodology**: [`reports/tevv/TEVV_methodology_document.md`](reports/tevv/TEVV_methodology_document.md)
- **FCSM × NIST Crosswalk**: [`reports/tevv/pure_crosswalk_part1.md`](reports/tevv/pure_crosswalk_part1.md), [`reports/tevv/pure_crosswalk_part2.md`](reports/tevv/pure_crosswalk_part2.md)
- **Barrier Taxonomy**: [`reports/master/appendices/B_taxonomy.qmd`](reports/master/appendices/B_taxonomy.qmd)
- **Numbers Map**: [`docs/NUMBERS_MAP.md`](docs/NUMBERS_MAP.md) — Single source of truth for all metrics
- **Script Artifact Map**: [`docs/SCRIPT_ARTIFACT_MAP.md`](docs/SCRIPT_ARTIFACT_MAP.md) — Maps outputs to scripts

## Data

Source data: ~7,000 questions from 47 publicly available Census Bureau demographic survey instruments. See [`data/raw/`](data/raw/).

## Setup

```bash
conda create -n survey-mapper python=3.10
conda activate survey-mapper
pip install -r requirements.txt
```

## Building

**Master report (primary deliverable):**
```bash
cd reports/master
quarto render
# Output: _output/AI-Assisted-Federal-Survey-Harmonization.pdf
```

**Individual reports (superseded by master report):**
```bash
python report_builder.py
```

**Fact sheet:**
```bash
cd output/fact_sheet
quarto render fact_sheet.qmd
```

## License

MIT
