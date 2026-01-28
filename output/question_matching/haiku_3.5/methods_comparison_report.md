# Question-Level Matching: Methods Comparison

## Dataset

| Metric | Count |
|--------|-------|
| FoodAPS questions analyzed | 41 |
| ACS questions analyzed | 23 |
| Candidate pairs evaluated | 107 |
| Subtopics | SNAP (22 pairs), Age (36), Sex (9), Race (12), Relationship (12), Marital (16) |

## Prior Finding: Embedding Similarity Failure

Our earlier analysis using RoBERTa-large embeddings demonstrated a critical limitation:
- **Mean cosine similarity**: ~0.99 across all question pairs
- **Problem**: Standardized federal survey language creates uniformly high semantic similarity
- **Result**: Embeddings cannot discriminate between truly duplicative questions and merely similar ones

This motivated exploring alternative approaches: fuzzy string matching and LLM-based classification.

## Fuzzy String Matching Results

### Score Distributions by Subtopic

| Subtopic | fuzz_ratio | fuzz_partial | fuzz_token_set | jaccard |
|----------|------------|--------------|----------------|---------|
| SNAP | 39.2 | 48.4 | 49.4 | 20.6 |
| Age | 38.8 | 52.0 | 47.3 | 14.7 |
| Sex | 26.7 | 32.6 | 25.0 | 3.3 |
| Race | 33.7 | 53.5 | 38.1 | 17.9 |
| Relationship | 36.7 | 48.7 | 41.8 | 13.0 |
| Marital | 35.7 | 43.9 | 37.3 | 4.9 |

### Threshold-Based Classification

| Classification | Count | % |
|---------------|-------|---|
| Exact (≥90) | 0 | 0.0% |
| Near (70-89) | 6 | 5.6% |
| Distinct (<70) | 101 | 94.4% |

### Observations

**Where fuzzy matching works well:**
- Simple demographic questions with consistent wording (e.g., "What is your date of birth?")
- Questions with high lexical overlap

**Where fuzzy matching fails:**
- Questions with same concept but different phrasing
- Questions with different reference periods (fuzzy sees "SNAP" keywords, misses temporal difference)
- Questions asking related but distinct information

## LLM Classification Results

### Classification Distribution

| Classification | Count | % |
|---------------|-------|---|
| related_but_distinct | 35 | 32.7% |
| not_comparable | 28 | 26.2% |
| near_duplicate | 27 | 25.2% |
| reference_period_mismatch | 12 | 11.2% |
| response_format_mismatch | 4 | 3.7% |
| exact_duplicate | 1 | 0.9% |

### Consolidation Potential

If FoodAPS and ACS respondents were linked (same individuals):

| Potential | Count | % | Meaning |
|-----------|-------|---|---------|
| Yes (droppable) | 5 | 4.7% | FoodAPS question could be replaced by ACS |
| Partial | 69 | 64.5% | Some information overlap, but not fully substitutable |
| No | 33 | 30.8% | Questions collect distinct information |

## Methods Comparison

### Agreement Matrix

| Fuzzy \ LLM | exact_duplicate | near_duplicate | not_comparable | reference_period_mismatch | related_but_distinct | response_format_mismatch |
|---|---|---|---|---|---|---|
| distinct | 1 | 23 | 28 | 12 | 33 | 4 |
| near | 0 | 4 | 0 | 0 | 2 | 0 |

### Key Findings

1. **Fuzzy False Negatives (24 cases)**: Fuzzy says "distinct" but LLM identifies as near-duplicate
   - Caused by different phrasing for same concept
   - Example: "What is your date of birth?" vs "What is Person 1's age and date of birth?"

2. **Fuzzy False Positives (2 cases)**: Fuzzy says similar but LLM says distinct
   - High lexical overlap masks conceptual differences
   - Example: Questions about same topic but asking different specific information

3. **Reference Period Mismatches (12 cases)**: 
   - Fuzzy matching cannot detect temporal differences
   - Example: "Did you receive SNAP in the **last 30 days**?" vs "**In the past 12 months**, did you receive SNAP?"
   - This is critical for data harmonization

### Example: Reference Period Mismatch

> **FoodAPS**: "Have you received benefits from the Supplemental Nutrition Assistance Program in the last 30 days?"
> **ACS**: "IN THE PAST 12 MONTHS, did you or any member of this household receive benefits from SNAP?"
> 
> **Fuzzy token_set score**: 63 (classified as "distinct")
> **LLM classification**: reference_period_mismatch
> **LLM reasoning**: "Questions ask about same SNAP benefit receipt but differ in time window: 30 days vs 12 months"

### Value of LLM Reasoning

LLM classification captures information that string similarity cannot:

1. **Temporal alignment**: Identifies questions that measure the same concept at different time scales
2. **Response format differences**: Detects when same concept has different answer formats (yes/no vs amount)
3. **Specificity differences**: Distinguishes between asking for one piece of info vs multiple
4. **Consolidation assessment**: Provides actionable guidance on data harmonization potential

## Conclusions

1. **Embedding similarity fails** because federal survey questions share standardized vocabulary, creating uniformly high similarity scores that cannot discriminate duplicates from related questions.

2. **Fuzzy string matching** captures lexical overlap but:
   - Misses conceptually similar questions with different phrasing (24 false negatives)
   - Cannot detect reference period differences
   - Has high false negative rate (22.4%)

3. **LLM classification adds value** by:
   - Providing nuanced classifications (6 categories vs 3)
   - Detecting temporal mismatches critical for data harmonization
   - Explaining reasoning for each classification
   - Assessing consolidation potential directly

4. **Estimated consolidation potential**: 
   - 5 of 107 pairs (4.7%) are fully substitutable
   - 69 pairs (64.5%) have partial overlap
   - With person-linked data, 69.2% of pairs could benefit from harmonization

## Files Generated

| File | Description |
|------|-------------|
| `foodaps_questions_snap_demo.csv` | FoodAPS questions in target subtopics |
| `acs_questions_snap_demo.csv` | ACS questions in target subtopics |
| `candidate_pairs.csv` | All question pairs by subtopic |
| `fuzzy_matching_results.csv` | Fuzzy similarity scores and classifications |
| `llm_classification_results.csv` | LLM classifications with reasoning |
| `methods_comparison_summary.csv` | Side-by-side comparison |
| `validation_template.csv` | Template for human validation |

---
*Generated: 2026-01-26 17:07*
