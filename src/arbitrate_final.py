#!/usr/bin/env python3
"""
Final arbitration with dual-modal support and confidence tiers.

Strategy:
- Arbitrate all disagreements where min_confidence < 0.90
- Auto-mark high-confidence disagreements (>=0.90) as dual-modal
- Arbitrator can choose: pick model A, pick model B, dual-modal, or new concept
- Dual-modal is rare and requires justification
- Track confidence tiers for all decisions

Confidence tiers:
- Very Low: <0.60
- Low: 0.60-0.75
- Medium: 0.75-0.90
- High: 0.90-0.95
- Very High: >=0.95
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
RESULTS_DIR = Path('../output/results')
COMPARISON_DIR = Path('../output/comparison')
OUTPUT_DIR = Path('../output/arbitration_final')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CONFIDENCE_THRESHOLD = 0.90
MAX_ROUNDS = 3
BATCH_SIZE = 5
MAX_WORKERS = 3  # Parallel arbitration workers

def load_taxonomy() -> Dict[str, List[str]]:
    """Load Census taxonomy."""
    taxonomy_path = Path('../data/raw/census_survey_explorer_taxonomy.json')
    with open(taxonomy_path, 'r') as f:
        data = json.load(f)
    return data['taxonomy']

def load_questions() -> pd.DataFrame:
    """Load original questions."""
    df = pd.read_csv('../data/raw/PublicSurveyQuestionsMap.csv')
    
    questions = []
    for idx, row in df.iterrows():
        question = row['Question']
        surveys = [col for col in df.columns if col != 'Question' and pd.notna(row[col])]
        
        questions.append({
            'id': idx,
            'question': question,
            'primary_survey': surveys[0] if surveys else 'Unknown'
        })
    
    return pd.DataFrame(questions)

def load_disagreements() -> pd.DataFrame:
    """Load comparison results and identify disagreements."""
    comp_df = pd.read_csv(COMPARISON_DIR / 'full_comparison.csv')
    
    # Load original questions to get question text
    questions_df = load_questions()
    comp_df = comp_df.merge(questions_df[['id', 'question', 'primary_survey']], on='id', how='left')
    
    # Find disagreements (topic OR subtopic)
    disagreements = comp_df[
        (comp_df['primary_topic_openai'] != comp_df['primary_topic_claude']) |
        (comp_df['primary_subtopic_openai'] != comp_df['primary_subtopic_claude'])
    ].copy()
    
    # Calculate min confidence and tier
    disagreements['min_confidence'] = disagreements[
        ['confidence_openai', 'confidence_claude']
    ].min(axis=1)
    
    def assign_tier(conf):
        if conf < 0.60:
            return 'very_low'
        elif conf < 0.75:
            return 'low'
        elif conf < 0.90:
            return 'medium'
        elif conf < 0.95:
            return 'high'
        else:
            return 'very_high'
    
    disagreements['confidence_tier'] = disagreements['min_confidence'].apply(assign_tier)
    
    return disagreements

def extract_json_robust(content: str) -> dict:
    """Robustly extract JSON from LLM response."""
    
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
        start = content.find('{')
        if start == -1:
            raise ValueError("No JSON object found")
        
        brace_count = 0
        for i, char in enumerate(content[start:], start):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    json_str = content[start:i+1]
                    return json.loads(json_str)
        
        raise ValueError("No complete JSON object found")
    except (ValueError, json.JSONDecodeError) as e:
        raise ValueError(f"Could not extract valid JSON: {e}")

def create_arbitration_prompt(row: pd.Series, taxonomy: Dict[str, List[str]]) -> str:
    """Create arbitration prompt with dual-modal support."""
    
    prompt = f"""You are arbitrating between two AI categorizations using the official Census Bureau taxonomy.

IMPORTANT RULES:
1. Most questions have ONE primary topic - this is the default
2. Only mark as "dual_modal" if the question GENUINELY spans two topics equally
3. Dual-modal should be RARE (<10% of cases) - justify it thoroughly
4. All topics and subtopics MUST exist in the provided taxonomy

CENSUS TAXONOMY:
{json.dumps(taxonomy, indent=2)}

QUESTION:
Survey: {row['primary_survey']}
Question: {row['question']}

MODEL CATEGORIZATIONS:
gpt-5-mini:
- Topic: {row['primary_topic_openai']}
- Subtopic: {row['primary_subtopic_openai']}
- Confidence: {row['confidence_openai']:.2f}

claude-haiku-4-5:
- Topic: {row['primary_topic_claude']}
- Subtopic: {row['primary_subtopic_claude']}
- Confidence: {row['confidence_claude']:.2f}

CONFIDENCE CONTEXT:
- Min confidence: {row['min_confidence']:.2f}
- Tier: {row['confidence_tier']}

