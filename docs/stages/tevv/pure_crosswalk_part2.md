# When AI Enters Federal Statistics: A Crosswalk Between Data Quality and AI Trustworthiness Frameworks

**Part 2: The Critical Gap, Implications, and a Path Forward**

---

## The Gap That Neither Framework Covers

The correspondence table in Part 1 reveals four direct correspondences, four partial correspondences, and seven framework-specific concerns. But the most important finding is not in any cell. It is in the empty space between them.

### The AI-Specific Failure Mode in Statistical Work

Consider a concrete scenario. A federal agency uses a large language model to classify whether survey questions across two instruments measure the same construct — a common task in survey harmonization, data integration, and questionnaire design. The LLM examines question texts, response options, and contextual metadata, then produces a classification: "These questions are equivalent" or "These questions differ because of [specific barrier]."

FCSM 20-04 provides the vocabulary to evaluate the classification's quality. Is it accurate? (Accuracy & Reliability.) Is it consistent with other assessments? (Coherence.) Was the method scientifically sound? (Scientific Integrity.) Are the results documented? (Transparency.)

NIST AI RMF provides the vocabulary to evaluate the AI system's trustworthiness. Does it perform as intended? (Valid & Reliable.) Are its operations understandable? (Explainable & Interpretable.) Does it produce systematically biased results? (Fair with Harmful Bias Managed.)

But neither framework addresses the specific failure mode where these concerns intersect: **the AI system confidently fabricates a classification that has no basis in the underlying data.**

An LLM can assert with apparent certainty that two questions measure the same construct when they do not. It can propose a statistical bridge between concepts that are incommensurable. It can generate plausible-sounding reasoning that cites nonexistent methodological precedent. This is not measurement error in the FCSM sense — the input data is unchanged. It is not invalidity in the NIST sense — the system is performing the task it was designed to perform. It is a failure mode specific to AI systems operating in domains where the correctness of outputs requires domain expertise to verify.

FCSM was not designed to detect this because FCSM addresses quality threats that arise from data collection, processing, and estimation — the Total Survey Error framework and its extensions. The idea that the analytical tool itself might fabricate results with high confidence is outside the framework's design assumptions.

NIST was not designed to detect this *at the domain level* because NIST evaluates system-level properties (validity, reliability, fairness) without specifying what validity means in any particular domain. NIST can tell you that an AI system should be valid and reliable. It cannot tell you what validity looks like for survey harmonization classification, because that requires knowing what survey harmonization is.

This gap is not a deficiency in either framework. It is a structural consequence of their different scopes. FCSM addresses *what* quality means for statistical products. NIST addresses *how* to manage risks in AI systems. The intersection — what quality means for statistical products produced by AI systems — requires both frameworks simultaneously, plus domain-specific validation methods that neither framework provides on its own.

### Why Multi-Framework Evaluation Is Not Optional

The temptation in practice is to pick one framework and treat it as sufficient. A federal statistical agency might evaluate an AI-assisted product using FCSM alone, reasoning that "we've always evaluated data quality this way." An AI governance team might evaluate the same system using NIST alone, reasoning that "this is the authoritative AI risk framework."

Both approaches leave blind spots:

**FCSM-only evaluation** would assess whether the AI's outputs are accurate, coherent, and transparently documented — but would not assess whether the AI system's decision-making process is explainable, whether it exhibits systematic biases traceable to training data, or whether it is robust to adversarial or unusual inputs. An AI system that produces statistically accurate outputs 95% of the time but fails catastrophically on edge cases would score well on FCSM Accuracy & Reliability while failing NIST Valid & Reliable (which includes robustness under expected conditions, not just average-case accuracy).

**NIST-only evaluation** would assess whether the AI system is valid, reliable, fair, and transparent — but would not assess whether its outputs are relevant to user needs, timely, appropriately granular, or coherent with established statistical concepts. An AI system that produces technically valid classifications but at the wrong level of detail, with a six-month turnaround, for a construct nobody asked about, would score well on NIST trustworthiness while failing FCSM Utility entirely.

