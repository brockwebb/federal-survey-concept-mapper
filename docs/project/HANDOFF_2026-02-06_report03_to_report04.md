# Session Handoff: Report 03 Slide Reframe → Report 04 Analysis

**Date:** 2026-02-06  
**Session:** Report 03 presentation slide fixes (data corrections + strategic reframe + architecture)

---

## What Was Done

### Session 1: Data Audit & Fix Script
- Audited all slide numbers against source files (`expert_review_combined.csv`, stage2/stage3 metrics JSONs)
- Found 7 data discrepancies, created fix script at `cc_tasks/fix_slides.sh`
- Key corrections: CPS 100→102 (42.5%), total 168→170, κ 0.845→0.843

### Session 2: Strategic Reframe + Architecture + Batch Edit
- Diagnosed that `STRATEGIC_REFRAME_enrichment_over_consolidation.md` (approved 2026-02-05) was never applied to slide component files
- Diagnosed component file overwrite problem: edits to `slides.qmd` get clobbered when recompiled from `slides_3a`/`slides_3b` components
- Designed two-view architecture replacement:
  - **Pipeline A (mermaid diagram):** Pure data flow — models, tiers, arrows. No stats in boxes.
  - **Pipeline B (validation table):** What was measured at each stage, what it means.
- Rewrote "Why It Matters" slide with enrichment-primary framing (approved language)
- Created comprehensive batch task: `cc_tasks/CLAUDE_CODE_TASK_batch_slide_reframe.md` (15 sections, 12-item validation checklist)
- Task reportedly executed by Claude Code — **NOT YET VERIFIED by user**

---

## What Needs Verification (Report 03)

User will check in a separate thread. Key items from the validation checklist:

- [ ] κ = 0.843 everywhere (not 0.845)
- [ ] CPS: 102 harmonizable, 42.5%
- [ ] Totals: 170 harmonizable, 210 constrained
- [ ] "Why It Matters" matches approved enrichment-primary prose
- [ ] Architecture uses mermaid + table, no broken image refs
- [ ] No "overlapping questions" in framing slides
- [ ] Titles updated (slides.qmd, slides_3a)
- [ ] "enrichment" / "bridge variable" appears on ≥5 slides
- [ ] "consolidation" retained as secondary finding
- [ ] Appendix content unchanged
- [ ] F1/F2/F3 framework definitions unchanged
- [ ] Components (slides_3a, slides_3b) are source of truth; slides.qmd matches

---

## Key Decisions Made

1. **"Overlap" is a trigger word** — use "touchpoints" or "shared concepts" instead. Overlap implies redundancy/waste, touchpoints implies connection/opportunity.

2. **Enrichment hierarchy:**
   - PRIMARY: Enrichment — bridge variables enable cross-survey linkage, increasing explanatory power from existing data
   - SECONDARY: Consolidation — where questions are truly interchangeable, with language standardization as side benefit
   - CONNECTION: Better explanatory power naturally reduces need for follow-ups, tolerates non-response, may reduce total surveys

3. **Architecture is two concerns:**
   - Pipeline A = data processing (operational): pairs → rate → arbitrate → rollup → table
   - Pipeline B = validation analysis (analytical): runs ON outputs of Pipeline A, measures agreement, bias, construct validity
   - These were incorrectly mixed in previous diagram attempts

4. **Parallel, not funnel:** Rating and Arbitration tiers both process ALL 1,598 pairs independently. Not a filter (rate → disagree → arbitrate). Deliberate design enabling full behavioral comparison.

---

## Report 04: Where We're Headed

### Core Question
Given bridge variables identified and quality-scored in Report 03, can AI identify cross-survey enrichment relationships that domain experts haven't surfaced — not because experts lack intelligence, but because no human holds the full topology of 7,000+ questions across 48 surveys in working memory simultaneously?

### What's Already Built
- `expert_review_combined.csv`: 380 questions with F1/F2/F3 classifications, barrier codes, confidence scores
- IPUMS-CPS and IPUMS-USA microdata (2021-2023) sourced for empirical validation
- Earnings variables identified for initial validation (hourly wages, weekly earnings, overtime/tips/commissions)
- Neo4j graph database available for topology analysis
- Survey question corpus: 7,417 questions across 49 survey instruments

### Report 04 Analysis Plan
1. **Empirical validation:** Test whether AI-classified "harmonizable" pairs show statistically comparable response distributions (using public microdata) while "constrained" pairs diverge
2. **Multi-hop enrichment discovery:** AI analysis of full survey topology to find bridge variable paths that exceed human working memory (Survey A → B → C via chained bridges)
3. **Graph-based analysis:** Surveys as nodes, bridge variables as weighted edges, enrichment paths as deliverable

### Key Files
- `docs/project/STRATEGIC_REFRAME_enrichment_over_consolidation.md` — governs framing
- `output/analysis/expert_review_combined.csv` — Report 03 primary deliverable
- `reports/03_harmonization_constraints/presentation/` — slides (just edited)
- `cc_tasks/` — task files for Claude Code execution

---

## Active Concerns

- **Additional Google arbitration data** still being collected to strengthen statistical power
- **Mermaid rendering in Quarto revealjs** — the inline mermaid block may need testing; if it doesn't render, fall back to pre-rendered PNG from the mermaid chart tool
- **Missing slide images** — only 5 of ~15 referenced images exist in `presentation/images/`. Several slides reference PNGs that were never generated. The reframe task removed the broken architecture refs but others may remain (heatmaps, synthesis rates, bias analysis, etc.)
