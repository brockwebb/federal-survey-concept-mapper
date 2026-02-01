# Decision 016: Two-Axis Triage for Pair Prioritization

**Date:** 2026-01-31  
**Status:** VALIDATED (bake-off complete, sober framing adopted)  
**Authors:** Brock Webb, Claude

---

## Context

Stage 4 requires prioritizing question pairs for expert review. Binary F1/F2/F3 classification doesn't tell us which pairs need human attention.

**Problem:** How do we route pairs to different review processes based on classifier agreement?

**Decision:** Use two-axis triage (Direction × Stability) instead of single-score ranking.

---

## What We Tried

Implemented 4 scoring methods and compared them:

---

## The Ensemble Hypothesis

No single scoring method captures all relevant signal. Each method makes different assumptions and may be sensitive to different aspects of the data:

| Method | What it captures | Blind spots |
|--------|------------------|-------------|
| Composite | Feasibility × Agreement (simple) | Treats agreement as linear |
| Entropy | Information-theoretic uncertainty | Ignores feasibility direction |
| Bayesian | Posterior probability with uncertainty | Sensitive to prior choice |
| Borda | Ordinal rank aggregation | Loses magnitude information |

**Ensemble rationale:** If all 4 methods rank a pair highly → robust confidence. If methods diverge → genuine ambiguity worth flagging.

This follows the bias-variance tradeoff principle: individual methods may have high precision but systematic blind spots (bias). Combining diverse methods reduces bias at modest variance cost.

---

## Method 1: Composite Score

### What it is
A weighted product of feasibility level and agreement strength.

```
Score = Feasibility_weight × Agreement_weight

Feasibility: F1=3, F2=2, F3=1  
Agreement: HIGH=1.0, MODERATE=0.67, LOW=0.33

Range: 0.33 to 3.0
```

### Why it works
- **Feasibility weight** captures direction (consolidable vs. not)
- **Agreement weight** captures confidence (did classifiers agree?)
- Product ensures both matter — high feasibility with low agreement gets penalized

### Assumptions
- Linear relationship between agreement levels
- Feasibility categories are ordinally scaled (F1 > F2 > F3)
- Independence between feasibility and agreement (multiplicative)

### Precedent
Weighted scoring is standard in multi-criteria decision analysis (MCDA). The specific weights (3/2/1 and 1.0/0.67/0.33) are interpretable defaults that can be sensitivity-tested.

### Citation queries for Perplexity
- "multi-criteria decision analysis weighted scoring methods"
- "composite scoring inter-rater agreement weighting"
- "ordinal scale weighting survey research"

---

## Method 2: Entropy-Based Confidence

### What it is
Shannon entropy measures the "disorder" or uncertainty in the vote distribution. Lower entropy = more agreement = more confidence.

```
H = -Σ p(vote) × log₂(p(vote))

Score = 1 - (H / H_max)  # inverted, normalized
```

For 3 categories (F1/F2/F3), H_max = log₂(3) ≈ 1.58 bits.

### Why it works (the energy landscape hypothesis)

**Key insight:** Each LLM classifier is a sophisticated probabilistic sampler traversing a high-dimensional solution space. The classification output represents where that sampler "settled" — a local minimum in some implicit energy landscape.

When multiple independent samplers (3 raters + 3 arbitrators) converge on the same classification:
- This is evidence of a **stable attractor** — a deep basin in the energy landscape
- Multiple independent trajectories fell into the same well
- The "answer" is robust to sampling variation

When samplers diverge:
- The "answer" lives in a **flat region** of the energy landscape
- Small perturbations → different outputs
- The classification is inherently unstable or genuinely ambiguous

**Entropy quantifies this:** Low entropy = deep basin, high agreement, stable answer. High entropy = flat landscape, disagreement, unstable answer.

This framing treats LLM ensembles not as voters but as **physical systems seeking energy minimization**. Whether they find global or local minima is unknown, but convergence suggests robustness.

### Assumptions
- Classifiers are approximately independent (different models, different prompts)
- Convergence implies stability, not correctness (but stability is valuable)
- The "energy landscape" metaphor is useful even if not literally true

### Precedent
- Shannon entropy is foundational in information theory (Shannon 1948)
- Entropy as uncertainty measure in ensemble methods (Kuncheva 2003)
- Energy-based models in machine learning (LeCun et al. 2006)

### Citation queries for Perplexity
- "Shannon entropy inter-rater reliability measurement"
- "entropy as confidence measure ensemble classification"
- "energy-based models machine learning convergence"
- "ensemble classifier agreement entropy information theory"

### Novel contribution (potentially)
Using entropy as a confidence measure for multi-LLM ensemble classification on inherently subjective/fuzzy categorization tasks appears underexplored in the literature we reviewed. The energy landscape framing provides useful intuition, though the core insight (entropy ≠ vote-count) is mathematically unsurprising. See "Sober Assessment" section below for post-review framing.

---

## Method 3: Bayesian Posterior

### What it is
Estimate P(truly consolidable | observed votes) using Bayesian updating.

