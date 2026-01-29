# 6. Implementation Overview

This section summarizes the technical implementation. Complete details including prompt templates, API configurations, batch processing architecture, and code examples are provided in **Appendix A: Technical Implementation Details**.

## 6.1 Key Implementation Decisions

**Prompt Engineering**: Each model received structured prompts containing the task definition, complete Census taxonomy, survey context, question text, and output format specification. Three few-shot examples demonstrated edge cases including context-sensitive questions and dual-modal assignments. Prompt optimization testing rejected chain-of-thought reasoning (higher cost, no accuracy gain) and multiple subtopic assignment (too many false positives).

**Serial Model Execution**: Models ran sequentially rather than in parallel—Claude Haiku 4.5 processed all questions first, then GPT-5-mini. This simplified debugging, checkpoint/resume logic, and independent auditing of each model's outputs. Within each model run, 6 concurrent API calls processed batches of 10 questions.

**Robust Error Handling**: The pipeline implemented exponential backoff for rate limits, three-strategy JSON parsing (direct, regex extraction, field extraction), and checkpoint saves every 10 batches enabling resume after interruption.

## 6.2 Processing Metrics

| Stage | Time | Cost |
|-------|------|------|
| Claude Haiku 4.5 (6,987 questions) | ~12 minutes | ~$3 |
| GPT-5-mini (6,987 questions) | ~67 minutes | ~$2 |
| Arbitration (1,368 questions) | ~52 minutes | ~$10 |
| **Total** | **~2 hours** | **~$15** |

## 6.3 Reproducibility

The complete implementation is available in the project GitHub repository (`federal-survey-concept-mapper`). Dependencies are minimal: Python 3.10, pandas, openai, anthropic, and standard scientific computing libraries. Default API parameters were used for both models.

Full technical specifications, prompt templates, validation procedures, and code snippets are provided in **Appendix A**.
