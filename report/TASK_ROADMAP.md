# Master Report Project — Task Roadmap

**Created:** 2026-02-18  
**Last updated:** 2026-02-19  
**Status:** Active  
**Prioritization principle:** Risk-based. Things that are confusing to stakeholders or block credibility get done first.

---

## BLOCK 1: Fix Known Issues (before any more writing)

- [x] **T01** — ✅ Fact sheet scoping already correct: says "47 Census Bureau demographic survey instruments" which properly scopes it. No fix needed.
- [x] **T02** — ✅ Copied `apa.csl` to `reports/master/`
- [ ] **T03** — Git commit all current work (master report scaffold, archive moves, CLAUDE.md update, NARRATIVE_CHECKLIST, appendices B & C, TEVV companion doc, references.bib, FCSM PDFs)

## BLOCK 2: Barrier Taxonomy & TEVV (high priority — stakeholder confusion risk)

These are the two things the lead researcher flagged as confusing. They need to be clear, citable, and defensible before the report can land.

### 2A: Barrier Taxonomy (Appendix B)

The harmonization codes (TC, CC, PC, RS, MC, PM) and feasibility tiers (F1/F2/F3) need a clear, cited appendix so readers know what each code means and where it came from.

- [x] **T04** — ✅ Located `taxonomy_v1.md`, verified complete with full citations.
- [x] **T05** — ✅ Appendix B written: `reports/master/appendices/B_taxonomy.qmd`. Feasibility tiers, barrier codes, literature crosswalk, subtypes, coding hierarchy. All citations resolve.
- [x] **T06** — ✅ `references.bib` populated with 13 BibTeX entries (8 taxonomy + 5 TEVV/FCSM).
- [ ] **T07** — Design "friendly" version of taxonomy for the main report body. Not the full appendix — a plain-language presentation a deputy director absorbs in 30 seconds. Design problem, not just writing. Likely needed when writing Ch 4 (T16).

### 2B: TEVV Framework (Appendix C + companion doc)

The methodology makes a claim: AI-assisted methods can do this work reliably. The TEVV appendix is the evidence. Without it, that claim is unsupported.

Reference: `handoffs/2026-02-18_tevv_framework_from_census_mcp.md`

**What TEVV covers (these are INDEPENDENT of the barrier taxonomy):**

- Process reliability: Do models agree with each other? (kappa at rater and arbitrator stages)
- Order invariance: Does randomized presentation order affect results?
- Vendor independence: Do different vendors produce systematically different behaviors? (behavioral analysis)
- Arbitration quality: When models disagree, does the structured protocol produce defensible resolutions?
- Reproducibility: Can someone else run the pipeline and get the same results?
- Transparency: Are prompts, code, and data public?
- **Classification accuracy: Did the AI assign the right codes?** This is where human SME review matters — experts who know the surveys review a sample and validate assignments.

**The barrier taxonomy connects to TEVV in ONE place:** classification accuracy validation. SMEs check whether a pair coded CC (construct barrier) is actually a construct barrier and not a temporal one. That's one TEVV measure, not the whole framework.

Tasks:

- [x] **T08** — ✅ NIST AI RMF crosswalk table built. 11 pipeline measures mapped to 7 NIST trustworthiness characteristics. Validated row-by-row against FCSM 20-04 and NIST AI RMF 1.0 source PDFs. Three corrections applied from validation (Row 8: Accuracy & Reliability not Objectivity; Row 10: dropped Granularity; Section 2.4: FCSM 25-03 is "parallel extension" not "bridge").
- [x] **T09** — ✅ Evaluation dimensions defined with measurable criteria in both Appendix C and TEVV companion doc.
- [x] **T10** — ✅ "N/A cell" identified: confident AI fabrication — neither FCSM (data quality) nor NIST (system trustworthiness) covers AI confidently asserting equivalence where none exists. Documented in pure crosswalk and companion doc.
- [x] **T11** — ✅ Appendix C written: `reports/master/appendices/C_tevv.qmd`. NIST-only crosswalk (no FCSM), 3-4 pages. Needs wiring into `_quarto.yml`.
- [x] **T12** — ✅ SME review protocol documented in both Appendix C and TEVV companion doc. Stratified sampling, domain expertise requirements, disagreement resolution.

