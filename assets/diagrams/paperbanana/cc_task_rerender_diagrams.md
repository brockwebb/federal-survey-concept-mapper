# CC Task: RE-RENDER Pipeline Diagrams via PaperBanana (Take 2)

**Date:** 2026-03-01
**Repo:** `/Users/brock/Documents/GitHub/federal-survey-concept-mapper`
**Priority:** High
**Why redo:** Previous run used wrong model names from training data instead of config.

---

## BEFORE YOU DO ANYTHING

```bash
cat /Users/brock/Documents/GitHub/PaperBanana/configs/model_config.yaml
```

Read the output. Use ONLY those model names. Your training data model names are WRONG.

---

## Method.txt Files (absolute paths, all exist, do not modify)

1. `/Users/brock/Documents/GitHub/federal-survey-concept-mapper/assets/diagrams/paperbanana/pipeline_overview_method.txt`
2. `/Users/brock/Documents/GitHub/federal-survey-concept-mapper/assets/diagrams/paperbanana/stage1_classification_method.txt`
3. `/Users/brock/Documents/GitHub/federal-survey-concept-mapper/assets/diagrams/paperbanana/stage2_overlap_method.txt`
4. `/Users/brock/Documents/GitHub/federal-survey-concept-mapper/assets/diagrams/paperbanana/stage3_rating_method.txt`
5. `/Users/brock/Documents/GitHub/federal-survey-concept-mapper/assets/diagrams/paperbanana/stage4_arbitration_method.txt`

Do NOT generate stage5 (.HOLD file).

## Deploy Outputs To

1. `/Users/brock/Documents/GitHub/federal-survey-concept-mapper/assets/diagrams/fig_pipeline_overview.png`
2. `/Users/brock/Documents/GitHub/federal-survey-concept-mapper/assets/diagrams/fig_stage1_classification.png`
3. `/Users/brock/Documents/GitHub/federal-survey-concept-mapper/assets/diagrams/fig_stage2_overlap.png`
4. `/Users/brock/Documents/GitHub/federal-survey-concept-mapper/assets/diagrams/fig_stage3_rating.png`
5. `/Users/brock/Documents/GitHub/federal-survey-concept-mapper/assets/diagrams/fig_stage4_arbitration.png`

## PaperBanana Location

`/Users/brock/Documents/GitHub/PaperBanana`

Use whatever invocation method PaperBanana provides (demo.py, main.py, or direct agent calls). The method.txt content is the prompt input. Generate with up to 3 critic iterations per diagram.

## Rules

- Read `configs/model_config.yaml` for model names. Do not override.
- Read `.env` for API key names. Do not override.
- Do not modify method.txt files.
- Do not modify model_config.yaml or .env.
- Record provenance (run directory) for each output.
