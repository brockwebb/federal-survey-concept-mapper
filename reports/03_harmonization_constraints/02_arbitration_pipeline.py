#!/usr/bin/env python3
"""
Arbitration Pipeline v3.1
Report 03: Harmonization Constraints

Three-arbitrator design with blind masking and order randomization.
Implements Decision 008 from methodology_log.md.

Key features:
- Processes ALL 1,598 pairs (not just disagreements)
- Three arbitrators: opus-4-5, gpt-5.2, gemini-3-pro
- Blind masking: Raters shown as "Rater A", "Rater B", "Rater C"
- Order randomization: 50% fixed order, 50% randomized for position bias detection
- Tracks rater_order and order_type metadata per record
- PARALLEL PROCESSING with ThreadPoolExecutor (v3.1)

Usage:
    python arbitration_pipeline.py --arbitrator anthropic
    python arbitration_pipeline.py --arbitrator openai
    python arbitration_pipeline.py --arbitrator google
"""

import os
import json
import time
import random
import hashlib
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dotenv import load_dotenv
from pydantic import BaseModel
from tqdm import tqdm
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load environment variables
load_dotenv()
load_dotenv(Path(__file__).parent.parent.parent / '.env')

# Thread locks
checkpoint_lock = threading.Lock()
write_lock = threading.Lock()

# Fixed seed for reproducibility of randomization
RANDOM_SEED = 42


# =============================================================================
# PYDANTIC SCHEMA FOR STRUCTURED OUTPUT
# =============================================================================

class ArbitrationResult(BaseModel):
    """Schema for arbitration response."""
    final_barrier_code: str
    final_feasibility: str
    selected_rater: str  # "A", "B", "C", or "synthesis"
    reasoning: str
    specific_conflict: Optional[str] = None


# =============================================================================
# TAXONOMY REFERENCE (v1.1 with NHB.0)
# =============================================================================

BARRIER_TAXONOMY = """
## Harmonization Barrier Taxonomy (v1.1)

### Level 1: Constraint Type (7 categories)
| Code | Type | Definition |
|------|------|------------|
| TC | Temporal | Reference period or timing differences |
| CC | Construct | Concept definition or operationalization differences |
| PC | Population/Coverage | Universe, frame, or sample design differences |
| RS | Response Scale | Scale type, categories, or format differences |
| MC | Mode/Context | Interview mode or questionnaire context differences |
| PM | Processing/Metadata | Coding, weighting, or documentation differences |
| NHB | No Harmonization Barrier | Questions are functionally equivalent or near-duplicates |

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

**NHB (No Harmonization Barrier):**
- NHB.0: No barrier - questions are functionally equivalent requiring only minor standardization

### Feasibility Classification
| Code | Feasibility | Definition |
|------|-------------|------------|
| F1 | Direct recode | Mechanically transformable (simple recoding) |
| F2 | Statistical adjustment | Requires modeling or assumptions |
| F3 | Incompatible | Fundamentally different, not harmonizable |

### Coding Rules
1. If all three raters agree, confirm their consensus.
2. If two raters agree, strongly consider their position unless the third has compelling reasoning.
3. When multiple constraints apply, code the PRIMARY constraint that would need to be resolved first.
4. Hierarchy for ambiguous cases:
   - CC (Construct) > TC (Temporal) - if the temporal difference implies a construct difference
   - CC (Construct) > RS (Response Scale) - if scale difference reflects construct difference
   - PC (Population) > MC (Mode) - if population difference is the binding constraint
5. Use NHB.0 only when questions are truly functionally equivalent with no meaningful harmonization barrier.
"""


# =============================================================================
# ORDER RANDOMIZATION
# =============================================================================

def get_rater_order(pair_id: str, rater_keys: List[str], randomize: bool) -> Tuple[List[str], str]:
    """Determine rater presentation order for a pair.
    
    Args:
        pair_id: Unique pair identifier
        rater_keys: List of rater keys (e.g., ['openai', 'anthropic', 'google'])
        randomize: Whether to randomize order
        
    Returns:
        Tuple of (ordered rater keys, order_type string)
    """
    if not randomize:
        return rater_keys.copy(), "fixed"
    
    # Use pair_id hash for deterministic randomization
    hash_val = int(hashlib.md5(pair_id.encode()).hexdigest(), 16)
    rng = random.Random(hash_val)
    shuffled = rater_keys.copy()
    rng.shuffle(shuffled)
    return shuffled, "randomized"


