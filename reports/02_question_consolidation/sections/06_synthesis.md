# Synthesis and Conclusions

## The Central Finding

After analyzing 1,702 question pairs across two major federal surveys, we find that **survey consolidation through ACS record linkage has real but structurally limited potential**. The convergence of both survey pairs on ~11% consolidation—despite serving vastly different purposes (food acquisition behavior vs. labor force statistics)—suggests this is a **fundamental ceiling** imposed by how federal surveys are designed.

This ceiling is not a failure. It reflects the reality that surveys optimize for different analytical needs, and those differences are encoded in question design.

---

## What We Learned

### 1. Topic Overlap ≠ Question Substitutability

| Level of Analysis | Apparent Overlap | Actual Substitutability |
|-------------------|------------------|------------------------|
| Domain ("both measure employment") | ~80-90% | — |
| Topic ("both ask about work hours") | ~40-60% | — |
| **Question (actual text comparison)** | — | **~11%** |

Concept-level analysis dramatically overestimates consolidation potential.

### 2. Three Structural Barriers Explain Most Non-Consolidation

| Barrier | Description | Example |
|---------|-------------|---------|
| **Construct mismatch** | Same topic, different operationalization | CPS work-limiting disability vs ACS functional limitations |
| **Reference period incompatibility** | Same construct, different time windows | CPS "last 4 weeks" vs ACS "last week" |
| **Screener vs battery** | Same topic, different depth | ACS "received SNAP?" vs FoodAPS "how many cards?" |

These barriers are **features, not bugs**.

### 3. Content Type Predicts Consolidation Rate

| Content Type | Consolidation Rate | Why |
|--------------|-------------------|-----|
| Core demographics | 60-100% | Stable characteristics, standardized |
| Habitual measures | 25-30% | "Usually/normally" has no temporal anchor |
| Point-in-time status | 10-15% | Reference periods rarely align |
| Program-specific | 0-10% | Specialized needs require specialized questions |

### 4. LLMs Can Reliably Identify Consolidation Opportunities

The Disability case study provides validation:

| Test | Result |
|------|--------|
| True positive: ACS6 diagonal | 6/6 (100%) |
| True negative: Off-diagonal | 336/336 (100%) |

When constructs genuinely align, LLMs find them.

---

## Policy Implications

### The Optimistic View

11% is not nothing. For a 100-question survey:
- ~11 questions could potentially be dropped with ACS linkage
- Demographics (5-10 questions typically) are nearly fully consolidable

### The Realistic View

11% is a ceiling, not a floor. Actual consolidation will be lower because:
- Linkage isn't free (consent, matching error, privacy)
- Skip logic creates dependencies
- Analytical continuity matters
- High-burden questions rarely consolidate

### The Strategic View

Target high-value opportunities:

| Opportunity | Value | Feasibility |
|-------------|-------|-------------|
| Demographic battery consolidation | High | High |
| Habitual framing coordination | Medium | Medium |
| Full survey consolidation | Low | Low |

---

## Recommendations

### For Statistical Agencies

1. **Target demographics first** - Near-certain wins with minimal risk

2. **Coordinate framing conventions** - Habitual framing consolidates; point-in-time doesn't

3. **Don't expect specialized content to consolidate** - SNAP mechanics, disability work-limitations, monthly employment flows require specialized questions by design

4. **Use question-level analysis for planning** - Concept-level studies overestimate by 5-10x

### For Survey Design

1. **Consolidation potential is a design choice** - Surveys needing ACS-linkable data should adopt ACS constructs

2. **Standardization has tradeoffs** - ACS6 disability consolidates perfectly but doesn't measure work-limitation

3. **Reference periods are load-bearing** - "Last week" vs "last 4 weeks" vs "past 12 months" aren't interchangeable

---

## Methodological Contributions

### Question-Level Analysis Framework

We demonstrate that question-level comparison using LLM classification is:
- **Feasible:** 1,702 pairs classified for ~$1.50
- **Scalable:** Full-population runs preferred over sampling
- **Validated:** ACS6 diagonal provides ground truth

### Proposed Taxonomy Addition: Construct Mismatch

Current categories don't capture the Disability pattern. Proposed addition:

**construct_mismatch:** Questions address the same topic but operationalize different constructs serving different analytical purposes. Cannot be substituted regardless of linkage quality.

### Dual-Model Validation

Using two independent LLMs provides:
- Confidence scoring (both agree = high confidence)
- Ambiguity detection (disagreement = needs review)
- Bias mitigation

---

## Limitations

1. **No human validation** - LLM classifications need expert review
2. **Assumed contemporaneous collection** - Real linkage has temporal gaps
3. **Skip logic not evaluated** - Survey flow dependencies exist
4. **Perfect linkage assumed** - Real matching has error

---

## Final Thoughts

Survey consolidation has real but limited potential. The ~11% ceiling allows agencies to:
- Set realistic expectations
- Target high-value opportunities
- Avoid costly efforts on incompatible content
- Design new surveys with linkage in mind

**Survey design encodes analytical purpose at the question level.** Two surveys can "measure employment" while asking fundamentally different questions because they serve fundamentally different needs. This is good survey design, not wasteful duplication.

The goal is not to maximize consolidation but to **identify the subset where consolidation genuinely serves both surveys' analytical purposes**—and our analysis shows that subset is real, identifiable, and worth pursuing.
