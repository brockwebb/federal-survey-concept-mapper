# 4. Methodology

## 4.1 Overview

This study employed a dual-model Large Language Model (LLM) categorization pipeline to systematically map 6,987 survey questions from 46 federal surveys to the U.S. Census Bureau's Survey Explorer topic taxonomy. The approach was designed to balance accuracy, scalability, and cost-effectiveness while addressing the fundamental limitation of traditional embedding-based methods for this task.

### Pipeline Workflow

```
┌──────────────────┐
│  Survey Question │
│  + Survey Context│
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│        DUAL-MODEL CATEGORIZATION         │
│  ┌─────────────┐     ┌─────────────┐     │
│  │Claude Haiku │     │  GPT-5-mini │     │
│  │    4.5      │     │             │     │
│  └──────┬──────┘     └──────┬──────┘     │
│         │                   │            │
│         └─────────┬─────────┘            │
└───────────────────┼──────────────────────┘
                    │
                    ▼
            ┌───────────────┐
            │   AGREEMENT   │
            │    CHECK      │
            └───────┬───────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
┌───────────────┐       ┌───────────────┐
│    AGREE      │       │   DISAGREE    │
│   (67.4%)     │       │   (32.6%)     │
│               │       │               │
│ Use agreed    │       │ Confidence    │
│ categorization│       │ ≥0.90? ───────┼──► Auto Dual-Modal
└───────────────┘       │               │
                        │ <0.90 ────────┼──► Arbitration
                        └───────────────┘    (Claude Sonnet 4.5)
                                                    │
                                                    ▼
                                        ┌───────────────────┐
                                        │ ARBITRATOR DECIDES│
                                        │ • Pick Model 1    │
                                        │ • Pick Model 2    │
                                        │ • New Concept     │
                                        │ • Dual-Modal      │
                                        └─────────┬─────────┘
                                                  │
                                                  ▼
                                        ┌───────────────────┐
                                        │  FINAL CATEGORY   │
                                        │  + Confidence     │
                                        │  + Decision Trail │
                                        └───────────────────┘
```

The methodology consisted of five sequential stages:

1. **Serial Dual-Model Categorization** - Independent categorization by two production-grade LLMs (executed sequentially)
2. **Agreement Analysis** - Quantitative assessment of inter-rater reliability 
3. **Disagreement Stratification** - Confidence-based tiers for resolution strategy
4. **Arbitration with Dual-Modal Support** - Higher-capability model resolves disagreements
5. **Final Reconciliation** - Master dataset generation with decision tracking

This section details each stage, the rationale for key design decisions, and the computational infrastructure supporting the analysis.

## 4.2 Why LLMs Over Embeddings

Prior to developing the LLM-based approach, we extensively tested semantic embeddings using RoBERTa-large, a state-of-the-art transformer model pre-trained on massive text corpora. This approach failed completely due to fundamental information asymmetry between the inputs being compared.

**The Core Problem**: Survey questions are detailed (50-150 words), while Census taxonomy labels are sparse (1-3 words). For example:
- Question: "During the past 12 months, did you receive any income from wages, salary, commissions, bonuses, or tips from all jobs?"
- Taxonomy label: "Income"

When embedded in the same semantic space, all questions exhibited uniformly high similarity (0.85-0.95) to all concepts, making discrimination impossible. The embedding vectors captured that all questions were "survey-like text" but could not bridge the specificity gap between detailed questions and abstract concept labels.

**Key Finding**: Cosine similarity distributions were effectively uniform across all question-concept pairs, providing no signal for categorization. Even with survey context and question trimming, the approach remained non-viable. See `docs/lessons_learned_embedding_failure.md` for empirical evidence and detailed analysis.

This failure motivated the LLM approach: modern LLMs can perform **semantic reasoning** rather than just semantic similarity, understanding that a detailed question about "wages and salary" maps to the abstract concept "Income" through conceptual inference, not string matching.

## 4.3 Dual-Model Categorization Framework

### 4.3.1 Model Selection

We employed two production-grade LLMs in parallel for initial categorization:

**Model 1: gpt-5-mini (OpenAI)**
- Reasoning: Fast inference, cost-effective ($0.15/1M input, $0.60/1M output)
- Configuration: Default API parameters, max_tokens 500
- Specialization: Strong semantic understanding, consistent JSON formatting