def should_randomize(pair_id: str) -> bool:
    """Determine if this pair should have randomized order (50/50 split).
    
    Uses pair_id hash for deterministic assignment.
    """
    hash_val = int(hashlib.md5((pair_id + "_order").encode()).hexdigest(), 16)
    return hash_val % 2 == 0


# =============================================================================
# DATA LOADING
# =============================================================================

def load_all_pairs(config: Dict) -> Optional[pd.DataFrame]:
    """Load ALL pairs for arbitration (not just disagreements).
    
    Merges all three rater results and adds question texts.
    Recodes null/None barrier values to NHB.0.
    
    Args:
        config: Pipeline configuration dictionary
        
    Returns:
        DataFrame of all pairs with rater codings, or None if error
    """
    
    output_dir = Path(config['paths']['output_dir'])
    results_dir = output_dir / config['paths']['results_subdir']
    analysis_dir = output_dir / config['paths']['analysis_subdir']
    data_dir = Path(config['paths']['data_dir'])
    
    # Check for existing merged results
    merged_path = analysis_dir / 'barrier_coding_merged_3rater.csv'
    if merged_path.exists():
        print(f"Loading existing merged results: {merged_path}")
        merged = pd.read_csv(merged_path)
    else:
        # Merge rater results
        print("Merging three-rater results...")
        merged = merge_rater_results(config)
        if merged is None:
            return None
        
        # Save merged results
        analysis_dir.mkdir(parents=True, exist_ok=True)
        merged.to_csv(merged_path, index=False)
        print(f"Saved merged results: {merged_path}")
    
    # Add question texts
    cps_source = data_dir / 'cps_comparison_merged.csv'
    foodaps_source = data_dir / 'foodaps_comparison_merged.csv'
    
    source_dfs = []
    if cps_source.exists():
        source_dfs.append(pd.read_csv(cps_source))
    if foodaps_source.exists():
        source_dfs.append(pd.read_csv(foodaps_source))
    
    if source_dfs:
        source = pd.concat(source_dfs, ignore_index=True)
        source = source[['pair_id', 'survey_text', 'acs_text']].drop_duplicates(subset='pair_id')
        merged = merged.merge(source, on='pair_id', how='left')
    
    # Recode null/None barrier values to NHB.0
    rater_keys = list(config['raters'].keys())
    for rk in rater_keys:
        col = f'primary_barrier_{rk}'
        if col in merged.columns:
            null_mask = merged[col].isna() | (merged[col].astype(str).str.lower().isin(['none', 'na', 'null', '']))
            null_count = null_mask.sum()
            if null_count > 0:
                print(f"  Recoding {null_count} null/None values to NHB.0 for {rk}")
                merged.loc[null_mask, col] = 'NHB.0'
    
    print(f"\nLoaded {len(merged)} pairs for arbitration")
    
    return merged


def merge_rater_results(config: Dict) -> Optional[pd.DataFrame]:
    """Merge results from all three raters into a single dataframe."""
    
    output_dir = Path(config['paths']['output_dir'])
    results_dir = output_dir / config['paths']['results_subdir']
    
    rater_dfs = {}
    
    for rater_key, rater_config in config['raters'].items():
        model = rater_config['model']
        model_safe = model.replace('/', '-').replace(':', '-')
        results_path = results_dir / f'barrier_results_{rater_key}_{model_safe}.jsonl'
        
        if not results_path.exists():
            print(f"WARNING: Results not found for {rater_key}: {results_path}")
            continue
        
        # Load JSONL
        records = []
        with open(results_path, 'r') as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        
        if not records:
            print(f"WARNING: No records in {results_path}")
            continue
        
        df = pd.DataFrame(records)
        
        # Rename columns with rater suffix
        rename_map = {
            'primary_barrier': f'primary_barrier_{rater_key}',
            'feasibility': f'feasibility_{rater_key}',
            'specific_conflict': f'specific_conflict_{rater_key}',
            'reasoning': f'reasoning_{rater_key}',
            'additional_barriers': f'additional_barriers_{rater_key}'
        }
        df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
        
        rater_dfs[rater_key] = df
        print(f"  Loaded {len(df)} results from {rater_key}")
    
    if len(rater_dfs) < 3:
        print(f"WARNING: Only {len(rater_dfs)} raters found (expected 3)")
    
    if len(rater_dfs) < 1:
        print("ERROR: No rater results found")
        return None
    
    # Merge all raters on pair_id
    merged = None
    for rater_key, df in rater_dfs.items():
        if merged is None:
            merged = df
        else:
            # Keep only the columns we need from subsequent raters
            cols_to_keep = ['pair_id'] + [c for c in df.columns if rater_key in c]
            merged = merged.merge(df[cols_to_keep], on='pair_id', how='outer')
    
    print(f"\nMerged {len(merged)} pairs from {len(rater_dfs)} raters")
    
    return merged