YOUR DECISION OPTIONS:
1. "pick_gpt5mini" - gpt-5-mini is correct (single primary)
2. "pick_haiku45" - claude-haiku-4-5 is correct (single primary)
3. "dual_modal" - Question genuinely spans TWO topics (requires strong justification)
4. "new_concept" - Both wrong; provide correct concept (single primary)

DUAL-MODAL CRITERIA (must meet ALL):
- Question asks about two distinct topics simultaneously
- Cannot be accurately answered with single primary
- Not just that secondary concepts exist (most questions have those)
- Example: "What is your household income from employment benefits?" = Economic + Social

Return JSON:
{{
  "decision": "pick_gpt5mini" | "pick_haiku45" | "dual_modal" | "new_concept",
  
  "primary_topic": "Topic from taxonomy",
  "primary_subtopic": "Subtopic from taxonomy",
  "primary_confidence": 0.0-1.0,
  
  "secondary_primary_topic": "Topic from taxonomy" | null,
  "secondary_primary_subtopic": "Subtopic from taxonomy" | null,
  "secondary_primary_confidence": 0.0-1.0 | null,
  
  "all_relevant_subtopics": [
    "Topic.Subtopic",
    ...
  ],
  
  "reasoning": "Explanation (2-3 sentences). If dual_modal, justify why single primary is insufficient.",
  "is_dual_modal": true | false
}}