**Model 2: Claude Haiku 4.5 (Anthropic)**  
- Reasoning: Complementary architecture, excellent instruction following
- Configuration: Default API parameters, max_tokens 500
- Specialization: Nuanced reasoning, handles ambiguity well

**Rationale for Dual Models**: Using two independent models provides cross-validation and reduces single-model bias. High agreement indicates clear categorization; disagreement flags genuinely ambiguous cases requiring deeper analysis. This is analogous to dual-coder practices in qualitative research but executed at machine scale.

### 4.3.2 Prompt Engineering

Each model received identical structured prompts containing:

1. **Task Definition**: Map question to Census taxonomy (5 topics, 152 subtopics)
2. **Taxonomy Context**: Complete hierarchical structure with descriptions
3. **Survey Context**: Source survey name and domain (e.g., "SIPP - economic survey")
4. **Question Text**: Full verbatim text
5. **Output Schema**: Required JSON format with primary/secondary topics, confidence, reasoning
6. **Few-Shot Examples**: 3 exemplar categorizations showing edge cases

**Critical Design Choice**: We provided survey context because identical questions may have different conceptual framings depending on survey purpose. For example, "What is your age?" in a health survey measures health risk factors, while in an education survey it measures demographic characteristics.

### 4.3.3 Serial Processing Architecture

Categorization was executed serially to simplify auditing and avoid restart complications:

**Model-Level Execution**: Models ran sequentially—Claude Haiku 4.5 completed all questions first, then GPT-5-mini processed the same questions. This serial approach simplified debugging, made checkpoint/resume more reliable, and enabled easier auditing of each model's outputs independently.

**Batch-Level Concurrency**: Each model used 6 concurrent API calls processing batches of questions. This balanced throughput against rate limits while keeping execution manageable.

**Error Handling**: 
- Exponential backoff for rate limits (1s → 2s → 4s → 8s → 16s delays)
- Three-strategy JSON parsing (direct parse, regex extraction, fallback parse)
- Checkpoint system tracking progress every 10 batches for resume capability
- Thread-safe file writing with atomic operations to prevent corruption

**Processing Time** (serial execution):
- Claude Haiku 4.5: ~12 minutes (6,987 questions)
- GPT-5-mini: ~67 minutes (6,987 questions)
- Arbitration: ~52 minutes (1,368 questions)
- Total wall time: ~2 hours

## 4.4 Agreement Analysis

### 4.4.1 Metrics

Inter-rater reliability was assessed using multiple metrics:

**Cohen's Kappa (κ)**: Measures agreement beyond chance
- κ = (p_o - p_e) / (1 - p_e)
- where p_o = observed agreement, p_e = expected agreement by chance
- Interpretation: κ > 0.80 = "almost perfect", 0.60-0.80 = "substantial"

**Simple Agreement Rate**: Percentage of identical categorizations
- Topic-level: Both models assign same primary topic
- Subtopic-level: Both models assign same primary subtopic

**Confidence Distributions**: Mean and distribution of model confidence scores (0-1 scale) for agreed vs. disagreed cases

### 4.4.2 Results Summary

Agreement metrics are detailed in Section 7, but key findings:
- **Topic Agreement**: 89.4% (6,218/6,954 valid questions)
- **Subtopic Agreement**: 68.7% (4,778/6,954 valid questions)  
- **Cohen's Kappa (Topics)**: 0.842 ("almost perfect agreement")
- **Cohen's Kappa (Subtopics)**: 0.692 ("substantial agreement")

The lower subtopic agreement reflects genuinely ambiguous granular distinctions (e.g., "Employment Status" vs. "Work Arrangement" for gig economy questions) rather than model failure. These cases were forwarded to arbitration.

## 4.5 Disagreement Resolution

### 4.5.1 Confidence-Based Tiers

Disagreements were stratified into tiers based on minimum model confidence:

| Tier | Min Confidence | Strategy | Count | % |
|------|----------------|----------|-------|---|
| **Very Low** | < 0.50 | Arbitration | 103 | 4.7% |
| **Low** | 0.50-0.70 | Arbitration | 161 | 7.4% |
| **Medium** | 0.70-0.90 | Arbitration | 1,104 | 50.4% |
| **High** | ≥ 0.90 | Auto Dual-Modal | 821 | 37.5% |