# =============================================================================
# PROMPT BUILDING (with blind masking)
# =============================================================================

def build_arbitration_prompt(row: pd.Series, config: Dict, rater_order: List[str]) -> str:
    """Build prompt for arbitrator with blind masking.
    
    Args:
        row: DataFrame row with pair data and rater codings
        config: Pipeline configuration
        rater_order: List of rater keys in presentation order (maps to A, B, C)
        
    Returns:
        Prompt string with blind labels
    """
    
    survey_text = row.get('survey_text', '[Question text not available]')
    acs_text = row.get('acs_text', '[Question text not available]')
    
    # Build rater sections with blind labels
    rater_sections = []
    labels = ['A', 'B', 'C']
    
    for i, rater_key in enumerate(rater_order):
        label = labels[i]
        barrier = row.get(f'primary_barrier_{rater_key}', 'N/A')
        feasibility = row.get(f'feasibility_{rater_key}', 'N/A')
        specific = row.get(f'specific_conflict_{rater_key}', 'N/A')
        reasoning = row.get(f'reasoning_{rater_key}', 'N/A')
        
        section = f"""**Rater {label}:**
- Barrier Code: {barrier}
- Feasibility: {feasibility}
- Specific Conflict: {specific}
- Reasoning: {reasoning}"""
        rater_sections.append(section)
    
    rater_text = "\n\n".join(rater_sections)
    
    prompt = f"""You are an expert survey methodologist adjudicating barrier coding from three independent raters.

## Task
Three raters coded the harmonization barrier for this question pair. Review their codings and determine the correct classification.

## Question Pair
**Survey Question:** {survey_text}

**ACS Question:** {acs_text}

## Rater Codings

{rater_text}

## Taxonomy Reference
{BARRIER_TAXONOMY}

## Your Task
1. Analyze all three codings and their reasoning
2. If two or three raters agree, strongly consider their consensus
3. Determine the correct coding, selecting the best rater's answer or synthesizing if needed
4. If you believe there is truly no harmonization barrier, use NHB.0

Respond in this exact JSON format:
{{
    "final_barrier_code": "<code like CC.1, TC.2, NHB.0, etc.>",
    "final_feasibility": "<F1, F2, or F3>",
    "selected_rater": "<A | B | C | synthesis>",
    "reasoning": "<your explanation for why this is the correct coding>",
    "specific_conflict": "<concise description of the specific harmonization barrier, or 'None' if NHB.0>"
}}

Return ONLY the JSON object, no other text."""

    return prompt


# =============================================================================
# API CALLERS
# =============================================================================

def call_google(prompt: str, model_config: Dict, pipeline_config: Dict, max_retries: int = 5) -> Optional[Dict[str, Any]]:
    """Call Gemini for arbitration using structured output."""
    from google import genai
    
    model = model_config['model']
    max_tokens = pipeline_config.get('max_tokens', 8192)
    temperature = model_config.get('temperature', 1.0)
    
    api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY not set")
    
    for attempt in range(max_retries):
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': ArbitrationResult,
                    'max_output_tokens': max_tokens,
                    'temperature': temperature,
                }
            )
            
            text = response.text.strip()
            
            if text.startswith('```'):
                text = text.split('```')[1]
                if text.startswith('json'):
                    text = text[4:]
            
            return json.loads(text)
        
        except json.JSONDecodeError as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                time.sleep(wait_time)
            else:
                print(f"JSON parse error after {max_retries} attempts: {e}")
                return None
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                time.sleep(wait_time)
            else:
                print(f"Gemini API error after {max_retries} attempts: {e}")
                return None
    
    return None


