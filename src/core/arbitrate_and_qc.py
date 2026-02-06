#!/usr/bin/env python3
"""
Arbitrate disagreements using claude-sonnet-4-5, then QC validate with gpt-5-2.

Phase 1: Arbitration (234 disagreements)
- Send to claude-sonnet-4-5 with both model answers
- Track decision method
- Generate reconciled dataset

Phase 2: QC Validation (10% random sample)
- Send same questions to gpt-5-2
- Compare decisions
- Validate arbitration quality
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv
import anthropic
from openai import OpenAI
from tqdm import tqdm
import time

load_dotenv()

# Configuration
ANALYSIS_DIR = Path('../output/analysis')
OUTPUT_DIR = Path('../output/arbitration')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BATCH_SIZE = 10
QC_SAMPLE_RATE = 0.10  # 10% for QC validation

def load_arbitration_candidates() -> pd.DataFrame:
    """Load candidates that need arbitration."""
    return pd.read_csv(ANALYSIS_DIR / 'arbitration_candidates.csv')

def load_taxonomy() -> Dict[str, List[str]]:
    """Load Census taxonomy."""
    taxonomy_path = Path('../data/raw/census_survey_explorer_taxonomy.json')
    with open(taxonomy_path, 'r') as f:
        data = json.load(f)
    return data['taxonomy']

def create_arbitration_prompt(row: pd.Series, taxonomy: Dict[str, List[str]]) -> str:
    """Create prompt for arbitrator."""
    
    prompt = f"""You are arbitrating between two AI categorizations of a federal survey question using the Census Bureau taxonomy.

TAXONOMY:
{json.dumps(taxonomy, indent=2)}

QUESTION:
Survey: {row['survey']}
Question: {row['question']}

CATEGORIZATION 1 (gpt-5-mini):
- Primary: {row['primary_topic_openai']} / {row['primary_subtopic_openai']}
- Confidence: {row['confidence_openai']:.2f}

CATEGORIZATION 2 (claude-haiku-4-5):
- Primary: {row['primary_topic_claude']} / {row['primary_subtopic_claude']}
- Confidence: {row['confidence_claude']:.2f}

YOUR TASK:
Evaluate which categorization is more accurate, or if both capture important aspects.

DECIDE ONE OF:
1. "pick_gpt5mini" - gpt-5-mini is correct
2. "pick_haiku45" - claude-haiku-4-5 is correct
3. "combine" - Both are valid; question spans multiple topics
4. "new_concept" - Neither is correct; provide better categorization

Return JSON:
{{
  "decision": "pick_gpt5mini" | "pick_haiku45" | "combine" | "new_concept",
  "final_primary_topic": "Topic name",
  "final_primary_subtopic": "Subtopic name",
  "additional_concepts": [
    {{"topic": "...", "subtopic": "..."}}, 
    ...
  ],
  "reasoning": "Brief explanation (1-2 sentences)"
}}

