#!/usr/bin/env python3
"""
LLM-based harmonization barrier coding for survey question pairs.

Adapts the existing categorization pipeline to code non-consolidatable pairs
with barrier types (TC, CC, PC, RS, MC, PM) and feasibility (F1, F2, F3).

Based on llm_categorization.py from Report 02.
"""

import os
import json
import time
import re
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv
import anthropic
from openai import OpenAI
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Load environment variables
load_dotenv()

# Configuration
BATCH_SIZE = 10
MAX_WORKERS = 6
CHECKPOINT_FILE = Path('./output/barrier_coding_checkpoint.json')
RESULTS_DIR = Path('./output/results')

# Thread locks
checkpoint_lock = threading.Lock()
write_lock = threading.Lock()
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Taxonomy definition (embedded for portability)
BARRIER_TAXONOMY = """
## Harmonization Barrier Taxonomy

### Level 1: Constraint Type (6 categories)
| Code | Type | Definition |
|------|------|------------|
| TC | Temporal | Reference period or timing differences |
| CC | Construct | Concept definition or operationalization differences |
| PC | Population/Coverage | Universe, frame, or sample design differences |
| RS | Response Scale | Scale type, categories, or format differences |
| MC | Mode/Context | Interview mode or questionnaire context differences |
| PM | Processing/Metadata | Coding, weighting, or documentation differences |

### Level 2: Subtypes
**TC (Temporal):**
- TC.1: Reference period length (e.g., 7-day vs 12-month)
- TC.2: Temporal framing (point-in-time vs habitual vs retrospective)
- TC.3: Calendar alignment (fixed vs rolling reference periods)

**CC (Construct):**
- CC.1: Concept definition (different meaning of core term)
- CC.2: Operationalization (different behavioral indicators)
- CC.3: Boundary conditions (different thresholds or cutoffs)
- CC.4: Scope inclusions (different components counted)

**PC (Population/Coverage):**
- PC.1: Universe definition (target population differs)
- PC.2: Frame exclusions (different exclusions from sampling)
- PC.3: Age bounds (different age eligibility)
- PC.4: Geographic scope (different geographic coverage)

**RS (Response Scale):**
- RS.1: Scale type (fundamentally different response formats)
- RS.2: Category structure (different number/boundaries of categories)
- RS.3: Anchoring/labels (different verbal anchors or direction)
- RS.4: Numeric vs verbal (numeric scale vs labeled categories)

**MC (Mode/Context):**
- MC.1: Interview mode (different data collection modes)
- MC.2: Question routing (different skip patterns or filters)
- MC.3: Contextual priming (preceding questions affect interpretation)
- MC.4: Proxy response (proxy vs self-report rules)

**PM (Processing/Metadata):**
- PM.1: Coding schemes (different classification or coding)
- PM.2: Derived variables (different algorithms for constructed variables)
- PM.3: Documentation gaps (insufficient metadata to assess)

### Feasibility Classification
| Code | Feasibility | Definition |
|------|-------------|------------|
| F1 | Direct recode | Mechanically transformable (simple recoding) |
| F2 | Statistical adjustment | Requires modeling or assumptions |
| F3 | Incompatible | Fundamentally different, not harmonizable |
"""


def load_question_pairs(cps_path: str = None, foodaps_path: str = None) -> pd.DataFrame:
    """Load and filter question pairs that need barrier coding."""
    
    pairs = []
    
    # Load CPS data
    if cps_path and Path(cps_path).exists():
        cps_df = pd.read_csv(cps_path)
        # Filter to non-consolidatable pairs (partial or no)
        cps_filtered = cps_df[
            (cps_df['claude_consolidation_potential'].isin(['partial', 'no'])) |
            (cps_df['gpt_consolidation_potential'].isin(['partial', 'no']))
        ].copy()
        cps_filtered['source_survey'] = 'CPS'
        pairs.append(cps_filtered)
        print(f"  Loaded {len(cps_filtered)} CPS pairs for barrier coding")
    
    # Load FoodAPS data
    if foodaps_path and Path(foodaps_path).exists():
        foodaps_df = pd.read_csv(foodaps_path)
        # Filter to non-consolidatable pairs
        foodaps_filtered = foodaps_df[
            (foodaps_df['claude_consolidation_potential'].isin(['partial', 'no'])) |
            (foodaps_df['gpt_consolidation_potential'].isin(['partial', 'no']))
        ].copy()
        foodaps_filtered['source_survey'] = 'FoodAPS'
        pairs.append(foodaps_filtered)
        print(f"  Loaded {len(foodaps_filtered)} FoodAPS pairs for barrier coding")
    
    if pairs:
        combined = pd.concat(pairs, ignore_index=True)
        print(f"  Total pairs for barrier coding: {len(combined)}")
        return combined
    else:
        raise FileNotFoundError("No data files found!")