def call_anthropic(prompt: str, model_config: Dict, pipeline_config: Dict, max_retries: int = 5) -> Optional[Dict[str, Any]]:
    """Call Anthropic Claude for arbitration."""
    import anthropic
    
    model = model_config['model']
    max_tokens = pipeline_config.get('max_tokens', 8192)
    temperature = model_config.get('temperature', 0.0)
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")
    
    for attempt in range(max_retries):
        try:
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            text = response.content[0].text.strip()
            
            if text.startswith('```'):
                text = text.split('```')[1]
                if text.startswith('json'):
                    text = text[4:]
            
            return json.loads(text)
        
        except json.JSONDecodeError as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                time.sleep(wait_time)
            else:
                print(f"JSON parse error after {max_retries} attempts: {e}")
                return None
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                time.sleep(wait_time)
            else:
                print(f"Anthropic API error after {max_retries} attempts: {e}")
                return None
    
    return None


def call_openai(prompt: str, model_config: Dict, pipeline_config: Dict, max_retries: int = 5) -> Optional[Dict[str, Any]]:
    """Call OpenAI for arbitration."""
    from openai import OpenAI
    
    model = model_config['model']
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set")
    
    for attempt in range(max_retries):
        try:
            client = OpenAI(api_key=api_key)
            
            # gpt-5.2 is minimal - only model + messages
            params = {
                'model': model,
                'messages': [{"role": "user", "content": prompt}],
                'response_format': {"type": "json_object"},
            }
            
            response = client.chat.completions.create(**params)
            
            text = response.choices[0].message.content.strip()
            return json.loads(text)
        
        except json.JSONDecodeError as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                time.sleep(wait_time)
            else:
                print(f"JSON parse error after {max_retries} attempts: {e}")
                return None
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                time.sleep(wait_time)
            else:
                print(f"OpenAI API error after {max_retries} attempts: {e}")
                return None
    
    return None


def get_api_caller(provider: str):
    """Get the appropriate API caller function for a provider."""
    callers = {
        'google': call_google,
        'anthropic': call_anthropic,
        'openai': call_openai
    }
    if provider not in callers:
        raise ValueError(f"Unknown provider: {provider}")
    return callers[provider]


# =============================================================================
# CHECKPOINT & RESULTS
# =============================================================================

def get_checkpoint_path(config: Dict, arb_key: str) -> Path:
    """Get checkpoint file path for an arbitrator."""
    base = Path(config['paths']['output_dir'])
    checkpoints = base / config['paths']['checkpoints_subdir']
    return checkpoints / f'arbitration_v3_checkpoint_{arb_key}.json'


def get_results_path(config: Dict, arb_key: str, model: str) -> Path:
    """Get results file path for an arbitrator."""
    base = Path(config['paths']['output_dir'])
    results = base / config['paths']['results_subdir']
    model_safe = model.replace('/', '-').replace(':', '-')
    return results / f'arbitration_v3_results_{arb_key}_{model_safe}.jsonl'


def load_checkpoint(checkpoint_path: Path) -> set:
    """Load checkpoint of already-processed pair IDs."""
    with checkpoint_lock:
        if checkpoint_path.exists():
            try:
                with open(checkpoint_path, 'r') as f:
                    data = json.load(f)
                    return set(data.get('processed_pairs', []))
            except (json.JSONDecodeError, Exception):
                print("  Warning: Corrupted checkpoint file, starting fresh")
                return set()
        return set()


def save_checkpoint(checkpoint_path: Path, processed: set, arb_key: str, model: str):
    """Save checkpoint with metadata."""
    with checkpoint_lock:
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        temp_file = checkpoint_path.with_suffix('.tmp')
        with open(temp_file, 'w') as f:
            json.dump({
                'arbitrator': arb_key,
                'model': model,
                'processed_pairs': list(processed),
                'version': '3.1'
            }, f)
        temp_file.replace(checkpoint_path)


def save_result(result: Dict[str, Any], results_path: Path):
    """Append result to JSONL file."""
    with write_lock:
        results_path.parent.mkdir(parents=True, exist_ok=True)
        with open(results_path, 'a') as f:
            f.write(json.dumps(result) + '\n')


# =============================================================================
# MAIN ENTRY POINT - PARALLEL PROCESSING
# =============================================================================

