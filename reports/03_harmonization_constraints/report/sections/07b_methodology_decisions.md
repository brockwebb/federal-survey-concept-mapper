# Appendix B: Methodology Decisions

<!-- Pull from: docs/methodology_log.md, docs/methodology_log_decision_016.md -->

This appendix documents key methodological decisions made during the analysis, including rationale and alternatives considered.

---

## Decision 001: Three-Model Ensemble

**Date**: 2026-01-28

**Decision**: Use three frontier LLMs (OpenAI gpt-4o-mini, Anthropic claude-3-5-haiku, Google gemini-2.0-flash-exp) as independent raters.

**Rationale**:
- Reduces single-model bias
- Different training data and architectures provide diversity
- Ensemble agreement validates consistency of judgments

**Alternatives Considered**:
- Single model only - rejected due to bias risk
- Five+ models - rejected due to cost and diminishing returns

**Outcome**: High inter-rater agreement (κ = 0.845) validated approach.

---

## Decision 002: Structured JSON Output

**Date**: 2026-01-28

**Decision**: Require models to output structured JSON with feasibility, barrier_code, confidence, and reasoning fields.

**Rationale**:
- Enables automated parsing and aggregation
- Forces models to provide explicit reasoning
- Confidence field supports triage

**Alternatives Considered**:
- Free-text output - rejected due to parsing complexity
- Single classification only - rejected as insufficient for expert review

**Outcome**: 100% successful parsing with robust extraction strategies.

---

## Decision 003: Parallel Processing with Checkpointing

**Date**: 2026-01-28

**Decision**: Process pairs in parallel (6 workers) with checkpoint/resume capability.

**Rationale**:
- Reduces runtime (hours vs. days)
- Allows graceful recovery from API failures
- Supports cost control (stop/resume as needed)

**Implementation**:
- Batch size: 10 pairs per API call
- Exponential backoff for rate limits
- JSON checkpoint file tracks progress

**Outcome**: Robust execution with zero data loss.

---

## Decision 004: Google Rate Limit Acceptance

**Date**: 2026-01-29

**Decision**: Proceed with OpenAI-Anthropic two-way comparison after Google rate-limited at 751 pairs (47%).

**Rationale**:
- Two-way agreement sufficient for validation (κ = 0.845)
- Google subset (751 pairs) confirms consistency (κ = 0.833)
- Cost/benefit of waiting for Google rate limit unfavorable

**Alternatives Considered**:
- Wait for rate limit reset - rejected due to timeline
- Replace Google with another model - rejected as Google data still valuable validation

**Outcome**: Primary findings based on OpenAI-Anthropic, Google used for validation subset.

---

## Decision 005: Arbitration for Disagreements Only

**Date**: 2026-01-29

**Decision**: Arbitrate only disagreements (339 pairs, 21.2%), not all pairs.

**Rationale**:
- Cost efficiency (arbitration uses stronger models)
- High-agreement pairs don't benefit from arbitration
- Focuses arbitrator attention on genuinely uncertain cases

**Alternatives Considered**:
- Arbitrate all pairs - rejected due to cost
- No arbitration - rejected as disagreements need resolution

**Outcome**: Arbitration resolved 339 pairs with 87.6% arbitrator agreement.

---

## Decision 006: Question-Level Rollup (Not Pair-Level Reporting)

**Date**: 2026-01-30

**Decision**: Report primary findings at question level (380 questions), not pair level (1,598 pairs).

**Rationale**:
- Pair-level inflates denominator (multiple comparisons per question)
- Question-level answers stakeholder question: "Is this question consolidable?"
- Statistical dependencies at pair level violate independence assumptions

**Alternatives Considered**:
- Pair-level only - rejected as misleading (one F1 match makes question consolidable regardless of other pairs)
- Report both - **SELECTED**: Pair-level for research detail, question-level for stakeholder summary

**Outcome**: Primary findings at question level (44.2% consolidable), pair-level data in appendix.

---

## Decision 007: Best-Match Selection per Question

**Date**: 2026-01-30

**Decision**: For each source question, select single best ACS match using hierarchy: F1 > F2 > F3, then highest Borda score within tie.