def create_barrier_prompt(batch: List[Dict[str, Any]]) -> str:
    """Create barrier coding prompt for a batch of question pairs."""
    
    prompt = f"""You are coding harmonization barriers between federal survey questions using an established taxonomy from the survey methodology literature.

{BARRIER_TAXONOMY}

## TASK
For each question pair below, identify WHY they cannot be directly consolidated. Code:
1. **Primary barrier**: The main constraint preventing consolidation (Level 1 code + Level 2 subtype)
2. **Feasibility**: How difficult would it be to harmonize? (F1, F2, or F3)
3. **Specific conflict**: Brief description of the exact difference
4. **Additional barriers**: If multiple barriers apply, list them (optional)

## QUESTION PAIRS TO CODE
{json.dumps(batch, indent=2)}

## OUTPUT FORMAT
Return a JSON array with one object per pair, in the same order:
[
  {{
    "pair_id": "CPS_0023",
    "primary_barrier": "TC.1",
    "feasibility": "F2",
    "specific_conflict": "CPS asks current/usual hours; ACS asks past 12 months",
    "additional_barriers": ["CC.2"],
    "reasoning": "Primary issue is temporal reference mismatch. CPS measures point-in-time usual hours while ACS retrospectively averages over a year."
  }},
  ...
]

Return ONLY the JSON array, no other text."""
    
    return prompt