def process_single_pair(
    pair_data: Tuple[str, pd.Series],
    config: Dict,
    arb_config: Dict,
    pipeline_config: Dict,
    rater_keys: List[str],
    api_call,
    model: str,
    arb_key: str
) -> Optional[Dict[str, Any]]:
    """Process a single pair - designed for parallel execution.
    
    Args:
        pair_data: Tuple of (pair_id, row Series)
        config: Full pipeline config
        arb_config: Arbitrator-specific config
        pipeline_config: Pipeline settings
        rater_keys: List of rater keys
        api_call: API caller function
        model: Model name
        arb_key: Arbitrator key
        
    Returns:
        Result dict with all metadata, or None if failed
    """
    pair_id, row = pair_data
    
    # Determine presentation order
    randomize = should_randomize(pair_id)
    rater_order, order_type = get_rater_order(pair_id, rater_keys, randomize)
    
    # Build prompt with blind masking
    prompt = build_arbitration_prompt(row, config, rater_order)
    
    # Call API
    result = api_call(prompt, arb_config, pipeline_config)
    
    if result:
        # Add metadata
        result['pair_id'] = pair_id
        result['arbitrator'] = arb_key
        result['arbitrator_model'] = model
        result['rater_order'] = rater_order
        result['order_type'] = order_type
        
        # Decode selected_rater from blind label to actual rater
        selected = result.get('selected_rater', 'synthesis')
        if selected in ['A', 'B', 'C']:
            label_to_idx = {'A': 0, 'B': 1, 'C': 2}
            result['selected_rater_key'] = rater_order[label_to_idx[selected]]
        else:
            result['selected_rater_key'] = 'synthesis'
        
        # Add original rater codings for reference
        for rk in rater_keys:
            result[f'{rk}_barrier'] = row.get(f'primary_barrier_{rk}')
            result[f'{rk}_feasibility'] = row.get(f'feasibility_{rk}')
        
        return result
    
    return None


def run_single_arbitrator(config: Dict, arb_key: str, all_pairs_df: pd.DataFrame) -> bool:
    """Run arbitration for one arbitrator model on ALL pairs with parallel processing.
    
    Args:
        config: Pipeline configuration dictionary
        arb_key: Key into config['arbitrators'] (e.g., 'anthropic', 'openai', 'google')
        all_pairs_df: DataFrame of ALL pairs to arbitrate
        
    Returns:
        True if successful, False if failed
    """
    
    arb_config = config['arbitrators'][arb_key]
    pipeline_config = config['pipeline']
    
    model = arb_config['model']
    provider = arb_config['provider']
    api_key_env = arb_config['api_key_env']
    temperature = arb_config.get('temperature')
    max_tokens = pipeline_config.get('max_tokens', 8192)
    
    # Pipeline settings - USE CONFIG VALUES
    max_workers = pipeline_config.get('arbitration_max_workers', 3)
    checkpoint_interval = pipeline_config.get('arbitration_checkpoint_interval', 5)
    
    # Get rater keys for order randomization
    rater_keys = list(config['raters'].keys())
    
    # Check API key
    if not os.getenv(api_key_env):
        print(f"ERROR: {api_key_env} not set in environment")
        return False
    
    # Get paths
    checkpoint_path = get_checkpoint_path(config, arb_key)
    results_path = get_results_path(config, arb_key, model)
    
    print(f"\nArbitrator: {arb_key}")
    print(f"  Model: {model}")
    print(f"  Provider: {provider}")
    print(f"  Temperature: {temperature}")
    print(f"  Max tokens: {max_tokens}")
    print(f"  Max workers: {max_workers}")
    print(f"  Results: {results_path}")
    print(f"  Checkpoint: {checkpoint_path}")
    print(f"  Rater order base: {rater_keys}")
    
    # Get API caller
    api_call = get_api_caller(provider)
    
    # Load checkpoint
    processed = load_checkpoint(checkpoint_path)
    
    # Filter to unprocessed pairs
    to_process_df = all_pairs_df[~all_pairs_df['pair_id'].isin(processed)]
    
    print(f"\nArbitration status:")
    print(f"  - Total pairs: {len(all_pairs_df)}")
    print(f"  - Already processed: {len(processed)}")
    print(f"  - Remaining: {len(to_process_df)}")
    
    if len(to_process_df) == 0:
        print("All pairs already processed!")
        return True
    
    # Prepare work items: list of (pair_id, row) tuples
    work_items = [(row['pair_id'], row) for _, row in to_process_df.iterrows()]
    
    # Process in parallel
    success_count = 0
    failed_count = 0
    order_stats = {'fixed': 0, 'randomized': 0}
    
    print(f"\nProcessing {len(work_items)} pairs with {max_workers} workers...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_pair = {
            executor.submit(
                process_single_pair,
                item,
                config,
                arb_config,
                pipeline_config,
                rater_keys,
                api_call,
                model,
                arb_key
            ): item[0]  # pair_id for tracking
            for item in work_items
        }
        
        with tqdm(total=len(work_items), desc=f"  {arb_key}") as pbar:
            for future in as_completed(future_to_pair):
                pair_id = future_to_pair[future]
                
                try:
                    result = future.result()
                    
                    if result:
                        save_result(result, results_path)
                        processed.add(pair_id)
                        success_count += 1
                        order_stats[result['order_type']] += 1
                    else:
                        failed_count += 1
                
                except Exception as e:
                    print(f"\n  Pair {pair_id} exception: {str(e)[:80]}")
                    failed_count += 1
                
                pbar.update(1)
                
                # Checkpoint periodically
                if (success_count + failed_count) % checkpoint_interval == 0:
                    save_checkpoint(checkpoint_path, processed, arb_key, model)
    
    # Final checkpoint
    save_checkpoint(checkpoint_path, processed, arb_key, model)
    
    print(f"\n{arb_key.upper()} arbitration complete!")
    print(f"  Successful: {success_count}")
    print(f"  Failed: {failed_count}")
    print(f"  Order distribution: {order_stats}")
    
    return failed_count == 0