**Rationale**: When both models have high confidence (≥0.90) but disagree, the question likely genuinely spans two topics. These were automatically assigned as dual-modal rather than forcing a single categorization. Lower confidence disagreements went to arbitration.

### 4.5.2 Arbitration Protocol

Disagreements requiring arbitration (n=1,368, 62.5% of disagreements) were resolved by Claude Sonnet 4.5, a higher-capability model:

**Input to Arbitrator**:
- Question text and survey context
- Model 1 categorization + reasoning + confidence
- Model 2 categorization + reasoning + confidence  
- Complete Census taxonomy
- Instructions to evaluate both arguments and select or propose new categorization

**Decision Options**:
1. **Pick Model 1** - Model 1's categorization is more accurate
2. **Pick Model 2** - Model 2's categorization is more accurate
3. **Propose New Concept** - Both models missed the correct category
4. **Assign Dual-Modal** - Question genuinely spans two topics

**Arbitration Results** (detailed in Section 7):
- Pick GPT: 522 cases (38.2%)
- Pick Claude: 487 cases (35.6%)
- New concept: 340 cases (24.9%)
- Dual-modal: 19 cases (1.4%)

The high rate of "new concept" decisions indicates both models sometimes converged on incorrect categories, highlighting the value of arbitration over simple majority voting.

### 4.5.3 Dual-Modal Assignment

Questions assigned dual-modal status receive two primary topic/subtopic pairs:
- **Primary**: Higher confidence model's categorization (or arbitrator's first choice)
- **Secondary Primary**: Lower confidence model's categorization (or arbitrator's second choice)

Example dual-modal question:
> "How much income did you receive from Social Security or Railroad Retirement last month?"

- Primary: Economic.Income (96% confident)
- Secondary Primary: Social.Government Programs (88% confident)  
- Reasoning: Question measures income amount (economic) from government programs (social)

**Total Dual-Modal Questions**: 840 (12.0% of valid categorizations)
- 821 auto-assigned (high confidence disagreements)
- 19 arbitrator-assigned (after evaluation)

This dual-modal approach reflects the reality that survey questions often intentionally span concepts, and forcing single categorizations would lose information critical for downstream analysis.

## 4.6 Quality Assurance

### 4.6.1 Categorization Failure Handling

A small number of questions (n=38, 0.5%) could not be categorized successfully:
- Very short questions (< 10 characters): "Yes/No?", "Other"
- Purely administrative text: "END OF SURVEY"
- Malformed question text from data entry errors

These were flagged as `categorization_failed` and excluded from final analysis but retained in the master dataset for completeness.

### 4.6.2 Output Validation

At each pipeline stage, outputs were validated for:
- **Completeness**: Expected number of questions processed
- **Schema Compliance**: Required fields present in correct format
- **Referential Integrity**: All concept labels exist in taxonomy
- **Consistency**: Confidence scores in [0,1], topics match subtopics

Failed validations triggered pipeline halt to prevent propagating errors downstream.

### 4.6.3 Reproducibility

All code, data, and intermediate outputs are version-controlled and documented. The pipeline is fully reproducible given:
- Input data (`PublicSurveyQuestionsMap.csv`)
- Census taxonomy (`census_survey_explorer_taxonomy.json`)  
- API credentials (OpenAI, Anthropic)

Total computational cost: ~$15 in API fees for complete pipeline execution on 6,987 questions.

## 4.7 Computational Infrastructure

**Development Environment**:
- Python 3.10
- Key libraries: pandas 2.0.3, openai 1.12.0, anthropic 0.21.0
- Hardware: MacBook Pro M3 (local development)
- API-based inference (no local GPU required)

**Pipeline Execution**:
- Total runtime: ~2 hours (including arbitration)
- Peak memory: <2GB (streaming JSONL processing)
- Checkpoint/resume capability for interrupted runs
- Fully offline operation after API calls complete

**Version Control**:
- GitHub repository: `federal-survey-concept-mapper`
- Documentation: `docs/pipeline_documentation.md` (technical details)
- Lessons learned: `docs/lessons_learned_embedding_failure.md` (embedding approach)

This methodology represents a scalable, cost-effective approach to survey concept mapping that can process thousands of questions in hours rather than the weeks required for manual analysis. The dual-model architecture with arbitration provides both efficiency and quality assurance, while the dual-modal framework captures the genuine complexity of survey questions that span conceptual boundaries.
