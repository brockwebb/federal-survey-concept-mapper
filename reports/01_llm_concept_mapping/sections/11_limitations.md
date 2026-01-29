# 11. Limitations

## 11.1 Data Quality Limitations

### 11.1.1 Missing Survey Context

The most significant limitation stems from question decontextualization. Questions were extracted without:
- **Skip logic**: Conditional routing determining when questions are asked
- **Response options**: Answer categories providing interpretation context
- **Question order**: Sequential flow affecting meaning
- **Interviewer instructions**: Clarifications for ambiguous questions

This missing context affected approximately 3-5% of questions (200-350), which were either miscategorized or flagged as ambiguous when full context would have enabled accurate categorization.

**Example Impact**: 
- Question: "Amount?"
- Without context: Impossible to categorize (income? expenditure? time? quantity?)
- With skip logic: "If yes to Q47 (received Social Security), Amount?" → Clearly Economic.Income

Future iterations should extract questions from structured survey metadata (DDI files) preserving full context.

### 11.1.2 Manual Data Collection Errors

Questions were manually copied from survey PDFs and web documents, introducing:
- **Transcription errors**: Typos, formatting issues, encoding problems
- **Incomplete coverage**: Some surveys may have questions not included in dataset
- **Version ambiguity**: Unclear which survey year/version questions came from
- **Administrative text**: Non-substantive survey content incorrectly included

While data cleaning addressed many issues, residual errors remain. The 1,538 "unresolved disagreements" (22% of dataset) likely include many data quality issues rather than genuine categorization failures.

### 11.1.3 Temporal Snapshot

Data reflect survey instruments fielded 2019-2024. Federal surveys evolve continuously through:
- Annual questionnaire updates
- Redesigns following OMB clearance
- Addition/removal of topical modules
- Methodology changes

This analysis captures one temporal slice. Longitudinal patterns require repeated analysis over time.

## 11.2 Methodological Limitations

### 11.2.1 No Ground Truth Validation

The analysis achieved high inter-rater reliability between two LLMs (κ = 0.842) but lacks validation against expert human categorization. We cannot definitively state that LLM judgments are "correct" - only that they are consistent across models.

Ideally, a random sample (e.g., 200-300 questions) would be independently categorized by 2-3 Census Bureau subject matter experts to establish ground truth. LLM performance could then be assessed against this gold standard.

**Mitigation**: The high agreement between completely independent models (different companies, different architectures) and confidence scores exceeding 0.85 for most questions provide substantial, though not definitive, evidence of accuracy.

### 11.2.2 Model-Specific Biases

