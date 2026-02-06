#!/usr/bin/env python3
"""
Barrier Coding Pipeline v2.0
Report 03: Harmonization Constraints

Config-driven LLM barrier coding for survey question pairs.
All model names come from config.yaml - no hardcoding.

Usage:
    Called from run_pipeline.py, not directly.
"""

import os
import json
import time
import re
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from tqdm import tqdm
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load environment variables
load_dotenv()
load_dotenv(Path(__file__).parent.parent.parent / '.env')

# Thread locks
checkpoint_lock = threading.Lock()
write_lock = threading.Lock()

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


# =============================================================================
# DATA LOADING
# =============================================================================

def load_question_pairs(config: Dict) -> pd.DataFrame:
    """Load and filter question pairs that need barrier coding."""

    data_dir = Path(config['paths']['data_dir'])
    cps_path = data_dir / 'cps_comparison_merged.csv'
    foodaps_path = data_dir / 'foodaps_comparison_merged.csv'

    pairs = []

    # Load CPS data
    if cps_path.exists():
        cps_df = pd.read_csv(cps_path)
        cps_filtered = cps_df[
            (cps_df['claude_consolidation_potential'].isin(['partial', 'no'])) |
            (cps_df['gpt_consolidation_potential'].isin(['partial', 'no']))
        ].copy()
        cps_filtered['source_survey'] = 'CPS'
        pairs.append(cps_filtered)
        print(f"  Loaded {len(cps_filtered)} CPS pairs for barrier coding")

    # Load FoodAPS data
    if foodaps_path.exists():
        foodaps_df = pd.read_csv(foodaps_path)
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


# =============================================================================
# PROMPT BUILDING
# =============================================================================

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


# =============================================================================
# API CALLERS
# =============================================================================

def call_openai(batch: List[Dict[str, Any]], model_config: Dict, pipeline_config: Dict, max_retries: int = 5) -> List[Dict[str, Any]]:
    """Call OpenAI API with exponential backoff.
    
    IMPORTANT: gpt-5-mini is finicky. The working code in categorize_openai.py
    uses MINIMAL parameters - just model and messages. Adding extra params
    like max_completion_tokens or temperature can cause empty responses.
    """
    from openai import OpenAI

    model = model_config['model']
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    prompt = create_barrier_prompt(batch)

    for attempt in range(max_retries):
        try:
            # MINIMAL PARAMS - matches working categorize_openai.py
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a survey methodology expert specializing in data harmonization."},
                    {"role": "user", "content": prompt}
                ]
            )

            content = response.choices[0].message.content
            
            if content is None or content == '':
                raise ValueError(f"Empty response from {model}")
            
            content = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', content)

            try:
                result = json.loads(content)
            except json.JSONDecodeError:
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


def call_anthropic(batch: List[Dict[str, Any]], model_config: Dict, pipeline_config: Dict, max_retries: int = 5) -> List[Dict[str, Any]]:
    """Call Anthropic Claude API with exponential backoff."""
    import anthropic

    model = model_config['model']
    max_tokens = pipeline_config.get('max_tokens', 1024)
    temperature = model_config.get('temperature', 0.0)

    client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    prompt = create_barrier_prompt(batch)

    for attempt in range(max_retries):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text

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


def call_google(batch: List[Dict[str, Any]], model_config: Dict, pipeline_config: Dict, max_retries: int = 5) -> List[Dict[str, Any]]:
    """Call Google Gemini API with exponential backoff."""
    from google import genai

    model = model_config['model']
    max_tokens = pipeline_config.get('max_tokens', 1024)
    temperature = model_config.get('temperature', 1.0)

    api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY not set")

    client = genai.Client(api_key=api_key)
    prompt = create_barrier_prompt(batch)

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config={
                    'response_mime_type': 'application/json',
                    'max_output_tokens': max_tokens,
                    'temperature': temperature,
                }
            )

            content = response.text.strip()

            if content.startswith('```'):
                content = content.split('```')[1]
                if content.startswith('json'):
                    content = content[4:]

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


def get_api_caller(provider: str):
    """Get the appropriate API caller function for a provider."""
    callers = {
        'openai': call_openai,
        'anthropic': call_anthropic,
        'google': call_google
    }
    if provider not in callers:
        raise ValueError(f"Unknown provider: {provider}")
    return callers[provider]


# =============================================================================
# CHECKPOINT & RESULTS
# =============================================================================

def get_checkpoint_path(config: Dict, rater_key: str) -> Path:
    """Get checkpoint file path for a rater."""
    base = Path(config['paths']['output_dir'])
    checkpoints = base / config['paths']['checkpoints_subdir']
    return checkpoints / f'barrier_checkpoint_{rater_key}.json'


def get_results_path(config: Dict, rater_key: str, model: str) -> Path:
    """Get results file path for a rater."""
    base = Path(config['paths']['output_dir'])
    results = base / config['paths']['results_subdir']
    # Sanitize model name for filename
    model_safe = model.replace('/', '-').replace(':', '-')
    return results / f'barrier_results_{rater_key}_{model_safe}.jsonl'


def load_checkpoint(checkpoint_path: Path) -> int:
    """Load checkpoint - returns batch number to resume from."""
    with checkpoint_lock:
        if checkpoint_path.exists():
            try:
                with open(checkpoint_path, 'r') as f:
                    content = f.read().strip()
                    if not content:
                        return 0
                    data = json.loads(content)
                    return data.get('batch', 0)
            except (json.JSONDecodeError, Exception):
                print("  Warning: Corrupted checkpoint file, starting fresh")
                return 0
        return 0


