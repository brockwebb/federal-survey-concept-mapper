# Question-Level Survey Consolidation Analysis

This directory contains the complete research documentation for analyzing question-level consolidation potential between federal surveys and the American Community Survey (ACS).

## Quick Start

**Main findings:** [`question_level_matching_design.md`](question_level_matching_design.md)

**TL;DR:** ~11% of question pairs are consolidable through ACS record linkage, structurally bounded by reference period mismatches and construct differences.

---

## Document Index

| Document | Purpose | Read This If... |
|----------|---------|-----------------|
| [`question_level_matching_design.md`](question_level_matching_design.md) | Main findings, detailed results, data tables | You want the full analysis |
| [`synthesis_and_conclusions.md`](synthesis_and_conclusions.md) | Cross-survey synthesis, policy implications, recommendations | You want actionable takeaways |
| [`methodology_classification_workflow.md`](methodology_classification_workflow.md) | Classification pipeline, prompts, decision logic, diagrams | You want to understand/replicate the method |
| [`case_studies_foodaps.md`](case_studies_foodaps.md) | SNAP, Race, Hours/Week deep-dives with question text | You want concrete examples from FoodAPS |
| [`case_studies_cps.md`](case_studies_cps.md) | Disability, Employment Status deep-dives with question text | You want concrete examples from CPS |
| [`acs_linked_supplements_background.md`](acs_linked_supplements_background.md) | Background on ACS-linked supplement model | You want policy context |

---

## Key Findings

### 1. Consolidation Potential Is Real but Limited (~11%)

| Survey Pair | Total Pairs | Consolidable | Rate |
|-------------|-------------|--------------|------|
| FoodAPS-ACS | 610 | 74 | 12.1% |
| CPS-ACS | 1,092 | 118 | 10.8% |
| **Combined** | **1,702** | **192** | **11.3%** |

### 2. Content Type Predicts Consolidation Rate

| Content Type | Typical Rate | Why |
|--------------|--------------|-----|
| Core demographics (sex, age, race) | 60-100% | Stable characteristics, standardized constructs |
| Habitual measures (hours/week) | 25-30% | "Usually/normally" framing has no temporal anchor |
| Point-in-time status (employment) | 10-15% | Reference period mismatches |
| Program-specific content | 0-10% | Specialized needs require specialized questions |

### 3. Three Structural Barriers Explain Most Non-Consolidation

1. **Construct mismatch:** Same topic, different operationalization (e.g., work-limiting vs functional disability)
2. **Reference period incompatibility:** Same construct, different time windows (e.g., "last 4 weeks" vs "last week")
3. **Screener vs battery:** Same topic, different depth (e.g., "received SNAP?" vs "how many cards, who's on each?")

### 4. LLMs Reliably Identify Consolidation Opportunities

The CPS Disability case provides strong validation:
- 6/6 ACS6 standardized question matches correctly identified
- 336/336 non-matching pairs correctly rejected
- Model agreement: 94.7% on clear cases

---

## Data Sources

| File | Location | Contents |
|------|----------|----------|
| `foodaps_comparison_merged.csv` | `output/question_matching/foodaps/` | 610 FoodAPS-ACS pair classifications |
| `cps_comparison_merged.csv` | `output/question_matching/cps/` | 1,092 CPS-ACS pair classifications |

---

## Methodology Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  INPUT DATA     │     │ PAIR GENERATION │     │ CLASSIFICATION  │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ • Survey A Qs   │────▶│ • Assign topics │────▶│ • Claude Haiku  │
│ • Survey B Qs   │     │ • Match by      │     │ • GPT-5-mini    │
│ • Taxonomy      │     │   subtopic      │     │ • Compare       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │    OUTPUT       │
                                               ├─────────────────┤
                                               │ • Consolidation │
                                               │   flags         │
                                               │ • Disagreement  │
                                               │   flags         │
                                               └─────────────────┘
```

**Interactive diagrams:** See [`methodology_classification_workflow.md`](methodology_classification_workflow.md) for Mermaid diagrams with live editor links.

---

## Resource Summary

| Item | Value |
|------|-------|
| Total pairs analyzed | 1,702 |
| Total API cost | ~$1.50 |
| Analysis time | ~16 hours |
| Consolidable pairs found | 192 (11.3%) |

---

## Citation

If using this methodology or findings:

```
Webb, B. (2026). Question-Level Survey Consolidation Analysis: 
FoodAPS-ACS and CPS-ACS Comparison. Federal Survey Concept Mapper Project.
https://github.com/brockwebb/federal-survey-concept-mapper
```

---

*Last updated: January 27, 2026*