**Rationale**:
- Provides actionable recommendation (one pairing per question)
- Reflects real-world use case (each question maps to at most one alternative)
- Simplifies expert review table

**Alternatives Considered**:
- Show all matches - rejected as overwhelming for stakeholders
- Average across matches - rejected as statistically inappropriate (dependencies)

**Outcome**: 380 question-level records with clear best-match recommendation.

---

## Decision 008: Four Scoring Methods (Ensemble Approach)

**Date**: 2026-01-30

**Decision**: Compute four complementary scores: Composite, Entropy, Bayesian, Borda.

**Rationale**:
- Different scores capture different dimensions:
  - Composite: Baseline (unanimous/majority)
  - Entropy: Stability (how much they argued)
  - Bayesian: Probabilistic (with prior beliefs)
  - Borda: Direction (leaning consolidable or not)
- Ensemble avoids over-reliance on single metric

**Alternatives Considered**:
- Single score only - rejected as insufficient to capture complexity
- More than four - rejected as diminishing returns

**Outcome**: Borda and Entropy selected for triage (Decision 016).

---

## Decision 009: Median Split for Thresholds

**Date**: 2026-01-30

**Decision**: Use median split on question-level best-match scores to define Borda and Entropy thresholds.

**Rationale**:
- Pragmatic, interpretable (50th percentile)
- Avoids arbitrary threshold selection
- Creates balanced quadrants for triage

**Values**:
- Borda median: 0.167
- Entropy median: 0.330

**Alternatives Considered**:
- Optimize thresholds - rejected as no ground truth for optimization
- Fixed thresholds (0.5, 0.75) - rejected as not data-driven

**Outcome**: Balanced quadrant distribution (Q1=151, Q2=136, Q3=40, Q4=53).

---

## Decision 010: Question-Level Medians (Not Pair-Level)

**Date**: 2026-01-30

**Decision**: Compute threshold medians from 380 question-level scores, not 1,598 pair-level scores.

**Rationale**:
- Pair-level distribution dominated by unanimous F3 pairs (median Borda ≈ 0)
- Question-level reflects actual triage decision space
- Threshold goal is to separate questions, not pairs

**Alternatives Considered**:
- Pair-level medians - rejected as produces degenerate thresholds (Borda median ≈ 0)
- Fixed thresholds - rejected as not data-driven

**Outcome**: See `docs/stage4_ensemble_methodology.md` "Threshold Computation" section for detailed justification.

---

## Decision 016: Two-Axis Triage Framework (Borda × Entropy)

**Date**: 2026-01-31

**Decision**: Use Borda (direction) and Entropy (stability) as two-axis triage framework for expert review routing.

**Rationale**:
- **Borda**: Captures ensemble direction (consolidable or not)
- **Entropy**: Captures ensemble stability (agreement or disagreement)
- **Orthogonal dimensions**: Separates "what's the answer?" from "how certain are we?"

**Quadrant Interpretation**:
- Q1 (High Borda, High Entropy): Confident consolidable → auto-accept
- Q2 (Low Borda, High Entropy): Confident non-consolidable → auto-reject
- Q3 (High Borda, Low Entropy): Uncertain accept (leaning yes but unstable) → **expert priority**
- Q4 (Low Borda, Low Entropy): Uncertain reject (ambiguous) → expert secondary

**Alternatives Considered**:
1. Composite score only - rejected as single dimension insufficient
2. Entropy only - rejected as doesn't indicate direction
3. Bayesian + Borda - rejected as Bayesian highly correlated with Borda (r=0.95)
4. **Borda + Entropy (SELECTED)** - orthogonal (r=0.26), complementary dimensions

**Correlation Analysis**:
```
          Composite  Entropy  Bayesian  Borda
Composite    1.000    0.398     0.955   0.945
Entropy      0.398    1.000     0.341   0.260
Bayesian     0.955    0.341     1.000   0.950
Borda        0.945    0.260     0.950   1.000
```

**Key Insight**: Borda and Entropy are least correlated (r=0.26), maximizing information from two-axis framework.

