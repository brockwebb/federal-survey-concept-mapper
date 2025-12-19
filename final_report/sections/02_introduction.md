# 2. Introduction

## 2.1 The Federal Survey Landscape

The U.S. federal government operates one of the world's most comprehensive statistical systems, fielding dozens of demographic surveys annually to inform policy, allocate resources, and track societal well-being. These surveys span economic security (Survey of Income and Program Participation), health access (National Health Interview Survey), housing quality (American Housing Survey), education outcomes (National Teacher and Principal Survey), and myriad other domains critical to evidence-based governance.

Yet this breadth comes with complexity. The federal survey ecosystem has evolved organically over decades, with individual agencies developing specialized instruments to address emerging policy needs. While this flexibility has enabled responsive measurement, it has also resulted in potential inefficiencies: surveys that measure overlapping concepts using inconsistent methodologies, gaps where important phenomena go unmeasured, and duplicative burden on the same respondent populations.

As federal agencies face pressure to reduce respondent burden while maintaining data quality, a fundamental question emerges: **How efficiently is the federal survey ecosystem structured?** Answering this requires systematic analysis of what concepts are measured, where redundancies exist, and which critical topics lack coverage.

## 2.2 The Concept Mapping Challenge

Traditional approaches to survey harmonization have relied on manual expert review - subject matter specialists comparing questionnaires line-by-line to identify similar questions. While thorough, this approach is resource-intensive, requiring hundreds of hours for comprehensive cross-survey analysis. The 2019 Federal Committee on Statistical Methodology's report on survey integration noted that "manual concept mapping across federal surveys is rarely attempted due to the sheer volume of questions and the difficulty of achieving consistent categorizations."

Moreover, manual approaches face methodological challenges:
- **Inconsistent judgments**: Different reviewers may categorize identical questions differently
- **Survey context blindness**: Questions identical in wording may measure different concepts depending on survey purpose
- **Scale limitations**: Human reviewers cannot efficiently process thousands of questions across dozens of surveys
- **Temporal constraints**: By the time manual analysis concludes, surveys may have already been updated

These limitations motivated our exploration of automated approaches. Initial attempts using semantic embeddings (RoBERTa-large) failed due to fundamental information asymmetry between detailed question text and sparse taxonomy labels (Section 4.2). This failure prompted development of a Large Language Model (LLM) based approach that could perform semantic reasoning rather than mere similarity matching.

## 2.3 Research Objectives

This study addresses three interconnected questions:

**1. Can modern AI methods reliably map survey questions to standardized taxonomies at scale?**

Specifically, can LLMs categorize thousands of survey questions with accuracy comparable to human experts, enabling systematic cross-survey concept analysis previously infeasible due to resource constraints?

**2. What patterns of redundancy and gaps exist in the federal survey ecosystem?**

By mapping all questions to a common taxonomy, where do we observe:
- Conceptual redundancy (multiple surveys measuring identical concepts)?
- Consolidation opportunities (surveys with high conceptual overlap)?
- Coverage gaps (important concepts unmeasured or measured by only one survey)?

**3. Can this methodology scale to support ongoing survey portfolio management?**

Beyond one-time analysis, can an LLM-based approach be operationalized for regular concept mapping as surveys evolve, providing continuous insight into ecosystem efficiency?

## 2.4 Study Scope and Context

This analysis examines **6,987 questions from 46 federal demographic surveys**, covering the major household surveys fielded by:
- **Census Bureau**: American Community Survey (ACS), American Housing Survey (AHS), Survey of Income and Program Participation (SIPP), Consumer Expenditure Survey (CE), Current Population Survey (CPS)
- **National Center for Education Statistics**: National Teacher and Principal Survey (NTPS), Teacher Follow-up Survey (TFS), Private School Survey (PSS), School Survey on Crime and Safety (SSOCS)
- **National Center for Health Statistics**: National Health Interview Survey (NHIS), National Hospital Ambulatory Medical Care Survey (NHAMCS), National Ambulatory Medical Care Survey (NAMCS)
- **Health Resources and Services Administration**: National Survey of Children's Health (NSCH), National Sample Survey of Registered Nurses (NSSRN)
- **Bureau of Justice Statistics**: National Crime Victimization Survey (NCVS), School Crime Supplement (SCS)
- **Other agencies**: National Science Foundation (NSCG, NTEWS), USDA (FoodAPS), various state and administrative surveys