**Combined evaluation** addresses both blind spots. But it also reveals the gap: neither framework provides domain-specific validation criteria for AI-generated statistical products. That validation requires the third element — subject matter expertise applied through structured review protocols designed for the specific AI application.

---

## Implications for Federal Agencies

### For Statistical Agencies Adopting AI

Federal statistical agencies subject to OMB Statistical Policy Directives and the Information Quality Act already operate within FCSM's quality framework. When these agencies introduce AI into their workflows, they need to:

1. **Maintain FCSM compliance** for the data products that AI helps produce. AI does not create an exemption from data quality requirements — it creates new threats to data quality that must be identified and managed within the existing framework.

2. **Add NIST AI RMF evaluation** for the AI systems themselves. The AI components of a statistical workflow introduce risks (opacity, training data bias, confident fabrication) that FCSM was not designed to address. NIST AI RMF provides the structure for identifying and managing these risks.

3. **Develop domain-specific validation** for the intersection. Neither framework specifies what validation looks like for a specific AI application in a specific statistical domain. This must be developed by the agencies themselves, informed by both frameworks but not fully determined by either.

### For AI Governance Practitioners Working with Federal Data

AI governance professionals applying NIST AI RMF to federal statistical applications need to understand that:

1. **NIST's Valid & Reliable characteristic has a pre-existing, highly developed specification** in the federal statistical context. FCSM's Accuracy & Reliability dimension includes decades of methodological work on measurement error, coverage error, processing error, and estimation error. "Validity" for a federal statistical AI system means something much more specific than generic AI validity — it means meeting the same quality standards that the statistical product would face if produced by traditional methods.

2. **NIST's Accountable & Transparent characteristic has regulatory teeth** in the federal context. Federal statistical transparency is not merely a best practice — it is a legal requirement under OMB Statistical Policy Directive 4, the Information Quality Act, and the OPEN Government Data Act. AI opacity that might be tolerable in a commercial context may be legally insufficient in a federal statistical context.

3. **NIST's Fair with Harmful Bias Managed characteristic requires domain-specific reinterpretation.** The primary bias concern in federal statistical AI applications is often epistemic rather than demographic — whether the AI systematically favors or disfavors certain classifications, not whether it discriminates against protected groups. Both concerns are valid, but the former is more immediately relevant to most statistical AI applications.

### For FCSM and the Broader Statistical Community

The Federal Committee on Statistical Methodology has already demonstrated leadership in extending its framework to AI contexts with FCSM 25-03. But FCSM 25-03 addresses only one direction of the AI-statistics intersection: AI systems consuming federal data. The other direction — AI systems producing, transforming, or classifying statistical data — remains unaddressed.

A formal FCSM × NIST AI RMF crosswalk, developed by the statistical community and submitted to NIST's crosswalk program, would:

1. **Establish the statistical community's voice** in AI governance. The current NIST crosswalk inventory includes international standards bodies, industry groups, and national AI governance bodies. The federal statistical community — which produces the data that many AI systems consume and is increasingly using AI in its own production processes — is absent.

2. **Provide practical guidance** for federal agencies navigating both frameworks simultaneously. A crosswalk with domain-specific annotation would help agencies understand which FCSM measures address which NIST concerns, where additional AI-specific measures are needed, and where NIST concerns can be satisfied through existing statistical quality practices.

3. **Identify the gap formally.** Naming the blind spot — where domain quality frameworks and AI trustworthiness frameworks leave AI-specific failure modes in statistical work unaddressed — is the first step toward developing methods to address it.

---

## What a Formal Crosswalk Would Require

This article presents a conceptual crosswalk — a mapping of correspondences, partial correspondences, and gaps between FCSM 20-04 and NIST AI RMF 1.0. A formal crosswalk suitable for submission to NIST's crosswalk program would require additional work:

**Subcategory-level mapping.** This crosswalk maps at the dimension/characteristic level. NIST's Core framework includes specific subcategories under each function (e.g., MEASURE 2.6: "The AI system is evaluated for validity and reliability" with specific suggested actions). A full crosswalk would map FCSM dimensions to NIST subcategories, identifying which specific NIST actions are satisfied by which specific FCSM practices.

