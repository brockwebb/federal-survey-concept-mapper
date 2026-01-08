# 3. Background and Related Work

## 3.1 The Census Bureau Taxonomy

The U.S. Census Bureau maintains the Survey Explorer taxonomy as the authoritative framework for categorizing federal survey content. This taxonomy serves multiple purposes:
- Standardized vocabulary for cross-survey discovery
- Metadata tagging for public data repositories  
- Conceptual organization for survey design and planning
- Framework for assessing federal statistical priorities

### 3.1.1 Taxonomy Structure

The taxonomy is organized hierarchically:

**Level 1 - Topics (5 categories)**:
- **Economic**: Income, employment, expenditures, business operations
- **Social**: Health, education, crime, social welfare
- **Housing**: Physical characteristics, costs, tenure, neighborhood
- **Demographic**: Age, race, ethnicity, citizenship, family structure
- **Government**: Operations, finances, programs, services

**Level 2 - Subtopics (152 categories)**:
Each topic contains 12-52 subtopics providing granular concept labels. For example, Economic contains 48 subtopics including:
- Income (wages, benefits, transfers)
- Employment Status (employed, unemployed, not in labor force)
- Expenditures (consumption categories)
- Class of Worker (private, government, self-employed)
- Health Insurance (coverage type, source)
- And 43 additional economic subtopics

The full taxonomy spans consumer behavior, labor market dynamics, health access, educational attainment, housing quality, demographic characteristics, and government operations - essentially all domains measured by federal demographic surveys.

### 3.1.2 Taxonomy Philosophy

The Census Bureau taxonomy reflects several design principles:

**Neutrality**: Category labels are descriptive, not normative. "Crime" is a subtopic, not "Criminal Behavior" (which implies individual-level attribution).

**Inclusivity**: The taxonomy accommodates diverse survey types - household surveys, establishment surveys, administrative records - though this analysis focuses exclusively on demographic household surveys.

**Stability**: Major taxonomy revisions are infrequent to maintain consistency, though subtopics can be added as new measurement needs emerge.

**Context-Sensitivity**: The taxonomy recognizes that identical questions may map to different concepts depending on survey purpose. This context-dependency is a key challenge for automated categorization.

## 3.2 Prior Approaches to Survey Harmonization

### 3.2.1 Manual Expert Review

The traditional approach to cross-survey concept mapping involves subject matter experts comparing questionnaires and identifying similar content. The National Institutes of Health's PhenX Toolkit exemplifies this approach - panels of experts curated "consensus measures" for common health research concepts through multi-year deliberations.

**Strengths**:
- Deep domain expertise ensures accurate concept identification
- Consideration of survey context and measurement intent
- Ability to handle edge cases and ambiguous questions

**Weaknesses**:
- Extremely time-intensive (5-10 minutes per question for thorough review)
- Inter-coder reliability challenges (different experts may disagree)
- Scale limitations (infeasible for thousands of questions)
- Difficult to update as surveys evolve

For the 6,987 questions in this analysis, manual expert review would require an estimated ~70 hours (assuming 100 questions/hour, a conservative estimate for expert categorization with taxonomy reference; ~2 weeks of full-time work), making comprehensive ecosystem analysis prohibitively expensive for routine execution.

### 3.2.2 Metadata-Based Approaches

Some initiatives have attempted to harmonize surveys through standardized metadata. The Data Documentation Initiative (DDI) provides XML schemas for describing survey content, enabling keyword-based searching across surveys tagged with DDI metadata.

**Limitations**:
- Requires manual metadata creation for each question
- Keyword matching is brittle (synonyms, alternative phrasings missed)
- No semantic understanding (cannot infer that "wages and salary" relates to "income")
- Metadata quality varies widely across agencies

Metadata approaches work well for exact matches ("What is your age?") but fail for conceptually similar questions with different wording ("In what year were you born?" also measures age).

### 3.2.3 Text Mining and Embeddings

Recent work has explored computational text analysis for survey harmonization. Researchers have applied:
- **Topic modeling** (LDA, NMF): Discovers latent themes but doesn't map to predefined taxonomies
- **Word embeddings** (Word2Vec, GloVe): Captures semantic similarity but struggles with information asymmetry
- **Contextualized embeddings** (BERT, RoBERTa): Improved semantic understanding but still fails for taxonomy mapping

Our own embedding experiments using RoBERTa-large (Section 4.2) revealed fundamental limitations: embeddings excel at comparing texts of similar length and specificity but break down when comparing detailed questions (100+ words) to sparse concept labels (1-3 words).

