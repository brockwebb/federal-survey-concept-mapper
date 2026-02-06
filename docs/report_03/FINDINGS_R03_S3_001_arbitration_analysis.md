# Stage 3 Arbitration Analysis Findings

**Document ID:** FINDINGS_R03_S3_001  
**Version:** 1.0  
**Created:** 2026-01-30  
**Status:** DRAFT  
**Spec Reference:** SPEC-R03-S3-001, Amendment A

---

## 1. Executive Summary

Stage 3 arbitration analysis reveals three distinct arbitrator behavioral profiles:

| Arbitrator | Synthesis Style | Bias Pattern | Overall Characterization |
|------------|-----------------|--------------|--------------------------|
| OpenAI | Moderate (59%) | Self-preferring | Synthesizes often, favors own rater when not |
| Anthropic | High (77%) | Neutral | Almost always synthesizes, no family preference |
| Google | Low (7%) | Position-driven | Rarely synthesizes, strong primacy bias |

**Key finding:** OpenAI and Anthropic both synthesize MORE when raters agree than when they disagree - the opposite of expected "conflict resolution" behavior. This suggests synthesis functions as evidence aggregation rather than disagreement reconciliation.

---

## 2. Validation Status

### 2.1 Spec Compliance

| Requirement | Status | Notes |
|-------------|--------|-------|
| Inter-arbitrator agreement (2-way) | ✓ Complete | n=1,598 |
| Inter-arbitrator agreement (3-way) | ✓ Complete | n=503 (CPS only) |
| Arbitrator-rater concordance | ✓ Complete | All 3 arbitrators |
| Synthesis detection (Amendment A) | ✓ Complete | Stratified metrics added |
| Position bias | ✓ Complete | Chi-square tests |
| Family bias | ✓ Complete | Chi-square tests |
| Barrier summary by survey | ✓ Complete | CPS + FoodAPS |

### 2.2 Internal Consistency Check

| Metric | synthesis_detection | position_bias | Match |
|--------|---------------------|---------------|-------|
| OpenAI synthesis rate | 59.4% | 59.4% | ✓ |
| Anthropic synthesis rate | 77.2% | 77.2% | ✓ |
| Google synthesis rate | 7.0% | 7.0% | ✓ |

Bug from previous implementation fixed. Both sections now use `selected_rater_key == "synthesis"` consistently.

---

## 3. Inter-Arbitrator Agreement

### 3.1 Two-Way Agreement (Full Dataset, n=1,598)

| Metric | % Agreement | Cohen's κ | Interpretation | Quality Gate |
|--------|-------------|-----------|----------------|--------------|
| L1 barrier | 94.7% | 0.796 | Substantial | NOT PASSED (threshold: 0.80) |
| Full barrier code (L1.L2) | 85.0% | 0.755 | Substantial | NOT PASSED |
| Feasibility | 94.7% | 0.843 | Almost Perfect | PASSED |
| Binary consolidability | 96.7% | 0.896 | Almost Perfect | PASSED |

**Interpretation:** Arbitrators agree strongly on whether pairs are consolidable (κ=0.896) but show more variance on specific barrier classification. The L1 kappa of 0.796 falls just below the 0.80 quality gate, indicating room for improvement in barrier taxonomy application.

### 3.2 Three-Way Agreement (CPS Only, n=503)

| Metric | Fleiss' κ | Krippendorff's α | Interpretation |
|--------|-----------|------------------|----------------|
| L1 barrier | 0.833 | 0.833 | Almost Perfect |
| Full barrier code | 0.747 | 0.747 | Substantial |
| Feasibility | 0.871 | 0.872 | Almost Perfect |
| Binary consolidability | 0.903 | 0.903 | Almost Perfect |

**Notable:** Three-way L1 agreement (0.833) exceeds two-way (0.796). This is counterintuitive - adding a third arbitrator typically increases disagreement opportunity. Possible explanation: CPS subset may have clearer barrier signals than FoodAPS.

### 3.3 Pairwise Breakdown (Three-Way Subset)

| Pair | L1 % Agree | L1 κ | L2 % Agree | L2 κ |
|------|------------|------|------------|------|
| OpenAI vs Anthropic | 93.6% | 0.813 | 81.9% | 0.714 |
| OpenAI vs Google | 93.0% | 0.795 | 81.1% | 0.702 |
| Anthropic vs Google | 95.8% | 0.887 | 89.3% | 0.827 |

