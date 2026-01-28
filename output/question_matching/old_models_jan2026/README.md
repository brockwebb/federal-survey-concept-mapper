# Old Models Run - January 2026

## What Happened
Claude Code ignored task instructions and used wrong model strings:
- Used `claude-3-haiku` instead of `claude-haiku-4-5-20251001`
- Used `gpt-4o-mini` instead of `gpt-5-mini`
- Attempted `claude-haiku-4.5` (wrong format) which returned 404 errors

## Files Preserved

| File | Model Used | Notes |
|------|------------|-------|
| `llm_results_claude_haiku3.csv` | claude-3-haiku | 107 pairs, 0 errors |
| `llm_results_gpt4omini.csv` | gpt-4o-mini | 107 pairs, 0 errors |
| `llm_results_claude_haiku45_FAILED.csv` | claude-haiku-4.5 (wrong string) | All 404 errors |
| `llm_comparison_claude_vs_gpt.csv` | claude-3-haiku vs gpt-4o-mini | Side-by-side |
| `multimodel_comparison_report.md` | Analysis of wrong models | |
| `validation_all_models.csv` | Combined template | |

## Results Summary (for historical reference)

Inter-Model Agreement (wrong models):
- Claude 3 Haiku vs GPT-4o-mini: 74.8% agreement, Cohen's Kappa = 0.608

Classification distributions varied significantly between deprecated and current models.

## Lesson Learned
Always verify model strings in generated code. CC will hallucinate model names even when explicitly specified.
