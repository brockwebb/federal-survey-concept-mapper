# TEVV Methodology Document: AI-Assisted Survey Harmonization Assessment

**Status:** Working draft
**Version:** 0.1
**Date:** 2026-02-19
**Scope:** Full Test, Evaluation, Verification, and Validation framework for AI-assisted harmonization classification pipeline

---

## 1. Purpose and Scope

This document provides the complete TEVV evidence supporting the claim that AI-assisted methods can classify survey question pairs with sufficient reliability to guide expert review and inform harmonization decisions across 47 Census Bureau demographic survey instruments.

The document serves three functions:

1. **Framework justification:** Why the quality measures built into the pipeline are the right things to measure, grounded in two authoritative frameworks — FCSM 20-04 (federal statistical data quality) and NIST AI RMF 1.0 (AI system trustworthiness).
2. **Evidence inventory:** What evidence exists, what evidence is partial, and what evidence requires further validation.
3. **Methodology reference:** How each quality measure was implemented, including statistical methods, design choices, and known limitations.

### Relationship to the Master Report

The master report's Appendix C provides a condensed 3-4 page summary of TEVV evidence focused on the NIST AI RMF crosswalk and evidence status. This companion document provides the full three-way framework mapping, detailed methodology, and complete statistical results that Appendix C summarizes.

### Relationship to the Barrier Taxonomy

The barrier taxonomy (Appendix B) defines the classification scheme applied to harmonization outcomes — barrier codes (TC, CC, PC, RS, MC, PM) and feasibility tiers (F1, F2, F3). The TEVV framework evaluates the **process** by which those classifications were produced. They connect at exactly one point: SME review validates whether the AI assigned the correct barrier codes and feasibility tiers. The taxonomy is one input to one TEVV measure (classification accuracy), not the whole framework.

---

## 2. Framework Foundations

### 2.1 FCSM 20-04: A Framework for Data Quality

The Federal Committee on Statistical Methodology published FCSM 20-04 in September 2020, establishing a common framework for federal agencies to assess data quality. The framework organizes 11 quality dimensions under three domains:

**Utility** — the extent to which the data product is well-targeted to identified and anticipated needs:

| Dimension | Definition |
|-----------|-----------|
| Relevance | Degree to which data meet current and potential user needs |
| Accessibility | Ease with which data can be obtained, including documentation quality |
| Timeliness/Punctuality | Currency of data relative to user needs; adherence to release schedules |
| Granularity | Level of detail available in the data product |

**Objectivity** — whether information is accurate, reliable, and unbiased:

| Dimension | Definition |
|-----------|-----------|
| Accuracy & Reliability | Closeness of estimates to true values; consistency of measurement |
| Coherence | Consistency and comparability across sources, methods, and time |

**Integrity** — maintenance of rigorous standards and protection of information:

| Dimension | Definition |
|-----------|-----------|
| Scientific Integrity/Credibility | Adherence to accepted scientific methods; shielding from influence |
| Transparency | Openness about methods, sources, limitations, and quality |
| Confidentiality | Protection of respondent information from unauthorized disclosure |
| Computer & Physical Security | Protection from unauthorized access, modification, or destruction |
| Objectivity of Presentation | Accurate, clear, and unbiased presentation of information |

FCSM 20-04 emphasizes that quality is fitness-for-purpose: the same data product may have high quality for one use and low quality for another. Threats to quality exist across all dimensions, and managing trade-offs among them is an explicit part of the framework.

**Why FCSM matters for this research:** This research operates entirely within the federal statistical system. The outputs — harmonization classifications, feasibility assessments, expert review lists — are data products that federal agencies would use to guide survey design decisions. FCSM 20-04 is the authoritative framework for evaluating such products.

### 2.2 NIST AI RMF 1.0: Artificial Intelligence Risk Management Framework

NIST published the AI Risk Management Framework 1.0 in January 2023, providing voluntary guidance for managing risks in AI systems. The framework defines seven characteristics of trustworthy AI:

| Characteristic | Definition |
|---------------|-----------|
| Valid & Reliable | System performs as intended, produces consistent results under expected conditions |
| Safe | System does not endanger human life, health, property, or environment |
| Secure & Resilient | System resists unauthorized access, adversarial attacks, and recovers from disruption |
| Accountable & Transparent | Mechanisms exist to attribute responsibility; methods, data, and limitations are documented |
| Explainable & Interpretable | System operations can be understood; outputs are meaningful in context |
| Privacy-Enhanced | Data collection, use, and retention follow privacy principles and regulations |
| Fair with Harmful Bias Managed | System does not produce systematically different outcomes based on protected characteristics |

