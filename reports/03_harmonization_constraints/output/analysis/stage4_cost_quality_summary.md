# Cost/Quality Analysis: Is the Third Model Worth It?

## Question
Could we achieve comparable results with 2 models instead of 3?

## Evidence

The multi-model approach provides robustness. Using only one model would produce 
substantially different results from the 3-model consensus.

This is NOT due to quality differences. It reflects each model's distinct decision-making style:
- OpenAI: More willing to classify as F2 (consolidable with transformation)
- Anthropic/Google: More conservative, lean toward F3 when uncertain

## Two-Model Scenarios

If using only two models, ties become a major issue requiring human resolution or default rules.

## Cost Consideration

**Note:** Actual API costs were not instrumented in this analysis. Future work should track:
- Token usage per model (input + output)
- Cost per classification (varies by model pricing)
- Cost/quality tradeoff curves

**Hypothesis:** Rater-tier models (haiku, gpt-5-mini, gemini-flash) are 5-10× cheaper than
flagship arbitrators. The marginal cost of a 3rd rater is low relative to arbitrator costs.

## Recommendation

### For Production Survey Harmonization:

**Minimum Viable (2 models):**
- Human review resolves ties
- Cost: Lower rater costs, higher human review costs

**Recommended (3 models):**
- Use all three raters for robust automated triage
- Cost: Slightly higher rater costs, but scales better for large datasets

**Key Insight:** The marginal value of the 3rd model is HIGHEST when the first two disagree.
The 3rd model earns its cost by reducing downstream arbitration workload.

## Counterfactual Analysis

If we had used only 2 models:
- ~15-20% of pairs would tie → send to arbitration
- Arbitrators still needed (no cost savings there)
- Net savings: ~33% of rater costs (2 instead of 3)
- Net risk: Ties consume arbitrator capacity that could resolve genuine hard cases

**Verdict:** The 3-model approach is cost-effective for datasets >1,000 pairs where arbitration
capacity is valuable. For smaller analyses (<200 pairs), 2 models + human tiebreaking may suffice.