def run_arbitration_stage(config: Dict) -> bool:
    """Run arbitration stage for all configured arbitrators.
    
    Args:
        config: Pipeline configuration dictionary
        
    Returns:
        True if all arbitrators succeeded, False otherwise
    """
    
    print("="*60)
    print("ARBITRATION STAGE v3.1 (Three Arbitrators, Parallel Processing)")
    print("="*60)
    
    # Load all pairs
    all_pairs = load_all_pairs(config)
    if all_pairs is None or len(all_pairs) == 0:
        print("ERROR: No pairs to arbitrate. Run rating stage first.")
        return False
    
    # Run each arbitrator
    results = {}
    for arb_key in config['arbitrators'].keys():
        print(f"\n{'='*40}")
        print(f"Running arbitrator: {arb_key}")
        print(f"{'='*40}")
        
        success = run_single_arbitrator(config, arb_key, all_pairs)
        results[arb_key] = success
        
        if not success:
            print(f"WARNING: Arbitrator {arb_key} had failures")
    
    # Summary
    print("\n" + "="*60)
    print("ARBITRATION STAGE COMPLETE")
    print("="*60)
    
    for arb_key, success in results.items():
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"  {arb_key}: {status}")
    
    return all(results.values())


# =============================================================================
# STANDALONE MODE
# =============================================================================

def main():
    """Standalone execution for testing."""
    import yaml
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Arbitration Pipeline v3.1 (standalone mode)',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--arbitrator', '-a',
        default=None,
        help='Single arbitrator to run (default: all)'
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("ARBITRATION PIPELINE v3.1 (standalone mode)")
    print("="*60)
    print("\nThis script is designed to be called from run_pipeline.py")
    print("For standalone testing, loading config.yaml...")
    
    config_path = Path('./config.yaml')
    if not config_path.exists():
        print(f"ERROR: {config_path} not found")
        return
    
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Show config values being used
    pipeline_config = config['pipeline']
    print(f"\nPipeline settings from config.yaml:")
    print(f"  arbitration_max_workers: {pipeline_config.get('arbitration_max_workers', 3)}")
    print(f"  arbitration_checkpoint_interval: {pipeline_config.get('arbitration_checkpoint_interval', 5)}")
    
    # Load all pairs
    all_pairs = load_all_pairs(config)
    if all_pairs is None or len(all_pairs) == 0:
        print("ERROR: No pairs to arbitrate. Run rating stage first.")
        return
    
    if args.arbitrator:
        # Run single arbitrator
        if args.arbitrator not in config['arbitrators']:
            print(f"ERROR: Unknown arbitrator: {args.arbitrator}")
            print(f"Available: {list(config['arbitrators'].keys())}")
            return
        
        success = run_single_arbitrator(config, args.arbitrator, all_pairs)
        if not success:
            print(f"\nERROR: Arbitrator {args.arbitrator} failed")
    else:
        # Run all arbitrators
        run_arbitration_stage(config)
    
    print("\n" + "="*60)
    print("STANDALONE PROCESSING COMPLETE")
    print("="*60)


if __name__ == '__main__':
    main()
