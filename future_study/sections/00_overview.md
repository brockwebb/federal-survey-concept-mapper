# Overview

## Project Context

This report documents the methodology and findings from a question-level consolidation analysis comparing federal surveys with the American Community Survey (ACS). The goal is to determine realistic consolidation potential through record linkage by examining actual question pairs rather than relying solely on concept-level overlap.

## Analysis Process

The analysis follows a four-phase approach:

![Process Flow](figures/process_flow.png)

**Phase 1: Concept Mapping** (Prior Work)
- Classified 47 federal surveys using Census Bureau topic taxonomy
- Generated overlap matrices by subtopic
- Identified survey "families" with shared conceptual domains

**Phase 2: Survey Selection** (This Analysis Begins)
- Focused on "Family 2" - Economic Household Surveys
- Compared 5 surveys against ACS: SIPP, CE, AHS, CPS, FoodAPS
- Selected FoodAPS (123 overlap) and CPS (181 overlap) as pilot cases due to manageable question counts

**Phase 3: Question Analysis**
- Generated 1,702 question pairs within shared subtopics
- Applied dual-model LLM classification (Claude Haiku 4.5 + GPT-5-mini)
- Classified pairs as consolidable, partially consolidable, or not consolidable

**Phase 4: Findings**
- ~11% overall consolidation potential (structural ceiling)
- Identified three primary barriers: construct mismatch, reference period incompatibility, screener vs. battery design
- Validated methodology through case studies (SNAP, Disability, Employment Status)

## Key Finding

**Concept overlap is a ceiling, not an estimate.**

The 123 FoodAPS questions sharing subtopics with ACS yielded only 74 consolidable pairs (12.1%). The 181 CPS questions yielded 118 consolidable pairs (10.8%). The ~90% gap between concept overlap and actual consolidation potential reflects real methodological differences in how surveys operationalize the same constructs.

## Report Structure

| Section | Content |
|---------|---------|
| 1. Survey Selection | Why Family 2, why FoodAPS & CPS |
| 2. Concept Overlap | Treemap visualization of subtopic distribution |
| 3. Methodology | Classification workflow, prompts, decision logic |
| 4. Results | Consolidation rates, agreement metrics, data tables |
| 5. Case Studies | Deep-dives: SNAP, Race, Disability, Employment |
| 6. Synthesis | Cross-survey patterns, barrier taxonomy, recommendations |
| 7. Future Work | Next surveys, extensions, limitations |
