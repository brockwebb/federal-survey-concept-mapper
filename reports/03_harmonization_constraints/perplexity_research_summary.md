# Perplexity Research: Census Bureau Survey Consolidation

**Source:** Perplexity AI deep research query
**Query:** "Census Bureau ACS has conceptual overlap with many surveys. At the question level, there are many differences so surveys like: SIPP, AHS, CE, CPS, FoodAPS have many matching questions, but could they be consolidated at any level?"
**Date retrieved:** 2025-01-28
**Citations:** 100+

## Summary

Comprehensive analysis of federal survey harmonization feasibility. Key conclusions:

1. **Full consolidation not feasible** due to distinct statutory mandates, incompatible temporal designs, varied units of analysis
2. **"Harmonization within tailoring" is achievable** via 5 strategic pathways
3. **6-category barrier taxonomy** confirmed by literature (matches our draft)
4. **International precedents** demonstrate viability (Statistics Netherlands, WMH Surveys)
5. **Implementation timeline:** 5-10 years, $3-5M near-term investment

## Key Sections for Report 03

### Section 2: Barrier Classification (Lines 77-230)
- Population coverage barriers (2.1)
- Construct definition barriers (2.2) - health insurance, income, employment, homeownership examples
- Temporal/reference period barriers (2.3)
- Response scale barriers (2.4)
- Mode/context barriers (2.5)
- Processing/metadata barriers (2.6)

### Section 3: Harmonization Frameworks (Lines 195-263)
- SDR (Survey Data Recycling) methodology
- DataSHaPER compatibility classification (fully/partially/non-equivalent)
- WMH Surveys ex-ante harmonization model
- IPUMS harmonization infrastructure

### Section 4: Consolidation Pathways (Lines 266-700)
- Pathway 1: Administrative records integration
- Pathway 2: Core module standardization
- Pathway 3: Sample integration and record linkage
- Pathway 4: Reference period alignment
- Pathway 5: Content specialization

### Section 6: Challenges and Risks (Lines 714-798)
- Stakeholder resistance / time series disruption
- Administrative data quality gaps
- Legal/privacy constraints (CIPSEA)
- Operational complexity
- Budget constraints

## High-Value Citations for Our Work

| Citation | Content | Use in Report 03 |
|----------|---------|------------------|
| [^31] PMC5993837 | SDR framework, methodological variability taxonomy | Theoretical basis |
| [^33] Wolf et al. SAGE | Question-level harmonization barriers | Literature review |
| [^34] PMC6685455 | DataSHaPER compatibility classification | Feasibility framework |
| [^6] NAP 25098 Ch 6 | National Academies economic survey harmonization | Policy recommendations |
| [^15] PMC3034271 | CPS-ASEC health insurance temporal issues | Case study |
| [^14] PMC2677056 | ACS-CPS comparability | Case study |
| [^35] Fed Reserve 2025 | Homeownership construct differences | Construct barrier example |

## Specific Examples to Code

From this document, extract these pairs for barrier coding:

1. **Health insurance (ACS vs CPS-ASEC)** - TC + CC
   - ACS: "currently covered" (point-in-time)
   - CPS-ASEC: "any time during [year]" (ambiguous)
   - Plus state-specific Medicaid naming (CPS) vs generic (ACS)

2. **Income reference period (ACS vs CPS vs SIPP)** - TC
   - ACS: past 12 months (rolling)
   - CPS: calendar year
   - SIPP: monthly within year

3. **Employment status (ACS vs CPS)** - TC + CC
   - ACS: "worked at any time in past 12 months"
   - CPS: "worked last week"

4. **Homeownership (SHED vs ACS/CPS)** - CC
   - SHED: "Does respondent or spouse own home?"
   - Census: "Is home owned by you or someone in household?"

5. **Consumer unit vs household (CE vs others)** - PC
   - CE: consumer units (pooled income for major expenses)
   - Others: household definition

---

## Full Document

[See uploaded file: Census_Bureau_ACS_has_conceptual_overlap_with_many.md]