The NIST framework organizes risk management through four core functions: GOVERN (establish AI risk management culture and processes), MAP (identify and contextualize AI risks), MEASURE (assess risks quantitatively or qualitatively), and MANAGE (allocate resources to address risks).

**Why NIST matters for this research:** The pipeline uses large language models (LLMs) from three commercial vendors to classify survey question pairs. LLMs introduce failure modes — hallucination, confident fabrication, training data bias — that traditional survey methodology frameworks were not designed to address. NIST AI RMF provides the vocabulary and structure for evaluating these AI-specific risks.

### 2.3 The Gap Between Frameworks

Neither framework alone is sufficient for evaluating AI-assisted federal statistical work:

- **FCSM covers domain quality but not AI failure modes.** FCSM 20-04 was developed for survey-based and integrated data products. It addresses measurement error, processing error, coverage gaps, and disclosure risk. It does not address the possibility that an AI system fabricates results with high confidence, or that training data biases systematically distort classifications.

- **NIST covers AI trustworthiness but not domain quality.** NIST AI RMF evaluates whether an AI system is valid, fair, transparent, and secure. It does not evaluate whether the system's outputs are relevant to user needs, coherent with established statistical concepts, or produced with scientific integrity.

- **The intersection is where evaluation lives.** An AI system that is valid and reliable (NIST) but produces irrelevant outputs (FCSM) is not useful. A system that is relevant and accurate by domain standards (FCSM) but opaque and unreproducible (NIST) is not trustworthy. Both must be addressed.

The three-way crosswalk in Section 3 maps specific pipeline quality measures against both frameworks simultaneously, identifying where each measure provides evidence and where gaps remain.

### 2.4 FCSM 25-03: A Parallel Extension

In 2025, FCSM released FCSM 25-03, "AI-Ready Federal Statistical Data: An Extension of Communicating Data Quality," which extends the FCSM 20-04 framework to address AI-mediated access to federal statistics. FCSM 25-03 focuses on making federal data "AI-ready" for consumption by generative AI and large language models — optimizing APIs, metadata, and data structures so that AI systems can discover, interpret, and relay federal statistics accurately.

FCSM 25-03 represents a parallel effort to extend traditional quality frameworks to AI contexts, not a bridge between FCSM and NIST. It does not reference the NIST AI RMF or map FCSM dimensions to AI trustworthiness characteristics. It addresses a different use case (AI systems *consuming* federal data) than this research (AI systems *classifying* survey metadata). However, it demonstrates the same principle: federal statistical data quality frameworks must be extended — not replaced — when AI is introduced into the data pipeline.

This research applies that principle by mapping the AI-assisted classification pipeline to both FCSM (domain quality) and NIST AI RMF (AI trustworthiness) simultaneously. Where FCSM 25-03 extends the framework in one direction (data consumption), this TEVV framework extends it in another (data production and classification).

---

## 3. Three-Way Crosswalk: FCSM × NIST AI RMF × Pipeline Quality Measures

This is the intellectual core of the TEVV framework. Each row maps a specific pipeline quality measure to the FCSM dimension(s) and NIST characteristic(s) it addresses, with the current evidence status.

### 3.1 Full Crosswalk Table