**Bidirectional completeness verification.** This crosswalk was developed FCSM-first (mapping each FCSM dimension to NIST) and then verified NIST-first (checking each NIST characteristic for FCSM coverage). A formal crosswalk would include systematic bidirectional verification with explicit documentation of the mapping rationale for each cell.

**Stakeholder review.** Both the FCSM community and the NIST AI RMF community would need to validate the mappings. What seems like an obvious correspondence to a statistician might be contested by an AI governance practitioner, and vice versa.

**Worked examples.** The crosswalk's practical value would be greatly enhanced by concrete examples showing how an agency would apply both frameworks to a specific AI application (e.g., automated coding, data linkage, harmonization assessment, AI-mediated data dissemination).

---

## Conclusion

Federal statistics and AI trustworthiness are governed by two authoritative frameworks that address overlapping but distinct concerns. Neither references the other. No published crosswalk connects them. As AI becomes embedded in federal statistical work — both consuming data and producing it — the absence of this crosswalk creates a real risk: agencies may evaluate AI-assisted statistical products using only one framework, leaving systematic blind spots in either data quality assessment or AI risk management.

The crosswalk presented here identifies four direct correspondences, four partial correspondences, and seven framework-specific concerns between FCSM 20-04 and NIST AI RMF 1.0. The structural pattern reveals that FCSM's Objectivity and Integrity domains map well to NIST's trustworthiness characteristics, while FCSM's Utility domain and NIST's AI-specific characteristics (Safety, Explainability, demographic Fairness) address concerns the other framework does not.

The most important finding is the gap between the frameworks: neither addresses the domain-specific failure modes that arise when AI systems produce statistical classifications. FCSM was designed for data quality threats from collection and processing. NIST was designed for system-level AI risks. The intersection — AI-specific quality threats to statistical products — requires both frameworks plus domain-specific validation that neither provides alone.

The federal statistical community has the expertise to develop this intersection. NIST has the infrastructure to publish and maintain crosswalks. The mechanism exists. The crosswalk does not.

---

## References

Federal Committee on Statistical Methodology. (2020). *A Framework for Data Quality* (FCSM 20-04). Federal Committee on Statistical Methodology. https://nces.ed.gov/fcsm/pdf/FCSM.20.04_A_Framework_for_Data_Quality.pdf

Federal Committee on Statistical Methodology. (2025). *AI-Ready Federal Statistical Data: An Extension of Communicating Data Quality* (FCSM 25-03). Federal Committee on Statistical Methodology. https://statspolicy.gov/assets/fcsm/files/docs/FCSM.25.03_AI-Ready-Extension-Data-Quality.pdf

National Institute of Standards and Technology. (2023). *Artificial Intelligence Risk Management Framework (AI RMF 1.0)* (NIST AI 100-1). U.S. Department of Commerce. https://doi.org/10.6028/NIST.AI.100-1

National Institute of Standards and Technology. (2024). *Artificial Intelligence Risk Management Framework: Generative Artificial Intelligence Profile* (NIST AI 600-1). U.S. Department of Commerce. https://doi.org/10.6028/NIST.AI.600-1

Parker, J. D., Mirel, L. B., Lee, P., Mintz, R., Tungate, A., & Vaidyanathan, A. (2024). Evaluating data quality for blended data using a data quality framework. *Statistical Journal of the IAOS*, 40(1), 125-136. https://doi.org/10.3233/SJI-230125

---

## About the Author

*[Author bio placeholder — Brock Webb, contributor to FCSM 20-04, Census Bureau researcher, etc.]*

---

## Disclosure

This crosswalk was developed as part of research on AI-assisted survey harmonization assessment across 47 Census Bureau demographic surveys. The applied version of this crosswalk — mapping specific pipeline quality measures to both frameworks — appears in the research methodology documentation. This article presents the pure framework-level crosswalk, which stands independent of any specific application.

The author is acknowledged as a contributor to FCSM 20-04 for input on the computer and physical security sections (FCSM, 2020, Acknowledgments, p. 10).