**Outcome**:
- 76% auto-processed (Q1 + Q2)
- 24% expert review (Q3 + Q4)
- Q3 prioritized for review (uncertain accept cases)

**Framing**: This is an **operational tool**, not a theoretical contribution. We do not claim novelty - the approach is a pragmatic application of ensemble scoring for triage purposes. See `docs/stage4_ensemble_methodology.md` for extended discussion with "sober framing".

**Documentation**: Full decision rationale, correlation analysis, and literature review in `docs/methodology_log_decision_016.md`.

---

## Decision 017: Sober Framing for Two-Axis Approach

**Date**: 2026-01-31

**Decision**: Frame two-axis triage as operational tool, not theoretical contribution.

**Rationale**:
- Approach is pragmatic heuristic for this project
- No claim of optimality or theoretical novelty
- Avoid over-claiming in research framing

**Language Used**:
- "Operational framework" not "novel methodology"
- "Useful heuristic" not "discovery"
- "Performed well in this context" not "best practice"

**Contrast**:
- **Overstated**: "We introduce a novel two-axis framework..."
- **Appropriate**: "We use a two-axis triage approach (Borda direction × Entropy stability) as an operational tool..."

**Documentation**:
- Technical details in methodology section
- "Future Exploration" section in `stage4_ensemble_methodology.md` for research threads
- Citation queries in `docs/citation_queries_decision_016.md` remain available if needed

**Outcome**: Clear, honest framing that serves operational needs without inflated claims.

---

## Decision 018: Expert Review Tables as Primary Deliverable

**Date**: 2026-01-31

**Decision**: Generate CSV tables (expert_review_cps.csv, expert_review_foodaps.csv, expert_review_combined.csv) as primary stakeholder deliverable.

**Rationale**:
- Stakeholders need actionable, reviewable data
- CSV format enables filtering, sorting, annotation
- Includes all context (question text, match text, scores, reasoning)

**Columns Included**:
- Source question ID and text
- Best ACS match ID and text
- Feasibility classification (F1/F2/F3)
- Barrier code (if F3)
- Scores (Borda, Entropy)
- Triage quadrant (Q1-Q4)
- Reasoning summary

**Outcome**: 380 rows ready for expert review and validation.

---

## Decision 019: Visualization Strategy

**Date**: 2026-02-02

**Decision**: Generate both pair-level and question-level visualizations.

**Rationale**:
- **Pair-level** (1,598 pairs): Shows research rigor (exhaustive comparison)
- **Question-level** (380 questions): Shows practical outcome (consolidation candidates)
- Both perspectives validate each other and serve different audiences

**Visualizations Created**:
1. Consolidation rates by survey (question-level)
2. Barrier distribution (pair-level)
3. Expert review load (question-level)
4. Harmonization code distribution (pair-level)
5. Question consolidation distribution (question-level by survey)

**Outcome**: Comprehensive visual evidence for both research and stakeholder audiences.

---

## Decision 020: Pipeline Integration

**Date**: 2026-01-31

**Decision**: Integrate all stages into `run_pipeline.py` orchestrator with resume capability.

**Rationale**:
- Reproducibility requires unified execution
- Resume capability handles failures gracefully
- Documentation through code (pipeline is the specification)

**Implementation**:
- Stage dependencies checked automatically
- Output validation before proceeding
- Command-line flags: `--clean`, `--from`, `--only`

**Outcome**: Full pipeline runnable via single command: `python run_pipeline.py`

---

## Summary of Key Principles

Across all decisions, several principles guided methodology:

1. **Transparency**: Document rationale, alternatives, and trade-offs
2. **Reproducibility**: Version control, checkpointing, deterministic execution
3. **Validation**: Inter-rater agreement, quality checks, expert review
4. **Pragmatism**: Operational tools over theoretical claims
5. **Stakeholder Focus**: Deliverables answer real questions ("Is this question consolidable?")

These principles ensured that analysis serves its intended purpose: **providing evidence for federal survey consolidation decisions**.

---

**For complete decision log, see**: `docs/methodology_log.md` (all decisions) and `docs/methodology_log_decision_016.md` (detailed Decision 016 documentation).