| Pipeline Quality Measure | FCSM 20-04 Dimension(s) | NIST AI RMF Characteristic(s) | What It Demonstrates | Evidence Status |
|--------------------------|------------------------|-------------------------------|---------------------|----------------|
| **Multi-vendor rater agreement** — 3 independent models from 3 vendors (Anthropic, OpenAI, Google) classify each pair | Accuracy & Reliability; Coherence | Valid & Reliable | Independent replication: classifications are not artifacts of a single model's training data or biases. Coherent results across independent sources. | ✅ Established. Cohen's κ at rater stage computed pairwise; Fleiss' κ for three-way agreement. |
| **Randomized presentation order** — question A/B order randomized per rater per pair | Accuracy & Reliability | Valid & Reliable | Order invariance: results are not artifacts of presentation sequence. Controls for primacy/recency bias in LLM classification. | ✅ Established. Randomization implemented in pipeline; documented in code. |
| **Multi-vendor arbitration** — 3 independent arbitrators from 3 vendors resolve rater disagreements | Accuracy & Reliability; Coherence | Valid & Reliable; Accountable & Transparent | Vendor independence at resolution stage. No single vendor's decision-making pattern dominates final classifications. | ✅ Established. Behavioral analysis documents distinct vendor patterns (synthesis rates, selection biases). |
| **Structured arbitration protocol** — arbitrators see all 3 rater outputs, must select or synthesize, must provide reasoning | Scientific Integrity/Credibility; Transparency | Accountable & Transparent; Explainable & Interpretable | Decision traceability: every arbitrated outcome has a documented rationale. Protocol follows established multi-rater methodology. | ✅ Established. All arbitration records include reasoning field; protocol documented. |
| **Public code, prompts, and data** — full pipeline, all prompt templates, all anonymized outputs in public repository | Transparency; Accessibility | Accountable & Transparent | Full transparency and reproducibility. Another researcher can inspect every decision, replicate the entire analysis, and verify claims against source data. | ✅ Established. GitHub repository with complete pipeline code, prompt templates, and analysis outputs. |
| **Deterministic pipeline** — same inputs + same random seeds = same outputs; checkpoint/resume architecture | Accuracy & Reliability; Scientific Integrity/Credibility | Valid & Reliable | Reproducibility: results are not artifacts of non-deterministic inference or interrupted execution. | ✅ Established. Pipeline uses fixed seeds; checkpoint files enable resume from any stage. |
| **Construct validity checks** — demographics score ~100% consolidable; barrier distribution matches domain expectations; cross-survey rate stability | Coherence; Scientific Integrity/Credibility | Valid & Reliable | Internal consistency: results are coherent with known properties of the data (demographics should always match; specialized content should often diverge). | ✅ Established. Sanity checks documented; results match expectations. |
| **Behavioral analysis of vendor patterns** — synthesis rates, self-selection bias, deferential vs. synthesizing arbitration | Coherence; Accuracy & Reliability | Fair with Harmful Bias Managed; Accountable & Transparent | Epistemic bias detection: identifies whether vendors systematically favor certain outcomes, and whether the multi-vendor design effectively diversifies decision-making. | ✅ Established. Google shows deferential patterns (~7% synthesis), OpenAI moderate with self-bias (~59% synthesis), Anthropic high synthesis with neutral bias (~77% synthesis). |
| **Human SME review protocol** — domain experts review sample of classified pairs; validate barrier codes and feasibility tiers | Accuracy & Reliability; Scientific Integrity/Credibility | Valid & Reliable | Classification accuracy: the AI assigned the correct barrier codes and feasibility tiers. The only direct measure of outcome quality (vs. process quality). | ⬜ By design, not yet executed. Protocol defined (Section 5). Expert review lists generated. |
| **Two-axis triage framework** — Borda (direction) × Entropy (stability) quadrants prioritize expert review | Relevance | Valid & Reliable; Explainable & Interpretable | Efficient resource allocation: expert attention is directed to cases where it matters most (ambiguous and edge cases), not wasted on high-confidence pairs. | ✅ Established. Quadrant assignments computed; distribution documented (Q1=151, Q2=136, Q3=40, Q4=53). |
| **AI-specific failure mode awareness** (see Section 4) | *N/A in FCSM* | Valid & Reliable | Fabrication detection: the AI did not invent harmonization paths that do not exist or assert equivalence where concepts are incommensurable. | ⚠️ Partially addressed. Multi-vendor agreement provides indirect evidence; direct validation requires SME review. |

### 3.2 Reading the Crosswalk

**Rows with "✅ Established"** represent quality measures where the pipeline provides direct evidence. These are process quality measures — they establish that the methodology is sound, not that every individual classification is correct.

**The row with "⬜ By design"** (SME review) is the classification accuracy measure. It is designed into the methodology but requires human domain experts to execute. This is not a gap — it is the intentional boundary between what AI-assisted methods can establish autonomously and what requires human judgment.

**The row with "⚠️ Partially addressed"** (AI-specific failure mode) is the most important honest limitation. Multi-vendor agreement provides strong indirect evidence (three independent models are unlikely to independently fabricate the same incorrect harmonization path), but indirect evidence is not direct validation. See Section 4.

