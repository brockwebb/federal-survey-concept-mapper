# Analysis Requirements: Model Validation & Expert Deliverables

**Created:** 2026-02-02  
**Status:** TODO - Insert into pipeline  
**Priority:** High - These are key findings, not just nice-to-haves

---

## Context

Three analysis threads identified but not yet formalized:
1. Construct validity / model evaluation
2. Cost/quality tradeoff analysis
3. Expert review table completeness

These need to be:
- Integrated into Stage 4 (Findings) or Stage 5 (Deliverables)
- Documented in methodology
- Included in report and presentation

---

## Thread 1: Construct Validity / Model Evaluation

### What We Need

**Pairwise Model Agreement (Raters)**
- Agreement matrix: gpt-5-mini vs claude-haiku vs gemini-3-flash
- κ for each pair, not just overall
- Where do specific pairs disagree? (question types, concept categories?)

**Pairwise Arbitrator Agreement**
- Agreement matrix: gpt-5.2 vs claude-opus vs gemini-3-pro
- Synthesis rate by arbitrator (already have: Google 7%, OpenAI 59%, Anthropic 77%)
- Self-bias analysis: does arbitrator favor same-vendor rater?

**Convergent Validity Argument**
- If 3 models with different architectures/training converge (κ=0.845), that's evidence the task is well-defined
- Document this explicitly as construct validity evidence
- Behavioral differences + convergence = meaningful signal, not noise

### Where It Fits

- **Pipeline:** Stage 4 (Findings) — add `stage4_model_validation.py`
- **Report:** Methodology section (model selection rationale) + Results (validation findings)
- **Presentation:** Backup slide on model agreement patterns

### Data Sources

- `output/results/stage1_ratings_*.jsonl` — rater outputs
- `output/results/stage3_arbitration_*.jsonl` — arbitrator outputs
- `output/analysis/stage2_agreement_*.csv` — agreement stats (may need expansion)

---

## Thread 2: Cost/Quality Tradeoff

### What We Need

**Counterfactual Analysis: 2 Models vs 3**
- Simulate dropping each rater one at a time
- Compare: agreement rates, verdict distribution, flagged-for-review count
- Question: Does 3rd model add signal or just cost?

**Cost Tracking**
- Did we track API costs per model? (tokens × price)
- If not, estimate from token counts in outputs

**Inflection Point**
- At what agreement threshold does adding a 3rd model stop mattering?
- If 2 models agree 95% of time, 3rd model only matters for 5% of cases
- Cost/quality curve

### Where It Fits

- **Pipeline:** Stage 4 (Findings) — add `stage4_cost_quality_analysis.py`
- **Report:** Discussion section (practical implications for future work)
- **Presentation:** Backup slide on cost efficiency

### Data Sources

- Rater outputs — can simulate 2-model ensembles from existing 3-model data
- API pricing (document in config or separate file)

---

## Thread 3: Expert Review Table Completeness

### What We Need

**Verify Current Content**
Check `output/analysis/expert_review_combined.csv`:
- [ ] Source question text
- [ ] ACS match text
- [ ] Final feasibility (F1/F2/F3)
- [ ] Barrier code (for F3)
- [ ] Triage quadrant (Q1-Q4)
- [ ] Arbitrator reasoning — **CRITICAL, verify present**
- [ ] All 3 arbitrator opinions or just final verdict?

**If Reasoning Missing**
- Pull from `stage3_arbitration_*.jsonl`
- Add `arbitrator_reasoning` column to expert tables
- Consider adding `rater_votes` column showing 3-model split

**The Real Product**
The 93 questions (Q3+Q4) for expert review ARE the deliverable. An expert seeing "F3/CC" with no explanation is useless. They need:
- Why the AI classified it this way
- What the disagreement was (if any)
- Enough context to quickly validate or override

### Where It Fits

- **Pipeline:** Stage 5 (Deliverables) — update `scripts/build_expert_review_table.py`
- **Report:** Appendix C (expert review tables)
- **Presentation:** Reference to deliverable artifact

### Data Sources

- `output/analysis/expert_review_combined.csv` — current state
- `output/results/stage3_arbitration_*.jsonl` — arbitrator reasoning
- `output/results/stage1_ratings_*.jsonl` — rater votes

---

## Implementation Plan

### Immediate (Before Google Data Completes)

1. **Verify expert table content** — check what's there now
2. **Document model names** — ensure config.yaml models are in methodology docs
3. **Outline validation analysis** — what metrics, what comparisons

### When Google Data Completes

4. **Run Stage 4 validation analysis** — pairwise agreement, counterfactual
5. **Update expert tables** — add reasoning if missing
6. **Finalize report sections** — methodology, results, discussion

### Scripts to Create/Modify

| Script | Purpose | Stage |
|--------|---------|-------|
| `stage4_model_validation.py` | Pairwise agreement, convergent validity | Stage 4 |
| `stage4_cost_quality_analysis.py` | 2 vs 3 model counterfactual | Stage 4 |
| `build_expert_review_table.py` | Add reasoning column if missing | Stage 5 |

---

## Success Criteria

1. Pairwise model agreement documented (not just overall κ)
2. Construct validity argument formalized in methodology
3. Cost/quality tradeoff quantified
4. Expert review tables include arbitrator reasoning
5. All analysis reproducible via pipeline scripts

---

## Notes

- These analyses use EXISTING data — no new API calls needed
- This is about extracting more insight from what we have
- The behavioral differences finding (Google deferential, etc.) IS a result, not a limitation
- Document model names from config.yaml — stop hallucinating model names