```
Prior: Beta(α, β) calibrated to base rate (~20% consolidable)
Likelihood: Binomial (votes as Bernoulli trials)
Posterior: Beta(α + successes, β + failures)

Score = Posterior mean = (α + successes) / (α + β + n)
```

### Why it works
- **Incorporates prior knowledge:** We know ~20% of pairs are consolidable from data
- **Handles uncertainty:** Fewer votes → posterior stays closer to prior
- **Principled updating:** More agreement → posterior moves toward observed rate

### Assumptions
- Votes are conditionally independent given true consolidability
- Binary reduction (F1/F2 = success, F3 = failure) is appropriate
- Prior is reasonably calibrated (weak prior, α+β=2)

### Precedent
Beta-Binomial is the standard conjugate model for binary outcomes. Bayesian approaches to inter-rater reliability are well-established (Agresti & Hitchcock 2005).

### Citation queries for Perplexity
- "Bayesian inter-rater reliability beta-binomial"
- "Bayesian posterior classification confidence"
- "conjugate prior inter-rater agreement"

---

## Method 4: Borda Count (Rank Aggregation)

### What it is
Each classifier assigns ordinal points. Sum points across classifiers.

```
Points: F1=2, F2=1, F3=0
Score = Σ points / max_possible

Range: 0 (all F3) to 1 (all F1)
```

### Why it works
- **Non-parametric:** Makes no distributional assumptions
- **Ordinal only:** Respects that F1 > F2 > F3 without assuming equal intervals
- **Robust to outliers:** One extreme vote can't dominate

### Assumptions
- Ordinal scale only (doesn't assume F1-F2 gap equals F2-F3 gap)
- All classifiers weighted equally
- Points assignment (2/1/0) is reasonable

### Precedent
Borda count originates in social choice theory (Borda 1781). Widely used in rank aggregation, voting systems, and meta-analysis.

### Citation queries for Perplexity
- "Borda count rank aggregation machine learning"
- "ordinal voting methods inter-rater reliability"
- "non-parametric rank aggregation ensemble methods"
- "social choice theory classifier combination"

---

## Ensemble Combination

### Approach
1. Normalize each score to [0, 1] range (min-max normalization)
2. Compute ensemble score as mean of normalized scores
3. Rank by ensemble score

### Why mean (not weighted)?
- No prior reason to weight methods differently
- Equal weighting is the maximum entropy choice (least informative prior)
- Can analyze post-hoc if one method dominates

### Alternative: Rank-based ensemble
Instead of averaging scores, average ranks. More robust to score distribution differences.

---

## Validation Plan

1. **Correlation matrix:** Do methods agree? High correlation → redundant. Low → capturing different signal.

2. **Divergent pairs:** Where do methods disagree most? Manual inspection for insight.

3. **Face validity:** Do top-ranked pairs look obviously consolidable? Do bottom-ranked look obviously not?

4. **Sensitivity analysis:** How do rankings change with different weights/priors?

---

## Bake-Off Results (2026-01-31)

### Key Finding: Entropy is Orthogonal

| Method Pair | Spearman ρ |
|-------------|------------|
| Bayesian ↔ Borda | 0.909 (redundant) |
| Entropy ↔ Bayesian | 0.083 (orthogonal) |
| Entropy ↔ Borda | 0.073 (orthogonal) |
| Composite ↔ others | 0.52-0.62 (moderate) |

### What This Means

- Bayesian and Borda measure the same thing (vote direction) — redundant
- Entropy measures something different (agreement strength) — distinct signal
- Simple ensemble averaging doesn't work — redundant methods dominate

### Revised Decision: Two-Axis Triage

Instead of a single score, use two dimensions:

| Axis | Measure | Question |
|------|---------|----------|
| Direction | Borda | Did classifiers lean toward consolidable? |
| Stability | Entropy | Did classifiers agree with each other? |

This creates four quadrants for routing:
- **Q1 (High/High):** Accept with confidence → auto-process
- **Q2 (Low/High):** Reject with confidence → low priority
- **Q3 (High/Low):** Accept but uncertain → human review priority
- **Q4 (Low/Low):** Genuinely ambiguous → human review secondary

---

## Sober Assessment

### What This Is
- A useful operational framework for triage
- An empirically curious observation (near-zero correlation when negative expected)
- Potentially task-specific (subjective classification without ground truth)

### What This Is NOT
- A theoretical discovery
- A novel mathematical insight (entropy ≠ vote-count by definition)
- Necessarily generalizable to other tasks

### Why the Near-Zero Correlation Is Curious

In typical ensembles, high consensus → low entropy (strong agreement). The expected correlation is *negative*. Our ρ ≈ 0 is unexpected.

Possible explanations (not validated):
1. Subjective task without ground truth
2. Middle-case vote patterns (4-2-0 vs 3-2-1 splits)
3. Borda metric artifact
4. Task-specific phenomenon

Parked for future exploration if pattern replicates elsewhere.

---

## References

See `docs/literature/decision_016_citations.md` for gathered citations:
- Shannon (1948) — Information theory
- Hopfield (1982) — Energy landscapes
- Kuncheva (2003) — Ensemble diversity
- MUSE (2025), DiverseAgentEntropy (2024) — Multi-LLM uncertainty