**The "N/A in FCSM" cell** is deliberate. FCSM 20-04 was designed for survey data quality, not AI system evaluation. The absence of an AI-specific failure mode dimension is expected, not a deficiency in FCSM. This cell is precisely why the NIST framework is needed in addition to FCSM — it addresses the AI-specific risks that domain frameworks do not.

### 3.3 FCSM Dimensions Not Directly Addressed

Three FCSM dimensions are not addressed by pipeline quality measures because they apply to the eventual use of harmonization results, not to the classification process itself:

- **Timeliness/Punctuality.** The pipeline has no time-critical delivery requirements. Timeliness becomes relevant when harmonization results inform actual survey redesign decisions.
- **Confidentiality.** All input data is public survey questionnaire text. No respondent data is processed.
- **Computer & Physical Security.** The pipeline processes public metadata through commercial APIs using standard security practices. This is not a novel contribution.

### 3.4 NIST Characteristics Not Directly Addressed

Three NIST characteristics are not addressed because the research context does not create the relevant risks:

- **Safe.** Offline classification of public metadata creates no physical safety risk. Misclassification harm (misguided harmonization decisions) is addressed by the SME review gate.
- **Secure & Resilient.** No adversarial attack surfaces are relevant to the classification task.
- **Privacy-Enhanced.** No personally identifiable information is processed.

---

## 4. The AI-Specific Failure Mode

### 4.1 What FCSM Doesn't Cover

FCSM 20-04's Accuracy & Reliability dimension addresses measurement error, coverage error, processing error, and estimation error — the components of Total Survey Error. These are errors that arise from the data collection and statistical production process.

AI-assisted classification introduces a different category of error: **confident fabrication.** An LLM can assert with apparent certainty that two survey questions measure the same construct when they do not, or propose a statistical bridge where the underlying concepts are incommensurable. This is not measurement error (the input data is unchanged) or processing error (the pipeline executes correctly). It is a failure of the AI system to correctly interpret the semantic content of the survey questions.

FCSM was not designed to detect this. This is not a criticism of FCSM — it is a recognition that AI introduces error sources outside the scope of traditional statistical quality frameworks.

### 4.2 How the Pipeline Mitigates This Risk

**Indirect mitigation (established):**

- **Multi-vendor agreement:** Three independent models from different vendors, trained on different data, must classify each pair. Independent fabrication of the same incorrect harmonization path by all three is unlikely (though not impossible — shared training data or similar pre-training biases could produce correlated errors).
- **Structured arbitration:** When models disagree, arbitrators must review all three rater outputs and provide reasoning. This creates a second opportunity to detect fabrication.
- **Construct validity checks:** Known properties of the data (demographics should match; specialized content should diverge) serve as sanity checks. Systematic fabrication would likely violate these patterns.

**Direct validation (designed, not yet executed):**

- **SME review:** Domain experts who know the specific surveys review a sample of classified pairs and confirm or reject the AI's assignments. This is the only measure that directly validates classification accuracy.

### 4.3 Residual Risk

Even after SME review, some residual risk remains:

- SME review covers a sample, not the full dataset. Errors in unreviewed pairs are possible.
- Correlated vendor biases (from shared training data or similar pre-training objectives) could produce agreement on incorrect classifications.
- Novel or unusual question pairs may not be well-represented in any model's training data, reducing classification quality.

These residual risks are managed, not eliminated. The triage framework prioritizes expert review toward high-risk pairs (ambiguous and edge cases), and the methodology explicitly produces the expert review lists needed for ongoing validation.

---

## 5. SME Review Protocol

### 5.1 Purpose

Validate that AI-assigned barrier codes and feasibility tiers are correct for a stratified sample of classified pairs. This is the classification accuracy measure — the only TEVV element that provides direct evidence of outcome quality.

### 5.2 Sample Selection

Pairs are drawn from each of the four triage quadrants:

| Quadrant | Characteristics | Count | Purpose of Review |
|----------|----------------|-------|-------------------|
| Q1 | High direction, High stability | 151 | Verify that high-confidence consolidable pairs are correctly classified |
| Q2 | Low direction, High stability | 136 | Verify that high-confidence non-consolidable pairs are correctly classified |
| Q3 | High direction, Low stability | 40 | Resolve edge cases where models agree on direction but disagree on barrier specifics |
| Q4 | Low direction, Low stability | 53 | Resolve ambiguous cases where neither direction nor barrier is clear |

