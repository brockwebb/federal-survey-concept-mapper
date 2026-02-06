# Synthesis and Conclusions: Federal Survey Consolidation Potential

## The Central Finding

After analyzing 1,702 question pairs across two major federal surveys, we find that **survey consolidation through ACS record linkage has real but structurally limited potential**. The convergence of both survey pairs on ~11% consolidation—despite serving vastly different purposes (food acquisition behavior vs. labor force statistics)—suggests this is not a survey-specific finding but a **fundamental ceiling** imposed by how federal surveys are designed.

This ceiling is not a failure. It reflects the reality that surveys optimize for different analytical needs, and those differences are encoded in question design at a level invisible to topic-based overlap analysis.

---

## What We Learned

### 1. Topic Overlap ≠ Question Substitutability

The most important finding is the magnitude of the gap between conceptual overlap and operational substitutability:

| Level of Analysis | Apparent Overlap | Actual Substitutability |
|-------------------|------------------|------------------------|
| Domain ("both measure employment") | ~80-90% | — |
| Topic ("both ask about work hours") | ~40-60% | — |
| **Question (actual text comparison)** | — | **~11%** |

Concept-level analysis is necessary for scoping but dramatically overestimates consolidation potential. Question-level analysis is required for realistic estimates.

### 2. Three Structural Barriers Explain Most Non-Consolidation

| Barrier | Description | Example |
|---------|-------------|---------|
| **Construct mismatch** | Same topic, different operationalization | CPS work-limiting disability vs ACS functional limitations |
| **Reference period incompatibility** | Same construct, different time windows | CPS "last 4 weeks" vs ACS "last week" |
| **Screener vs battery** | Same topic, different depth | ACS "received SNAP?" vs FoodAPS "how many cards, who's on each?" |

These barriers are **features, not bugs**. They exist because surveys serve different analytical purposes that require different measurement approaches.

### 3. Content Type Predicts Consolidation Rate

| Content Type | Consolidation Rate | Why |
|--------------|-------------------|-----|
| Core demographics | 60-100% | Stable characteristics, OMB-standardized constructs |
| Habitual measures | 25-30% | "Usually/normally" framing has no temporal anchor |
| Point-in-time status | 10-15% | Reference periods rarely align across surveys |
| Program-specific | 0-10% | Specialized needs require specialized questions |

**Demographics are the only reliable consolidation target.** Everything else faces structural barriers that vary by survey design.

### 4. Habitual Framing Is the Exception That Proves the Rule

Hours/Week shows ~26-29% consolidation across both surveys because all three (FoodAPS, CPS, ACS) use habitual framing:

- "How many hours do you **usually** work?"
- "How many hours do you **normally** work?"

No specific reference period means no reference period mismatch. This pattern suggests that **survey coordination on framing conventions** could increase consolidation potential for non-demographic content—but only if analytical needs permit.

### 5. LLMs Can Reliably Identify Consolidation Opportunities

The Disability case study provides strong validation:

| Test | Result |
|------|--------|
| True positive: ACS6 diagonal matches | 6/6 (100%) |
| True negative: Off-diagonal rejection | 30/30 (100%) |
| True negative: Work-limiting rejection | 306/306 (100%) |

When constructs genuinely align, LLMs find them. When they don't, LLMs correctly reject. Model agreement (68-75%) is high enough for screening; disagreements flag cases for human review.

### 6. Newer Models Are More Discerning

During development, we observed that more recent LLMs (Claude Haiku 4.5, GPT-5-mini) produced **lower consolidation rates** than earlier models. This pattern suggests improved nuance handling rather than model degradation—newer models catch reference period and construct mismatches that earlier models missed.

**Implication:** Historical LLM-based consolidation estimates may be inflated. Current ~11% rates may be more accurate.

---

## What This Means for Survey Consolidation Policy

### The Optimistic Interpretation

11% is not nothing. For a 100-question survey:
- ~11 questions could potentially be dropped with ACS linkage
- Demographics (5-10 questions typically) are nearly fully consolidable
- Hours/week and some habitual measures add incremental gains

For respondent burden reduction, this is meaningful—especially for demographic batteries that appear on nearly every survey.

### The Realistic Interpretation

11% is a ceiling, not a floor. Actual consolidation will be lower because:

1. **Linkage isn't free.** Consent requirements, matching error, temporal misalignment, and privacy concerns all impose costs.

2. **Skip logic creates dependencies.** Surveys may need "dropped" questions to route respondents correctly.

3. **Analytical continuity matters.** Changing question sources mid-series affects trend analysis.

4. **Not all 11% are equal.** Some consolidable questions are low-burden anyway (sex, age). High-burden questions (detailed income, program participation) rarely consolidate.

### The Strategic Interpretation

Rather than maximizing consolidation, agencies should **target high-value opportunities**:

| Opportunity | Value | Feasibility |
|-------------|-------|-------------|
| Demographic battery consolidation | High (appears on all surveys) | High (standardized constructs) |
| Habitual framing coordination | Medium (reduces future mismatches) | Medium (requires survey redesign) |
| Full survey consolidation | Low (specialized needs persist) | Low (analytical purposes differ) |

---

## Methodological Contributions

### 1. Question-Level Analysis Framework

We demonstrate that question-level comparison using LLM classification is:
- **Feasible:** 1,702 pairs classified for ~$1.50
- **Scalable:** Full-population runs preferred over sampling
- **Validated:** ACS6 diagonal provides ground truth confirmation

This framework can be applied to additional survey pairs (SIPP, CE, NHIS) with minimal modification.

