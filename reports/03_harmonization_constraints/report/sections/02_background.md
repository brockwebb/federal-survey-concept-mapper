# Background

<!-- TODO: Expand with citations from literature/ directory -->
<!-- Pull from: docs/literature/, docs/citation_queries_decision_016.md -->

## Survey Harmonization Frameworks

### DataSHaPER/Maelstrom Framework

<!-- Pull from: docs/coding_procedure.md, docs/taxonomy_v1.md -->

The DataSHaPER (Data Schema and Harmonization Platform for Epidemiological Research) framework, developed by @fortier2011maelstrom and @fortier2017harmonizing, provides a structured approach to retrospective data harmonization. This framework classifies variable pairs into three feasibility categories:

| Code | Feasibility | Definition | Action Required |
|------|-------------|------------|-----------------|
| **F1** | **Direct recode** | Variables are mechanically transformable through simple recoding, collapsing categories, or unit conversion | Simple data transformation |
| **F2** | **Statistical adjustment** | Variables require modeling, imputation, or bridging studies to make comparable | Statistical harmonization methods |
| **F3** | **Incompatible** | Variables measure fundamentally different constructs and cannot be harmonized without re-fielding | No harmonization possible |

@fortier2011maelstrom applied this framework across 53 epidemiological studies and found that 38% of variables could be harmonized through direct or statistical methods.

### Barrier Taxonomy

When variables are classified as F3 (incompatible), the framework identifies specific barrier types:

#### Construct/Concept (CC)
- **CC.1**: Concept definition differences (e.g., "employment" including/excluding unpaid work)
- **CC.2**: Operationalization differences (different behavioral indicators for same concept)
- **CC.3**: Boundary conditions (different thresholds or cutoffs)
- **CC.4**: Scope inclusions (different components counted)

#### Temporal Constraints (TC)
- **TC.1**: Reference period length (7-day vs 12-month recall)
- **TC.2**: Temporal framing (point-in-time vs habitual vs retrospective)
- **TC.3**: Calendar alignment (fixed vs rolling reference periods)

#### Response Scale (RS)
- **RS.1**: Scale type (binary vs Likert vs continuous)
- **RS.2**: Category structure (different number/boundaries)
- **RS.3**: Anchoring/labels (different verbal anchors)
- **RS.4**: Numeric vs verbal scales

#### Population/Coverage (PC)
- **PC.1**: Universe definition (target population differs)
- **PC.2**: Frame exclusions (different sampling exclusions)
- **PC.3**: Age bounds (different age eligibility)
- **PC.4**: Geographic scope (different coverage)

#### Mode/Context (MC)
- **MC.1**: Interview mode (CATI vs web vs in-person)
- **MC.2**: Question routing (different skip patterns)
- **MC.3**: Contextual priming (question order effects)
- **MC.4**: Proxy response rules

#### Processing/Metadata (PM)
- **PM.1**: Coding schemes (different classification systems)
- **PM.2**: Derived variables (different construction algorithms)
- **PM.3**: Documentation gaps (insufficient metadata)

**See Appendix A** for complete taxonomy definitions with examples.

## Cross-Survey Data Enrichment

Harmonized survey questions serve a dual purpose beyond instrument consolidation: they function as **bridge variables** enabling cross-survey statistical linkage and data enrichment.

**Statistical data fusion** (also called synthetic matching or data integration) is an established technique that combines information from multiple data sources when direct record linkage is not possible [@dorazio2006statistical; @rassler2002statistical]. The key requirement is a set of overlapping variables — bridge variables — measured in both datasets that enable statistical matching.

In the federal survey ecosystem, overlapping questions across surveys represent potential bridge variables. However, the sheer scale of the system (7,000+ questions across 48 surveys) has prevented systematic identification of these opportunities. Individual researchers identify linkage possibilities through domain knowledge and manual review, but no infrastructure exists for discovering cross-survey enrichment patterns at scale.

As federal survey response rates decline (ACS from mid-90s to ~85%, CPS around 70%), extracting more analytical value from existing data becomes increasingly critical. Cross-survey enrichment through bridge variables offers this capability without requiring additional respondent contact or data collection. The DataSHaPER harmonization framework — originally developed for epidemiological research — provides quality ratings for potential bridge variables (F1 = direct use, F2 = methodological adjustment needed, F3 = not viable).

This analysis demonstrates that AI-assisted harmonization analysis can systematically identify bridge variables across the federal survey ecosystem, enabling data enrichment strategies that complement traditional consolidation approaches.

## Related Literature

<!-- TODO: Add key citations from docs/literature/ -->

### Survey Data Harmonization

- @wolf2016harmonizing: Harmonizing survey questions between cultures and over time
- @saris2014design: Design, evaluation, and analysis of questionnaires for survey research
- @slomczynski2018basic: Basic principles of survey data recycling

### AI-Assisted Survey Analysis

<!-- TODO: Add any relevant citations on LLMs for survey methodology -->

### Expert Aggregation and Multi-Rater Methods

The methodological approach in this report—independent LLM raters with structured arbitration—draws from established traditions in expert aggregation and inter-rater reliability assessment.

