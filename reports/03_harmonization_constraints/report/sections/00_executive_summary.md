# Executive Summary {.unnumbered}

## Problem

The federal survey ecosystem collects overlapping data across agencies that currently exists in silos. These overlaps represent untapped analytical potential: harmonizable questions serve as **bridge variables** enabling cross-survey data integration, which increases explanatory power without additional data collection. As survey response rates decline, extracting more value from existing data becomes critical. Determining which questions are harmonizable requires expert judgment and traditionally takes weeks or months of manual review. A secondary benefit: overlaps also represent opportunities for survey consolidation to reduce respondent burden.

## Approach

We developed an AI-assisted pairwise analysis system using:
- **Multi-model ensemble** (OpenAI, Anthropic, Google) for initial classification
- **Arbitration pattern** to resolve disagreements
- **Question-level rollup** using two-axis triage (Borda direction × Entropy stability)
- **1,598 question pairs** analyzed (CPS-ACS, FoodAPS-ACS)

## Key Results

- **CPS**: 41.7% harmonizable (100 of 240 questions)
- **FoodAPS**: 48.6% harmonizable (68 of 140 questions)
- **Combined**: ~44% harmonization rate

These **168 linkage-ready questions** represent potential bridge variables for cross-survey data enrichment. Harmonization feasibility levels characterize bridge variable quality:
- **F1** (direct harmonization): High-quality bridge variables usable for statistical matching without adjustment
- **F2** (harmonization with transformation): Usable bridge variables requiring methodological adjustment
- **F3** (not harmonizable): Characterized linkage constraints defining where cross-survey enrichment is not viable

**Barrier Analysis:**
- 97% of F3 pairs = Construct/Concept (CC) differences
- CC.1 (concept definition) accounts for 70% of all incompatible pairs
- These barriers validate survey specialization: most non-harmonizable pairs serve fundamentally different analytical purposes, defining precisely where linkage works and where it doesn't

**Expert Review Load:**
- 76% auto-processed with high confidence
- 24% (93 questions) routed to expert review
- AI handles breadth; humans judge edge cases

## Deliverables

1. **168 harmonizable question pairs** characterized as potential bridge variables for cross-survey enrichment
2. **212 non-harmonizable pairs** with linkage quality constraints documented via barrier codes
3. **93 questions flagged for expert review** (uncertain or contested cases)
4. **Reproducible methodology** applicable to entire federal survey ecosystem

## Implications

This work demonstrates that AI-assisted methods can:
- **Identify** bridge variables for cross-survey data integration, increasing analytical power of existing data
- **Characterize** linkage quality constraints, defining where enrichment is viable
- **Accelerate** harmonization analysis (days instead of weeks)
- **Preserve** human oversight and expert judgment
- **Scale** to analyze 7,000+ questions across the federal survey ecosystem

For agencies considering survey consolidation, the same analysis identifies where instrument streamlining is technically feasible as a burden reduction strategy.

## Next Steps

1. Expert validation of bridge variable quality ratings
2. Report 04: AI-assisted discovery of cross-survey enrichment patterns using bridge variable catalog
3. Enrichment pilots: test statistical matching using identified bridge variables
4. Expansion to additional federal surveys
5. Application to survey editing and imputation workflows
