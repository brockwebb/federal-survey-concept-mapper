# Core Value Proposition: Expert Review Table as Primary Deliverable

**Created:** 2026-02-02  
**Purpose:** Frame the project's central contribution correctly throughout all deliverables

---

## THE WHY: Respondent Burden & Data Quality

**The fundamental problem:**
- Survey response rates are declining
- Collection costs are increasing
- Getting people to fill out surveys is harder and more expensive
- Federal surveys ask overlapping questions across agencies
- Respondents answer similar questions multiple times

**What consolidation enables:**
- **Burden reduction:** Fewer redundant questions for respondents
- **Data interoperability:** Enable cross-survey analysis and data linkage
- **Resource efficiency:** Agencies do more with less collection effort
- **Data quality:** Less respondent fatigue = better response quality

**The stakes:** If we can identify which questions truly overlap and can share data, we reduce hours spent filling out and processing survey information across the federal statistical system.

---

## THE HOW: AI-Assisted Analysis

**The operational challenge:**
Determining which questions can actually consolidate requires expert judgment. But expert time is scarce and expensive.

**Traditional approach:** 
- Experts manually read and compare thousands of question pairs
- Timeline: weeks to months
- Cost: significant expert labor

**Our approach:**
- AI handles the pre-work (reading, comparing, documenting)
- Experts focus on validation and edge cases
- Timeline: < 1 day processing + focused expert review

---

## THE PROOF: Evaluating AI for Survey Harmonization

**Report 03 does double duty:**
1. Produce consolidation results (the deliverable)
2. Evaluate whether AI methods actually work for this task (the methodology contribution)

**What we're proving:**

*Construct Validity*
- Three different model architectures (OpenAI, Anthropic, Google) with different training
- If they converge on classifications (κ = 0.845), the task is well-defined
- Behavioral differences documented as findings, not hidden as noise

*Model Agreement Patterns*
- Pairwise rater agreement (gpt-5-mini vs claude-haiku vs gemini-3-flash)
- Pairwise arbitrator agreement (gpt-5.2 vs claude-opus vs gemini-3-pro)
- Where and why models disagree

*Cost/Quality Tradeoffs*
- Fast models rate (cheap, parallel)
- Flagship models arbitrate (expensive, judgment calls)
- Could 2 models have worked? Where's the inflection?

*Documented Behavioral Profiles*
- Google: deferential, low synthesis (7%)
- OpenAI: moderate synthesis, slight self-bias (59%)
- Anthropic: high synthesis, neutral (77%)

**This is methodological contribution:** Future survey harmonization work can use (or improve on) these methods with evidence of what works.

---

## The Thesis

**The goal was never to bypass human judgment — it was to make human judgment more valuable.**

AI does the hard pre-work:
- Reading thousands of question pairs
- Making initial assessments against harmonization criteria
- Assigning preliminary consolidation judgments
- Documenting reasoning for each decision
- Flagging uncertainty and disagreement

**Result:** What would traditionally require weeks or months of expert labor — reading, comparing, categorizing, documenting — was accomplished in less than a day of processing time.

**The product:** A structured expert review table with:
- 380 questions with best ACS matches
- Consolidation verdicts with confidence scores
- Barrier codes explaining why consolidation fails
- Full reasoning from three independent AI arbitrators
- Triage routing so experts focus on highest-value decisions

---

## What Experts Get

Instead of starting from scratch with thousands of question pairs, experts receive:

| What AI Provides | What Experts Do |
|------------------|-----------------|
| Pre-screened pairs with best matches | Validate match quality |
| Initial F1/F2/F3 classification | Confirm or override |
| Documented reasoning | Understand and critique |
| Confidence scores | Prioritize review effort |
| Barrier codes | Verify diagnosis |

**76% of questions** classified with high confidence — experts can spot-check these.

**24% of questions** (93 total) flagged for expert review — this is where human judgment adds most value.

---

## The Efficiency Claim

Traditional approach:
- Expert reads Question A
- Expert reads Question B  
- Expert considers harmonization criteria
- Expert makes judgment
- Expert documents reasoning
- Repeat × 1,598 pairs
- **Timeline: weeks to months**

AI-assisted approach:
- Pipeline processes all pairs in parallel
- Three models provide independent assessments
- Arbitration resolves disagreements
- Reasoning documented automatically
- Expert reviews pre-structured output
- **Timeline: < 1 day processing + focused expert review**

---

## What This Is NOT

- NOT claiming AI is better than experts
- NOT claiming AI replaces expert judgment
- NOT claiming 100% accuracy
- NOT claiming this is final — it's input for expert validation

---

## Where This Goes

### Report
- **Abstract:** Lead with burden reduction motivation, then efficiency claim
- **Introduction:** WHY = burden/data quality; HOW = AI-assisted analysis
- **Discussion:** Explicitly address human-AI collaboration model
- **Conclusion:** The table is the deliverable; expert validation is next step

### Presentation
- **Slide 1-2 (Problem/Why It Matters):** Burden reduction, declining response rates, cost
- **Slide 3 (The Challenge):** Expert time scarcity, traditional timeline vs. AI-assisted
- **Slide 15 (Expert Review Load):** 76% auto / 24% expert focus
- **Slide 16 (What This Proves):** < 1 day processing claim
- **Final slide:** Link to expert review table as the artifact

### Expert Table Documentation
- Header/README explaining what experts receive and how to use it
- Clear statement that AI provides initial judgment, human provides final validation

---

## Suggested Language

### For Abstract/Exec Summary (WHY then HOW)
> Federal surveys collect overlapping information, creating respondent burden and missed opportunities for data integration. Identifying consolidation potential traditionally requires extensive expert analysis. This project demonstrates that AI-assisted methods can compress weeks of manual survey comparison work into less than a day of processing time, producing structured expert review materials that preserve human judgment for the highest-value decisions.

### For Why It Matters (Burden)
> Survey response rates are declining while collection costs rise. Reducing redundant questions across federal surveys directly addresses respondent burden and enables cross-survey data integration.

### For Discussion (Human-AI Collaboration)
> Our goal was not to replace expert judgment but to multiply its impact. By automating the labor-intensive comparison and documentation work, we enable experts to focus their limited time on validating recommendations and resolving genuinely ambiguous cases — the 24% of questions where human insight adds most value.

### For Presentation Closing
> **The real product:** 380 questions, pre-analyzed, with reasoning documented. What used to take weeks now takes a day — and experts still make the final call.

---

## Verification

The expert review table (`output/analysis/expert_review_combined.csv`) contains:
- ✅ Source question text
- ✅ ACS match text
- ✅ Consolidation verdict (F1/F2/F3)
- ✅ Barrier codes with subcodes
- ✅ Confidence scores (Borda, Entropy)
- ✅ Triage quadrant (Q1-Q4)
- ✅ Specific conflicts from raters
- ✅ Full arbitrator reasoning (all 3 models, with verdicts)

**This table is complete and ready for expert use.**
