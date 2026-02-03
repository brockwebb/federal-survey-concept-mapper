# Executive Summary {.unnumbered}

<!-- TODO: Write 1-page summary after completing all sections -->

## Problem

Federal surveys ask overlapping questions across agencies, creating respondent burden and data integration challenges. Determining which questions can be harmonized requires expert judgment and traditionally takes weeks or months of manual review.

## Approach

We developed an AI-assisted pairwise analysis system using:
- **Multi-model ensemble** (OpenAI, Anthropic, Google) for initial classification
- **Arbitration pattern** to resolve disagreements
- **Question-level rollup** using two-axis triage (Borda direction × Entropy stability)
- **1,598 question pairs** analyzed (CPS-ACS, FoodAPS-ACS)

## Key Results

<!-- TODO: Add specific numbers from consolidability analysis -->

- **CPS**: 41.7% consolidable (100 of 240 questions)
- **FoodAPS**: 48.6% consolidable (68 of 140 questions)
- **Combined**: ~44% consolidation potential

**Barrier Analysis:**
- 97% of failures = Construct/Concept (CC) differences
- CC.1 (concept definition) accounts for 70% of all incompatible pairs
- Not fixable without re-fielding questions

**Expert Review Load:**
- 76% auto-processed with high confidence
- 24% (93 questions) routed to expert review
- AI handles grunt work; humans judge edge cases

## Deliverables

1. **168 consolidable mappings** with specific question-to-question recommendations
2. **212 non-consolidable questions** with barrier codes explaining why
3. **93 questions flagged for expert review** (uncertain or contested cases)
4. **Reproducible methodology** applicable to additional federal surveys

## Implications

This work demonstrates that AI-assisted methods can:
- **Accelerate** survey harmonization analysis (days instead of weeks)
- **Preserve** human oversight and expert judgment
- **Focus** expert effort on highest-ROI decisions
- **Scale** to analyze entire federal survey ecosystem

## Next Steps

1. Expert validation of recommendations
2. Expansion to additional federal surveys
3. Application to survey editing and imputation workflows