### 2. Proposed Taxonomy Addition: Construct Mismatch

Current classification categories don't adequately capture the Disability pattern. We propose adding:

**construct_mismatch:** Questions address the same topic domain but operationalize different constructs serving different analytical purposes. Cannot be substituted regardless of linkage quality.

Distinct from:
- `reference_period_mismatch` (same construct, different time window)
- `response_format_mismatch` (same construct, different response type)
- `related_but_distinct` (catch-all for topical relation)

### 3. Dual-Model Validation Approach

Using two independent LLMs (Claude, GPT) provides:
- **Confidence scoring:** Both agree = high confidence
- **Ambiguity detection:** Disagreement = needs human review
- **Bias mitigation:** Reduces single-model artifacts

Model agreement rates (68-75%) are interpretable: perfect agreement would suggest insufficient sensitivity; low agreement would suggest unreliable classification.

---

## Limitations

### What We Didn't Test

1. **Human validation.** LLM classifications are not ground truth. A validation sample with expert adjudication would strengthen findings.

2. **Temporal alignment.** We assumed contemporaneous collection. Real linkage involves ACS from month X substituting for Survey Y in month Z.

3. **Skip logic compatibility.** We evaluated questions in isolation. Survey flow dependencies may require "consolidable" questions for routing.

4. **Response quality effects.** Linked data may have different error properties than direct collection.

5. **Practical linkage rates.** We assumed perfect linkage. Real matching has error, refusal, and coverage gaps.

### What We Can't Conclude

- Specific questions are definitively consolidable (requires human validation)
- Consolidation would improve data quality (might introduce linkage error)
- Burden reduction would be perceived by respondents (short surveys feel long if complex)
- Cost savings would exceed linkage costs (infrastructure isn't free)

---

## Recommendations

### For Statistical Agencies

1. **Target demographics first.** Near-certain wins with minimal analytical risk.

2. **Coordinate framing conventions.** Habitual framing ("usually/normally") consolidates; point-in-time doesn't. New survey development should consider this.

3. **Don't expect specialized content to consolidate.** SNAP program mechanics, disability work-limitations, monthly employment flows—these require specialized questions by design.

4. **Use question-level analysis for planning.** Concept-level overlap studies overestimate potential by 5-10x.

### For Researchers

1. **Question-level comparison is tractable.** LLM costs are negligible (~$1 per survey pair). No reason to rely on concept-level proxies.

2. **Dual-model validation improves confidence.** Single-model classifications have unknown bias. Agreement rates provide interpretable confidence.

3. **Document failures as findings.** Low consolidation rates (SNAP 8.7%, Disability 1.8%) aren't analytical failures—they're discoveries about survey design.

4. **Sampling doesn't help.** Full-population runs are cheap and more accurate than stratified samples.

### For Survey Design

1. **Consolidation potential is a design choice.** Surveys that need ACS-linkable data should adopt ACS constructs and reference periods.

2. **Standardization has tradeoffs.** ACS6 disability questions consolidate perfectly—but they don't measure work-limitation. Standardization serves some purposes, not all.

3. **Reference periods are load-bearing.** "Last week" vs "last 4 weeks" vs "past 12 months" aren't interchangeable. Choose deliberately.

---

## Future Directions

### Immediate Extensions

| Survey Pair | Estimated Pairs | Expected Pattern |
|-------------|-----------------|------------------|
| SIPP-ACS | ~1,500-2,000 | Similar ~10-12% (income/program focus) |
| CE-ACS | ~800-1,200 | Lower ~5-8% (expenditure detail) |
| NHIS-ACS | ~1,000-1,500 | Higher ~15-20% (demographic heavy) |

### Methodological Improvements

1. **Human validation sample:** 100-200 pairs with expert adjudication to calibrate LLM accuracy

2. **Construct mismatch detection:** Develop classifier for this specific barrier type

3. **Cross-survey framing analysis:** Systematic comparison of reference period conventions

4. **Linkage simulation:** Model actual substitution scenarios with temporal misalignment

---

## Final Thoughts

Survey consolidation through record linkage is a reasonable policy goal with real but limited potential. The ~11% ceiling we identify is not a discouraging finding—it's an accurate one. Knowing the ceiling allows agencies to:

- Set realistic expectations for burden reduction
- Target high-value consolidation opportunities
- Avoid costly efforts to consolidate inherently incompatible content
- Design new surveys with linkage potential in mind

The deeper finding is that **survey design encodes analytical purpose at the question level**. Two surveys can "measure employment" while asking fundamentally different questions because they serve fundamentally different needs. This is good survey design, not wasteful duplication.

Consolidation policy should respect this reality rather than assuming all topical overlap represents redundancy. The goal is not to maximize consolidation but to **identify the subset where consolidation genuinely serves both surveys' analytical purposes**—and our analysis suggests that subset is real, identifiable, and worth pursuing.

---

*Analysis completed: January 27, 2026*
*Total pairs analyzed: 1,702*
*Total API cost: ~$1.50*

---

## Document Index

| Document | Contents |
|----------|----------|
| [`question_level_matching_design.md`](question_level_matching_design.md) | Main findings, methodology, detailed results |
| [`case_studies_foodaps.md`](case_studies_foodaps.md) | SNAP, Race, Hours/Week deep-dives with question text |
| [`case_studies_cps.md`](case_studies_cps.md) | Disability, Employment Status deep-dives with question text |
| **`synthesis_and_conclusions.md`** | This document - cross-survey synthesis and recommendations |
