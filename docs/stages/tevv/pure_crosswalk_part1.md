# When AI Enters Federal Statistics: A Crosswalk Between Data Quality and AI Trustworthiness Frameworks

**Part 1: The Frameworks and Their Structural Correspondence**

---

## The Problem Nobody Has Mapped

Two authoritative frameworks govern quality and trustworthiness when artificial intelligence is used in federal statistical work. One comes from the statistical community. The other comes from the AI governance community. Neither references the other. No published crosswalk connects them.

The Federal Committee on Statistical Methodology published FCSM 20-04, *A Framework for Data Quality*, in September 2020. It organizes 11 quality dimensions under three domains — Utility, Objectivity, and Integrity — and provides the standard vocabulary for federal agencies evaluating data products (FCSM, 2020).

The National Institute of Standards and Technology published the AI Risk Management Framework (AI RMF 1.0) in January 2023. It defines seven characteristics of trustworthy AI and organizes risk management through four core functions — GOVERN, MAP, MEASURE, and MANAGE (NIST, 2023).

As of February 2026, NIST's official crosswalk page lists twelve mappings between AI RMF and other frameworks: ISO/IEC 42001, ISO/IEC 23894, ISO 5338/5339, ISO/IEC 42005, the EU AI Act, OECD AI Principles, Singapore's AI Verify, Korea's TTA Guidebook, Japan's AI Guidelines for Business, Executive Order 13960, the BSA Framework, and UC Berkeley's Taxonomy of Trustworthiness. Every crosswalk addresses either international standards harmonization or regulatory alignment. None addresses federal statistical data quality.

This matters because federal agencies are already deploying AI in statistical workflows — from automated coding and classification to data integration, quality assurance, and dissemination through AI-mediated interfaces. FCSM itself recognized this trajectory in 2025, publishing FCSM 25-03, *AI-Ready Federal Statistical Data*, which extends the FCSM 20-04 framework to address AI systems consuming federal statistics through APIs and large language models (FCSM, 2025). But FCSM 25-03 addresses one direction of the AI-statistics intersection (AI consuming data) without mapping to the AI governance framework that addresses the other (AI producing or transforming data). The two communities — federal statisticians and AI governance practitioners — are working in parallel without a shared vocabulary.

This crosswalk provides that vocabulary.

---

## What Each Framework Covers

### FCSM 20-04: Data Quality for Federal Statistics

FCSM 20-04 was developed by a working group of the Federal Committee on Statistical Methodology, established under OMB's Statistical Policy Directives. It provides a comprehensive inventory of data quality elements organized under three domains (FCSM, 2020, pp. 13-29):

**Utility** — the extent to which the data product is well-targeted to identified and anticipated needs:

| Dimension | Core Concern |
|-----------|-------------|
| Relevance | Does the data product address current and potential user needs? |
| Accessibility | Can users obtain and understand the data product? |
| Timeliness/Punctuality | Is the data current relative to user needs? Is it delivered on schedule? |
| Granularity | Does the data provide sufficient detail for the intended use? |

**Objectivity** — whether information is accurate, reliable, and unbiased:

| Dimension | Core Concern |
|-----------|-------------|
| Accuracy & Reliability | How close are estimates to true values? How consistent is measurement? |
| Coherence | Are results consistent and comparable across sources, methods, and time? |

**Integrity** — maintenance of rigorous standards and protection of information:

| Dimension | Core Concern |
|-----------|-------------|
| Scientific Integrity/Credibility | Does the work adhere to accepted scientific methods? Is it shielded from inappropriate influence? |
| Transparency | Are methods, sources, limitations, and quality openly documented? |
| Confidentiality | Is respondent information protected from unauthorized disclosure? |
| Computer & Physical Security | Is the system protected from unauthorized access, modification, or destruction? |
| Objectivity of Presentation | Is information presented accurately, clearly, and without bias? |

The framework emphasizes that quality is fitness-for-purpose: the same data product may score high on one dimension and low on another, and managing trade-offs among dimensions is an explicit part of data quality practice (FCSM, 2020, p. 14).

### NIST AI RMF 1.0: Trustworthiness for AI Systems

NIST AI RMF was developed under the National Artificial Intelligence Initiative Act of 2020. It defines seven characteristics of trustworthy AI (NIST, 2023, pp. 13-18):

