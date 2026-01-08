# 14. Appendices

## Appendix A: Technical Implementation Details

This appendix provides complete technical documentation for reproducibility. The implementation is available in the GitHub repository `federal-survey-concept-mapper`.

### A.1 Pipeline Architecture

The categorization pipeline consists of five sequential stages:

```
┌─────────────────────────────────────────────────────────────────┐
│  Stage 1: Initial Categorization (Serial LLM Processing)        │
│  - Claude Haiku 4.5 processes all 6,987 questions               │
│  - GPT-5-mini processes all 6,987 questions                     │
│  - 6 concurrent workers per model, batches of 10                │
├─────────────────────────────────────────────────────────────────┤
│  Stage 2: Comparison Analysis                                   │
│  - Merge results on question ID                                 │
│  - Calculate agreement metrics (topic, subtopic)                │
│  - Compute Cohen's Kappa                                        │
├─────────────────────────────────────────────────────────────────┤
│  Stage 3: Disagreement Analysis                                 │
│  - Identify failures (both models returned None)                │
│  - Calculate confidence metrics                                 │
│  - Assign confidence tiers                                      │
├─────────────────────────────────────────────────────────────────┤
│  Stage 4: Arbitration                                           │
│  - High confidence (≥0.90): Auto dual-modal                     │
│  - Lower confidence: Claude Sonnet 4.5 arbitration              │
├─────────────────────────────────────────────────────────────────┤
│  Stage 5: Final Reconciliation                                  │
│  - Apply decision tree                                          │
│  - Generate master dataset                                      │
│  - Create summary visualizations                                │
└─────────────────────────────────────────────────────────────────┘
```

### A.2 Prompt Engineering

#### A.2.1 Prompt Structure

Both models received identical structured prompts containing six components:

**1. Task Definition**
```
You are a survey methodologist specializing in federal demographic surveys. 
Your task is to categorize the following survey question according to the 
Census Bureau's published taxonomy at https://www.census.gov/data/data-tools/survey-explorer/topics.html.
```

**2. Taxonomy Structure**
```
The taxonomy has two levels:
- Topic (5 categories): Economic, Social, Housing, Demographic, Government
- Subtopic (152 categories): Income, Health Insurance, Employment Status, ...

[Complete taxonomy hierarchy provided]
```

**3. Survey Context**
```
This question appears in: [Survey Name]
Survey domain: [Brief survey description]
Target population: [Survey respondents]
```

**4. Question Text**
```
Question: "[Full verbatim question text]"
```

**5. Categorization Instructions**
```
Assign:
1. Primary topic and subtopic (most central concept measured)
2. Confidence score (0-1) indicating categorization certainty
3. Brief reasoning explaining your choice

If the question genuinely spans two topics (e.g., income from government 
programs spans Economic and Social), you may assign a secondary topic/subtopic.
However, most questions have a single primary concept.
```

**6. Output Format**
```json
{
  "primary_topic": "Economic",
  "primary_subtopic": "Income",
  "secondary_primary_topic": null,
  "secondary_primary_subtopic": null,
  "confidence": 0.95,
  "reasoning": "Question asks about income amount from all sources..."
}
```

#### A.2.2 Few-Shot Examples

Three examples demonstrated edge cases:

**Example 1: Straightforward Categorization**
- Question: "What is your current marital status?"
- Category: Demographic.Marital Status
- Confidence: 0.98
- Reasoning: Direct demographic characteristic

**Example 2: Survey Context Matters**
- Question: "Do you have health insurance?"
- NHIS context → Social.Health Insurance (health access focus)
- SIPP context → Economic.Health Insurance (economic security focus)

**Example 3: Dual-Modal Question**
- Question: "How much rent do you pay, including government housing subsidy?"
- Primary: Housing.Rent Costs
- Secondary: Economic.Government Assistance

#### A.2.3 Rejected Approaches

**Chain-of-thought reasoning**: Lengthier responses, no accuracy improvement, higher API costs.

**Multiple subtopics (list all relevant)**: Too many false positives, unclear primary concept.

### A.3 Model Configuration

#### A.3.1 API Parameters

**gpt-5-mini (OpenAI)**:
```python
{
  "model": "gpt-5-mini",
  "max_tokens": 500,
  "response_format": {"type": "json_object"}
}
```

