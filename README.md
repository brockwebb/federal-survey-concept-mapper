# Federal Survey Concept Mapper

A semantic analysis system for mapping and categorizing questions across 46 U.S. federal demographic surveys.

## Overview

This project analyzes 6,987 survey questions from federal demographic surveys to:
- Identify conceptual overlap and redundancy across surveys
- Create a unified taxonomy of survey concepts
- Enable survey consolidation recommendations
- Map coverage gaps in the federal survey ecosystem
- Support data substitution decisions

## Data Source

Survey questions compiled from public federal demographic surveys including:
- Survey of Income and Program Participation (SIPP)
- Consumer Expenditure Survey (CE)
- American Housing Survey (AHS)
- National Health Interview Survey (NHIS)
- Current Population Survey (CPS)
- American Community Survey (ACS)
- And 42 additional federal surveys

All data is from publicly available survey instruments.

## Methodology

1. **Dual-LLM Categorization**: Questions independently categorized by claude-haiku-4-5 and gpt-5-mini
2. **Agreement Analysis**: Calculate inter-rater reliability (Cohen's Kappa: 0.84)
3. **Arbitration**: Disagreements resolved by claude-sonnet-4-5 with dual-modal support
4. **Analysis**: Cross-survey overlap, consolidation opportunities, coverage gaps

**Note**: Initial embedding approach (RoBERTa-large) failed due to information asymmetry. See `docs/lessons_learned_embedding_failure.md`.

## Setup

```bash
# Create conda environment
conda create -n survey-mapper python=3.10
conda activate survey-mapper

# Install dependencies
pip install -r requirements.txt

# Download and cache RoBERTa model (one-time, for offline use)
python src/download_model.py
```

## Project Structure

```
federal-survey-concept-mapper/
├── data/
│   ├── raw/              # Original survey question CSV
│   ├── processed/        # Melted/transformed data
│   └── reference/        # Census taxonomy definitions
├── models/
│   └── roberta-large/    # Cached model files (offline)
├── src/
│   ├── data_prep.py      # Data transformation utilities
│   ├── embeddings.py     # RoBERTa embedding generation
│   ├── clustering.py     # Similarity and clustering
│   └── download_model.py # One-time model download
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_embedding_generation.ipynb
│   ├── 03_clustering_analysis.ipynb
│   └── 04_categorization.ipynb
├── config/
│   └── census_taxonomy.yaml
└── output/
    ├── embeddings/
    ├── clusters/
    └── analysis/
```

## Usage

Work through notebooks sequentially:
1. **Data exploration**: Load, melt, explore survey question distributions
2. **Generate embeddings**: Create RoBERTa-large embeddings (runs offline)
3. **Cluster analysis**: Find similar questions at various thresholds
4. **Categorization**: Apply Census taxonomy and multi-dimensional scoring

## Key Features

- **100% Offline Processing**: All models cached locally, no external dependencies after setup
- **Question Dependencies**: Preserves skip logic and conditional universes
- **Multi-dimensional Scoring**: Shadow scores across Census concept dimensions (threshold: exploratory)
- **Survey Context Preservation**: Questions categorized with survey metadata for context-dependent classification

## Notes on Methodology

### Shadow Scores
Questions receive scores across multiple Census taxonomy dimensions, capturing the multi-faceted nature of survey questions. For example, "household income" scores high on Economics.Income but also has meaningful presence in Demographics.Socioeconomic and Housing.Affordability.

### Survey Context Matters
Identical questions may receive different categorizations based on survey context. "What is your age?" is categorized differently in a health survey (health risk factors) vs. an education survey (career progression).

### Question Universes
Questions include universe metadata (who gets asked) and conditional logic (skip patterns), enabling proper substitution recommendations.

## Context

This analysis was interrupted by a federal government shutdown and resumed after a 2-month furlough. The goal is to provide actionable insights for federal statistical agencies to optimize their survey portfolios and reduce respondent burden.

## License

Data from public federal survey instruments. Analysis code [specify license].