Both models used (gpt-5-mini, Claude Haiku 4.5) are:
- Trained on similar internet corpora (potential shared biases)
- Commercial products with proprietary training (can't inspect for systematic errors)
- Periodically updated by providers (reproducibility concerns as models evolve)

While dual-model cross-validation reduces model-specific bias, it cannot eliminate systematic biases shared by all contemporary LLMs. For instance, if both models underweight certain taxonomy concepts due to training data gaps, this wouldn't be detected by cross-validation.

### 11.2.3 Confidence Calibration

LLM confidence scores may not be well-calibrated. A model reporting 0.95 confidence may be correct 95% of the time, or 85%, or 99% - we don't know without validation.

The analysis used confidence scores to stratify questions for arbitration (Section 4.5), but threshold selection (0.90 for auto dual-modal) was somewhat arbitrary. Different thresholds would yield different results.

**Empirical Calibration**: Future work could assess actual accuracy by confidence level using a validated subset, enabling optimal threshold selection.

### 11.2.4 Single Taxonomy

Results are specific to the Census Bureau taxonomy. Different taxonomies might yield different categorizations. For instance:
- WHO International Classification of Diseases (ICD) would categorize health questions differently
- OMB's Standard Application for Employment categories differ from Census employment subtopics
- Subject Matter Specific Taxonomies (e.g., education) have finer granularity

The analysis demonstrates **a** valid categorization, not **the** categorization. Taxonomy choice shapes results.

## 11.3 Scope Limitations

### 11.3.1 Federal Demographic Surveys Only

This analysis excluded:
- **Establishment surveys**: Business surveys have different conceptual structures
- **Administrative records**: Censuses and registries lack "questions" to categorize
- **State/local surveys**: Non-federal surveys not included
- **International surveys**: Cross-national comparisons not attempted
- **Private sector surveys**: Market research, polling not covered

Findings about redundancy and gaps apply specifically to the federal demographic household survey ecosystem. Claims about "federal surveys" more broadly would be overclaiming.

### 11.3.2 English-Language Only

All questions were in English. Multilingual surveys (e.g., Spanish-language questionnaires fielded alongside English versions) were represented only by their English versions.

This likely underrepresents some concepts more relevant to non-English-speaking populations (e.g., language use, immigration, cultural practices) if those questions appear primarily in non-English survey versions.

### 11.3.3 Survey Design Questions Only

The analysis focused on questions asked of respondents. It excluded:
- **Derived variables**: Calculated fields combining multiple questions
- **Imputed values**: Missing data filled in statistically
- **Administrative linkages**: Data merged from external sources
- **Survey paradata**: Timing, interview mode, response patterns

Federal statistical products often combine survey questions with these other data sources. Concept coverage analysis based solely on questions provides an incomplete picture of actual measurement capabilities.

## 11.4 Inference Limitations

### 11.4.1 Causality

This is a descriptive analysis of survey content, not a causal study. We observe:
- Concept overlap between surveys (correlation)
- Coverage gaps in taxonomy (absence of evidence)
- High concentration in certain topics (distribution patterns)

We cannot infer:
- **Why** surveys overlap (historical path dependence? deliberate coordination?)
- **Whether** gaps are problematic (some may be intentional)
- **What** caused concentration patterns (policy priorities? ease of measurement?)

Causal claims about survey design processes would require additional evidence (archival research, interviews with survey designers, policy document analysis).

### 11.4.2 Optimal Survey Structure

Finding that surveys X and Y have 80% overlap does not prove they should be merged. This analysis identifies **opportunities** for consolidation, not **imperatives**.

Decisions about survey structure must consider:
- **User communities**: Who relies on each survey? What would they lose from consolidation?
- **Sample design**: Do surveys sample the same populations?
- **Periodicity**: Are measurement frequencies compatible?
- **Budget allocation**: Does cost savings from consolidation flow to implementing agency?
- **Statistical continuity**: Can time series be maintained through consolidation?

The analysis provides necessary but not sufficient evidence for consolidation decisions.

### 11.4.3 Representativeness

The 46 surveys analyzed represent major federal demographic surveys but not the complete federal statistical ecosystem. Findings may not generalize to:
- Specialized surveys with <100 questions (underrepresented here)
- New surveys developed after 2024 data collection
- Surveys that declined to participate in original data compilation
- Surveys with restricted data access (classified/sensitive content)

Claims apply to the surveys studied, not necessarily to unobserved surveys.

## 11.5 Reproducibility Limitations

### 11.5.1 Proprietary Models

The analysis relies on commercial LLM APIs (OpenAI, Anthropic). These models:
- Evolve over time (gpt-5-mini in 2025 ≠ gpt-5-mini in 2024)
- Are proprietary (training data, architecture not fully documented)
- Could be discontinued or substantially changed

Exact reproducibility requires either:
- Archiving specific model versions (API providers don't guarantee this)
- Using open-source models (which currently have lower performance)

Approximate reproducibility is feasible (re-run with current models), but results may differ slightly.

### 11.5.2 Cost and Access Barriers

While the $15 cost is low compared to manual review, it's not zero. Academic researchers or small agencies may lack:
- API credit accounts with OpenAI/Anthropic
- Budget for commercial API usage
- Technical infrastructure for parallel processing
- Expertise to implement pipeline

This creates barriers to independent replication and limits democratization of the methodology.

**Mitigation**: For agencies with security or compliance requirements, FedRAMP-authorized AI services such as Azure OpenAI or Claude on AWS Bedrock provide compliant deployment options that preserve the methodology without requiring on-premises infrastructure.

### 11.5.3 Data Availability

The full question dataset contains survey content that may be proprietary or subject to disclosure restrictions. While the analysis code is fully documented, data access may be constrained by:
- Census Bureau data use agreements
- OMB survey confidentiality rules
- Agency-specific policies on survey content sharing

Public replication may require negotiating data access through formal channels.

## 11.6 Limitations Summary

The principal limitations are:

1. **Data Quality**: Missing survey context (skip logic, response options) affects ~3-5% of questions
2. **No Ground Truth**: High inter-rater reliability between models doesn't prove accuracy without expert validation
3. **Scope**: Federal demographic surveys only; doesn't generalize to establishment surveys or administrative data
4. **Causality**: Descriptive findings about overlap and gaps, not causal explanations
5. **Reproducibility**: Reliance on evolving proprietary models limits exact replication

Despite these limitations, the analysis provides valuable insights about federal survey structure and demonstrates LLM-based concept mapping viability. Future work should prioritize:
- Expert validation of a sample of categorizations
- Automated question extraction preserving full context
- Extension to broader federal statistical ecosystem
- Regular longitudinal updates tracking survey evolution

These improvements would address the most significant limitations while leveraging the demonstrated strengths of the LLM-based approach.