This failure motivated the LLM-based approach: modern LLMs can perform **semantic reasoning** (understanding that detailed income questions map to the abstract concept "Income") rather than just semantic similarity matching (which sees all questions as uniformly "question-like").

## 3.3 Large Language Models for Semantic Categorization

### 3.3.1 LLM Capabilities

Modern LLMs (GPT-4, Claude 3, Llama 3) demonstrate several capabilities relevant to survey concept mapping:

**1. Semantic Abstraction**: LLMs can map detailed text to abstract concepts through reasoning rather than string matching.

Example: "During the past 12 months, did you receive any income from wages, salary, commissions, bonuses, or tips from all jobs?" → Concept: "Income"

The model understands that this detailed enumeration is asking about income, not because of keyword matching on "income" (which appears in the question) but through semantic reasoning about the question's purpose.

**2. Context Integration**: LLMs can consider survey context when categorizing questions.

Example: "What is your age?" 
- In NHIS (health survey) → Social.Health_Risk_Factors (age as disease risk)
- In ACS (demographic survey) → Demographic.Age (age as characteristic)

**3. Hierarchical Classification**: LLMs can simultaneously categorize at multiple levels (topic + subtopic) and assign confidence scores.

**4. Reasoning Transparency**: Unlike neural classifiers, LLMs can provide natural language explanations for categorization decisions, enabling audit and quality assurance.

### 3.3.2 LLM Limitations

LLMs also have important limitations for this task:

**Training Data Bias**: LLMs are trained on internet text, which may not represent specialized survey terminology. However, federal surveys are extensively documented online, mitigating this concern.

**Hallucination Risk**: LLMs occasionally generate plausible-sounding but incorrect information. This risk is managed through cross-validation (dual-model approach) and confidence scoring.

**Inconsistency**: LLMs with temperature > 0 produce non-deterministic outputs. We set temperature = 0.3 for reduced variability while preserving some diversity for arbitration.

**Cost**: Commercial LLM APIs charge per token processed. Our full pipeline cost ~$15, a fraction of manual expert review cost but non-trivial for very large datasets.

### 3.3.3 Prior LLM Applications in Survey Research

Several recent studies have explored LLMs for survey-related tasks:

- **Questionnaire generation**: LLMs drafting survey questions given research objectives
- **Response classification**: LLMs coding open-ended survey responses  
- **Survey translation**: LLMs translating questionnaires while preserving measurement equivalence
- **Semantic harmonization**: LLMs mapping questions across surveys (closest to our work)

Our work applies LLM-based concept mapping at scale (6,987 questions, 46 surveys) and incorporates cross-validation with dual models and confidence-based arbitration.

## 3.4 Inter-Rater Reliability in Content Analysis

Content analysis methodology provides benchmarks for assessing categorization quality. Cohen's Kappa (κ) is the standard metric, with interpretation guidelines from Landis & Koch (1977):

- κ < 0.20: Slight agreement
- κ = 0.21-0.40: Fair agreement
- κ = 0.41-0.60: Moderate agreement
- κ = 0.61-0.80: Substantial agreement
- κ = 0.81-1.00: Almost perfect agreement

Our dual-LLM approach achieved κ = 0.842 for topic-level categorization and κ = 0.692 for subtopic-level (Section 7.2). Per the Landis & Koch (1977) interpretation scale, these represent "almost perfect" and "substantial" agreement respectively.

## 3.5 Research Gap and Study Positioning

Despite growing interest in AI for survey methodology, no prior work has:

1. **Scaled LLM categorization** to thousands of questions across dozens of federal surveys
2. **Validated dual-model approaches** for cross-checking LLM judgments
3. **Developed arbitration protocols** for resolving disagreements between models
4. **Implemented dual-modal frameworks** for questions genuinely spanning multiple concepts
5. **Assessed coverage gaps** across entire survey ecosystems using LLM-based mapping

This study fills these gaps, providing both methodological innovation (dual-model with arbitration) and substantive findings (patterns in measurement concentration, survey overlap, and coverage distribution) that inform understanding of the federal survey ecosystem.

## 3.6 Summary

The Census Bureau taxonomy provides an authoritative framework for categorizing federal survey content, but manually mapping thousands of questions to this taxonomy is prohibitively expensive. Prior automated approaches using embeddings failed due to information asymmetry between detailed questions and sparse labels. Modern LLMs offer semantic reasoning capabilities that can bridge this gap, but require careful validation through cross-checking and arbitration. This study applies LLM-based categorization at unprecedented scale to provide the first comprehensive concept map of the federal demographic survey ecosystem.