**Finding:** Anthropic-Google pair shows highest agreement despite having most divergent synthesis behaviors. Agreement on classification is independent of synthesis style.

---

## 4. Synthesis Behavior Analysis

### 4.1 Stratified Synthesis Rates

| Arbitrator | When Raters Agree | When Raters Disagree | Δ | Pattern |
|------------|-------------------|----------------------|---|---------|
| OpenAI | 64.0% (825/1289) | 40.1% (124/309) | +23.9pp | backwards |
| Anthropic | 86.7% (1117/1289) | 37.9% (117/309) | +48.8pp | backwards |
| Google | 8.4% (32/383) | 2.5% (3/120) | +5.9pp | deferential |

### 4.2 Pattern Classification per Amendment A

| Pattern | Definition | Observed |
|---------|------------|----------|
| efficient | Low unanimous (<30%), high split (>50%) | None |
| always_synthesizes | High both (>70%) | None |
| deferential | Low both (<30%) | Google |
| backwards | Unanimous > split by >20pp | OpenAI, Anthropic |
| moderate | Other | None |

### 4.3 Interpretation Challenge

**Spec assumption:** Synthesis is most valuable for conflict resolution → "backwards" = problematic behavior

**Alternative hypothesis (flagged for investigation):** Synthesis functions as evidence aggregation, not conflict resolution.

Under this interpretation:
- When raters agree: Arbitrator combines their supporting arguments into unified reasoning
- When raters disagree: Arbitrator must *choose* between incompatible classifications - synthesis of "CC.1" and "TC.2" is meaningless

**Implication:** "Backwards" may be rational behavior. The interpretation matrix in Amendment A may need revision.

**ACTION ITEM:** Examine actual reasoning text to determine whether synthesis reads as "combining evidence" or "reconciling conflict". See Section 8.1.

### 4.4 Precision/Recall Metrics

| Arbitrator | Precision | Recall | F1 |
|------------|-----------|--------|-----|
| OpenAI | 0.869 | 0.640 | 0.737 |
| Anthropic | 0.905 | 0.867 | 0.885 |
| Google | 0.914 | 0.084 | 0.153 |

**Note:** These metrics assume "synthesis when unanimous = correct" (TP). If synthesis-as-evidence-aggregation hypothesis is correct, this framing may be inappropriate.

---

## 5. Bias Analysis

### 5.1 Position Bias

All three arbitrators show statistically significant position bias (p < 0.05).

**OpenAI** (n=649 non-synthesis selections):
| Position | Count | % | Expected |
|----------|-------|---|----------|
| A | 310 | 47.8% | 33.3% |
| B | 278 | 42.8% | 33.3% |
| C | 61 | 9.4% | 33.3% |

χ² = 169.7, p < 0.001. Strong primacy bias (A > B > C).

**Anthropic** (n=364 non-synthesis selections):
| Position | Count | % | Expected |
|----------|-------|---|----------|
| A | 152 | 41.8% | 33.3% |
| B | 133 | 36.5% | 33.3% |
| C | 79 | 21.7% | 33.3% |

χ² = 23.6, p < 0.001. Moderate primacy bias.

**Google** (n=468 non-synthesis selections):
| Position | Count | % | Expected |
|----------|-------|---|----------|
| A | 240 | 51.3% | 33.3% |
| B | 158 | 33.8% | 33.3% |
| C | 70 | 15.0% | 33.3% |

χ² = 92.7, p < 0.001. Strong primacy bias (A heavily favored).

**Interpretation:** All models show primacy effects. Google's is most pronounced, possibly compensating for its low synthesis rate - when it doesn't synthesize (93% of cases), it defaults to position A.

### 5.2 Family Bias

| Arbitrator | Same-Family Rate | Expected | χ² | p | Significant |
|------------|------------------|----------|-----|---|-------------|
| OpenAI | **51.8%** | 33.3% | 99.3 | <0.001 | YES |
| Anthropic | 36.8% | 33.3% | 1.98 | 0.159 | no |
| Google | **12.0%** | 33.3% | 37.8 | <0.001 | YES (opposite) |

**Finding: Asymmetric family bias patterns**

1. **OpenAI:** Self-preferring. When not synthesizing, selects OpenAI rater 51.8% of the time (expected: 33.3%). This could reflect:
   - Stylistic similarity in reasoning that reads as "more correct"
   - Training data overlap creating similar classification patterns
   - Genuine quality difference in OpenAI rater output

