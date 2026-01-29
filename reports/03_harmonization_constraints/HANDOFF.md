# Session Handoff: Report 03 Harmonization Constraints

**Date:** 2025-01-28
**Status:** Skeleton complete, ready for barrier coding

---

## Project Context

Three-report structure for federal survey consolidation research:
- **Report 01**: LLM concept mapping validation (complete, in `final_report/`)
- **Report 02**: Question-level consolidation analysis (complete, in `future_study/`)
- **Report 03**: Harmonization constraints taxonomy (NEW - this work)

---

## Report 03 Purpose

Research question: **What prevents survey question consolidation, and what would fix it?**

Contribution: Systematic taxonomy of harmonization constraints with prevalence estimates - fills gap in literature which lacks quantitative data on barrier frequency.

---

## Completed Work

### Files Created in `future_study/report_03_skeleton/`

| File | Purpose |
|------|---------|
| `README.md` | Report overview, status checklist |
| `taxonomy_v1.md` | 6-category taxonomy with 19 subtypes, feasibility classification |
| `coding_procedure.md` | Operationalized rules, saturation criteria, edge cases |
| `literature_frameworks.md` | Citation collector with processed sources |
| `perplexity_research_summary.md` | Key findings from 900-line Perplexity research |
| `framing_ai_assisted.md` | Positioning on AI-assisted analysis value proposition |
| `literature/README.md` | Citation index |

### Taxonomy Structure (from taxonomy_v1.md)

**Level 1 - Constraint Types:**
1. TC - Temporal (reference period differences)
2. CC - Construct (concept definition/operationalization)
3. PC - Population/Coverage (universe, frame, sample design)
4. RS - Response Scale (scale type, categories, format)
5. MC - Mode/Context (interview mode, question order, routing)
6. PM - Processing/Metadata (coding schemes, weighting, documentation)

**Feasibility Classification:**
- F1: Direct recode (mechanically transformable)
- F2: Statistical adjustment (requires modeling/assumptions)
- F3: Incompatible (not harmonizable without re-fielding)

### Key Literature Integrated

- SDR Framework (PMC5993837) - methodological variability taxonomy
- Wolf et al. (2016) - question-level harmonization barriers
- DataSHaPER - compatibility classification
- National Academies 2018 (NAP 25098) - implementation framework
- Perplexity deep research - 100+ citations on federal survey consolidation

---

## Pending Work

### Immediate Next Steps

1. **Sample non-consolidatable pairs** from existing merged CSVs:
   - `/output/question_matching/cps/cps_comparison_merged.csv`
   - `/output/question_matching/foodaps/foodaps_comparison_merged.csv`

2. **Begin barrier coding** using saturation-based approach:
   - Start with 30 pairs from each survey comparison
   - Code iteratively, refine taxonomy
   - Stop when 10 consecutive pairs fit existing taxonomy

3. **Execute folder reorganization** (optional):
   - Script at repo root: `refactor_structure.sh`
   - Moves `final_report/` → `reports/01_llm_concept_mapping/`
   - Moves `future_study/` → `reports/02_question_consolidation/`

### Subsequent Work

- Full barrier coding of all non-consolidatable pairs
- Inter-rater reliability check (10% dual-coded)
- Prevalence analysis by constraint type
- "Path to consolidation" synthesis
- Report drafting

---

## Key Decisions Made

1. **Terminology**: "Harmonization constraints" (not barriers) - implies actionability
2. **Report 03 is independent contribution**, not extension of Report 02
3. **AI-assisted framing**: Not about staff cuts, about enabling previously infeasible analysis
4. **Grounded theory approach**: Iterative coding with saturation criterion

---

## Data Sources

Existing merged CSVs contain LLM classifications with reasoning:
- Questions already classified as "not consolidatable" or "related but not equivalent"
- Reasoning field contains preliminary barrier identification
- Ready for systematic coding

---

## Repository Structure

```
federal-survey-concept-mapper/
├── final_report/           # Report 01 (existing)
├── future_study/           # Report 02 (existing)
│   └── report_03_skeleton/ # Report 03 (NEW)
├── output/
│   └── question_matching/
│       ├── cps/cps_comparison_merged.csv
│       └── foodaps/foodaps_comparison_merged.csv
└── refactor_structure.sh   # Optional reorganization script
```

---

## Resume Instructions

To continue this work:
1. Read this handoff document
2. Review `taxonomy_v1.md` for coding schema
3. Review `coding_procedure.md` for methodology
4. Load sample from merged CSVs
5. Begin barrier coding

For context on earlier decisions, see transcript at:
`/mnt/transcripts/2026-01-28-20-22-46-report-reorg-harmonization-constraints.txt`
