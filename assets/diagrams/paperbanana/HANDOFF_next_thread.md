# Handoff: PaperBanana Diagram Generation Issues

**Date:** 2026-03-01
**From thread:** PaperBanana pipeline diagram setup + generation attempts
**Status:** BLOCKED — outputs are garbage, root cause not fully diagnosed

---

## What We Built (good)

- 5 method specs in `assets/diagrams/paperbanana/` (Stage 5 on hold as `.HOLD`)
- Stage 1 spec fully verified against `master_dataset.csv` actual data
- Pipeline overview spec verified against NUMBERS_MAP
- CC task file with postmortem instructions
- CLAUDE.md updated with PaperBanana workflow section

## What's Wrong

### 1. Model mismatch
- `configs/model_config.yaml` says: `gemini-3.1-pro` (VLM) + `gemini-3.1-flash-image-preview` (image)
- Actual runs used: `gemini-2.5-flash` (VLM) + `gemini-3-pro-image-preview` (image)
- See `outputs/run_20260301_181053_c85e33/metadata.json` for proof

### 2. Old specs were used
- `planning.json` shows the planner ingested the PRE-CORRECTION Stage 1 spec (89%/11% routing, ~700 arbitrated, X symbol chart junk)
- The specs have since been corrected but CC ran before corrections

### 3. Only 1 iteration ran (config says 3)

### 4. Zero retrieved reference examples
- `"retrieved_examples": []` in planning.json
- Brock says he made successful complex diagrams before — those should be reference examples

### 5. Outputs are fabricated
- Pipeline overview: "Literation," "Hinting," "Classifption," "Donovort questions" — gibberish
- Stage 1: Completely wrong pipeline, hallucinated from training priors
- Google image gen (pasting the same spec directly) produced correct output

## Numbers Issues Brock Flagged (UNRESOLVED)

Brock said there are issues with outputs and numbers he doesn't understand. These need investigation in the next thread:

- Stage 1 agreement routing: confirmed subtopic-level (68%), not topic-level (89%)
- `master_dataset.csv` shows 6,949 with final_topic vs NUMBERS_MAP saying 6,954 classified — small discrepancy unexplained
- 840 dual-modal (12%) vs pipeline doc prediction of 2-5% — is this a real finding or a bug?
- Stage 5 method spec on hold — Brock doesn't understand what it should show

## Key Files

```
assets/diagrams/paperbanana/pipeline_overview_method.txt    (corrected)
assets/diagrams/paperbanana/stage1_classification_method.txt (corrected, verified)
assets/diagrams/paperbanana/stage2_overlap_method.txt        (corrected)
assets/diagrams/paperbanana/stage3_rating_method.txt         (needs same verification pass)
assets/diagrams/paperbanana/stage4_arbitration_method.txt    (needs same verification pass)
assets/diagrams/paperbanana/stage5_results_method.txt.HOLD   (on hold)
assets/diagrams/paperbanana/cc_task_generate_diagrams.md     (updated for 5 diagrams)
assets/diagrams/paperbanana/outputs/                         (18 failed runs)
```

## Next Steps

1. Diagnose why PaperBanana used wrong models (config override? hardcoded defaults?)
2. Verify Stage 3 and Stage 4 method spec numbers against actual pipeline outputs
3. Resolve the numbers discrepancies Brock flagged
4. Decide Stage 5 diagram scope
5. Re-run generation with correct models and corrected specs