2. **Anthropic:** Neutral. No significant same-family preference. Most balanced arbitrator.

3. **Google:** Anti-self. Selects Google rater only 12% of the time - significantly *below* chance. Combined with strong position A preference (51.3%), suggests Google's selection is dominated by presentation order, not rater identity. When Google rater appears in position A, it may be selected; otherwise, position A wins regardless of vendor.

**Selection breakdown when not synthesizing:**

| Arbitrator | Selected OpenAI | Selected Anthropic | Selected Google |
|------------|-----------------|--------------------|-----------------| 
| OpenAI arb | **336** (51.8%) | 237 (36.5%) | 76 (11.7%) |
| Anthropic arb | 135 (37.1%) | 134 (36.8%) | 95 (26.1%) |
| Google arb | 92 (50.0%) | 70 (38.0%) | **22** (12.0%) |

---

## 6. Barrier Distribution Findings

### 6.1 L1 Barrier Categories - Full Distribution

| L1 Code | Description | CPS (n=1,030) | FoodAPS (n=568) |
|---------|-------------|---------------|-----------------|
| CC | Construct/Concept | 85.1% (877) | 88.9% (505) |
| TC | Temporal/Chronological | 7.9% (81) | 5.5% (31) |
| RS | Response Scale | 4.1% (42) | 3.3% (19) |
| NHB | No Harmonization Barrier | 1.1% (11) | 0.5% (3) |
| MC | Mode/Context | 1.0% (10) | 0.7% (4) |
| PC | Population/Coverage | 0.7% (7) | 0.9% (5) |
| PM | Policy/Market | 0.2% (2) | 0.2% (1) |

**Key finding: Construct/Concept dominates.** 85-89% of all barriers stem from questions measuring fundamentally different things. This is the primary obstacle to survey consolidation.

**The long tail is negligible.** Mode/Context (MC), Population/Coverage (PC), and Policy/Market (PM) combined account for under 2% of barriers. These categories—which we hypothesized might matter for cross-survey harmonization—barely register in practice.

**NHB (No Harmonization Barrier) is rare.** Only 14 pairs total (0.9%) across both surveys achieved true equivalence. This represents the ceiling of direct substitution potential.

### 6.2 Within CC: What's Driving the Dominance?

| L2 Code | Description | CPS | FoodAPS |
|---------|-------------|-----|---------|
| CC.1 | Different underlying construct | 610 (59.2%) | 311 (54.8%) |
| CC.2 | Different scope/granularity | 186 (18.1%) | 135 (23.8%) |
| CC.4 | Different measurement approach | 80 (7.8%) | 56 (9.9%) |

**CC.1 alone accounts for 55-60% of ALL barriers.** These are questions asking about fundamentally different things—no transformation can reconcile them.

**CC.2 (scope/granularity) offers potential.** When one question is a subset of another (e.g., "income from wages" vs "total income"), transformation may be possible. This represents 18-24% of CC barriers.

### 6.3 Top L2 Barriers - Cross-Survey Comparison

| Rank | CPS→ACS | FoodAPS→ACS |
|------|---------|-------------|
| 1 | CC.1 (610, 59.2%) | CC.1 (311, 54.8%) |
| 2 | CC.2 (186, 18.1%) | CC.2 (135, 23.8%) |
| 3 | CC.4 (80, 7.8%) | CC.4 (56, 9.9%) |
| 4 | TC.2 (51, 5.0%) | TC.2 (23, 4.0%) |
| 5 | RS.1 (35, 3.4%) | RS.1 (12, 2.1%) |

**Finding: Identical top-5 ranking.** Despite CPS (labor force) and FoodAPS (food security) serving very different analytical purposes, they face the same barrier profile when compared to ACS. This suggests barrier patterns are structural to the federal survey ecosystem, not survey-specific.

### 6.4 Feasibility Distribution

| Feasibility | Definition | CPS | FoodAPS |
|-------------|------------|-----|---------|
| F1 | Direct substitution possible | 4.6% (47) | 4.8% (27) |
| F2 | Substitution with transformation | 14.7% (151) | 15.8% (90) |
| F3 | Not feasible | 80.8% (832) | 79.4% (451) |

**~80% of question pairs cannot be consolidated.** This is the hard ceiling—these questions measure different things and no amount of clever transformation will change that.

**~20% consolidation potential** exists across both surveys:
- ~5% can be directly substituted (F1)
- ~15% require transformation (F2)—recoding, aggregation, or scope adjustment

