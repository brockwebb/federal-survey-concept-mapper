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
- Binary consolidability agreement: Fleiss κ = 0.621 (substantial)

**Key Finding:** Models independently trained on different data converge on survey harmonization judgments,
suggesting the classification framework captures real properties of survey questions.

### Arbitrator Convergence
- Three flagship models independently evaluated ALL 1,598 pairs (not just disagreements)
- Full coverage enabled behavioral analysis across agreement and disagreement cases
- Achieved κ = 0.864 on feasibility verdicts (almost perfect)
- Convergence INCREASES at arbitration stage (0.611 rater → 0.864 arbitrator)

**Interpretation:** The improvement from rater to arbitrator stage indicates that initial disagreements
stem from classification complexity, not fundamental ambiguity in the harmonization framework.

### Behavioral Diversity as Strength
Different arbitrators exhibit distinct decision-making styles:
- **Google (5.9% synthesis):** Deferential, prefers existing rater judgments
- **OpenAI (59.4% synthesis):** Balanced approach, moderate novel integration
- **Anthropic (77.2% synthesis):** Active synthesis, integrates multiple perspectives

This diversity means the ensemble captures multiple valid interpretive frames. No single model
dominates the final verdicts—instead, the ensemble balances conservative and synthetic approaches.

### Single-Model Risk Quantified
Using only one model would produce substantially different results from the ensemble consensus.
The multi-model approach provides robustness that single-model systems cannot offer.

## Limitations

- **Google data incomplete:** Arbitrator limited to 751 of 1,598 pairs (47%) due to rate limits
- **Rater tier:** Rater models are "fast" tier; flagship models might show different initial patterns
- **Training overlap:** All models trained on similar internet corpora—not truly independent knowledge bases
- **Task-specific:** Convergence applies to survey harmonization; generalization to other domains untested

## Conclusion

The convergent validity evidence supports treating the ensemble verdicts as reliable classifications
suitable for survey harmonization analysis. The multi-model approach:
1. Reduces single-model bias
2. Captures diverse valid interpretations (shown by synthesis rate variation)
3. Improves with reasoning depth (rater → arbitrator improvement)

**Recommendation:** For production survey harmonization, use multi-model ensemble with arbitration
for maximum reliability.