def call_openai(batch: List[Dict[str, Any]], max_retries: int = 5) -> List[Dict[str, Any]]:
    """Call OpenAI API with exponential backoff."""
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    prompt = create_barrier_prompt(batch)
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Using gpt-4o-mini as per Context7
                messages=[
                    {"role": "system", "content": "You are a survey methodology expert specializing in data harmonization."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )
            
            content = response.choices[0].message.content
            
            # Clean response
            content = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', content)
            
            # Try to parse JSON
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                # Extract array if wrapped
                start = content.find('[')
                end = content.rfind(']')
                if start != -1 and end != -1:
                    array_str = content[start:end+1]
                    array_str = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', array_str)
                    result = json.loads(array_str)
                else:
                    raise
            
            if not isinstance(result, list):
                if isinstance(result, dict) and len(result) == 1:
                    result = list(result.values())[0]
                else:
                    print(f"  Unexpected response format: {type(result)}")
                    return []
            
            return result
            
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"  Error: {str(e)[:100]}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"  Failed after {max_retries} attempts: {str(e)[:100]}")
                return []
    
    return []


def call_claude(batch: List[Dict[str, Any]], max_retries: int = 5) -> List[Dict[str, Any]]:
    """Call Claude API with exponential backoff."""
    client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    prompt = create_barrier_prompt(batch)
    
    for attempt in range(max_retries):
        try:
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",  # Using claude-haiku-4-5 as per Context7
                max_tokens=4096,
                temperature=0,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.content[0].text
            
            # Strip markdown if present
            if content.startswith('```json'):
                content = content.split('```json')[1]
            if content.endswith('```'):
                content = content.rsplit('```', 1)[0]
            content = content.strip()
            
            result = json.loads(content)
            
            if not isinstance(result, list):
                if isinstance(result, dict) and len(result) == 1:
                    result = list(result.values())[0]
                else:
                    print(f"  Unexpected response format: {type(result)}")
                    return []
            
            return result
            
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"  Error: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"  Failed after {max_retries} attempts: {e}")
                return []
    
    return []


def load_checkpoint() -> Dict[str, Any]:
    """Load checkpoint if exists."""
    with checkpoint_lock:
        if CHECKPOINT_FILE.exists():
            try:
                with open(CHECKPOINT_FILE, 'r') as f:
                    content = f.read().strip()
                    if not content:
                        return {'openai_batch': 0, 'claude_batch': 0}
                    return json.loads(content)
            except (json.JSONDecodeError, Exception):
                print("  Warning: Corrupted checkpoint file, starting fresh")
                return {'openai_batch': 0, 'claude_batch': 0}
        return {'openai_batch': 0, 'claude_batch': 0}


def save_checkpoint(checkpoint: Dict[str, Any]):
    """Save checkpoint."""
    with checkpoint_lock:
        CHECKPOINT_FILE.parent.mkdir(parents=True, exist_ok=True)
        temp_file = CHECKPOINT_FILE.with_suffix('.tmp')
        with open(temp_file, 'w') as f:
            json.dump(checkpoint, f)
        temp_file.replace(CHECKPOINT_FILE)


def save_results(results: List[Dict[str, Any]], model: str):
    """Append results to JSONL file."""
    output_file = RESULTS_DIR / f'barrier_results_{model}.jsonl'
    with write_lock:
        with open(output_file, 'a') as f:
            for result in results:
                f.write(json.dumps(result) + '\n')


def prepare_batch(df_slice: pd.DataFrame) -> List[Dict[str, Any]]:
    """Prepare a batch of pairs for the prompt."""
    batch = []
    for _, row in df_slice.iterrows():
        batch.append({
            'pair_id': row['pair_id'],
            'survey_question': row['survey_text'],
            'acs_question': row['acs_text'],
            'subtopic': row.get('subtopic', 'Unknown'),
            'prior_classification': row.get('claude_classification', 'Unknown'),
            'consolidation_potential': row.get('claude_consolidation_potential', 'Unknown')
        })
    return batch


def process_model(pairs_df: pd.DataFrame, model: str, start_batch: int = 0):
    """Process all pairs for a given model."""
    
    print(f"\n{'='*70}")
    print(f"Processing with {model.upper()} ({MAX_WORKERS} workers)")
    print(f"{'='*70}")
    
    # Create batches
    batches = []
    for i in range(0, len(pairs_df), BATCH_SIZE):
        batch_df = pairs_df.iloc[i:i + BATCH_SIZE]
        batches.append(prepare_batch(batch_df))
    
    total_batches = len(batches)
    print(f"Total batches: {total_batches}")
    print(f"Starting from batch: {start_batch}")
    
    api_call = call_openai if model == 'openai' else call_claude
    
    # Sequential processing with progress bar
    completed_count = start_batch
    with tqdm(total=total_batches - start_batch, desc=f"  {model}") as pbar:
        for batch_idx in range(start_batch, total_batches):
            batch = batches[batch_idx]
            results = api_call(batch)
            
            if results:
                save_results(results, model)
                completed_count += 1
                checkpoint = load_checkpoint()
                checkpoint[f'{model}_batch'] = completed_count
                save_checkpoint(checkpoint)
            else:
                print(f"\n  Warning: Batch {batch_idx} failed for {model}")
            
            pbar.update(1)
            
            # Small delay between batches to avoid rate limits
            time.sleep(0.5)
    
    print(f"\n{model.upper()} processing complete!")


def main():
    """Main execution."""
    import sys
    
    print("="*70)
    print("HARMONIZATION BARRIER CODING PIPELINE")
    print("Report 03: Why Can't These Questions Be Consolidated?")
    print("="*70)
    
    # Default paths - adjust as needed
    cps_path = './data/cps_comparison_merged.csv'
    foodaps_path = './data/foodaps_comparison_merged.csv'
    
    # Also check uploads directory
    if not Path(cps_path).exists():
        cps_path = '/mnt/user-data/uploads/cps_comparison_merged.csv'
    if not Path(foodaps_path).exists():
        foodaps_path = '/mnt/user-data/uploads/foodaps_comparison_merged.csv'
    
    # Load data
    print("\nLoading question pairs...")
    pairs_df = load_question_pairs(cps_path, foodaps_path)
    
    # Load checkpoint
    checkpoint = load_checkpoint()
    print(f"\nCheckpoint: OpenAI batch {checkpoint['openai_batch']}, Claude batch {checkpoint['claude_batch']}")
    
    # Check for model argument
    run_openai = True
    run_claude = True
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--openai-only':
            run_claude = False
        elif sys.argv[1] == '--claude-only':
            run_openai = False
    
    # Process with both models
    total_batches = (len(pairs_df) + BATCH_SIZE - 1) // BATCH_SIZE
    
    if run_openai and checkpoint['openai_batch'] < total_batches:
        process_model(pairs_df, 'openai', checkpoint['openai_batch'])
    elif run_openai:
        print("\nOpenAI processing already complete (skipping)")
    
    if run_claude and checkpoint['claude_batch'] < total_batches:
        process_model(pairs_df, 'claude', checkpoint['claude_batch'])
    elif run_claude:
        print("\nClaude processing already complete (skipping)")
    
    print("\n" + "="*70)
    print("ALL PROCESSING COMPLETE!")
    print("="*70)
    print(f"\nResults saved to:")
    print(f"  - {RESULTS_DIR}/barrier_results_openai.jsonl")
    print(f"  - {RESULTS_DIR}/barrier_results_claude.jsonl")


if __name__ == '__main__':
    main()
