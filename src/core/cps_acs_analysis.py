#!/usr/bin/env python3
"""
Generate CPS-ACS candidate pairs and run multi-model comparison.

Run from repo root:
    python src/cps_acs_analysis.py
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

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
OUTPUT_DIR = PROJECT_ROOT / 'output' / 'question_matching' / 'cps'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# CORRECT MODEL STRINGS - DO NOT CHANGE
CLAUDE_MODEL = "claude-haiku-4-5-20251001"
GPT_MODEL = "gpt-5-mini"

MAX_RETRIES = 5
MAX_WORKERS = 4

# CPS top subtopics from our overlap analysis
CPS_SUBTOPICS = [
    "Employment Status",
    "Earnings",
    "Hours/Week, Weeks/Year",
    "Occupation",
    "Industry",
    "School Enrollment",
    "Educational Attainment",
    "Health Insurance",
    "Age",
    "Sex",
    "Race",
    "Marital",
    "Relationship",
    "Household"
]

PROMPT_TEMPLATE = """Compare these two federal survey questions for equivalence:

QUESTION A (CPS): "{survey_a_text}"
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
    """Aggressive JSON cleaning"""
    content = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', content)
    content = content.strip()
    
    if '```' in content:
        parts = content.split('```')
        if len(parts) >= 2:
            content = parts[1]
            if content.startswith('json'):
                content = content[4:]
        content = content.strip()
    
    start = content.find('{')
    end = content.rfind('}')
    if start != -1 and end != -1:
        content = content[start:end+1]
    
    return content

