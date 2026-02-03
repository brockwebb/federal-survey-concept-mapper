# Cost/Quality Analysis: Is the Third Model Worth It?

## Question
Could we achieve comparable results with 2 models instead of 3?

## Evidence

### Single-Model Divergence from 3-Model Majority

| Model | Feasibility Divergence | Pairs Affected | Implication |
|-------|----------------------|----------------|-------------|
| **OpenAI** | 17.3% | ~277 of 1,598 | Would miss substantial consensus verdicts |
| **Anthropic** | 5.9% | ~94 of 1,598 | Would miss ~6% consensus verdicts |
| **Google** | 5.3% | ~85 of 1,598 | Would miss ~5% consensus verdicts |

**Source:** `stage2_agreement_metrics.json` - multimodel_value.single_model_risk

## Interpretation

OpenAI as solo rater would produce substantially different results from the 3-model consensus.
Anthropic and Google individually are closer to the ensemble, but still diverge on 5-6% of
cases—meaningful variance for a 1,598-pair analysis.

This is NOT due to quality differences. It reflects each model's distinct decision-making style:
- OpenAI: More willing to classify as F2 (consolidable with transformation)
- Anthropic/Google: More conservative, lean toward F3 when uncertain

## Two-Model Scenarios

If using only two models, ties become a major issue:

### Tie Frequency by Pair

| Pair | L1 Disagreement | Feasibility Disagreement | Combined |
|------|----------------|-------------------------|----------|
| **OA + AN** | 12.1% (194/1,598) | 23.2% (370/1,598) | Moderate ties |
| **OA + GO** | 14.0% (223/1,598) | 22.1% (353/1,598) | Higher ties |
| **AN + GO** | 14.8% (236/1,598) | 11.0% (176/1,598) | **Lowest ties** |

**Analysis:** Anthropic + Google is the most aligned pair, minimizing tie scenarios. However,
11-14% ties still require resolution via tiebreaker (human review or default rule).

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
- Use Anthropic + Google pair (lowest disagreement rate: 11% feasibility)
- Human review resolves ties
- Cost: Lower rater costs, higher human review costs

**Recommended (3 models):**
- Use all three raters for robust automated triage
- Arbitrators resolve disagreements (no human needed for initial pass)
- Cost: Slightly higher rater costs, but scales better for large datasets

**Key Insight:** The marginal value of the 3rd model is HIGHEST when the first two disagree.
With 11-23% disagreement rates across pairs, the 3rd model earns its cost by reducing downstream
arbitration workload.

## Counterfactual Analysis

If we had used only 2 models:
- ~15-20% of pairs would tie → send to arbitration
- Arbitrators still needed (no cost savings there)
- Net savings: ~33% of rater costs (2 instead of 3)
- Net risk: Ties consume arbitrator capacity that could resolve genuine hard cases

**Verdict:** The 3-model approach is cost-effective for datasets >1,000 pairs where arbitration
capacity is valuable. For smaller analyses (<200 pairs), 2 models + human tiebreaking may suffice.