If decision is "combine", put higher-confidence model's concept as primary and other in additional_concepts.
If decision is "new_concept", provide your own categorization in final_primary_topic/subtopic.
"""
    
    return prompt

def extract_json_robust(content: str) -> dict:
    """Robustly extract JSON from LLM response with multiple strategies."""
    
    # Strategy 1: Direct parse
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    
    # Strategy 2: Strip markdown
    if '```json' in content:
        content = content.split('```json')[1]
    if '```' in content:
        content = content.split('```')[0]
    content = content.strip()
    
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    
    # Strategy 3: Find first complete JSON object
    try:
        # Find opening brace
        start = content.find('{')
        if start == -1:
            raise ValueError("No JSON object found")
        
        # Count braces to find matching close
        brace_count = 0
        for i, char in enumerate(content[start:], start):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    # Found complete object
                    json_str = content[start:i+1]
                    return json.loads(json_str)
        
        raise ValueError("No complete JSON object found")
    except (ValueError, json.JSONDecodeError) as e:
        raise ValueError(f"Could not extract valid JSON: {e}")

def arbitrate_batch(batch: pd.DataFrame, taxonomy: Dict[str, List[str]], 
                   max_retries: int = 5) -> List[Dict[str, Any]]:
    """Send batch to claude-sonnet-4-5 for arbitration."""
    
    client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    results = []
    
    for idx, row in batch.iterrows():
        prompt = create_arbitration_prompt(row, taxonomy)
        
        for attempt in range(max_retries):
            try:
                response = client.messages.create(
                    model="claude-sonnet-4-5",
                    max_tokens=2048,
                    temperature=0,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                content = response.content[0].text
                
                # Use robust JSON extraction
                result = extract_json_robust(content)
                result['id'] = row['id']
                result['original_openai_topic'] = row['primary_topic_openai']
                result['original_openai_subtopic'] = row['primary_subtopic_openai']
                result['original_claude_topic'] = row['primary_topic_claude']
                result['original_claude_subtopic'] = row['primary_subtopic_claude']
                
                results.append(result)
                break
                
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"  Error on question {row['id']}: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"  Failed question {row['id']} after {max_retries} attempts")
                    results.append({
                        'id': row['id'],
                        'decision': 'failed',
                        'error': str(e)
                    })
    
    return results

def qc_validate_batch(batch: pd.DataFrame, arbitration_results: pd.DataFrame,
                     taxonomy: Dict[str, List[str]], max_retries: int = 5) -> List[Dict[str, Any]]:
    """Send batch to gpt-5-2 for QC validation."""
    
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    results = []
    
    # Merge to get arbitration decisions
    batch_with_arb = batch.merge(
        arbitration_results[['id', 'decision', 'final_primary_topic', 'final_primary_subtopic', 'reasoning']], 
        on='id'
    )
    
    for idx, row in batch_with_arb.iterrows():
        # Create QC prompt
        prompt = f"""You are validating an arbitration decision for a federal survey question categorization.

TAXONOMY:
{json.dumps(taxonomy, indent=2)}

QUESTION:
{row['question']}

ORIGINAL CATEGORIZATIONS:
1. gpt-5-mini: {row['primary_topic_openai']} / {row['primary_subtopic_openai']} (confidence: {row['confidence_openai']:.2f})
2. claude-haiku-4-5: {row['primary_topic_claude']} / {row['primary_subtopic_claude']} (confidence: {row['confidence_claude']:.2f})

ARBITRATOR DECISION (claude-sonnet-4-5):
- Decision: {row['decision']}
- Final: {row['final_primary_topic']} / {row['final_primary_subtopic']}
- Reasoning: {row['reasoning']}

YOUR TASK:
Evaluate if the arbitrator's decision is correct. What would you have chosen?

