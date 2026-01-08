# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a semantic analysis system for mapping and categorizing 6,987 survey questions from 48 U.S. federal demographic surveys (SIPP, CE, AHS, NHIS, CPS, ACS, etc.) to the Census Bureau's official taxonomy. The goal is to identify conceptual overlap, redundancy, and coverage gaps across the federal survey ecosystem.

**Key Context**: This analysis was interrupted by a federal government shutdown and resumed after a 2-month furlough.

## Architecture

The project uses a **dual-LLM categorization pipeline** with cross-validation and arbitration:

1. **Serial Categorization**: Two LLMs (gpt-5-mini and claude-haiku-4-5) independently categorize all questions (Claude runs first, then OpenAI)
2. **Agreement Analysis**: Compare results, calculate inter-rater reliability (Cohen's Kappa)
3. **Disagreement Resolution**: Higher-capability model (claude-sonnet-4-5) arbitrates disagreements in single pass
4. **Dual-Modal Support**: Questions can be assigned two primary topics if they genuinely span concepts

**Why Not Embeddings?** RoBERTa-large embeddings failed completely (uniform similarity distributions) due to information asymmetry between 100-word detailed questions and 2-word concept labels. See `docs/lessons_learned_embedding_failure.md` for empirical evidence.

### Pipeline Steps (Sequential)

| Step | Script | Purpose | Outputs |
|------|--------|---------|---------|
| 1 | `categorize_claude.py` | Categorize with claude-haiku-4-5 | `output/results/results_claude.jsonl` |
| 2 | `categorize_openai.py` | Categorize with gpt-5-mini | `output/results/results_openai.jsonl` |
| 3 | `compare_llm_results.py` | Calculate agreement metrics | `output/comparison/agreement_summary.csv` |
| 4 | `analyze_failures_disagreements.py` | Identify patterns in failures/disagreements | `output/analysis/arbitration_candidates.csv` |
| 5 | `arbitrate_final.py` | Arbitrate with dual-modal support | `output/arbitration_final/all_disagreement_resolutions.csv` |
| 6 | `create_final_outputs.py` | Generate master dataset + visualizations | `output/final/master_dataset.csv` |

### Key Design Decisions

**Confidence Threshold (0.90)**: Disagreements where both models have confidence ≥0.90 are auto-assigned as dual-modal (higher confidence = primary, lower = secondary). Below 0.90, questions go to arbitration.

**Dual-Modal Questions**: ~2-5% of questions genuinely span two topics (e.g., "income from government assistance" spans Economic.Income + Social.Programs). These get both `primary_topic/subtopic` and `secondary_primary_topic/subtopic`.

**Serial Execution**: Claude runs first (6 workers), then OpenAI runs (6 workers), batch size of 10 questions per call. Total runtime: ~2 hours.

## Running the Pipeline

### Environment Setup

```bash
# Create environment
conda create -n survey-mapper python=3.10
conda activate survey-mapper

# Install dependencies
pip install -r requirements.txt

# Set API keys
cp .env.example .env  # Then add your OPENAI_API_KEY and ANTHROPIC_API_KEY
```

### Pipeline Execution

```bash
cd src

# Run complete pipeline
python run_pipeline.py

# Clean re-run from scratch
python run_pipeline.py --clean

# Resume from specific step
python run_pipeline.py --from 3

# Run single step
python run_pipeline.py --only 4
```

### Running Individual Scripts

```bash
# Initial categorization (can run independently)
python categorize_claude.py
python categorize_openai.py

# Or run one model only
python llm_categorization.py --claude-only
python llm_categorization.py --openai-only

# Analysis and arbitration (sequential dependencies)
python compare_llm_results.py
python analyze_failures_disagreements.py
python arbitrate_final.py
python create_final_outputs.py
```

### Jupyter Notebooks (Exploratory Work)

Located in `notebooks/`:
- `01_data_exploration.ipynb` - Data structure and distributions
- `01b_data_cleaning.ipynb` - Data transformations
- `02_embedding_generation.ipynb` - RoBERTa embedding experiments
- `03_clustering_analysis.ipynb` - Similarity analysis

**Note**: The embedding notebooks document the failed embedding approach. The production pipeline uses LLM categorization.

## Data Files

### Input Data
- `data/raw/PublicSurveyQuestionsMap.csv` - Wide format: Question × Survey mappings (6,987 × 49)
- `data/raw/census_survey_explorer_taxonomy.json` - Official Census taxonomy (5 topics, 152 subtopics)
- `config/census_taxonomy.yaml` - Simplified taxonomy (legacy, reference only)

### Output Structure
```
output/
├── results/           # JSONL files from initial categorization
├── comparison/        # Agreement metrics, confusion matrices
├── analysis/          # Failure/disagreement analysis
├── arbitration_final/ # Arbitration decisions with reasoning
└── final/             # Master dataset, visualizations, summary report
```

## Key Files to Understand

### Core Pipeline Scripts
- `llm_categorization.py` - Shared categorization logic with batch processing, error handling, checkpointing
- `arbitrate_final.py` - Dual-modal arbitration logic with confidence tiers (single-pass production version)
- `arbitrate_agentic.py` - Multi-agent arbitration with feedback loops (experimental, future research)
- `run_pipeline.py` - Master orchestrator with resume capability

### Configuration
- `config/canonical_format.json` - Expected data schema
- `config/census_taxonomy.yaml` - Taxonomy reference (not used in production)
- `.env` - API keys (not committed)

### Documentation
- `docs/pipeline_documentation.md` - Complete technical documentation with Mermaid diagrams
- `docs/lessons_learned_embedding_failure.md` - Why embeddings failed (empirical evidence)
- `docs/VERIFICATION_CHECKLIST.md` - Quality assurance checklist

## Common Tasks

### Re-run Categorization for One Model

```bash
# If OpenAI results are incomplete/corrupted
cd src
python categorize_openai.py  # Or: python llm_categorization.py --openai-only

# Pipeline will skip if output already exists - use --clean to force re-run
python run_pipeline.py --clean --from 2
```

### Check Pipeline Progress

```bash
# Check which steps are complete
python run_pipeline.py  # Shows [✓] for completed steps

# View categorization checkpoint
cat ../output/categorization_checkpoint.json
```

### Analyze Specific Questions

```python
import pandas as pd
import json

# Load final results
df = pd.read_csv('../output/final/master_dataset.csv')

# Find disagreements
disagreements = df[~df['models_agree']]

# Find dual-modal questions
dual_modal = df[df['is_dual_modal']]

# Load arbitration reasoning
with open('../output/arbitration_final/arbitration_results.csv') as f:
    arbitrations = pd.read_csv(f)
```

## Error Handling & Recovery

The pipeline includes robust error handling:

- **Checkpointing**: `categorization_checkpoint.json` tracks progress, resume with `--from` flag
- **Exponential Backoff**: API rate limits handled with 1s, 2s, 4s, 8s, 16s delays
- **Robust JSON Parsing**: 3 extraction strategies for malformed LLM responses
- **Thread-Safe Writes**: File locks prevent corruption in parallel execution
- **Output Validation**: Steps verify expected file existence before proceeding

If a step fails, check:
1. API key environment variables
2. Input file existence/format
3. Available disk space for outputs
4. API rate limits/quotas

## Expected Quality Metrics

From production runs on 6,987 questions:

- **Categorization Success Rate**: 99.5% (35 failures, mostly very short questions <10 chars)
- **Cohen's Kappa (topics)**: 0.842 ("almost perfect agreement")
- **Topic Agreement**: ~89% (both models choose same high-level topic)
- **Subtopic Agreement**: ~68% (both models choose same granular subtopic)
- **Dual-Modal Rate**: 2-5% of all questions

## Survey Context Matters

Identical questions may be categorized differently based on survey context:
- "What is your age?" in NHIS (health survey) → Health - Risk Factors
- "What is your age?" in education survey → Demographic - Age

This is intentional and correct - context determines the conceptual framing.

## Cost Estimates

Production costs for 6,987 questions:
- Initial categorization (claude-haiku-4-5 + gpt-5-mini): ~$8
- Arbitration (claude-sonnet-4-5, single pass): ~$7
- **Total pipeline: ~$15**

## Development Notes

- **No Tests**: This is an exploratory analysis project, not production software
- **Notebooks for Exploration**: Use notebooks for ad-hoc analysis, scripts for pipeline
- **Models Cached Locally**: RoBERTa-large in `models/roberta-large/` (1.4GB, git-ignored)
- **Large Files Git-Ignored**: CSVs, embeddings, model files excluded via `.gitignore`
- **Python 3.10**: Required for compatibility with dependencies

## Taxonomy Reference

Census Bureau taxonomy structure (from `census_survey_explorer_taxonomy.json`):
- **5 Topics**: Economic, Demographic, Social, Health, Government
- **152 Subtopics**: Income, Age, Education, Health Insurance, etc.
- **Hierarchical**: Topic.Subtopic format (e.g., "Economic.Income")

Questions are assigned:
- Primary topic + subtopic (always)
- Secondary primary topic + subtopic (if dual-modal)
- All relevant subtopics (list of related concepts)
- Confidence score (0-1)
- Reasoning (explanation of assignment)

## Report Generation (Current Task)

After pipeline completion, generate scientific report for Census Bureau:

### Report Structure
- Location: `/final_report/`
- Format: Markdown sections → assembled master document
- Assets: figures/, tables/, data/

### Generate Report Assets
```bash
cd src
python generate_coverage_analysis.py     # Coverage visualizations
python generate_survey_tables.py         # Survey profiles & consolidation
python generate_visualizations_1_2_3.py  # Heatmaps & treemaps
```

### Writing Sections
See `/final_report/REPORT_PLAN.md` for:
- Section-by-section content guidance
- Writing order (start with Section 4 - Methodology)
- Target audience (Census Bureau leadership)

### Key Report Messages
1. **Speed**: Hours vs. 200+ hours manual analysis
2. **Accuracy**: 99.5% categorization success, 89% agreement
3. **Actionable**: Identified specific consolidation opportunities
4. **Reproducible**: Open methodology for other survey systems
