#!/usr/bin/env python3
"""
Survey Question Matching - Multi-Survey Analysis

Parameterized script for comparing any survey against ACS.
Run from repo root:
    python src/survey_question_matching.py --survey foodaps
    python src/survey_question_matching.py --survey cps
    python src/survey_question_matching.py --survey cps --generate-only  # Just create pairs, no LLM

Models: claude-haiku-4-5-20251001, gpt-5-mini
"""

import os
import sys
import json
import re
import argparse
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import anthropic
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from datetime import datetime

load_dotenv()

# === CONFIGURATION ===
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
OUTPUT_BASE = PROJECT_ROOT / 'output' / 'question_matching'

# Model strings - VERIFIED CORRECT
CLAUDE_MODEL = "claude-haiku-4-5-20251001"
GPT_MODEL = "gpt-5-mini"

MAX_RETRIES = 5
MAX_WORKERS = 4

# Survey configurations
SURVEY_CONFIG = {
    'foodaps': {
        'name': 'FoodAPS',
        'column': 'Food Acquisition and Purchase Survey (FoodAPS) Initial Interview/Household Survey',
        'output_dir': 'foodaps',
        'text_col_prefix': 'foodaps'
    },
    'cps': {
        'name': 'CPS',
        'column': 'Current Population Survey (CPS)',
        'output_dir': 'cps',
        'text_col_prefix': 'cps'
    },
    'sipp': {
        'name': 'SIPP',
        'column': 'Survey of Income and Program Participation (SIPP)',
        'output_dir': 'sipp',
        'text_col_prefix': 'sipp'
    }
}

ACS_COLUMN = 'American Community Survey (ACS)'

PROMPT_TEMPLATE = """Compare these two federal survey questions for equivalence:

QUESTION A ({survey_name}): "{survey_text}"
QUESTION B (ACS): "{acs_text}"
SUBTOPIC: {subtopic}

Classify this pair:

1. CLASSIFICATION (choose one):
   - exact_duplicate: Identical or nearly identical in meaning, reference period, and response format
   - near_duplicate: Same core concept, minor wording differences that don't change meaning
   - reference_period_mismatch: Same concept but different time frames (e.g., "last week" vs "past 12 months")
   - response_format_mismatch: Same concept but different answer formats (e.g., yes/no vs dollar amount)
   - related_but_distinct: Same general topic but asking different specific things
   - not_comparable: Different concepts despite surface similarity

2. CONFIDENCE: high / medium / low

3. REFERENCE_PERIOD_A: (extract time reference from Question A, or "not specified")

4. REFERENCE_PERIOD_B: (extract time reference from Question B, or "not specified")

5. REASONING: 2-3 sentences explaining your classification. Be specific about differences.

6. CONSOLIDATION_POTENTIAL: If surveys were person-linked, could Question A be dropped? (yes / no / partial)

Respond in JSON format only:
{{"classification": "...", "confidence": "...", "reference_period_a": "...", "reference_period_b": "...", "reasoning": "...", "consolidation_potential": "..."}}
"""

def clean_json_response(content):
    """Extract JSON from response, handling markdown and extra text"""
    if content is None:
        return None, "Empty response"
    
    original_len = len(content)
    content = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', content)
    content = content.strip()
    
    # Handle markdown code blocks
    if '```' in content:
        parts = content.split('```')
        if len(parts) >= 2:
            content = parts[1]
            if content.startswith('json'):
                content = content[4:]
        content = content.strip()
    
    # Find JSON object boundaries
    start = content.find('{')
    end = content.rfind('}')
    
    if start == -1 or end == -1 or end <= start:
        return None, f"No valid JSON found (len={original_len})"
    
    json_str = content[start:end+1]
    return json_str, None