## BLOCK 3: Chapter Rewrites (revised outline)

Walk through one at a time, Brock reviews before moving to next.

- [x] **T13** — Ch 1: Introduction — drafted, scope fixed, methodology light. REVIEW NEEDED.
- [ ] **T14** — Ch 2: Classification — topic distribution, breadth of coverage. Keep light on method.
- [ ] **T15** — Ch 3: Survey Overlap & Selection — ACS family, overlap counts, why CPS and FoodAPS.
- [ ] **T16** — Ch 4: Method (brief) — how pairs were built, why most fail, multi-model + arbitration summary, taxonomy table (friendly version). Lean. AI value thread: multi-vendor independence and arbitration as trustworthiness safeguards.
- [ ] **T17** — Ch 5: Results — THE TABLE. Per source survey, per topic/subtopic, F1/F2/F3. Centerpiece of the report.
- [ ] **T18** — Ch 6: Understanding the Results — what codes mean for matches, near-matches, and fails. Where the barrier taxonomy actually matters.
- [ ] **T19** — Ch 7: Implications & Next Steps — enrichment framing, expert review needed, "this changes what's feasible" (AI value), Report 04 as brief future work mention.

## BLOCK 4: Figures and Visuals

- [ ] **T20** — Audit existing figures. Brock decides keep/kill/redo for each.
- [ ] **T21** — Identify what NEW figures are needed for revised narrative.
- [ ] **T22** — Generate any new figures needed.
- [ ] **T23** — Set up figure symlinks in `reports/master/figures/`.
- [ ] **T24** — Wire approved figure references into chapters.

## BLOCK 5: Appendix A (Architecture Diagrams)

- [ ] **T25** — Review existing pipeline diagrams for accuracy.
- [ ] **T26** — Create/update one diagram per pipeline stage.

## BLOCK 6: Companion Documents (after master report is final)

- [x] **T27** — ✅ TEVV companion doc written: `reports/tevv/TEVV_methodology_document.md`. Full three-way crosswalk (FCSM × NIST × pipeline), behavioral analysis, construct validity, SME protocol. Corrections applied from PDF validation. FCSM 25-03 properly characterized as "parallel extension" not "bridge".
- [ ] **T28** — Methodology document: full protocol details, prompt templates, pipeline architecture.

### Bonus deliverables (not originally on roadmap)

- [x] **Pure FCSM × NIST crosswalk** — Framework-level correspondence without pipeline specifics. `reports/tevv/pure_crosswalk_part1.md` and `pure_crosswalk_part2.md`. Potential Medium article and/or NIST crosswalk submission.
- [x] **FCSM PDF validation** — Downloaded FCSM 20-04 and FCSM 25-03 to `docs/literature/`. Validation report: `docs/tevv_crosswalk_validation.md`. 9/11 rows correct, 2 corrected.
- [x] **CLAUDE.md cleanup** — Removed volatile metrics, replaced status table with pointer to TASK_ROADMAP, added C_tevv.qmd to appendices list.

## BLOCK 7: Build & Polish

- [ ] **T29** — Test Quarto render (`cd reports/master && quarto render`)
- [ ] **T30** — Proofread all chapters against NARRATIVE_CHECKLIST.md — every number traces to source
- [ ] **T31** — Final git commit and tag

---

## Rules

- Chapters reviewed and approved sequentially — don't jump ahead
- No figure goes in without Brock reviewing it first
- Fact sheet stays as-is (approved)
- "Friendly taxonomy" presentation (T07) is a design problem — tackle when Ch 4 needs it
- Report 04 is TBD — just a short "potential next steps" paragraph
- All expert review lists still require human SME validation before any claims about accuracy
- Human SME review is a design feature, not a limitation — frame it that way

## Housekeeping (do anytime)

- [ ] Wire `C_tevv.qmd` into `_quarto.yml`
- [ ] Delete `reports/master/appendices/test_write.txt` (artifact from Filesystem MCP debugging)
- [ ] Git commit everything (T03)