Minimum sample: 10% from Q1 and Q2 (process verification); 100% of Q3 and Q4 (substantive review needed). Total minimum: ~120 pairs.

### 5.3 Review Format

For each sampled pair, the expert receives:

1. The two question texts (survey source identified)
2. The assigned barrier code and feasibility tier
3. The reasoning provided by the arbitrating model (or majority rater if no arbitration was needed)

The expert answers:

1. Is the barrier code correct? (Y/N/Partially — if partially, which code is correct?)
2. Is the feasibility tier correct? (Y/N — if N, which tier is correct?)
3. If either is incorrect, brief explanation of why.

### 5.4 Agreement Metrics

Expert-AI agreement is computed:

- **Per barrier code:** Agreement rate for each of TC, CC, PC, RS, MC, PM. Confusion matrix to identify systematic misclassifications.
- **Per feasibility tier:** Agreement rate for F1, F2, F3. Direction of systematic disagreement (does AI over-rate or under-rate feasibility?).
- **By triage quadrant:** Does AI confidence (as measured by quadrant assignment) predict accuracy?

### 5.5 Success Criteria

The methodology does not require perfect AI-expert agreement. It requires:

1. **Triage efficiency:** The quadrant system correctly prioritizes expert review effort. Q1/Q2 pairs have higher accuracy than Q3/Q4 pairs.
2. **Systematic error detection:** Where the AI is wrong, the errors follow identifiable patterns (e.g., consistently miscoding temporal barriers as conceptual barriers) that can inform taxonomy or prompt refinement.
3. **Sufficient accuracy for decision support:** The overall classification is accurate enough that an expert using the AI's output as a starting point works significantly faster than classifying from scratch.

Specific numeric thresholds should be established collaboratively with domain experts before review begins, based on their assessment of what accuracy level would be useful in practice.

---

## 6. Detailed Evidence by Pipeline Stage

### 6.1 Stage 1: Rater Classification

*Source:* `output/report_03/analysis/stage2_agreement_metrics.json`

**Three independent raters** from different vendors classify each of the 1,598 question pairs using the barrier taxonomy. Each rater receives the pair in randomized order with identical structured prompts.

**Inter-rater agreement metrics:**

- Cohen's κ (pairwise): [to be populated from source data]
- Fleiss' κ (three-way): [to be populated from source data]
- Raw agreement percentage: [to be populated from source data]
- Agreement by barrier code: [to be populated from source data]
- Agreement by feasibility tier: [to be populated from source data]

**The kappa paradox:** When one category dominates (as is common when most pairs are non-consolidable), raw agreement can be high (e.g., 82.4%) while kappa is moderate (e.g., 0.530) because expected chance agreement is also high. This requires contextual interpretation rather than mechanical application of published kappa thresholds. See McHugh (2012), Hallgren (2012).

### 6.2 Stage 2: Arbitration

*Source:* `output/report_03/analysis/stage3_arbitration_metrics.json`

**Disagreement resolution:** When raters disagree, three independent arbitrators (from the same three vendors, using higher-capability model tiers) review all rater outputs and produce a resolved classification.

**Pre- vs. post-arbitration agreement:**

- Pre-arbitration agreement: [to be populated]
- Post-arbitration agreement: [to be populated]
- Improvement: [to be populated]

**Arbitrator behavioral analysis:**

| Vendor | Synthesis Rate | Selection Bias | Pattern |
|--------|---------------|----------------|---------|
| Google | ~7% | [to be populated] | Deferential — tends to select from existing rater outputs rather than synthesize |
| OpenAI | ~59% | ~51.8% same-family selection | Moderate synthesis with mild self-bias |
| Anthropic | ~77% | ~36.8% same-family selection | High synthesis with neutral bias |

These behavioral differences are a feature, not a bug. They demonstrate that the multi-vendor design produces genuine diversity in decision-making, and that no single vendor's pattern dominates outcomes.

### 6.3 Stage 3: Findings and Triage

*Source:* `output/report_03/analysis/stage4_survey_summary.json`

**Question-level consolidability rates:**

- CPS: 41.7% of source questions have at least one consolidable ACS match
- FoodAPS: 48.6% of source questions have at least one consolidable ACS match

**Triage distribution:**