Questions are mapped to the **Census Bureau's Survey Explorer taxonomy**, the authoritative framework for categorizing federal survey content. This taxonomy organizes concepts into 5 major topics (Economic, Social, Housing, Demographic, Government) and 152 granular subtopics.

**Important Limitation**: This analysis was conducted during and after a federal government shutdown that furloughed the research team for two months (October-December 2024). The interruption required developing robust checkpoint and resume capabilities in the analysis pipeline, but did not compromise data quality or completeness.

## 2.5 Contribution and Significance

This study makes three primary contributions:

**Methodological**: Demonstrates that dual-LLM categorization with arbitration achieves 99.5% successful categorization with Cohen's Kappa of 0.842, exceeding typical human inter-coder reliability while operating 200-300 times faster than manual analysis.

**Substantive**: Identifies specific consolidation opportunities (e.g., National Survey of Children's Health age variants show 100% conceptual overlap) and critical coverage gaps (30 taxonomy concepts have zero coverage), providing actionable intelligence for survey portfolio management.

**Operational**: Establishes a reproducible, cost-effective framework (~$15 for 7,000 questions, 3 hours processing time) that federal agencies can adopt for ongoing concept mapping as their survey portfolios evolve.

Beyond immediate policy applications, this work demonstrates how modern AI capabilities can augment statistical infrastructure, enabling analyses previously infeasible due to resource constraints. As LLMs continue advancing, their integration into federal statistical workflows promises substantial efficiency gains while maintaining or improving data quality.

## 2.6 Report Organization

The remainder of this report proceeds as follows:

**Section 3 (Background)** reviews the Census Bureau taxonomy structure, prior survey harmonization approaches, and the capabilities of modern LLMs for semantic categorization.

**Section 4 (Methodology)** details the dual-model categorization pipeline, including why LLMs succeeded where embeddings failed, the arbitration protocol for disagreements, and quality assurance procedures.

**Section 5 (Data Collection)** describes the source survey question dataset, data quality issues, and transformations required for analysis.

**Section 6 (Categorization Approach)** explains prompt engineering, model selection rationale, parallel processing architecture, and the dual-modal framework for questions spanning multiple concepts.

**Section 7 (Results)** reports categorization performance metrics, model agreement analysis, and processing efficiency compared to manual approaches.

**Section 8 (Coverage Analysis)** identifies over-sampled concepts, under-sampled concepts, and complete coverage gaps across the federal survey ecosystem.

**Section 9 (Consolidation Opportunities)** quantifies survey similarity to identify merger candidates, harmonization opportunities, and estimated burden reduction potential.

**Section 10 (Discussion)** interprets findings in the context of federal statistical policy, discusses LLM advantages and limitations, and situates results within broader survey methodology literature.

**Section 11 (Limitations)** addresses data quality constraints, model limitations, validation challenges, and threats to inference.

**Section 12 (Recommendations)** provides specific, prioritized guidance for Census Bureau and federal statistical agencies on survey consolidation, gap filling, and methodology adoption.

**Section 13 (Conclusion)** synthesizes key findings and discusses implications for future survey portfolio management and AI integration in federal statistics.

## 2.7 Intended Audience

This report serves multiple audiences:

**Primary**: Census Bureau leadership and survey managers responsible for questionnaire design, survey operations, and portfolio planning.

**Secondary**: Federal statistical agencies seeking reproducible methodologies for concept mapping and survey harmonization.

**Tertiary**: Academic researchers interested in applied AI for survey methodology and large-scale text categorization.

Technical details are provided for reproducibility, but the core findings and recommendations are accessible to non-technical readers. Where specialized knowledge aids understanding, we provide context and definitions rather than assuming expertise.