| Characteristic | Core Concern |
|---------------|-------------|
| Valid & Reliable | Does the system perform as intended? Does it produce consistent results under expected conditions? |
| Safe | Does the system avoid endangering human life, health, property, or environment? |
| Secure & Resilient | Does the system resist unauthorized access, adversarial attacks, and recover from disruption? |
| Accountable & Transparent | Can responsibility be attributed? Are methods, data, and limitations documented? |
| Explainable & Interpretable | Can system operations be understood? Are outputs meaningful in context? |
| Privacy-Enhanced | Does data collection, use, and retention follow privacy principles? |
| Fair with Harmful Bias Managed | Does the system avoid systematically different outcomes based on protected characteristics? |

Two structural features of the NIST framework matter for this crosswalk:

1. **Valid & Reliable is the base condition.** NIST's own Figure 4 shows it as the foundation on which all other characteristics rest. An AI system cannot be meaningfully safe, fair, or explainable if it is not first valid and reliable.

2. **Accountable & Transparent is cross-cutting.** NIST depicts it as a vertical element that relates to all other characteristics. Transparency is not one concern among many — it is the condition that makes all other characteristics assessable.

The framework is explicitly voluntary, non-sector-specific, and designed for tailoring. NIST states that "rarely do all characteristics apply in every setting" and that organizations should balance characteristics based on context (NIST, 2023, p. 14).

---

## The Crosswalk: Where They Correspond and Where They Don't

The crosswalk maps each FCSM dimension to the NIST characteristic(s) that address the same or analogous concern, and vice versa. Cells are populated only where a substantive conceptual correspondence exists — not where a vague thematic similarity could be argued.

### The Correspondence Table

| FCSM 20-04 Dimension | NIST AI RMF Characteristic(s) | Nature of Correspondence |
|----------------------|------------------------------|-------------------------|
| **Accuracy & Reliability** | **Valid & Reliable** | **Direct correspondence.** Both address whether outputs are correct and consistent. FCSM frames this as closeness to true values and measurement consistency; NIST frames it as intended performance and consistent results under expected conditions. These are the same concern expressed in domain-specific vs. system-level vocabulary. |
| **Coherence** | **Valid & Reliable** | **Partial correspondence.** FCSM coherence addresses consistency across sources, methods, and time — a comparative measure. NIST validity includes consistency but does not separately distinguish internal coherence from external validity. Coherence evidence supports a validity claim but is not identical to it. |
| **Scientific Integrity/Credibility** | **Valid & Reliable; Accountable & Transparent** | **Partial correspondence.** FCSM scientific integrity requires adherence to accepted methods and shielding from inappropriate influence. NIST validity addresses methodological soundness; NIST accountability addresses protection from inappropriate influence through documentation and attribution. No single NIST characteristic captures the full FCSM dimension. |
| **Transparency** | **Accountable & Transparent** | **Direct correspondence.** Both require openness about methods, sources, limitations, and quality. FCSM articulates this as a data quality dimension; NIST articulates it as a trustworthiness characteristic. The operational meaning is identical: document what you did, how you did it, and what the limitations are. |
| **Objectivity of Presentation** | **Accountable & Transparent; Fair with Harmful Bias Managed** | **Split correspondence.** FCSM presentation objectivity requires accurate, clear, unbiased presentation. The "accurate and clear" component maps to NIST transparency. The "unbiased" component maps to NIST fairness — specifically, whether outputs are presented in ways that systematically favor certain interpretations. |
| **Confidentiality** | **Privacy-Enhanced** | **Direct correspondence.** Both address protection of individual information from unauthorized disclosure. FCSM frames this as respondent confidentiality in statistical systems; NIST frames it as privacy principles in AI systems. The scope differs (statistical disclosure vs. broader data privacy) but the core concern is the same. |
| **Computer & Physical Security** | **Secure & Resilient** | **Direct correspondence.** Both address protection from unauthorized access, modification, and destruction. FCSM frames this as information security for data systems; NIST adds adversarial attack resistance and system resilience, which extend beyond traditional IT security. |
| **Relevance** | *No direct correspondence* | **FCSM-only concern.** Whether data addresses user needs is a fitness-for-purpose judgment that NIST AI RMF does not address. An AI system can be valid, reliable, fair, and transparent while producing outputs that are irrelevant to any actual decision. |
| **Accessibility** | *No direct correspondence* | **FCSM-only concern.** Whether users can obtain and understand the data product is a dissemination and documentation quality concern. NIST addresses documentation (under Accountable & Transparent) but not user access to outputs as a quality dimension. |
| **Timeliness/Punctuality** | *No direct correspondence* | **FCSM-only concern.** Whether data is current relative to user needs is a temporal fitness judgment. NIST does not address output currency or delivery schedules. |
| **Granularity** | *No direct correspondence* | **FCSM-only concern.** Whether data provides sufficient detail is a resolution/precision judgment. NIST addresses output accuracy but not the level of detail at which outputs are produced. |
| *No FCSM equivalent* | **Safe** | **NIST-only concern.** Whether a system endangers human life, health, or property is not a data quality dimension. FCSM operates in contexts where data products inform decisions but do not directly create physical safety risks. |
| *No FCSM equivalent* | **Explainable & Interpretable** | **NIST-only concern.** Whether system operations can be understood and outputs are meaningful in context has no FCSM analogue. Federal statistical methods are expected to be documented (Transparency) and scientifically sound (Scientific Integrity), but the specific concern about AI opacity — that a system might produce correct outputs through an incomprehensible process — is outside FCSM's scope. |
| *No FCSM equivalent* | **Fair with Harmful Bias Managed** (demographic) | **Partially NIST-only.** FCSM addresses bias in the statistical sense (systematic measurement error) under Accuracy & Reliability, and presentation bias under Objectivity of Presentation. But NIST's concern with systematically different outcomes based on protected characteristics — AI fairness in the civil rights sense — has no FCSM equivalent. Federal statistics address demographic equity through survey design (oversampling, coverage adjustment), not through a quality framework dimension. |