def generate_cps_pairs():
    """Generate candidate pairs from CPS and ACS questions in overlapping subtopics"""
    
    # Load the categorized questions from our pipeline
    questions_path = DATA_DIR / 'survey_questions_categorized_merged.csv'
    if not questions_path.exists():
        print(f"ERROR: {questions_path} not found")
        return None
    
    df = pd.read_csv(questions_path)
    print(f"Loaded {len(df)} categorized questions")
    
    # Get CPS and ACS questions
    cps_col = 'Current Population Survey (CPS)'
    acs_col = 'American Community Survey (ACS)'
    
    # Check columns exist
    if cps_col not in df.columns or acs_col not in df.columns:
        print(f"ERROR: Required columns not found")
        print(f"Available columns: {list(df.columns)[:10]}...")
        return None
    
    # Get questions present in each survey
    cps_questions = df[df[cps_col].notna() & (df[cps_col] != '')].copy()
    acs_questions = df[df[acs_col].notna() & (df[acs_col] != '')].copy()
    
    print(f"CPS questions: {len(cps_questions)}")
    print(f"ACS questions: {len(acs_questions)}")
    
    # Find overlapping subtopics
    cps_subtopics = set(cps_questions['subtopic'].dropna().unique())
    acs_subtopics = set(acs_questions['subtopic'].dropna().unique())
    overlap_subtopics = cps_subtopics & acs_subtopics
    
    print(f"Overlapping subtopics: {len(overlap_subtopics)}")
    
    # Generate pairs for questions in same subtopic
    pairs = []
    pair_id = 0
    
    for subtopic in overlap_subtopics:
        cps_sub = cps_questions[cps_questions['subtopic'] == subtopic]
        acs_sub = acs_questions[acs_questions['subtopic'] == subtopic]
        
        for _, cps_row in cps_sub.iterrows():
            for _, acs_row in acs_sub.iterrows():
                pairs.append({
                    'pair_id': f'CPS_{pair_id:04d}',
                    'cps_q_id': f"CPS_{cps_row.name}",
                    'survey_a_text': cps_row['Question'],
                    'acs_q_id': f"ACS_{acs_row.name}",
                    'acs_text': acs_row['Question'],
                    'subtopic': subtopic
                })
                pair_id += 1
    
    pairs_df = pd.DataFrame(pairs)
    print(f"Generated {len(pairs_df)} candidate pairs")
    
    # Save pairs
    pairs_df.to_csv(OUTPUT_DIR / 'cps_candidate_pairs.csv', index=False)
    print(f"Saved: {OUTPUT_DIR / 'cps_candidate_pairs.csv'}")
    
    # Show subtopic distribution
    print("\nPairs by subtopic:")
    print(pairs_df['subtopic'].value_counts().head(15).to_string())
    
    return pairs_df

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
            
        except anthropic.RateLimitError:
            wait_time = 2 ** attempt + 5
            print(f"  Rate limit. Waiting {wait_time}s...")
            time.sleep(wait_time)
        except (anthropic.APIError, json.JSONDecodeError) as e:
            wait_time = 2 ** attempt
            if attempt < MAX_RETRIES - 1:
                time.sleep(wait_time)
            else:
                return {'pair_id': pair['pair_id'], 'model': CLAUDE_MODEL, 'classification': 'error', 'error': str(e)[:100]}
        except Exception as e:
            return {'pair_id': pair['pair_id'], 'model': CLAUDE_MODEL, 'classification': 'error', 'error': str(e)[:100]}
    
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
                time.sleep(wait_time)
            else:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
                else:
                    return {'pair_id': pair['pair_id'], 'model': GPT_MODEL, 'classification': 'error', 'error': str(e)[:100]}
    
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
    print("=" * 60)
    print("CPS-ACS Question-Level Matching Analysis")
    print("=" * 60)
    print(f"Models: {CLAUDE_MODEL}, {GPT_MODEL}")
    print()
    
    # Step 1: Generate candidate pairs
    print("=== Step 1: Generate Candidate Pairs ===")
    pairs_df = generate_cps_pairs()
    
    if pairs_df is None or len(pairs_df) == 0:
        print("ERROR: No pairs generated")
        return
    
    # Check if pairs already processed
    claude_path = OUTPUT_DIR / 'llm_results_claude_haiku45.csv'
    gpt_path = OUTPUT_DIR / 'llm_results_gpt5mini.csv'
    
    if claude_path.exists() and gpt_path.exists():
        print("\nResults files already exist. Loading existing results...")
        claude_df = pd.read_csv(claude_path)
        gpt_df = pd.read_csv(gpt_path)
    else:
        # Step 2: Run LLM classification
        pairs = pairs_df.to_dict('records')
        
        # Sample for cost control - run on subset first
        if len(pairs) > 300:
            print(f"\nLarge dataset ({len(pairs)} pairs). Running on first 300 pairs.")
            print("Edit script to process all pairs if needed.")
            pairs = pairs[:300]
        
        print(f"\n=== Step 2: LLM Classification ({len(pairs)} pairs) ===")
        
        # Claude
        print(f"\nRunning {CLAUDE_MODEL}...")
        claude_results = run_model(pairs, call_claude, CLAUDE_MODEL)
        claude_df = pd.DataFrame(claude_results)
        claude_df.to_csv(claude_path, index=False)
        print(f"Saved: {claude_path}")
        
        # GPT
        print(f"\nRunning {GPT_MODEL}...")
        gpt_results = run_model(pairs, call_openai, GPT_MODEL)
        gpt_df = pd.DataFrame(gpt_results)
        gpt_df.to_csv(gpt_path, index=False)
        print(f"Saved: {gpt_path}")
    
    # Step 3: Analysis
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    
    # Error rates
    claude_errors = len(claude_df[claude_df['classification'] == 'error'])
    gpt_errors = len(gpt_df[gpt_df['classification'] == 'error'])
    print(f"\nError rates:")
    print(f"  Claude: {claude_errors}/{len(claude_df)} ({100*claude_errors/len(claude_df):.1f}%)")
    print(f"  GPT: {gpt_errors}/{len(gpt_df)} ({100*gpt_errors/len(gpt_df):.1f}%)")
    
    # Classification distributions
    print(f"\n{CLAUDE_MODEL} classifications:")
    print(claude_df['classification'].value_counts().to_string())
    
    print(f"\n{GPT_MODEL} classifications:")
    print(gpt_df['classification'].value_counts().to_string())
    
    # Merge for agreement calculation
    claude_valid = claude_df[claude_df['classification'] != 'error'].set_index('pair_id')
    gpt_valid = gpt_df[gpt_df['classification'] != 'error'].set_index('pair_id')
    
    common_ids = set(claude_valid.index) & set(gpt_valid.index)
    if common_ids:
        agreements = sum(claude_valid.loc[pid, 'classification'] == gpt_valid.loc[pid, 'classification'] for pid in common_ids)
        agreement_rate = agreements / len(common_ids)
        print(f"\nInter-model agreement: {agreement_rate:.1%} ({agreements}/{len(common_ids)})")
    
    # Consolidation potential
    print(f"\nConsolidation potential:")
    print(f"\nClaude:")
    if 'consolidation_potential' in claude_df.columns:
        print(claude_df['consolidation_potential'].value_counts().to_string())
    print(f"\nGPT:")
    if 'consolidation_potential' in gpt_df.columns:
        print(gpt_df['consolidation_potential'].value_counts().to_string())
    
    # Save merged comparison
    merged_path = OUTPUT_DIR / 'cps_comparison_merged.csv'
    merged = pairs_df.head(len(claude_df)).copy()
    for col in ['classification', 'confidence', 'reasoning', 'consolidation_potential']:
        if col in claude_valid.columns:
            merged[f'claude_{col}'] = merged['pair_id'].map(claude_valid[col].to_dict())
        if col in gpt_valid.columns:
            merged[f'gpt_{col}'] = merged['pair_id'].map(gpt_valid[col].to_dict())
    merged.to_csv(merged_path, index=False)
    print(f"\nSaved merged comparison: {merged_path}")

if __name__ == "__main__":
    main()