**Claude Haiku 4.5 (Anthropic)**:
```python
{
  "model": "claude-haiku-4-5-20241022",
  "max_tokens": 500
}
```

Default API parameters were used for both models. No temperature or sampling parameters were explicitly set.

#### A.3.2 Cost Analysis

**Per-Question Costs**:
- gpt-5-mini: ~$0.00025 per question
- Claude Haiku 4.5: ~$0.00045 per question

**Full Pipeline Costs**:
- Dual categorization: ~$5
- Arbitration (Sonnet): ~$10
- **Total**: ~$15

This represents approximately 0.2% of estimated manual expert review cost (~$7,000 at ~$100/hr × ~70 hours).

### A.4 Batch Processing Architecture

#### A.4.1 Serial Processing Strategy

Models ran sequentially to simplify auditing:
- Claude Haiku 4.5 processed all questions first (~12 minutes)
- GPT-5-mini then processed the same questions (~67 minutes)
- Each model's outputs could be independently audited

Within each model run, 6 concurrent API calls processed batches of 10 questions.

#### A.4.2 Rate Limiting

```python
try:
    response = api_call(batch)
except RateLimitError:
    wait = 2 ** retry_count  # 1s, 2s, 4s, 8s, 16s
    time.sleep(wait)
    retry_count += 1
```

#### A.4.3 Checkpoint System

Progress checkpointed every 10 batches:
```json
{
  "model": "claude-haiku-4-5",
  "last_completed_batch": 247,
  "questions_processed": 2470,
  "timestamp": "2024-12-15T14:32:18",
  "partial_results": "output/results_claude_partial.jsonl"
}
```

### A.5 Output Processing

#### A.5.1 JSON Parsing Strategy

Three-strategy parsing handled formatting issues:

1. **Direct Parse**: 94.2% of responses
2. **Regex Extraction** (from markdown code blocks): 4.7%
3. **Manual Field Extraction**: 1.0%
4. **Parsing failure**: 0.1%

#### A.5.2 Validation

Each response validated for:
- Required fields present
- Topic/subtopic exists in taxonomy
- Confidence in [0, 1] range

### A.6 Environment Specification

```yaml
python: 3.10
dependencies:
  - pandas==2.0.3
  - openai==1.12.0
  - anthropic==0.21.0
  - python-dotenv==1.0.0
  - tqdm==4.66.1
```

---

## Appendix B: Census Bureau Survey Explorer Taxonomy

The complete taxonomy used for categorization is available at:
https://www.census.gov/data/data-tools/survey-explorer/topics.html

**Structure**:
- 5 Topics: Economic, Social, Housing, Demographic, Government
- 152 Subtopics distributed across topics

**Topic Distribution**:
| Topic | Subtopics |
|-------|-----------|
| Economic | 48 |
| Social | 54 |
| Housing | 17 |
| Demographic | 23 |
| Government | 10 |

---

## Appendix C: Sample Categorizations

### C.1 Straightforward Categorizations

| Question | Topic | Subtopic | Confidence |
|----------|-------|----------|------------|
| "What is your age?" | Demographic | Age | 0.98 |
| "Are you currently employed?" | Economic | Employment Status | 0.96 |
| "Do you own or rent your home?" | Housing | Tenure | 0.97 |

### C.2 Dual-Modal Examples

| Question | Primary | Secondary | Reasoning |
|----------|---------|-----------|-----------|
| "How much income did you receive from Social Security?" | Economic.Income | Social.Government Programs | Financial amount from government program |
| "Does your employer offer health insurance?" | Economic.Employment Benefits | Social.Health Insurance | Employment benefit that is health coverage |

### C.3 Context-Sensitive Examples

**Same question, different surveys:**
- "What is your age?"
  - In NHIS (health survey): Maps to health risk factor context
  - In ACS (demographic survey): Maps to demographic characteristic context

---

## Appendix D: Detailed Agreement Statistics

### D.1 Cohen's Kappa Calculation

**Topic Level**: κ = 0.842
- Observed agreement: 89.4%
- Expected agreement by chance: 32.1%

**Subtopic Level**: κ = 0.692
- Observed agreement: 68.7%
- Expected agreement by chance: 8.3%

### D.2 Confidence Tier Distribution

Among disagreements (n=2,189):
| Tier | Min Confidence | Count | % |
|------|---------------|-------|---|
| Very Low | < 0.60 | 103 | 4.7% |
| Low | 0.60-0.75 | 161 | 7.4% |
| Medium | 0.75-0.90 | 1,104 | 50.4% |
| High | ≥ 0.90 | 821 | 37.5% |