Return JSON:
{{
  "agrees_with_arbitrator": true | false,
  "your_choice": "pick_gpt5mini" | "pick_haiku45" | "combine" | "new_concept",
  "your_topic": "Your topic choice",
  "your_subtopic": "Your subtopic choice",
  "reasoning": "Why you agree/disagree (1-2 sentences)"
}}
"""
        
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model="gpt-5.2",
                    messages=[
                        {"role": "system", "content": "You are a quality control validator for data categorization."},
                        {"role": "user", "content": prompt}
                    ]
                )
                
                content = response.choices[0].message.content
                
                # Use robust JSON extraction
                result = extract_json_robust(content)
                result['id'] = row['id']
                result['arbitrator_decision'] = row['decision']
                result['arbitrator_topic'] = row['final_primary_topic']
                result['arbitrator_subtopic'] = row['final_primary_subtopic']
                
                results.append(result)
                break
                
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"  QC Error on question {row['id']}: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"  QC Failed question {row['id']} after {max_retries} attempts")
                    results.append({
                        'id': row['id'],
                        'qc_failed': True,
                        'error': str(e)
                    })
    
    return results

def main():
    print("="*70)
    print("ARBITRATION + QC VALIDATION")
    print("="*70)
    
    # Load data
    print("\n1. Loading data...")
    candidates = load_arbitration_candidates()
    taxonomy = load_taxonomy()
    print(f"   Candidates for arbitration: {len(candidates)}")
    
    # === PHASE 1: ARBITRATION ===
    print("\n" + "="*70)
    print("PHASE 1: ARBITRATION (claude-sonnet-4-5)")
    print("="*70)
    
    arbitration_results = []
    
    print(f"\nProcessing {len(candidates)} questions in batches of {BATCH_SIZE}...")
    for i in tqdm(range(0, len(candidates), BATCH_SIZE), desc="Arbitrating"):
        batch = candidates.iloc[i:i+BATCH_SIZE]
        results = arbitrate_batch(batch, taxonomy)
        arbitration_results.extend(results)
        
        # Save incremental results
        pd.DataFrame(arbitration_results).to_csv(
            OUTPUT_DIR / 'arbitration_results.csv', 
            index=False
        )
    
    arb_df = pd.DataFrame(arbitration_results)
    print(f"\nArbitration complete! {len(arb_df)} decisions made.")
    
    # Decision breakdown
    print("\nDecision breakdown:")
    decision_counts = arb_df['decision'].value_counts()
    for decision, count in decision_counts.items():
        print(f"  {decision}: {count} ({count/len(arb_df)*100:.1f}%)")
    
    # === PHASE 2: QC VALIDATION ===
    print("\n" + "="*70)
    print("PHASE 2: QC VALIDATION (gpt-5-2)")
    print("="*70)
    
    # Random sample for QC
    qc_sample_size = int(len(candidates) * QC_SAMPLE_RATE)
    qc_sample = candidates.sample(n=qc_sample_size, random_state=42)
    print(f"\nQC sample: {len(qc_sample)} questions ({QC_SAMPLE_RATE*100:.0f}%)")
    
    qc_results = []
    
    print(f"\nProcessing QC validation...")
    for i in tqdm(range(0, len(qc_sample), BATCH_SIZE), desc="QC Validating"):
        batch = qc_sample.iloc[i:i+BATCH_SIZE]
        results = qc_validate_batch(batch, arb_df, taxonomy)
        qc_results.extend(results)
        
        # Save incremental results
        pd.DataFrame(qc_results).to_csv(
            OUTPUT_DIR / 'qc_validation_results.csv',
            index=False
        )
    
    qc_df = pd.DataFrame(qc_results)
    print(f"\nQC validation complete! {len(qc_df)} questions validated.")
    
    # QC analysis
    print("\n" + "="*70)
    print("QC VALIDATION RESULTS")
    print("="*70)
    
    agreement_rate = qc_df['agrees_with_arbitrator'].sum() / len(qc_df) * 100
    print(f"\nAgreement with arbitrator: {agreement_rate:.1f}%")
    
    print("\ngpt-5-2 choices (when disagreeing):")
    disagreements = qc_df[~qc_df['agrees_with_arbitrator']]
    if len(disagreements) > 0:
        choice_counts = disagreements['your_choice'].value_counts()
        for choice, count in choice_counts.items():
            print(f"  {choice}: {count}")
    
    print("\n" + "="*70)
    print("COMPLETE!")
    print("="*70)
    print(f"\nResults saved to: {OUTPUT_DIR}")
    print(f"  - arbitration_results.csv ({len(arb_df)} decisions)")
    print(f"  - qc_validation_results.csv ({len(qc_df)} validations)")
    print(f"\nKey metrics:")
    print(f"  - Arbitration decisions made: {len(arb_df)}")
    print(f"  - QC agreement rate: {agreement_rate:.1f}%")
    print(f"  - Cost estimate: ${(len(candidates)/10)*0.05 + (len(qc_sample)/10)*0.15:.2f}")

if __name__ == '__main__':
    import os
    main()
