# Stage 4 Methodological Framework: Ensemble Scoring for Consolidability Ranking

**Created:** 2026-01-31  
**Updated:** 2026-01-31 (post-bakeoff, post-review)  
**Author:** Brock Webb / Claude  
**Status:** Operationalized for project use

---

## Honest Assessment (Post-Review)

**What this is:** Operational instrumentation for prioritizing human review in a subjective classification task.

**What this is NOT:** A novel theoretical discovery about LLM ensembles.

### The Sober Framing

We found that Shannon entropy and vote-count methods (Bayesian, Borda) are empirically uncorrelated (ρ ≈ 0.07-0.08) in our data. This is:

- **Mathematically unsurprising:** Entropy measures distribution shape, vote-count measures distribution center. They're different statistics.
- **Empirically mildly interesting:** Usually these correlate (high consensus → low entropy). The near-zero correlation suggests our data is dominated by "middle cases" where this relationship breaks down.
- **Operationally useful:** We can create a 2D prioritization matrix for human review.

### What We're NOT Claiming

- ❌ This is a fundamental property of LLM ensembles
- ❌ This generalizes to supervised tasks with ground truth
- ❌ The energy-landscape metaphor is literally true
- ❌ This is peer-review novel

### What We ARE Claiming

- ✅ In *this* subjective task, entropy provides a stability signal independent of vote direction
- ✅ A two-axis framework (direction × stability) enables better triage than vote-thresholding alone
- ✅ This is useful instrumentation for our specific problem

### Why the Expected Correlation Vanished (Open Question)

Usually: strong consensus → high vote count AND low entropy. They should be negatively correlated.

Our ρ ≈ 0 suggests something about:
- The subjective nature of the task (no "right answer" to converge on)
- The distribution of cases (many 4-2-0 and 3-2-1 splits where the relationship breaks down)
- The specific Borda scoring (decouples win magnitude from voter confusion)

This is the genuinely curious bit — worth investigating later, not central to project completion.

---

## The Core Problem

We have pair-level classifications (F1/F2/F3) from an ensemble of 6 independent LLM classifiers (3 raters + 3 arbitrators). The binary question "is this pair consolidable?" is insufficient for stakeholders who need:

1. **Prioritized lists** — Which pairs to review first?
2. **Confidence assessment** — How certain is the classification?
3. **Edge case identification** — Where is human judgment most needed?

A continuous score that captures both *direction* (consolidable vs not) and *confidence* (agreement strength) enables all three.

---

## Theoretical Framing: LLMs as Stochastic Samplers in an Energy Landscape

### The Intuition

Each LLM classifier is a sophisticated probabilistic sampler. When we query "is this pair consolidable?", the model traverses a high-dimensional solution space shaped by its training, architecture, and the specific input context. The output is a sample from this space.

**Key insight:** When multiple independent samplers converge on the same classification, that's evidence of a **stable attractor** — a low-energy basin in the solution landscape that multiple trajectories fall into despite different starting conditions and perturbations.

### Physical Analogy

Think of a ball rolling on a hilly surface:
- **Deep basin (low energy):** Ball settles reliably into the same spot. Multiple trials → same result. *High agreement = stable classification.*
- **Flat plateau (high energy):** Ball's final position depends on tiny initial differences. Multiple trials → scattered results. *Low agreement = unstable classification, genuinely ambiguous.*
- **Ridge between basins:** Ball could go either way. *Moderate agreement = edge case, context-dependent.*

### Why This Matters

This framing suggests that **agreement among diverse LLM classifiers is not just a reliability metric — it's evidence about the underlying structure of the classification task itself.**

High disagreement isn't necessarily "noise" or "error" — it may indicate that the question is genuinely ambiguous, that reasonable experts would also disagree, or that the answer is highly sensitive to framing.

### Connection to Ensemble Methods

This connects to established principles:
- **Wisdom of crowds:** Independent judgments aggregate to better estimates than individuals
- **Ensemble learning:** Combining diverse models reduces variance and improves robustness
- **Bayesian model averaging:** Uncertainty in model selection propagates to prediction uncertainty

Our 6-classifier ensemble is effectively performing a form of Monte Carlo sampling over the space of possible judgments.

---

## The Four Scoring Methods

### Method 1: Composite Score (Weighted Product)

**What it is:** Simple utility function combining feasibility direction with agreement strength.