### D.3 Most Common Topic Boundary Disagreements

| Topic Pair | Disagreements | % of All Disagreements |
|------------|---------------|------------------------|
| Economic ↔ Social | 412 | 30.1% |
| Social ↔ Demographic | 198 | 14.5% |
| Economic ↔ Demographic | 156 | 11.4% |

---

## Appendix E: Data and Code Availability

### E.1 Outputs

| File | Description |
|------|-------------|
| `master_dataset.csv` | Complete question-level results (6,987 rows) |
| `survey_concept_matrix.csv` | Survey × concept aggregation |
| `agreement_summary.csv` | Agreement metrics |

### E.2 Repository

GitHub: `federal-survey-concept-mapper`

**Includes**:
- All analysis scripts
- Pipeline documentation
- Intermediate outputs
- Visualization code

**Excludes**:
- API keys (user-provided)
- Raw survey PDFs (proprietary)

### E.3 Reproducibility Notes

- Default API parameters used (no explicit temperature settings)
- Exact reproducibility requires archiving specific model versions
- FedRAMP-authorized services (Azure OpenAI, Claude on AWS Bedrock) available for agencies with compliance requirements

---

## Appendix F: Key Visualizations

This appendix contains the primary visualizations referenced throughout the report.

### F.1 Model Agreement Overview

**Figure 2** presents the agreement analysis between the two categorization models (gpt-5-mini and Claude Haiku 4.5), showing the distribution of agreement outcomes and confidence scores.

![Figure 2: Model Agreement Analysis](figures/figure_02_model_agreement.png)

*Figure 2: Comparison of dual-LLM categorization results showing agreement rates at topic and subtopic levels, confidence distributions, and disagreement patterns.*

### F.2 Topic Distribution by Subtopic

**Figure 4** shows the distribution of survey questions across all subtopics within the Census Bureau taxonomy, grouped by primary topic.

![Figure 4: Topic Distribution by Subtopic](figures/figure_04_topic_distribution.png)

*Figure 4: Horizontal bar chart showing question counts per subtopic, revealing the concentration of federal survey content in Economic and Social domains.*

---

## Appendix G: Why Embedding Approaches Failed

Before developing the LLM-based pipeline, we attempted semantic categorization using RoBERTa-large embeddings. This approach failed completely, but the failure is instructive for future research in this domain.

### G.1 The Approach

The initial methodology computed 1024-dimensional embeddings for all 6,987 survey questions and 152 taxonomy concept labels. Cosine similarity between each question embedding and each concept embedding would identify the closest matching concept. This approach has proven effective for semantic similarity tasks in other domains.

### G.2 Why It Failed

Federal survey questions exhibit **extreme baseline similarity** to each other. The mean pairwise similarity across all questions was **0.9916** (standard deviation: 0.0087). Even with survey context appended to question text, similarity distributions remained nearly uniform.

This occurs because survey questions share standardized linguistic patterns:
- Similar sentence structures ("During the past 12 months, did you...")
- Common vocabulary (income, employment, household, receive, amount)
- Consistent formality and register

When all questions are uniformly similar to each other, they are also uniformly similar to concept labels. Every question appeared roughly equally close to every concept, making differentiation impossible.

### G.3 The Information Asymmetry Problem

The fundamental issue is **information asymmetry** between questions and labels:
- Questions: 100+ words, detailed, specific
- Concept labels: 1-3 words, abstract, sparse

Embedding models excel at comparing texts of similar specificity. Comparing a detailed paragraph to a single word produces uninformative similarity scores because the embedding spaces don't align.

### G.4 Implications for Future Work

This failure suggests that **embedding-based approaches may be unsuitable for survey-to-taxonomy mapping** in any domain with:
1. Highly standardized source texts (high baseline similarity)
2. Abstract target categories (sparse labels)
3. Context-dependent meaning (same text → different concepts based on context)

LLMs succeed where embeddings fail because they perform **semantic reasoning** rather than similarity matching. An LLM understands that a detailed income question maps to the abstract concept "Income" through inference about what the question measures, not through geometric proximity in embedding space.

This finding saved substantial effort by ruling out embedding-based approaches early, allowing resources to focus on the LLM methodology that proved successful.
