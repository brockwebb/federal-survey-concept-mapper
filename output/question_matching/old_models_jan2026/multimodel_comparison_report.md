# Multi-Model Question Matching Comparison

## Overview

This report compares question-level matching results from three LLM models:
1. **Claude 3 Haiku** (claude-3-haiku-20240307) - Current Anthropic
2. **GPT-4o-mini** - Current OpenAI  
3. **Claude 3.5 Haiku** (historical baseline from earlier run)

All models classified 107 question pairs from FoodAPS and ACS surveys.

## Dataset Summary

| Metric | Count |
|--------|-------|
| Total pairs evaluated | 107 |
| Subtopics covered | 6 (SNAP, Age, Sex, Race, Relationship, Marital) |
| FoodAPS questions | 41 |
| ACS questions | 23 |

## Inter-Model Agreement

### Pairwise Agreement Rates

| Model Pair | Agreement Rate | Cohen's Kappa | Interpretation |
|------------|---------------|---------------|----------------|
| Claude 3 Haiku vs GPT-4o-mini | 74.8% | 0.608 | Substantial |
| Claude 3 Haiku vs Haiku 3.5 | 54.2% | 0.393 | Substantial |
| Haiku 3.5 vs GPT-4o-mini | 64.5% | 0.506 | Moderate |

### Three-Way Agreement

- **All 3 models agree**: 48.6% (52 of 107 pairs)
- **At least 2 models agree**: 96.3%

## Classification Distributions

| Classification | Claude 3 Haiku | GPT-4o-mini | Haiku 3.5 |
|---------------|----------------|-------------|-----------|
| exact_duplicate | 4 (3.7%) | 1 (0.9%) | 1 (0.9%) |
| near_duplicate | 10 (9.3%) | 12 (11.2%) | 27 (25.2%) |
| reference_period_mismatch | 19 (17.8%) | 11 (10.3%) | 12 (11.2%) |
| response_format_mismatch | 5 (4.7%) | 1 (0.9%) | 4 (3.7%) |
| related_but_distinct | 52 (48.6%) | 67 (62.6%) | 35 (32.7%) |
| not_comparable | 17 (15.9%) | 15 (14.0%) | 28 (26.2%) |

### Key Observations

1. **Claude 3 Haiku** detects more reference_period_mismatch cases (19 vs 11 for GPT)
2. **GPT-4o-mini** tends toward "related_but_distinct" (67 vs 52 for Claude 3)
3. **Haiku 3.5** had higher near_duplicate rate (27 vs 10-12 for newer models)
4. All models agree on low exact_duplicate rate (1-4 pairs)

## Consolidation Potential

| Potential | Claude 3 Haiku | GPT-4o-mini |
|-----------|----------------|-------------|
| Yes (droppable) | 14 (13.1%) | 12 (11.2%) |
| Partial | 21 (19.6%) | 1 (0.9%) |
| No | 72 (67.3%) | 94 (87.9%) |

## Comparison to Fuzzy String Matching

### Fuzzy Matching Baseline

| Fuzzy Classification | Count | % |
|---------------------|-------|---|
| Exact (≥90) | 0 | 0.0% |
| Near (70-89) | 6 | 5.6% |
| Distinct (<70) | 101 | 94.4% |

### LLM vs Fuzzy Agreement

Fuzzy matching classified 5.6% as similar (exact or near).
LLMs found 13.1% (Claude) and 12.1% (GPT) as true duplicates.

**Key insight**: LLMs detect nuanced differences (reference periods, response formats) that fuzzy matching misses.

## Disagreement Analysis

### Sample Disagreements

**P_0005** (Age):
- FoodAPS: "What is your date of birth?..."
- ACS: "What is Person 2’s age and what is Person 2’s date of birth?..."
- Claude 3 Haiku: response_format_mismatch
- GPT-4o-mini: related_but_distinct
- Fuzzy score: 90

**P_0007** (Age):
- FoodAPS: "What is your date of birth?..."
- ACS: "Where was this person born?..."
- Claude 3 Haiku: not_comparable
- GPT-4o-mini: related_but_distinct
- Fuzzy score: 44

**P_0009** (Age):
- FoodAPS: "What is your date of birth?..."
- ACS: "Is this grandparent currently responsible for most of the basic needs of any gra..."
- Claude 3 Haiku: related_but_distinct
- GPT-4o-mini: not_comparable
- Fuzzy score: 29

**P_0010** (Age):
- FoodAPS: "Please verify or enter correct age...."
- ACS: "What is Person 1’s age and what is Person 1’s date of birth?..."
- Claude 3 Haiku: response_format_mismatch
- GPT-4o-mini: related_but_distinct
- Fuzzy score: 40

**P_0011** (Age):
- FoodAPS: "Please verify or enter correct age...."
- ACS: "What is Person 2’s age and what is Person 2’s date of birth?..."
- Claude 3 Haiku: response_format_mismatch
- GPT-4o-mini: related_but_distinct
- Fuzzy score: 40

## Files Generated

| File | Description |
|------|-------------|
| `llm_results_claude_haiku3.csv` | Claude 3 Haiku classifications |
| `llm_results_gpt4omini.csv` | GPT-4o-mini classifications |
| `llm_comparison_claude_vs_gpt.csv` | Side-by-side comparison |
| `validation_all_models.csv` | Human validation template (all 3 models) |
| `haiku_3.5/` | Historical baseline results |

## Conclusions

1. **Model Agreement**: 74.8% agreement between Claude 3 Haiku and GPT-4o-mini (Cohen's Kappa = 0.608, substantial agreement)

2. **Temporal Detection**: Claude 3 Haiku appears more sensitive to reference period differences (19 vs 11 cases)

3. **Conservative vs Liberal**: GPT-4o-mini tends toward "related_but_distinct" while Claude provides more specific mismatch types

4. **Consolidation Estimate**: Both models identify ~33% of pairs as having some consolidation potential

5. **Human Validation Needed**: The 25.2% disagreement rate suggests human review would be valuable for borderline cases

---
*Generated: 2026-01-26 17:22*