### 6.5 Cross-Survey Consistency

| Metric | CPS→ACS | FoodAPS→ACS | Δ |
|--------|---------|-------------|---|
| CC rate | 85.1% | 88.9% | +3.8pp |
| Consolidable (F1+F2) | 19.2% | 20.6% | +1.4pp |
| F3 rate | 80.8% | 79.4% | -1.4pp |

**Remarkable consistency.** Two surveys with completely different purposes show nearly identical barrier profiles and consolidation potential when compared against ACS. This suggests:

1. ACS serves as a reasonable "anchor" survey for harmonization comparisons
2. Barrier patterns reflect structural characteristics of federal survey design, not domain-specific issues
3. The ~20% consolidation ceiling may be generalizable to other survey pairs

---

## 7. Final Verdict Quality

### 7.1 Confidence Distribution

| Confidence | Count | % |
|------------|-------|---|
| HIGH | 1,458 | 91.2% |
| MODERATE | 112 | 7.0% |
| LOW | 28 | 1.8% |

**HIGH:** Both arbitrators (OA + AN) agreed on L1 and feasibility
**MODERATE:** Partial agreement (L1 or feasibility mismatch)
**LOW:** Disagreement on both dimensions

### 7.2 Tiebreaker Usage

- Two-way disagreements resolved by OpenAI verdict (documented arbitrary choice)
- 112 MODERATE confidence cases used tiebreaker
- 28 LOW confidence cases flagged for potential manual review

---

## 8. Open Issues and Action Items

### 8.1 Synthesis Interpretation (FLAGGED)

**Question:** Does "synthesis" mean evidence aggregation or conflict resolution?

**Required analysis:** Pull 5-10 examples from arbitration JSONL files where:
- Raters unanimous AND arbitrator synthesized → examine reasoning
- Raters split AND arbitrator picked one → examine reasoning

**Expected outcome:** Determine if Amendment A interpretation matrix needs revision.

### 8.2 Google Prompt Investigation

**Question:** Why does Google show such different behavior (7% synthesis, strong primacy, anti-self bias)?

**Possible causes:**
1. Different prompt interpretation
2. Model-specific behavior
3. Rate limiting affecting response quality

**Action:** Compare prompts sent to each arbitrator; examine Google reasoning text quality.

### 8.3 L1 Quality Gate

**Issue:** Two-way L1 kappa (0.796) fails 0.80 quality gate.

**Question:** Is this acceptable given other strong metrics, or should barrier taxonomy be refined?

---

## 9. Limitations

1. **Google coverage:** Only 503/1,598 pairs (CPS only). Three-way analysis cannot be computed for FoodAPS.

2. **Tiebreaker arbitrariness:** OpenAI used as default for two-way disagreements. Alternative rules could change ~7% of final verdicts.

3. **No ground truth:** All metrics are relative (inter-rater, inter-arbitrator). No human expert validation of "correct" barrier classifications.

4. **Synthesis interpretation ambiguity:** "Backwards" pattern classification may mischaracterize rational behavior. See Section 8.1.

---

## 10. Conclusions

1. **Arbitration quality is adequate.** Binary consolidability achieves Almost Perfect agreement (κ=0.896-0.903). Feasibility agreement is strong (κ=0.843-0.871).

2. **Three distinct arbitrator profiles emerged.** OpenAI (self-preferring synthesizer), Anthropic (neutral synthesizer), Google (deferential position-picker). This has implications for future multi-model pipeline design.

3. **Synthesis behavior requires reinterpretation.** The "backwards" pattern (more synthesis when raters agree) may reflect evidence aggregation rather than conflict resolution. The Amendment A interpretation matrix should be revisited.

4. **Barrier findings are consistent across surveys.** CC.1 (construct difference) dominates both CPS and FoodAPS. ~20% consolidation potential in both cases.

5. **91% of verdicts are HIGH confidence.** The multi-model arbitration approach produces reliable final classifications for the vast majority of question pairs.

---

## Appendix A: File Inventory

| File | Description |
|------|-------------|
| `stage3_arbitration_metrics.json` | All computed statistics |
| `stage3_arbitration_report.md` | Human-readable summary |
| `final_verdicts.csv` | Pair-level classifications |
| `barrier_summary_by_survey.csv` | Survey-level distributions |
| `confusion_matrices/*.csv` | L2 disagreement patterns |

---

**Document Status:** DRAFT  
**Next Review:** After synthesis interpretation analysis (Section 8.1)
