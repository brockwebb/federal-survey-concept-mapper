#!/usr/bin/env python3
"""
Question-level matching with CORRECT models:
- claude-haiku-4-5-20251001 (NOT claude-haiku-4.5)
- gpt-5-mini (NOT gpt-4o-mini)

Matches exponential backoff pattern from concept mapper pipeline.
"""

import os
import json
import re
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import anthropic
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()

INPUT_DIR = Path('output/question_matching')
OUTPUT_DIR = INPUT_DIR

# CORRECT MODEL STRINGS - DO NOT CHANGE
CLAUDE_MODEL = "claude-haiku-4-5-20251001"
GPT_MODEL = "gpt-5-mini"

MAX_RETRIES = 5
MAX_WORKERS = 4

PROMPT_TEMPLATE = """Compare these two federal survey questions for equivalence:

QUESTION A (FoodAPS): "{foodaps_text}"
QUESTION B (ACS): "{acs_text}"
SUBTOPIC: {subtopic}

Classify this pair:

1. CLASSIFICATION (choose one):
   - exact_duplicate: Identical or nearly identical in meaning, reference period, and response format
   - near_duplicate: Same core concept, minor wording differences that don't change meaning
   - reference_period_mismatch: Same concept but different time frames (e.g., "last month" vs "past 12 months")
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
    """Aggressive JSON cleaning - matches concept mapper pattern"""
    # Remove control characters
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
    
    # Find JSON object
    start = content.find('{')
    end = content.rfind('}')
    if start != -1 and end != -1:
        content = content[start:end+1]
    
    return content

def call_claude(pair):
    """Call Claude Haiku 4.5 with proper retry logic"""
    client = anthropic.Anthropic()
    prompt = PROMPT_TEMPLATE.format(**pair)
    
    for attempt in range(MAX_RETRIES):
        try:
            response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}]
            )
            content = response.content[0].text
            content = clean_json_response(content)
            result = json.loads(content)
            result['pair_id'] = pair['pair_id']
            result['model'] = CLAUDE_MODEL
            return result
            
        except anthropic.RateLimitError as e:
            wait_time = 2 ** attempt + 5  # Extra buffer for rate limits
            print(f"  Rate limit hit. Waiting {wait_time}s...")
            time.sleep(wait_time)
            
        except anthropic.APIError as e:
            wait_time = 2 ** attempt
            print(f"  API error: {str(e)[:80]}. Retry {attempt+1}/{MAX_RETRIES} in {wait_time}s...")
            if attempt < MAX_RETRIES - 1:
                time.sleep(wait_time)
            else:
                return {'pair_id': pair['pair_id'], 'model': CLAUDE_MODEL, 'classification': 'error', 'error': str(e)}
                
        except json.JSONDecodeError as e:
            wait_time = 2 ** attempt
            print(f"  JSON parse error. Retry {attempt+1}/{MAX_RETRIES} in {wait_time}s...")
            if attempt < MAX_RETRIES - 1:
                time.sleep(wait_time)
            else:
                return {'pair_id': pair['pair_id'], 'model': CLAUDE_MODEL, 'classification': 'error', 'error': f'JSON parse: {str(e)}'}
                
        except Exception as e:
            wait_time = 2 ** attempt
            print(f"  Error: {str(e)[:80]}. Retry {attempt+1}/{MAX_RETRIES} in {wait_time}s...")
            if attempt < MAX_RETRIES - 1:
                time.sleep(wait_time)
            else:
                return {'pair_id': pair['pair_id'], 'model': CLAUDE_MODEL, 'classification': 'error', 'error': str(e)}
    
    return {'pair_id': pair['pair_id'], 'model': CLAUDE_MODEL, 'classification': 'error', 'error': 'Max retries exceeded'}

def call_openai(pair):
    """Call GPT-5-mini with proper retry logic"""
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    prompt = PROMPT_TEMPLATE.format(**pair)
    
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
            content = clean_json_response(content)
            result = json.loads(content)
            result['pair_id'] = pair['pair_id']
            result['model'] = GPT_MODEL
            return result
            
        except Exception as e:
            error_str = str(e).lower()
            if 'rate' in error_str or 'limit' in error_str:
                wait_time = 2 ** attempt + 5
                print(f"  Rate limit hit. Waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                wait_time = 2 ** attempt
                print(f"  Error: {str(e)[:80]}. Retry {attempt+1}/{MAX_RETRIES} in {wait_time}s...")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(wait_time)
                else:
                    return {'pair_id': pair['pair_id'], 'model': GPT_MODEL, 'classification': 'error', 'error': str(e)}
    
    return {'pair_id': pair['pair_id'], 'model': GPT_MODEL, 'classification': 'error', 'error': 'Max retries exceeded'}

def run_model(pairs, model_fn, model_name):
    """Run classification for all pairs with given model"""
    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(model_fn, pair): pair for pair in pairs}
        for future in tqdm(as_completed(futures), total=len(futures), desc=model_name):
            results.append(future.result())
    return results

def main():
    print(f"Question Matching - Multi-Model Comparison")
    print(f"=" * 50)
    print(f"Models:")
    print(f"  Claude: {CLAUDE_MODEL}")
    print(f"  OpenAI: {GPT_MODEL}")
    print(f"Settings: max_retries={MAX_RETRIES}, max_workers={MAX_WORKERS}")
    print()
    
    # Load candidate pairs
    pairs_df = pd.read_csv(INPUT_DIR / 'candidate_pairs.csv')
    pairs = pairs_df.to_dict('records')
    
    print(f"Processing {len(pairs)} pairs with 2 models...")
    
    # Run Claude Haiku 4.5
    print(f"\n=== {CLAUDE_MODEL} ===")
    claude_results = run_model(pairs, call_claude, CLAUDE_MODEL)
    claude_df = pd.DataFrame(claude_results)
    claude_df.to_csv(OUTPUT_DIR / 'llm_results_claude_haiku45.csv', index=False)
    print(f"Saved: llm_results_claude_haiku45.csv")
    
    # Check for errors
    claude_errors = claude_df[claude_df['classification'] == 'error']
    print(f"  Success: {len(claude_df) - len(claude_errors)}, Errors: {len(claude_errors)}")
    
    # Run GPT-5-mini
    print(f"\n=== {GPT_MODEL} ===")
    gpt_results = run_model(pairs, call_openai, GPT_MODEL)
    gpt_df = pd.DataFrame(gpt_results)
    gpt_df.to_csv(OUTPUT_DIR / 'llm_results_gpt5mini.csv', index=False)
    print(f"Saved: llm_results_gpt5mini.csv")
    
    # Check for errors
    gpt_errors = gpt_df[gpt_df['classification'] == 'error']
    print(f"  Success: {len(gpt_df) - len(gpt_errors)}, Errors: {len(gpt_errors)}")
    
    # Merge results for comparison
    print("\n=== Merging Results ===")
    merged = pairs_df.copy()
    
    # Add Claude results (excluding errors)
    claude_valid = claude_df[claude_df['classification'] != 'error'].set_index('pair_id')
    for col in ['classification', 'confidence', 'reasoning', 'consolidation_potential', 
                'reference_period_a', 'reference_period_b']:
        if col in claude_valid.columns:
            merged[f'claude_{col}'] = merged['pair_id'].map(claude_valid[col])
    
    # Add GPT results (excluding errors)
    gpt_valid = gpt_df[gpt_df['classification'] != 'error'].set_index('pair_id')
    for col in ['classification', 'confidence', 'reasoning', 'consolidation_potential',
                'reference_period_a', 'reference_period_b']:
        if col in gpt_valid.columns:
            merged[f'gpt_{col}'] = merged['pair_id'].map(gpt_valid[col])
    
    # Calculate agreement
    merged['models_agree'] = merged['claude_classification'] == merged['gpt_classification']
    
    merged.to_csv(OUTPUT_DIR / 'llm_comparison_haiku45_vs_gpt5mini.csv', index=False)
    print(f"Saved: llm_comparison_haiku45_vs_gpt5mini.csv")
    
    # Summary stats
    print("\n" + "="*60)
    print("INTER-MODEL AGREEMENT")
    print("="*60)
    
    valid_comparisons = merged.dropna(subset=['claude_classification', 'gpt_classification'])
    agreement_rate = valid_comparisons['models_agree'].mean()
    print(f"Valid pairs compared: {len(valid_comparisons)}")
    print(f"Agreement rate: {agreement_rate:.1%}")
    
    print(f"\n{CLAUDE_MODEL} classification distribution:")
    print(merged['claude_classification'].value_counts().to_string())
    
    print(f"\n{GPT_MODEL} classification distribution:")
    print(merged['gpt_classification'].value_counts().to_string())
    
    # Consolidation potential
    print("\n" + "="*60)
    print("CONSOLIDATION POTENTIAL")
    print("="*60)
    print("\nClaude assessment:")
    print(merged['claude_consolidation_potential'].value_counts().to_string())
    print("\nGPT assessment:")
    print(merged['gpt_consolidation_potential'].value_counts().to_string())

if __name__ == "__main__":
    main()