**Formula:**
```
Score = Feasibility_weight × Confidence_weight

Feasibility: F1=3, F2=2, F3=1
Confidence: HIGH=1.0, MODERATE=0.67, LOW=0.33

Range: 0.33 to 3.0
```

**Why use it:**
- **Interpretability:** Stakeholders immediately understand "higher = better"
- **Transparency:** No black-box calculations
- **Decision-theoretic grounding:** This is a linear utility function. The weights encode our value judgment that F1 is 3× more valuable than F3, and that HIGH confidence is 3× more valuable than LOW

**Theoretical basis:** Multi-attribute utility theory (MAUT). When combining multiple criteria into a single score, weighted products/sums are the standard approach in decision analysis.

**Limitations:**
- Weight choices are somewhat arbitrary (why 3/2/1, not 4/2/1?)
- Treats confidence as categorical when it could be continuous
- Assumes linear value function

---

### Method 2: Entropy-Based Confidence

**What it is:** Information-theoretic measure of classifier agreement.

**Formula:**
```
H = -Σ p(vote) × log₂(p(vote))  # Shannon entropy

Agreement = 1 - (H / H_max)     # Normalized, inverted

Score = Agreement × Feasibility_weight
```

**Why use it:**
- **Principled uncertainty quantification:** Entropy is THE measure of uncertainty in information theory
- **Distribution-sensitive:** Captures whether disagreement is 2-vs-1 or 3-way split
- **Connects to statistical mechanics:** Entropy measures disorder; low entropy = ordered/settled state

**Theoretical basis:** Shannon's foundational work on information theory. Entropy as uncertainty measure is axiomatic — it's the unique function satisfying certain desirable properties (additivity, continuity, maximality for uniform distributions).

**The energy landscape connection:**
- In statistical mechanics, entropy relates to the number of microstates compatible with a macrostate
- Low entropy = few compatible configurations = system is "settled" into a specific state
- Applied to LLM classifiers: low entropy means the ensemble has "settled" on a classification, suggesting a stable attractor in the solution space

**Limitations:**
- Treats all disagreement patterns equally (2 F1s + 1 F3 same entropy as 2 F3s + 1 F1)
- Doesn't account for which specific classifiers disagree (are some more reliable?)

---

### Method 3: Bayesian Posterior Probability

**What it is:** Estimate P(truly consolidable | observed votes) using Bayesian inference.

**Formula:**
```
Prior: Beta(α, β) where α/(α+β) = base_rate (~0.20)
Likelihood: Binomial — each vote as Bernoulli trial
Posterior: Beta(α + successes, β + failures)

Score = Posterior mean = (α + successes) / (α + β + n)
```

**Why use it:**
- **Principled probability:** Output is an actual probability, not arbitrary score
- **Incorporates base rates:** Rare events (consolidable pairs) require stronger evidence
- **Handles small samples gracefully:** Prior regularizes when we have few votes
- **Uncertainty quantification:** Can compute credible intervals, not just point estimates

**Theoretical basis:** Bayes' theorem. The Beta-Binomial is the conjugate model for binary outcomes — mathematically convenient and well-understood.

**Why Beta prior:**
- Beta is flexible (can represent many shapes)
- Conjugate to Binomial (posterior is also Beta)
- Parameters α, β interpretable as "pseudo-counts" of prior successes/failures