CRITICAL: 
- Single primary is default
- Dual-modal requires explicit justification in reasoning
- All concepts must be from taxonomy
- all_relevant_subtopics should include concepts from both models + any you identify
"""
    
    return prompt

def call_sonnet(prompt: str, max_retries: int = 5) -> Dict[str, Any]:
    """Call claude-sonnet-4-5 with retry logic."""
    client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    
    for attempt in range(max_retries):
        try:
            response = client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=2048,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            return extract_json_robust(content)
            
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                time.sleep(wait_time)
            else:
                raise e

def arbitrate_question(row: pd.Series, taxonomy: Dict[str, List[str]]) -> Dict[str, Any]:
    """Arbitrate a single question."""
    
    result = {
        'id': row['id'],
        'question': row['question'],
        'original_gpt5mini': f"{row['primary_topic_openai']}.{row['primary_subtopic_openai']}",
        'original_haiku45': f"{row['primary_topic_claude']}.{row['primary_subtopic_claude']}",
        'original_gpt_confidence': row['confidence_openai'],
        'original_claude_confidence': row['confidence_claude'],
        'min_confidence': row['min_confidence'],
        'confidence_tier': row['confidence_tier']
    }
    
    try:
        prompt = create_arbitration_prompt(row, taxonomy)
        arb_result = call_sonnet(prompt)
        
        result['decision'] = arb_result['decision']
        result['primary_topic'] = arb_result['primary_topic']
        result['primary_subtopic'] = arb_result['primary_subtopic']
        result['primary_confidence'] = arb_result['primary_confidence']
        result['secondary_primary_topic'] = arb_result.get('secondary_primary_topic')
        result['secondary_primary_subtopic'] = arb_result.get('secondary_primary_subtopic')
        result['secondary_primary_confidence'] = arb_result.get('secondary_primary_confidence')
        result['all_relevant_subtopics'] = json.dumps(arb_result.get('all_relevant_subtopics', []))
        result['reasoning'] = arb_result['reasoning']
        result['is_dual_modal'] = arb_result.get('is_dual_modal', False)
        result['status'] = 'arbitrated'
        
    except Exception as e:
        result['status'] = 'failed'
        result['error'] = str(e)
        result['decision'] = 'failed'
    
    return result

def main():
    print("="*70)
    print("FINAL ARBITRATION WITH DUAL-MODAL SUPPORT")
    print("="*70)
    
    # Load data
    print("\n1. Loading data...")
    taxonomy = load_taxonomy()
    questions_df = load_questions()
    disagreements = load_disagreements()
    
    print(f"   Total disagreements: {len(disagreements):,}")
    
    # Split by confidence threshold
    needs_arbitration = disagreements[disagreements['min_confidence'] < CONFIDENCE_THRESHOLD].copy()
    auto_dual_modal = disagreements[disagreements['min_confidence'] >= CONFIDENCE_THRESHOLD].copy()
    
    print(f"\n2. Categorization plan:")
    print(f"   Needs arbitration (min_conf < {CONFIDENCE_THRESHOLD}): {len(needs_arbitration):,}")
    print(f"   Auto dual-modal (min_conf >= {CONFIDENCE_THRESHOLD}): {len(auto_dual_modal):,}")
    
    # Show confidence tier breakdown for arbitration
    print(f"\n   Arbitration breakdown by tier:")
    tier_counts = needs_arbitration['confidence_tier'].value_counts().sort_index()
    for tier, count in tier_counts.items():
        print(f"     {tier}: {count}")
    
    # Process arbitration cases
    print(f"\n3. Arbitrating {len(needs_arbitration)} questions...")
    
    results = []
    
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import threading
    
    # Thread-safe result storage
    results_lock = threading.Lock()
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_row = {
            executor.submit(arbitrate_question, row, taxonomy): idx
            for idx, row in needs_arbitration.iterrows()
        }
        
        with tqdm(total=len(needs_arbitration), desc="  Arbitrating") as pbar:
            for future in as_completed(future_to_row):
                result = future.result()
                
                with results_lock:
                    results.append(result)
                    
                    # Save incrementally every 10 results
                    if len(results) % 10 == 0:
                        pd.DataFrame(results).to_csv(OUTPUT_DIR / 'arbitration_results.csv', index=False)
                
                pbar.update(1)
                time.sleep(0.2)  # Small delay to avoid rate limits
    
    arb_df = pd.DataFrame(results)
    arb_df.to_csv(OUTPUT_DIR / 'arbitration_results.csv', index=False)
    print(f"   ✓ Saved arbitration results")
    
    # Process auto dual-modal cases
    print(f"\n4. Processing {len(auto_dual_modal)} auto dual-modal cases...")
    
    auto_results = []
    for idx, row in auto_dual_modal.iterrows():
        # Pick higher confidence as primary, other as secondary
        if row['confidence_openai'] >= row['confidence_claude']:
            primary_topic = row['primary_topic_openai']
            primary_subtopic = row['primary_subtopic_openai']
            primary_conf = row['confidence_openai']
            secondary_topic = row['primary_topic_claude']
            secondary_subtopic = row['primary_subtopic_claude']
            secondary_conf = row['confidence_claude']
        else:
            primary_topic = row['primary_topic_claude']
            primary_subtopic = row['primary_subtopic_claude']
            primary_conf = row['confidence_claude']
            secondary_topic = row['primary_topic_openai']
            secondary_subtopic = row['primary_subtopic_openai']
            secondary_conf = row['confidence_openai']
        
        auto_results.append({
            'id': row['id'],
            'question': row['question'],
            'original_gpt5mini': f"{row['primary_topic_openai']}.{row['primary_subtopic_openai']}",
            'original_haiku45': f"{row['primary_topic_claude']}.{row['primary_subtopic_claude']}",
            'original_gpt_confidence': row['confidence_openai'],
            'original_claude_confidence': row['confidence_claude'],
            'min_confidence': row['min_confidence'],
            'confidence_tier': row['confidence_tier'],
            'decision': 'auto_dual_modal',
            'primary_topic': primary_topic,
            'primary_subtopic': primary_subtopic,
            'primary_confidence': primary_conf,
            'secondary_primary_topic': secondary_topic,
            'secondary_primary_subtopic': secondary_subtopic,
            'secondary_primary_confidence': secondary_conf,
            'all_relevant_subtopics': json.dumps([
                f"{primary_topic}.{primary_subtopic}",
                f"{secondary_topic}.{secondary_subtopic}"
            ]),
            'reasoning': f"Both models highly confident (min={row['min_confidence']:.2f}) but chose different topics. Auto-marked as dual-modal.",
            'is_dual_modal': True,
            'status': 'auto_dual_modal'
        })
    
    auto_df = pd.DataFrame(auto_results)
    auto_df.to_csv(OUTPUT_DIR / 'auto_dual_modal_results.csv', index=False)
    print(f"   ✓ Saved auto dual-modal results")
    
    # Combined results
    all_results = pd.concat([arb_df, auto_df], ignore_index=True)
    all_results.to_csv(OUTPUT_DIR / 'all_disagreement_resolutions.csv', index=False)
    
    # Summary statistics
    print("\n" + "="*70)
    print("SUMMARY STATISTICS")
    print("="*70)
    
    print(f"\nTotal disagreements processed: {len(all_results):,}")
    
    print(f"\nDecision breakdown:")
    decision_counts = all_results['decision'].value_counts()
    for decision, count in decision_counts.items():
        pct = count / len(all_results) * 100
        print(f"  {decision}: {count} ({pct:.1f}%)")
    
    print(f"\nDual-modal questions:")
    dual_modal_count = all_results['is_dual_modal'].sum()
    print(f"  Total: {dual_modal_count} ({dual_modal_count/len(all_results)*100:.1f}%)")
    print(f"  Arbitrated: {arb_df['is_dual_modal'].sum()}")
    print(f"  Auto-assigned: {len(auto_df)}")
    
    print(f"\nFailed arbitrations:")
    failed = all_results[all_results['status'] == 'failed']
    print(f"  Total: {len(failed)}")
    
    print("\n" + "="*70)
    print("COMPLETE!")
    print("="*70)
    print(f"\nOutputs saved to: {OUTPUT_DIR}")
    print(f"  - arbitration_results.csv ({len(arb_df)} questions)")
    print(f"  - auto_dual_modal_results.csv ({len(auto_df)} questions)")
    print(f"  - all_disagreement_resolutions.csv ({len(all_results)} questions)")

if __name__ == '__main__':
    import os
    main()
