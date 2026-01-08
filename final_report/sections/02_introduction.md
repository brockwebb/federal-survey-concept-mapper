# 2. Introduction

## 2.1 The Federal Survey Landscape

The U.S. federal government operates one of the world's most comprehensive statistical systems, fielding dozens of demographic surveys annually to inform policy, allocate resources, and track societal well-being. These surveys span economic security (Survey of Income and Program Participation), health access (National Health Interview Survey), housing quality (American Housing Survey), education outcomes (National Teacher and Principal Survey), and myriad other domains critical to evidence-based governance.

Yet this breadth comes with complexity. The federal survey ecosystem has evolved organically over decades, with individual agencies developing specialized instruments to address emerging policy needs. Understanding how this ecosystem is structured—which concepts are measured extensively, where surveys share conceptual territory, and how coverage varies across domains—has traditionally required labor-intensive manual analysis.

As federal agencies face pressure to reduce respondent burden while maintaining data quality, systematic knowledge of the survey ecosystem becomes increasingly valuable. **What concepts are being measured, by which surveys, and with what patterns of overlap and specialization?** Answering these questions at scale has been infeasible—until now.

## 2.2 The Concept Mapping Challenge

Traditional approaches to survey harmonization have relied on manual expert review - subject matter specialists comparing questionnaires line-by-line to identify similar questions. While thorough, this approach is resource-intensive, requiring hundreds of hours for comprehensive cross-survey analysis. Manual concept mapping across federal surveys is rarely attempted at ecosystem scale due to the sheer volume of questions and the difficulty of achieving consistent categorizations across diverse survey instruments.

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

**2. What patterns characterize the federal survey ecosystem?**

By mapping all questions to a common taxonomy, what do we observe about:
- Measurement concentration (which concepts receive intensive coverage across surveys)?
- Survey overlap patterns (which surveys share conceptual territory, and why)?
- Coverage distribution (how measurement effort is allocated across taxonomy domains)?

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

## 2.5 Contribution and Significance

This study makes three primary contributions:

**Methodological**: Demonstrates that dual-LLM categorization with arbitration achieves 99.5% successful categorization with Cohen's Kappa of 0.842 ("almost perfect agreement" per Landis & Koch, 1977) while operating approximately 20× faster than estimated manual analysis.

**Exploratory**: Identifies patterns in survey coverage—concepts with high measurement concentration (reflecting the demographic baseline surveys need), survey pairs with shared conceptual territory (reflecting intentional design for universe definition), and the distribution of coverage across taxonomy domains.

**Operational**: Establishes a reproducible, cost-effective framework (~$15 for ~7,000 questions, ~2 hours processing time) that could support ongoing concept mapping if validated by domain experts.

This work is an **exploratory proof-of-concept**. It demonstrates technical feasibility and generates structured data for expert review. Whether the patterns identified represent actionable opportunities or appropriate characteristics of a well-designed survey ecosystem requires domain expertise to determine.

## 2.6 Report Organization

The remainder of this report proceeds as follows:

**Section 3 (Background)** reviews the Census Bureau taxonomy structure, prior survey harmonization approaches, and the capabilities of modern LLMs for semantic categorization.

**Section 4 (Methodology)** details the dual-model categorization pipeline, including why LLMs succeeded where embeddings failed, the arbitration protocol for disagreements, and quality assurance procedures.

**Section 5 (Data Collection)** describes the source survey question dataset, data quality issues, and transformations required for analysis.

**Section 6 (Implementation Overview)** summarizes technical implementation decisions, with complete details provided in Appendix A.

**Section 7 (Results)** reports categorization performance metrics, model agreement analysis, and processing efficiency compared to manual approaches.

**Section 8 (Coverage Analysis)** identifies patterns in concept coverage—high-frequency concepts, sparsely measured concepts, and concepts without household survey coverage.

**Section 9 (Survey Overlap Patterns)** presents survey similarity findings as areas for expert investigation, without prescribing specific consolidation actions.

**Section 10 (Discussion)** interprets findings in the context of federal statistical policy, discusses broader applications for federal statistics, and situates results within existing Census AI capabilities.

**Section 11 (Limitations)** addresses data quality constraints, model limitations, validation challenges, and threats to inference.

**Section 12 (Next Steps)** outlines potential research directions and validation approaches, framed as questions for expert review rather than prescriptive recommendations.

**Section 13 (Conclusion)** synthesizes key findings, discusses implications for AI-assisted survey analysis, and invites collaboration.

## 2.7 Intended Audience

This report serves multiple audiences:

**Primary**: Census Bureau leadership and survey managers responsible for questionnaire design, survey operations, and portfolio planning.

**Secondary**: Federal statistical agencies seeking reproducible methodologies for concept mapping and survey harmonization.

**Tertiary**: Academic researchers interested in applied AI for survey methodology and large-scale text categorization.

Technical details are provided for reproducibility, but the core findings and recommendations are accessible to non-technical readers. Where specialized knowledge aids understanding, we provide context and definitions rather than assuming expertise.