**Limitations:**
- Assumes votes are exchangeable (doesn't matter which classifier said what)
- Binary reduction (F1/F2 vs F3) loses information about F1 vs F2 distinction
- Prior choice affects results (though weak prior minimizes this)

---

### Method 4: Borda Count (Rank Aggregation)

**What it is:** Social choice method — each classifier "votes" with points based on preference ordering.

**Formula:**
```
Points: F1=2, F2=1, F3=0

Score = Σ points / max_possible

Range: 0 (all F3) to 1 (all F1)
```

**Why use it:**
- **Non-parametric:** No distributional assumptions
- **Robust to outliers:** Single extreme vote has bounded influence
- **Well-studied properties:** Centuries of analysis in social choice theory
- **Intuitive:** "How many points did this pair get from the jury?"

**Theoretical basis:** Borda count dates to 1770. It satisfies many desirable properties (monotonicity, Pareto efficiency) though not all (susceptible to strategic voting, which is irrelevant for LLM classifiers).

**Connection to other rank methods:**
- Related to Mann-Whitney U (rank-based hypothesis test)
- Related to Kendall's tau (rank correlation)
- Part of broader family of "positional scoring rules"

**Limitations:**
- Treats ordinal scale as interval (is F1 really "twice as good" as F2?)
- All classifiers weighted equally (some may be more reliable)
- Loses information about confidence/agreement patterns

---

## The Ensemble Approach

### Rationale

Each method captures different aspects of the classification quality:
- **Composite:** Decision-theoretic utility
- **Entropy:** Information-theoretic uncertainty
- **Bayesian:** Probabilistic belief updating
- **Borda:** Rank-based aggregation

If all four agree on the ranking, we have high confidence. If they diverge, the divergence itself is informative — it identifies edge cases where the "right" ranking depends on what you value.

### Ensemble Score

```
Ensemble = mean(normalized scores)

Where normalized = (score - min) / (max - min) for each method
```

This gives each method equal weight. Alternatives:
- Weight by inverse variance (more consistent methods get more weight)
- Weight by domain expertise (if we had ground truth to validate)

### Identifying Divergent Cases

Pairs where methods strongly disagree (high rank standard deviation) are candidates for:
- Manual expert review
- Additional analysis
- Flagging as genuinely ambiguous

---

## Epistemological Note: Synthesis as Methodology

The entropy/energy-landscape framing emerged from pattern recognition across domains — statistical mechanics, information theory, neural network theory, ensemble methods. This kind of cross-domain synthesis is characteristic of "spatial intelligence" (seeing structural similarities across different fields) rather than sequential deduction.

**The challenge with synthesis-generated hypotheses:**
- They may be correct but hard to justify from first principles
- They may be confabulations that feel right but are wrong
- The only way to know is to test them empirically

**Our approach:**
1. Document the hypothesis clearly
2. Design tests that could falsify it
3. Accept that some insights may remain "fun unknowns" if unfalsifiable
4. Don't let inability to explain something prevent us from using it if it works

The bake-off is the empirical test: if entropy-based scores correlate highly with other methods and help identify edge cases, the framing is useful regardless of whether it's "literally true."

**Relevant precedent:** Many foundational ideas started as intuitions that resisted formal justification. Boltzmann's statistical mechanics was controversial for decades. Information theory seemed abstract until practical applications emerged. Sometimes the contrarian or oddball intuition is right.

---

## Literature Review (2026-01-31)

**Source:** Perplexity research review  
**Full review:** `docs/literature/perplexity_entropy_methodology_review.md`  
**Citations:** `docs/literature/decision_016_citations.md`

### What We Found

| Component | Status | Prior Art |
|-----------|--------|-----------|
| Shannon entropy as agreement measure | Established | Ensemble diversity, info-theoretic IRR |
| Energy landscape metaphor | Well-established | Hopfield, Boltzmann machines |
| Multi-LLM ensemble uncertainty | Emerging field | MUSE, DiverseAgentEntropy |

**Closest prior work:**
- **MUSE** (2025): Multi-LLM uncertainty via Jensen-Shannon divergence
- **DiverseAgentEntropy** (2024): Entropy over multiple agents

### Sober Assessment

The math is not novel — entropy and vote-count measure different things by definition. What's *empirically curious* is that they're nearly uncorrelated (ρ=0.07-0.08) in our data, when standard ensemble behavior would predict negative correlation (high consensus → low entropy).

**This is not a theoretical discovery. It's an operational observation specific to subjective classification tasks without ground truth.**

See "Future Exploration" section for research questions this raises.

---

## Hypotheses to Test

1. **Correlation hypothesis:** All four methods will be highly correlated (ρ > 0.85) because they're measuring related constructs
   - **RESULT: FALSIFIED (interestingly)** — Entropy is orthogonal to Bayesian (ρ=0.083) and Borda (ρ=0.073). This supports the hypothesis that entropy captures a distinct signal.

2. **Entropy-as-confidence hypothesis:** Entropy-based scores will correlate with the categorical confidence levels (HIGH/MODERATE/LOW) from arbitration
   - **RESULT: SUPPORTED** — Composite (which includes confidence) correlates ρ=0.622 with entropy.

3. **Divergent pairs hypothesis:** Pairs where methods disagree will disproportionately be edge cases (MODERATE/LOW confidence, mixed feasibility)
   - **RESULT: SUPPORTED** — Top 20 divergent pairs are mostly LOW confidence with mixed feasibility (F2/F3).

4. **Ensemble robustness hypothesis:** Ensemble ranking will be more stable than any single method (less sensitive to parameter choices)
   - **RESULT: UNDERMINED** — Ensemble is dominated by Bayesian (ρ=0.977) because Bayesian+Borda move together and dilute entropy signal. Simple averaging is suboptimal.

---

## Operational Framework: Two-Axis Triage

**Based on bake-off findings (2026-01-31)**

The original ensemble approach (averaging 4 methods) didn't work well because:
- Bayesian and Borda are highly correlated (ρ=0.909) — redundant
- Entropy is orthogonal (ρ=0.07-0.08) — different information
- Simple averaging lets redundant methods dominate

### Practical approach: Two dimensions for triage

| Dimension | Measure | Question it answers |
|-----------|---------|---------------------|
| **Direction** | Borda score | Did classifiers lean toward consolidable? |
| **Stability** | Entropy score | Did classifiers agree with each other? |

### Four-Quadrant Triage

```
                    HIGH Stability (classifiers agreed)
                           │
     ✅ Clear reject         │        ✅ Clear accept
        Auto-process        │        Auto-process
                           │
    LOW Direction ────────┼──────── HIGH Direction
    (leaning F3)           │        (leaning F1/F2)
                           │
     ❓ Uncertain reject     │        ❓ Uncertain accept
        Human review        │        Human review
                           │
                    LOW Stability (classifiers disagreed)
```

### Operational Routing

| Quadrant | Direction | Stability | Action |
|----------|-----------|-----------|--------|
| Q1 | High | High | Auto-accept as consolidable, verify sample |
| Q2 | Low | High | Auto-reject, low priority |
| Q3 | High | Low | Route to expert — leaning yes but contested |
| Q4 | Low | Low | Route to expert — genuinely ambiguous |

### Why This Is Useful

This separates two questions that vote-counting conflates:
- **"What's the answer?"** → Direction (Borda)
- **"How much did they argue?"** → Stability (Entropy)

A 4-2 vote for "consolidable" and a 4-2 vote for "not consolidable" have the same stability (moderate disagreement) but opposite directions. Standard ensemble confidence doesn't distinguish these cleanly.

---

## Future Exploration (Parked)

These are research threads worth revisiting if this methodology gets applied elsewhere or written up. Not needed for Report 03.

### The Curious Empirical Finding

**Why is ρ ≈ 0?** In typical ensembles, high vote-count correlates with low entropy (strong consensus = agreement). Our near-zero correlation is *not* mathematically guaranteed — it's an empirical observation.

Possible explanations to investigate:
1. **Subjective task effect:** No ground truth means wrong answers don't scatter predictably
2. **Middle-case dominance:** Data may be full of 4-2-0 vs 3-2-1 splits where the relationship breaks down
3. **Borda metric artifact:** Borda may decouple win magnitude from voter confusion differently than raw majority
4. **Task-specific:** May not replicate on other classification tasks

### If Writing This Up (Blog Post / Tech Note)

Defensible framing:
> "In subjective ensemble classification tasks without ground truth, entropy provides a stability signal that is empirically independent of majority vote and enables prioritization strategies not available from vote counts alone."

Dead-on-arrival framing:
> "A novel two-axis theory of ensemble confidence"

### Extensions If Pursuing Further

From external review suggestions:
1. **Geometric grounding:** Link entropy to embedding-space clustering (do low-entropy items cluster tighter?)
2. **Dynamic extension:** Iterated voting rounds to see if entropy decreases (relaxation dynamics)
3. **Human validation:** Do humans rate high-entropy items as more ambiguous?
4. **Cross-task replication:** Does the orthogonality hold on supervised tasks with ground truth?

### Key Literature (Already Gathered)

See `docs/literature/decision_016_citations.md` for:
- Entropy in ensemble diversity (Khairalla 2021, Cunningham 2008)
- Information-theoretic inter-rater agreement (Martins 2020)
- Energy landscapes (Hopfield, Boltzmann machines)
- Multi-LLM uncertainty (MUSE 2025, DiverseAgentEntropy 2024)

---

## Status

**For Report 03:** Use two-axis triage operationally. Don't oversell.

**For future:** Interesting observation worth revisiting if the pattern replicates elsewhere.