#### The Delphi Method

The Delphi method, developed at RAND Corporation in the 1950s for technology forecasting, formalized a structured approach to expert judgment aggregation [@dalkey1963experimental]. The method's core principles remain relevant:

- **Independent elicitation**: Experts provide judgments without knowledge of others' responses, preventing anchoring bias
- **Structured iteration**: Disagreements are systematically surfaced and resolved through controlled feedback
- **Anonymity**: Removes social pressure that can distort group judgment

@linstone1975delphi codified these principles in *The Delphi Method: Techniques and Applications*, which became the canonical reference for applications ranging from policy analysis to technology assessment. The method gained particular traction in the 1970s for problems where expert judgment was necessary but consensus was difficult to achieve through traditional deliberative processes.

#### Ensemble Methods in Machine Learning

The Netflix Prize competition (2006-2009) demonstrated that combining predictions from multiple independently-tuned algorithms consistently outperforms any single model [@bell2007lessons]. The winning solution achieved a 10% improvement in recommendation accuracy through ensemble methods rather than novel algorithmic approaches [@lohr2009netflix].

This principle—that aggregating diverse estimators reduces prediction variance—underlies random forests [@breiman2001random], boosting methods, and modern neural network ensembles. The key insight is that models with different architectures, training procedures, or optimization trajectories produce partially decorrelated errors, and averaging across them cancels noise while preserving signal.

#### Application to LLM Classification

Large language models trained by different organizations (Anthropic, OpenAI, Google) exhibit systematic differences in classification behavior due to:

- Different pre-training corpora and curation decisions
- Different alignment and fine-tuning procedures  
- Different architectural choices and model scales

These differences create the *error decorrelation* that makes ensemble methods effective. A classification that all three models agree on is more likely to reflect genuine signal than idiosyncratic model behavior.

Our arbitration pipeline operationalizes this insight: independent LLM classifications (analogous to anonymous Delphi expert judgments), followed by structured disagreement resolution (analogous to controlled Delphi iteration). The approach is not methodologically novel—it is a computational implementation of principles established in decision science and ensemble learning over the past seven decades.

## Prior Work: Reports 01-02

### Report 01: Concept Classification

<!-- TODO: Summarize Report 01 key findings -->

- Mapped 7,400+ survey questions to Census Bureau taxonomy
- Used LLM ensemble (Claude Haiku + GPT-4o-mini) with arbitration
- Achieved 99.5% categorization success rate
- Cohen's κ = 0.842 (almost perfect agreement)

### Report 02: Pairwise Comparison Setup

<!-- TODO: Summarize Report 02 key findings -->

- Identified 1,598 question pairs for harmonization analysis
- Selected CPS and FoodAPS as representative source surveys
- Developed sampling strategy based on concept categories
- Established pair-level comparison methodology

### Building Forward

Report 03 (this report) takes the validated pairwise comparisons from Report 02 and:

1. Classifies each pair using harmonization framework (F1/F2/F3)
2. Identifies barrier codes for F3 pairs
3. Rolls up pair-level results to question-level consolidability
4. Generates expert review tables for stakeholder use

## Census Bureau Context

The Census Bureau conducts multiple surveys covering demographics, economics, housing, and social conditions:

- **ACS**: Comprehensive demographic/economic data, ~3.5M households annually
- **CPS**: Labor force statistics, ~60K households monthly
- **SIPP**: Household dynamics and program participation
- **Others**: American Housing Survey, Survey of Income and Program Participation, etc.

**Declining response rates** create urgency for extracting more value from existing data. ACS response rates have declined from the mid-90s to approximately 85%, while CPS response rates hover around 70%. This trend makes cross-survey data enrichment increasingly valuable: harmonized questions serve as bridge variables enabling statistical linkage, which expands analytical capabilities without requiring additional respondent contact.

Harmonization across these surveys enables:

- **Cross-survey data enrichment**: Using bridge variables to integrate datasets and increase explanatory power
- **Improved inference**: Combining specialized survey content for richer analysis
- **Reduced respondent burden**: Secondary benefit through potential survey consolidation where feasible
- **Improved data quality**: Consistent measurement across surveys
- **Resource efficiency**: Coordinated questionnaire design

## Research Gap

While survey harmonization frameworks exist (DataSHaPER, SDR methodology), **no prior work has**:

1. Characterized federal survey overlaps as potential bridge variables for statistical data fusion and cross-survey enrichment
2. Applied harmonization frameworks systematically to federal survey questions at scale
3. Used AI-assisted methods to accelerate the classification process
4. Quantified harmonization potential across major federal surveys and identified linkage-ready bridge variables
5. Developed operational triage frameworks for expert review prioritization

This report addresses these gaps, with primary focus on identifying bridge variables for cross-survey data enrichment and secondary findings on consolidation potential.

---

**Key Takeaway**: Survey harmonization is well-established in epidemiology and international survey research, but has not been systematically applied to the U.S. federal survey ecosystem. This report demonstrates that AI-assisted methods can scale this analysis.