def save_checkpoint(checkpoint_path: Path, batch: int, rater_key: str, model: str):
    """Save checkpoint with metadata."""
    with checkpoint_lock:
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        temp_file = checkpoint_path.with_suffix('.tmp')
        with open(temp_file, 'w') as f:
            json.dump({
                'rater': rater_key,
                'model': model,
                'batch': batch
            }, f)
        temp_file.replace(checkpoint_path)


def save_results(results: List[Dict[str, Any]], results_path: Path, rater_key: str):
    """Append results to JSONL file."""
    with write_lock:
        results_path.parent.mkdir(parents=True, exist_ok=True)
        with open(results_path, 'a') as f:
            for result in results:
                result['rater'] = rater_key
                f.write(json.dumps(result) + '\n')


# =============================================================================
# BATCH PROCESSING
# =============================================================================

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


# =============================================================================
# MAIN ENTRY POINT (called from run_pipeline.py)
# =============================================================================

def run_single_rater(config: Dict, rater_key: str) -> bool:
    """Run barrier coding for one rater model.

    Args:
        config: Pipeline configuration dictionary
        rater_key: Key into config['raters'] (e.g., 'openai', 'anthropic', 'google')

    Returns:
        True if successful, False if failed
    """

    rater_config = config['raters'][rater_key]
    pipeline_config = config['pipeline']

    model = rater_config['model']
    provider = rater_config['provider']
    api_key_env = rater_config['api_key_env']
    temperature = rater_config.get('temperature')
    max_tokens = pipeline_config.get('max_tokens', 1024)

    # Pipeline settings
    batch_size = pipeline_config.get('rating_batch_size', 10)
    max_workers = pipeline_config.get('rating_max_workers', 6)
    checkpoint_interval = pipeline_config.get('rating_checkpoint_interval', 10)

    # Check API key
    if not os.getenv(api_key_env):
        print(f"ERROR: {api_key_env} not set in environment")
        return False

    # Get paths
    checkpoint_path = get_checkpoint_path(config, rater_key)
    results_path = get_results_path(config, rater_key, model)

    print(f"\nRater: {rater_key}")
    print(f"  Model: {model}")
    print(f"  Provider: {provider}")
    print(f"  Max workers: {max_workers}")
    print(f"  Results: {results_path}")
    print(f"  Checkpoint: {checkpoint_path}")

    # Load data
    print("\nLoading question pairs...")
    try:
        pairs_df = load_question_pairs(config)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return False

    # Get API caller
    api_call = get_api_caller(provider)

    # Create batches
    batches = []
    for i in range(0, len(pairs_df), batch_size):
        batch_df = pairs_df.iloc[i:i + batch_size]
        batches.append(prepare_batch(batch_df))

    total_batches = len(batches)

    # Load checkpoint
    start_batch = load_checkpoint(checkpoint_path)

    print(f"\nTotal batches: {total_batches}")
    print(f"Starting from batch: {start_batch}")

    if start_batch >= total_batches:
        print("All batches already processed!")
        return True

    # Get batches to process (from checkpoint onwards)
    batches_to_process = [(idx, batches[idx]) for idx in range(start_batch, total_batches)]
    
    # Process batches in parallel - matches working categorize_openai.py pattern
    completed_count = 0
    failed_batches = []

    def process_single_batch(batch_tuple):
        """Process one batch and return results."""
        batch_idx, batch = batch_tuple
        return batch_idx, api_call(batch, rater_config, pipeline_config)

    print(f"\nProcessing {len(batches_to_process)} batches with {max_workers} workers...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_batch = {
            executor.submit(process_single_batch, batch_tuple): batch_tuple[0]
            for batch_tuple in batches_to_process
        }

        with tqdm(total=len(batches_to_process), desc=f"  {rater_key}") as pbar:
            for future in as_completed(future_to_batch):
                batch_idx = future_to_batch[future]
                try:
                    _, results = future.result()
                    if results:
                        save_results(results, results_path, rater_key)
                        completed_count += 1
                    else:
                        failed_batches.append(batch_idx)
                except Exception as e:
                    print(f"\n  Batch {batch_idx} exception: {str(e)[:80]}")
                    failed_batches.append(batch_idx)
                
                pbar.update(1)

    # Save final checkpoint
    final_batch = total_batches if not failed_batches else start_batch + completed_count
    save_checkpoint(checkpoint_path, final_batch, rater_key, model)

    print(f"\n{rater_key.upper()} processing complete!")
    print(f"  Completed: {completed_count}")
    print(f"  Failed: {len(failed_batches)}")

    return len(failed_batches) == 0


# =============================================================================
# STANDALONE MODE (for testing)
# =============================================================================

def main():
    """Standalone execution for testing."""
    import yaml

    print("="*60)
    print("BARRIER CODING PIPELINE v2.0 (standalone mode)")
    print("="*60)
    print("\nThis script is designed to be called from run_pipeline.py")
    print("For standalone testing, loading config.yaml...")

    config_path = Path('./config.yaml')
    if not config_path.exists():
        print(f"ERROR: {config_path} not found")
        return

    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Run all raters sequentially
    for rater_key in config['raters'].keys():
        print(f"\n{'='*60}")
        print(f"Running rater: {rater_key}")
        print('='*60)

        success = run_single_rater(config, rater_key)
        if not success:
            print(f"\nERROR: Rater {rater_key} failed")
            break

    print("\n" + "="*60)
    print("STANDALONE PROCESSING COMPLETE")
    print("="*60)


if __name__ == '__main__':
    main()
