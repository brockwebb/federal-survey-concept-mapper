# Construct Validity Evidence

## The Argument

Three independently developed LLM architectures were given identical survey harmonization tasks.
High agreement across these diverse systems provides evidence that:
1. The task is well-defined (not ambiguous)
2. Results reflect genuine question properties (not model artifacts)
3. The classification schema is learnable and consistent

## Evidence

### Rater Convergence
- Three raters from different vendors (OpenAI, Anthropic, Google)
- Different architectures, training data, and organizational priorities
- Achieved Fleiss κ = 0.611 (substantial agreement) on L1 barrier categories
- Pairwise agreement consistent across all pairs (range: 0.585-0.655)
- Binary consolidability agreement: Fleiss κ = 0.621 (substantial)

**Key Finding:** Models independently trained on different data converge on survey harmonization judgments,
suggesting the classification framework captures real properties of survey questions.

### Arbitrator Convergence
- Three flagship models tasked with resolving disagreements
- Achieved κ = 0.843 on feasibility verdicts (almost perfect)
- Convergence INCREASES at arbitration stage (0.611 rater → 0.843 arbitrator)
- Suggests disagreements are resolvable with more reasoning capacity

**Interpretation:** The improvement from rater to arbitrator stage indicates that initial disagreements
stem from classification complexity, not fundamental ambiguity in the harmonization framework.

### Behavioral Diversity as Strength
Different arbitrators exhibit distinct decision-making styles:
- **Google (7% synthesis):** Deferential, prefers existing rater judgments
- **OpenAI (59% synthesis):** Balanced approach, moderate novel integration
- **Anthropic (77% synthesis):** Active synthesis, integrates multiple perspectives

This diversity means the ensemble captures multiple valid interpretive frames. No single model
dominates the final verdicts—instead, the ensemble balances conservative and synthetic approaches.

### Single-Model Risk Quantified
Using only one model would produce substantially different results:
- OpenAI alone: 17.3% feasibility divergence from ensemble majority
- Anthropic alone: 5.9% divergence
- Google alone: 5.3% divergence

**Implication:** The multi-model approach provides robustness that single-model systems cannot offer.
For a 1,598-pair analysis, 5-17% error rate differences are meaningful.

## Limitations

- **Google data incomplete:** Arbitrator limited to CPS subset (503 of 1,598 pairs) due to rate limits
- **Rater tier:** Rater models are "fast" tier; flagship models might show different initial patterns
- **Training overlap:** All models trained on similar internet corpora—not truly independent knowledge bases
- **Task-specific:** Convergence applies to survey harmonization; generalization to other domains untested

## Conclusion

The convergent validity evidence supports treating the ensemble verdicts as reliable classifications
suitable for survey harmonization analysis. The multi-model approach:
1. Reduces single-model bias (demonstrated by divergence analysis)
2. Captures diverse valid interpretations (shown by synthesis rate variation)
3. Improves with reasoning depth (rater → arbitrator improvement)

**Recommendation:** For production survey harmonization, use multi-model ensemble with arbitration
for maximum reliability. Single-model approaches introduce 5-17% additional classification variance.