| Quadrant | Count | Percentage |
|----------|-------|-----------|
| Q1 (Auto-accept) | 151 | 39.7% |
| Q2 (Auto-reject) | 136 | 35.8% |
| Q3 (Edge case) | 40 | 10.5% |
| Q4 (Ambiguous) | 53 | 13.9% |

### 6.4 Construct Validity

**Expected patterns confirmed:**

- Demographics consistently show high consolidability (approaching 100%), as expected for standardized demographic questions.
- Specialized content areas (food acquisition, labor force dynamics) show lower consolidability with identifiable barrier patterns.
- Reference period mismatches (TC) are the most common barrier for cross-survey pairs, consistent with the literature on survey harmonization.

**Unexpected patterns investigated:**

- FoodAPS-ACS and CPS-ACS show remarkably similar consolidability rates (48.6% vs 41.7%) despite very different survey purposes. This was initially surprising but explained by the fact that both surveys share substantial demographic content with ACS, and the rate difference reflects the proportion of specialized content.

---

## 7. Cost-Quality Analysis

*Source:* `output/report_03/analysis/stage4_cost_quality_summary.md`

**API costs by stage:**

[To be populated from source data]

**Comparison with manual methods:**

Traditional survey harmonization assessment at this scale (1,598 pairs across 47 surveys) would require subject matter experts spending 5-10 minutes per pair for initial assessment, plus additional time for documentation and quality assurance. At the lower end, this represents approximately 133 person-hours of expert time. At typical federal contractor rates, this translates to $15,000-$50,000+ in direct costs, with calendar time measured in months.

The AI-assisted pipeline completed the initial classification in days at API costs under $100. This is not a replacement for expert judgment — it is a compression of the screening phase that allows expert time to be redirected to cases where human judgment is actually needed (the ~25% of pairs in Q3 and Q4).

---

## 8. References

- Federal Committee on Statistical Methodology. (2020). *A Framework for Data Quality* (FCSM 20-04). https://nces.ed.gov/fcsm/pdf/FCSM.20.04_A_Framework_for_Data_Quality.pdf
- Federal Committee on Statistical Methodology. (2025). *AI-Ready Federal Statistical Data: An Extension of Communicating Data Quality* (FCSM 25-03). https://statspolicy.gov/assets/fcsm/files/docs/FCSM.25.03_AI-Ready-Extension-Data-Quality.pdf
- National Institute of Standards and Technology. (2023). *Artificial Intelligence Risk Management Framework (AI RMF 1.0)* (NIST AI 100-1). https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf
- National Institute of Standards and Technology. (2024). *Artificial Intelligence Risk Management Framework: Generative Artificial Intelligence Profile* (NIST AI 600-1). https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf
- Hallgren, K. A. (2012). Computing inter-rater reliability for observational data: An overview and tutorial. *Tutorials in Quantitative Methods for Psychology*, 8(1), 23-34.
- McHugh, M. L. (2012). Interrater reliability: The kappa statistic. *Biochemia Medica*, 22(3), 276-282.
- Parker, J. D., Mirel, L. B., Lee, P., Mintz, R., Tungate, A., & Vaidyanathan, A. (2024). Evaluating data quality for blended data using a data quality framework. *Statistical Journal of the IAOS*, 40(1), 125-136. https://doi.org/10.3233/sji-230125

---

## Appendix: Mapping to NIST AI RMF Core Functions

For completeness, the pipeline quality measures also map to NIST's four core functions:

| NIST Function | Pipeline Implementation |
|---------------|------------------------|
| **GOVERN** | Research design established multi-vendor independence as a trustworthiness requirement from the outset. Barrier taxonomy grounded in established literature. Public repository and documentation standards. |
| **MAP** | Risk identification: AI-specific failure modes (fabrication, confident assertion) identified as primary concern not covered by domain quality frameworks. Context: offline classification of public metadata; no safety, privacy, or security risks. |
| **MEASURE** | Inter-rater agreement (kappa); arbitration behavioral analysis; construct validity checks; triage quadrant distribution; cost-quality metrics. Measurement of process quality is established; measurement of outcome quality (classification accuracy) requires SME review. |
| **MANAGE** | Triage framework allocates expert review resources to highest-risk pairs. Multi-vendor design diversifies AI decision-making. SME review protocol designed for execution. Residual risks documented. |
