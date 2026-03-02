# CC Task: Generate Pipeline Architecture Diagrams via PaperBanana

**Date:** 2026-03-01 (v2 — post-V&V correction)
**Repo:** `/Users/brock/Documents/GitHub/federal-survey-concept-mapper`
**Priority:** High (T25-T26 on TASK_ROADMAP)
**Depends on:** Method specs corrected 2026-03-01 with V&V-verified numbers

---

## Context

Five method spec files define pipeline architecture diagrams for Report 03. All specs have been corrected with numbers verified by `src/validation/validate_stage1_classification.py` and cross-checked against `docs/NUMBERS_MAP.md`.

**Previous 18+ runs all failed.** Root causes identified:
1. `planning.json` ingested pre-correction specs (wrong numbers)
2. Model mismatch: config says `gemini-3.1-pro` / `gemini-3.1-flash-image-preview`, actual runs used different models. Verify the models in `configs/model_config.yaml` actually exist in the API before running.
3. Zero retrieved reference examples — the retriever found nothing
4. Only 1 iteration ran despite config saying 3

**Working reference examples exist** in `/Users/brock/Documents/GitHub/census-mcp-server/paper/assets/diagrams/` — these are successful complex PaperBanana outputs. If the retriever needs seeding, use those.

**PaperBanana repo:** `/Users/brock/Documents/GitHub/PaperBanana`
**PaperBanana config:** `configs/model_config.yaml` — read this FIRST for model names and API key config. Do not use model names from training data.

## Prerequisites

1. Ensure `.env` symlink exists:
```bash
cd /Users/brock/Documents/GitHub/federal-survey-concept-mapper/assets/diagrams/paperbanana
ls -la .env || ln -s ../../../.env .env
```

2. **Verify model availability before running:**
```bash
# Test that the models in configs/model_config.yaml actually respond
# If they 404, find the correct current model strings from Google's API
```

3. **Check that corrected specs are what the planner will ingest.** Read each method.txt and confirm the numbers match:
   - Stage 1: routing split 4,765 / 1,368 / 821 = 6,954. Consensus 68.5%. Output "6,954 compared · 6,987 total in master"
   - Pipeline overview: Stage 1 annotation "Routing agreement: 68.5%". No cost/time in bottom annotation.

## Generate These 5 Diagrams

All method specs are in `assets/diagrams/paperbanana/`. Generate each with 3 iterations.

| # | Method Spec | Caption | Deploy To |
|---|-------------|---------|-----------|
| 1 | `pipeline_overview_method.txt` | "AI-Assisted Federal Survey Harmonization Pipeline" | `assets/diagrams/fig_pipeline_overview.png` |
| 2 | `stage1_classification_method.txt` | "Stage 1: Topic and Subtopic Classification" | `assets/diagrams/fig_stage1_classification.png` |
| 3 | `stage2_overlap_method.txt` | "Stage 2: Concept Overlap Identification and Pair Generation" | `assets/diagrams/fig_stage2_overlap.png` |
| 4 | `stage3_rating_method.txt` | "Stage 3: Multi-Model Barrier Rating" | `assets/diagrams/fig_stage3_rating.png` |
| 5 | `stage4_arbitration_method.txt` | "Stage 4: Structured Arbitration Protocol" | `assets/diagrams/fig_stage4_arbitration.png` |

**NOT included:** `stage5_results_method.txt.HOLD` — on hold pending design discussion.

## After Generation

- Copy `final_output.png` (or best iteration) from each `outputs/run_*/` to the deploy path above
- Record which run directory produced each deployed PNG (for provenance)
- Update `docs/FIGURE_MAP.md` architecture diagrams table with provenance run IDs and status → `generated`

## On Human Review Rejection

When a generated diagram is rejected during human review:

1. Create `assets/diagrams/paperbanana/postmortem/` if it doesn't exist
2. Copy the full critic chain from the rejected run (`outputs/run_*/iter_*/`) into `postmortem/rejection_<fig_name>_<date>/`
3. Include: all iteration outputs, critic feedback, planner prompts, and metadata.json
4. Add a `rejection_notes.md` with:
   - Which diagram was rejected
   - What the human reviewer flagged (from conversation context)
   - Root cause hypothesis: Did the planner ignore the method spec? Did the critic miss the deviation? Did the visualizer hallucinate from training priors?
5. This data accumulates across runs to diagnose systematic PaperBanana failure patterns

## Do NOT

- Do not substitute model names from training data — read `configs/model_config.yaml`
- Do not edit the method.txt files — they are the source of truth
- Do not edit the output PNGs — if results are wrong, the method.txt needs fixing
- Do not generate Stage 5 — it is on hold
- Do not reuse any prior run outputs — all 18+ prior runs used wrong specs and/or wrong models