### Reading the Table

**Direct correspondences** (4 cells) exist where both frameworks address the same operational concern using different vocabulary. These are translation opportunities — a federal statistician and an AI governance practitioner talking about the same thing without knowing it.

**Partial correspondences** (4 cells) exist where one framework's dimension maps to parts of multiple characteristics in the other, or where the scope differs enough that equivalence is too strong a claim. These are the analytically interesting cases.

**Framework-specific concerns** (7 cells) exist where one framework addresses something the other simply does not. These are the gaps — and the reason you need both frameworks when AI enters federal statistical work.

---

## The Structural Pattern

The correspondence is not random. It follows a pattern that reflects the different design intents of the two frameworks.

**FCSM's Objectivity domain maps well to NIST.** This is where the frameworks overlap most. Accuracy, reliability, coherence, scientific integrity, and transparency are concerns that both the statistical community and the AI governance community recognize and address, albeit with different vocabulary and emphasis. An agency that demonstrates FCSM Objectivity has gone a long way toward demonstrating NIST trustworthiness (minus the AI-specific concerns).

**FCSM's Integrity domain maps well to NIST.** Confidentiality maps to Privacy-Enhanced; Computer Security maps to Secure & Resilient; Transparency maps to Accountable & Transparent. These are infrastructure and governance concerns that are framework-agnostic.

**FCSM's Utility domain does not map to NIST at all.** Relevance, Accessibility, Timeliness, and Granularity are fitness-for-purpose judgments that NIST's system-trustworthiness framework does not address. This is not a deficiency in NIST — it reflects a deliberate scope difference. NIST evaluates whether an AI system is trustworthy. FCSM evaluates whether a data product is useful. An AI system can be perfectly trustworthy and produce perfectly useless outputs.

**NIST's AI-specific characteristics do not map to FCSM.** Safety, Explainability, and demographic Fairness address concerns that arise specifically because a system is an AI system, not because it produces data. FCSM was designed before AI became a significant factor in federal statistical production, and these concerns are outside its design scope.

This structural pattern has a practical implication: **FCSM alone is necessary but not sufficient when AI is involved, and NIST alone is necessary but not sufficient when the outputs are federal statistics.** Neither framework is wrong or incomplete on its own terms. The gap is at the intersection.

---

*Part 2 continues with: the critical gap (what neither framework covers), implications for federal agencies, and the case for a formal FCSM × NIST AI RMF crosswalk as a federal statistical community contribution to the NIST crosswalk program.*

---

## References

Federal Committee on Statistical Methodology. (2020). *A Framework for Data Quality* (FCSM 20-04). Federal Committee on Statistical Methodology. https://nces.ed.gov/fcsm/pdf/FCSM.20.04_A_Framework_for_Data_Quality.pdf

Federal Committee on Statistical Methodology. (2025). *AI-Ready Federal Statistical Data: An Extension of Communicating Data Quality* (FCSM 25-03). Federal Committee on Statistical Methodology. https://statspolicy.gov/assets/fcsm/files/docs/FCSM.25.03_AI-Ready-Extension-Data-Quality.pdf

National Institute of Standards and Technology. (2023). *Artificial Intelligence Risk Management Framework (AI RMF 1.0)* (NIST AI 100-1). U.S. Department of Commerce. https://doi.org/10.6028/NIST.AI.100-1
