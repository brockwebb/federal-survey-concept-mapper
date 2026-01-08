# Federal Survey Concept Mapping - Results

## Overview

This analysis categorized 6,987 questions from 46 federal surveys using the Census Bureau's official taxonomy.

## Key Findings

### Categorization Success
- **Successfully categorized**: 6,949 questions (99.5%)
- **Needs human review**: 38 questions (0.5%)

### Decision Methods
- **agreement**: 4,765 (68.2%)
- **auto_dual_modal**: 821 (11.8%)
- **pick_gpt5mini**: 522 (7.5%)
- **pick_haiku45**: 482 (6.9%)
- **new_concept**: 340 (4.9%)
- **unresolved_disagreement**: 31 (0.4%)
- **dual_modal**: 19 (0.3%)
- **categorization_failed**: 7 (0.1%)

### Topic Coverage
- **Total topics**: 6
- **Questions span**: Economic, Social, Housing, Demographic, Government

### Data Quality
- Models achieved strong agreement on most questions
- Agentic arbitration resolved ambiguous cases
- Remaining disagreements flagged for human review

## Files

### Core Datasets
- `master_dataset.csv` - Complete question-level data with final categorizations
- `survey_concept_matrix.csv` - Aggregated survey × concept counts

### Visualizations
- `summary_dashboard.png` - Overview of categorization results

### Source Data
- `../results/` - Raw model outputs
- `../comparison/` - Model agreement analysis
- `../arbitration_agentic/` - Arbitration decisions and reasoning

## Next Steps

1. Review questions flagged for human review
2. Analyze survey redundancy and consolidation opportunities
3. Identify concept coverage gaps
4. Generate stakeholder-specific reports

## Methodology

1. **Initial Categorization**: gpt-5-mini and claude-haiku-4-5 independently categorized all questions
2. **Agreement Check**: Questions with model agreement were accepted
3. **Agentic Arbitration**: Disagreements sent through 3-round feedback loop (claude-sonnet-4-5 ↔ gpt-5.2)
4. **Final Reconciliation**: Combined results with decision tracking

Generated: 2025-12-17 12:16:59
