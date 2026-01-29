# Report 03: Harmonization Barrier Analysis

## Setup Instructions

### 1. Copy data files to the data directory:
```bash
cp /path/to/cps_comparison_merged.csv ./data/
cp /path/to/foodaps_comparison_merged.csv ./data/
```

### 2. Ensure environment variables are set:
Create a `.env` file with:
```
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
```

### 3. Install dependencies:
```bash
pip install pandas anthropic openai python-dotenv tqdm
```

### 4. Run the pipeline:
```bash
# Run both models
python barrier_coding_pipeline.py

# Run only OpenAI
python barrier_coding_pipeline.py --openai-only

# Run only Claude
python barrier_coding_pipeline.py --claude-only
```

### 5. Output files:
- `output/results/barrier_results_openai.jsonl`
- `output/results/barrier_results_claude.jsonl`
- `output/barrier_coding_checkpoint.json` (resume capability)

## Data Requirements

Input CSVs must have these columns:
- `pair_id`: Unique identifier
- `survey_text`: Survey question text
- `acs_text`: ACS question text
- `subtopic`: Topic category
- `claude_consolidation_potential`: yes/no/partial
- `gpt_consolidation_potential`: yes/no/partial
- `claude_classification`: near_duplicate/related_but_distinct/not_comparable/etc.

The pipeline filters to pairs where consolidation_potential is "partial" or "no".

## Model Configuration

Current models (from Context7, Jan 2025):
- OpenAI: `gpt-4o-mini`
- Anthropic: `claude-haiku-4-5-20251001`

These match the models used in Report 02 for consistency.

## Cost Estimate

With ~1,510 pairs at batch size 10 = ~151 batches per model
- OpenAI gpt-4o-mini: ~$0.15/1M input tokens, ~$0.60/1M output tokens
- Claude haiku: ~$0.25/1M input tokens, ~$1.25/1M output tokens

Estimated total cost: $5-15 depending on response verbosity