def call_claude(pair, survey_name):
    """Call Claude Haiku 4.5"""
    client = anthropic.Anthropic()
    prompt = PROMPT_TEMPLATE.format(
        survey_name=survey_name,
        survey_text=pair['survey_text'],
        acs_text=pair['acs_text'],
        subtopic=pair['subtopic']
    )
    
    for attempt in range(MAX_RETRIES):
        try:
            response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=4096,  # High ceiling - typical response is ~500 chars
                messages=[{"role": "user", "content": prompt}]
            )
            content = response.content[0].text
            stop_reason = response.stop_reason
            
            # Warn only if actually hit token limit
            if stop_reason == 'max_tokens':
                print(f"  WARNING: {pair['pair_id']} hit max_tokens limit!")
            
            cleaned, error = clean_json_response(content)
            if error:
                raise ValueError(f"{error}: {content[:100]}")
            
            result = json.loads(cleaned)
            result['pair_id'] = pair['pair_id']
            result['model'] = CLAUDE_MODEL
            return result
            
        except anthropic.RateLimitError:
            wait_time = 2 ** attempt + 5
            time.sleep(wait_time)
        except (anthropic.APIError, json.JSONDecodeError, ValueError) as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)
            else:
                return {
                    'pair_id': pair['pair_id'], 
                    'model': CLAUDE_MODEL, 
                    'classification': 'error', 
                    'error': str(e)[:200]
                }
        except Exception as e:
            return {
                'pair_id': pair['pair_id'], 
                'model': CLAUDE_MODEL, 
                'classification': 'error', 
                'error': str(e)[:200]
            }
    
    return {'pair_id': pair['pair_id'], 'model': CLAUDE_MODEL, 'classification': 'error', 'error': 'Max retries'}


def call_openai(pair, survey_name):
    """Call GPT-5-mini"""
    client = OpenAI()
    prompt = PROMPT_TEMPLATE.format(
        survey_name=survey_name,
        survey_text=pair['survey_text'],
        acs_text=pair['acs_text'],
        subtopic=pair['subtopic']
    )
    
    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=GPT_MODEL,
                messages=[
                    {"role": "system", "content": "You are a precise survey question comparison assistant. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ]
            )
            content = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason
            
            if finish_reason == 'length':
                print(f"  WARNING: {pair['pair_id']} hit length limit!")
            
            cleaned, error = clean_json_response(content)
            if error:
                raise ValueError(f"{error}: {content[:100]}")
            
            result = json.loads(cleaned)
            result['pair_id'] = pair['pair_id']
            result['model'] = GPT_MODEL
            return result
            
        except Exception as e:
            error_str = str(e).lower()
            if 'rate' in error_str or 'limit' in error_str:
                wait_time = 2 ** attempt + 5
                time.sleep(wait_time)
            else:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
                else:
                    return {
                        'pair_id': pair['pair_id'], 
                        'model': GPT_MODEL, 
                        'classification': 'error', 
                        'error': str(e)[:200]
                    }
    
    return {'pair_id': pair['pair_id'], 'model': GPT_MODEL, 'classification': 'error', 'error': 'Max retries'}


def run_model(pairs, model_fn, model_name, survey_name):
    """Run classification with progress tracking"""
    results = []
    errors = []
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(model_fn, pair, survey_name): pair for pair in pairs}
        for future in tqdm(as_completed(futures), total=len(futures), desc=model_name):
            result = future.result()
            results.append(result)
            if result.get('classification') == 'error':
                errors.append(result)
    
    return results, errors


def generate_candidate_pairs(survey_key, questions_map, master_df):
    """Generate candidate pairs for a survey against ACS"""
    config = SURVEY_CONFIG[survey_key]
    survey_col = config['column']
    
    # Get questions present in each survey
    survey_present = questions_map[survey_col].fillna('') != ''
    acs_present = questions_map[ACS_COLUMN].fillna('') != ''
    
    survey_questions = questions_map[survey_present].copy()
    acs_questions = questions_map[acs_present].copy()
    
    print(f"{config['name']} questions: {len(survey_questions)}")
    print(f"ACS questions: {len(acs_questions)}")
    
    # Merge with master to get subtopics
    master_subset = master_df[['question', 'final_topic', 'final_subtopic']].copy()
    master_subset.columns = ['Question', 'final_topic', 'final_subtopic']
    
    survey_with_subtopic = survey_questions.merge(master_subset, on='Question', how='left')
    acs_with_subtopic = acs_questions.merge(master_subset, on='Question', how='left')
    
    # Find overlapping subtopics
    survey_subtopics = set(survey_with_subtopic['final_subtopic'].dropna())
    acs_subtopics = set(acs_with_subtopic['final_subtopic'].dropna())
    overlap_subtopics = survey_subtopics & acs_subtopics
    
    print(f"Overlapping subtopics: {len(overlap_subtopics)}")
    
    # Generate pairs
    pairs = []
    pair_id = 0
    
    for subtopic in overlap_subtopics:
        survey_sub = survey_with_subtopic[survey_with_subtopic['final_subtopic'] == subtopic]
        acs_sub = acs_with_subtopic[acs_with_subtopic['final_subtopic'] == subtopic]
        
        for idx_survey, survey_row in survey_sub.iterrows():
            for idx_acs, acs_row in acs_sub.iterrows():
                pairs.append({
                    'pair_id': f'{survey_key.upper()}_{pair_id:04d}',
                    'survey_q_id': f'{survey_key.upper()}_{idx_survey}',
                    'survey_text': survey_row['Question'],
                    'acs_q_id': f'ACS_{idx_acs}',
                    'acs_text': acs_row['Question'],
                    'subtopic': subtopic
                })
                pair_id += 1
    
    pairs_df = pd.DataFrame(pairs)
    print(f"Total candidate pairs: {len(pairs_df)}")
    
    return pairs_df


def main():
    parser = argparse.ArgumentParser(description='Survey Question Matching Analysis')
    parser.add_argument('--survey', required=True, choices=list(SURVEY_CONFIG.keys()),
                        help='Survey to compare against ACS')
    parser.add_argument('--generate-only', action='store_true',
                        help='Only generate candidate pairs, skip LLM classification')
    parser.add_argument('--sample-size', type=int, default=None,
                        help='Sample size for pilot (default: all pairs up to 300)')
    parser.add_argument('--full', action='store_true',
                        help='Process all pairs (override 300 limit)')
    args = parser.parse_args()
    
    config = SURVEY_CONFIG[args.survey]
    output_dir = OUTPUT_BASE / config['output_dir']
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print(f"{config['name']}-ACS Question-Level Matching Analysis")
    print("=" * 60)
    print(f"Output directory: {output_dir}")
    print(f"Models: {CLAUDE_MODEL}, {GPT_MODEL}")
    print()
    
    # Load data
    print("Loading data...")
    
    # Try project files first, then repo data
    questions_map_path = Path('/mnt/project/PublicSurveyQuestionsMap.csv')
    if not questions_map_path.exists():
        questions_map_path = PROJECT_ROOT / 'data' / 'raw' / 'PublicSurveyQuestionsMap.csv'
    
    master_path = PROJECT_ROOT / 'output' / 'final' / 'master_dataset.csv'
    
    questions_map = pd.read_csv(questions_map_path)
    master_df = pd.read_csv(master_path)
    
    print(f"Questions map: {len(questions_map)} rows")
    print(f"Master dataset: {len(master_df)} rows")
    
    # Generate pairs
    print(f"\n=== Generating {config['name']}-ACS Pairs ===")
    pairs_df = generate_candidate_pairs(args.survey, questions_map, master_df)
    
    # Save all pairs
    pairs_df.to_csv(output_dir / f'{args.survey}_candidate_pairs_all.csv', index=False)
    print(f"Saved: {output_dir / f'{args.survey}_candidate_pairs_all.csv'}")
    
    # Show distribution
    print(f"\nPairs by subtopic:")
    print(pairs_df['subtopic'].value_counts().head(15).to_string())
    
    if args.generate_only:
        print("\n--generate-only flag set. Skipping LLM classification.")
        return
    
    # Sample if needed
    if args.full:
        sample_df = pairs_df
        print(f"\n--full flag: Processing all {len(sample_df)} pairs")
    elif args.sample_size:
        sample_df = pairs_df.sample(n=min(args.sample_size, len(pairs_df)), random_state=42)
        print(f"\nSampling {len(sample_df)} pairs (--sample-size {args.sample_size})")
    elif len(pairs_df) > 300:
        # Stratified sample by subtopic
        sample_dfs = []
        for subtopic in pairs_df['subtopic'].unique():
            st_pairs = pairs_df[pairs_df['subtopic'] == subtopic]
            n_sample = max(5, min(30, len(st_pairs)))  # At least 5, at most 30 per subtopic
            sample_dfs.append(st_pairs.sample(n=min(n_sample, len(st_pairs)), random_state=42))
        sample_df = pd.concat(sample_dfs, ignore_index=True)
        if len(sample_df) > 300:
            sample_df = sample_df.sample(n=300, random_state=42)
        print(f"\nLarge dataset. Stratified sample: {len(sample_df)} pairs")
    else:
        sample_df = pairs_df
        print(f"\nProcessing all {len(sample_df)} pairs")
    
    sample_df.to_csv(output_dir / f'{args.survey}_candidate_pairs_sample.csv', index=False)
    
    pairs = sample_df.to_dict('records')
    
    # Run Claude
    print(f"\n=== Running {CLAUDE_MODEL} ===")
    claude_results, claude_errors = run_model(pairs, call_claude, CLAUDE_MODEL, config['name'])
    claude_df = pd.DataFrame(claude_results)
    claude_df.to_csv(output_dir / f'{args.survey}_llm_results_claude.csv', index=False)
    print(f"Success: {len(claude_df) - len(claude_errors)}, Errors: {len(claude_errors)}")
    
    if claude_errors:
        print(f"  Errors: {[e.get('error', '')[:50] for e in claude_errors[:3]]}")
    
    # Run GPT
    print(f"\n=== Running {GPT_MODEL} ===")
    gpt_results, gpt_errors = run_model(pairs, call_openai, GPT_MODEL, config['name'])
    gpt_df = pd.DataFrame(gpt_results)
    gpt_df.to_csv(output_dir / f'{args.survey}_llm_results_gpt.csv', index=False)
    print(f"Success: {len(gpt_df) - len(gpt_errors)}, Errors: {len(gpt_errors)}")
    
    if gpt_errors:
        print(f"  Errors: {[e.get('error', '')[:50] for e in gpt_errors[:3]]}")
    
    # === RESULTS SUMMARY ===
    print("\n" + "=" * 60)
    print(f"{config['name']}-ACS CLASSIFICATION RESULTS")
    print("=" * 60)
    
    print(f"\n{CLAUDE_MODEL} classifications:")
    print(claude_df['classification'].value_counts().to_string())
    
    print(f"\n{GPT_MODEL} classifications:")
    print(gpt_df['classification'].value_counts().to_string())
    
    # Agreement
    claude_valid = claude_df[claude_df['classification'] != 'error'].set_index('pair_id')
    gpt_valid = gpt_df[gpt_df['classification'] != 'error'].set_index('pair_id')
    common_ids = set(claude_valid.index) & set(gpt_valid.index)
    
    if common_ids:
        agreements = sum(
            claude_valid.loc[pid, 'classification'] == gpt_valid.loc[pid, 'classification'] 
            for pid in common_ids
        )
        print(f"\nInter-model agreement: {agreements}/{len(common_ids)} ({100*agreements/len(common_ids):.1f}%)")
    
    # Consolidation potential
    print("\nConsolidation potential:")
    print(f"\n{CLAUDE_MODEL}:")
    if 'consolidation_potential' in claude_df.columns:
        print(claude_df['consolidation_potential'].value_counts().to_string())
    print(f"\n{GPT_MODEL}:")
    if 'consolidation_potential' in gpt_df.columns:
        print(gpt_df['consolidation_potential'].value_counts().to_string())
    
    # Merge and save comparison
    merged = sample_df.copy()
    for col in ['classification', 'confidence', 'reasoning', 'consolidation_potential', 
                'reference_period_a', 'reference_period_b']:
        if col in claude_valid.columns:
            merged[f'claude_{col}'] = merged['pair_id'].map(claude_valid[col].to_dict())
        if col in gpt_valid.columns:
            merged[f'gpt_{col}'] = merged['pair_id'].map(gpt_valid[col].to_dict())
    
    merged['models_agree'] = merged['claude_classification'] == merged['gpt_classification']
    merged.to_csv(output_dir / f'{args.survey}_comparison_merged.csv', index=False)
    
    # Summary by subtopic
    print("\n" + "=" * 60)
    print("CONSOLIDATION BY SUBTOPIC")
    print("=" * 60)
    
    for subtopic in sorted(merged['subtopic'].unique()):
        st_data = merged[merged['subtopic'] == subtopic]
        n_pairs = len(st_data)
        
        # Count classifications
        if 'claude_classification' in st_data.columns:
            exact = len(st_data[st_data['claude_classification'] == 'exact_duplicate'])
            near = len(st_data[st_data['claude_classification'] == 'near_duplicate'])
            ref_mismatch = len(st_data[st_data['claude_classification'] == 'reference_period_mismatch'])
            droppable = exact + near
            
            print(f"\n{subtopic}: {n_pairs} pairs")
            print(f"  Exact: {exact}, Near: {near}, Ref mismatch: {ref_mismatch}")
            print(f"  Droppable (Claude): {droppable} ({100*droppable/n_pairs:.0f}%)")
    
    print(f"\n\nResults saved to: {output_dir}")
    print(f"Timestamp: {datetime.now().isoformat()}")


if __name__ == "__main__":
    main()
