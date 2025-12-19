#!/usr/bin/env python3
"""
Agentic arbitration with feedback loop.

Round 1: Sonnet 4.5 makes initial decision
Round 2: gpt-5.2 reviews + provides feedback
Round 3: Sonnet 4.5 sees feedback, makes final decision

If still no agreement after 3 rounds: Flag for human review.
Full conversation context preserved throughout.
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv
import anthropic
from openai import OpenAI
from tqdm import tqdm
import time

load_dotenv()

# Configuration
ANALYSIS_DIR = Path('../output/analysis')
OUTPUT_DIR = Path('../output/arbitration_agentic')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MAX_ROUNDS = 3
BATCH_SIZE = 5  # Smaller batches since we're doing multiple rounds

def load_arbitration_candidates() -> pd.DataFrame:
    """Load candidates that need arbitration."""
    return pd.read_csv(ANALYSIS_DIR / 'arbitration_candidates.csv')

def load_taxonomy() -> Dict[str, List[str]]:
    """Load Census taxonomy."""
    taxonomy_path = Path('../data/raw/census_survey_explorer_taxonomy.json')
    with open(taxonomy_path, 'r') as f:
        data = json.load(f)
    return data['taxonomy']

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

def create_round1_prompt(row: pd.Series, taxonomy: Dict[str, List[str]]) -> str:
    """Round 1: Sonnet's initial arbitration."""
    
    prompt = f"""You are arbitrating between two AI categorizations using the official Census Bureau taxonomy.

IMPORTANT: You MUST choose concepts that exist in the provided taxonomy. Do not invent new subtopics.

CENSUS TAXONOMY:
{json.dumps(taxonomy, indent=2)}

QUESTION:
Survey: {row['survey']}
Question: {row['question']}

CATEGORIZATION 1 (gpt-5-mini):
- Topic: {row['primary_topic_openai']}
- Subtopic: {row['primary_subtopic_openai']}
- Confidence: {row['confidence_openai']:.2f}

CATEGORIZATION 2 (claude-haiku-4-5):
- Topic: {row['primary_topic_claude']}
- Subtopic: {row['primary_subtopic_claude']}
- Confidence: {row['confidence_claude']:.2f}

DECIDE:
1. "pick_gpt5mini" - gpt-5-mini is correct
2. "pick_haiku45" - claude-haiku-4-5 is correct
3. "combine" - Both valid; question spans multiple topics
4. "new_concept" - Neither correct; provide better option FROM TAXONOMY

Return JSON:
{{
  "decision": "pick_gpt5mini" | "pick_haiku45" | "combine" | "new_concept",
  "final_topic": "Topic from taxonomy",
  "final_subtopic": "Subtopic from taxonomy",
  "additional_concepts": [{{"topic": "...", "subtopic": "..."}}, ...],
  "reasoning": "Your reasoning (2-3 sentences)",
  "confidence": 0.0-1.0
}}

CRITICAL: All topics and subtopics MUST exist in the taxonomy above.
"""
    return prompt

def create_round2_prompt(row: pd.Series, round1_result: Dict, taxonomy: Dict[str, List[str]]) -> str:
    """Round 2: gpt-5.2 reviews Sonnet's decision."""
    
    prompt = f"""You are reviewing an arbitration decision. The arbitrator must use ONLY concepts from the Census taxonomy.

CENSUS TAXONOMY:
{json.dumps(taxonomy, indent=2)}

QUESTION:
{row['question']}

ORIGINAL CATEGORIZATIONS:
1. gpt-5-mini: {row['primary_topic_openai']} / {row['primary_subtopic_openai']} (conf: {row['confidence_openai']:.2f})
2. claude-haiku-4-5: {row['primary_topic_claude']} / {row['primary_subtopic_claude']} (conf: {row['confidence_claude']:.2f})

ARBITRATOR DECISION (claude-sonnet-4-5):
- Decision: {round1_result['decision']}
- Final: {round1_result['final_topic']} / {round1_result['final_subtopic']}
- Reasoning: {round1_result['reasoning']}
- Confidence: {round1_result['confidence']:.2f}

YOUR TASK:
Review this decision. Do you agree? If not, explain why and what you would choose instead.

Return JSON:
{{
  "agrees": true | false,
  "feedback": "Detailed feedback on the decision (3-4 sentences)",
  "suggested_decision": "pick_gpt5mini" | "pick_haiku45" | "combine" | "new_concept" | null,
  "suggested_topic": "Your suggested topic from taxonomy" | null,
  "suggested_subtopic": "Your suggested subtopic from taxonomy" | null,
  "reasoning": "Your reasoning if you disagree" | null,
  "confidence": 0.0-1.0
}}

If you agree, set agrees=true and leave suggestions as null.
If you disagree, provide your alternative using ONLY taxonomy concepts.
"""
    return prompt

def create_round3_prompt(row: pd.Series, round1_result: Dict, round2_result: Dict, 
                        taxonomy: Dict[str, List[str]]) -> str:
    """Round 3: Sonnet's final decision after seeing gpt-5.2 feedback."""
    
    prompt = f"""You are making a FINAL arbitration decision after receiving feedback from gpt-5.2.

CENSUS TAXONOMY:
{json.dumps(taxonomy, indent=2)}

QUESTION:
{row['question']}

ORIGINAL CATEGORIZATIONS:
1. gpt-5-mini: {row['primary_topic_openai']} / {row['primary_subtopic_openai']}
2. claude-haiku-4-5: {row['primary_topic_claude']} / {row['primary_subtopic_claude']}

YOUR ROUND 1 DECISION:
- Decision: {round1_result['decision']}
- Final: {round1_result['final_topic']} / {round1_result['final_subtopic']}
- Reasoning: {round1_result['reasoning']}

GPT-5.2 FEEDBACK (Round 2):
- Agrees: {round2_result['agrees']}
- Feedback: {round2_result['feedback']}
{"- Suggested: " + str(round2_result.get('suggested_topic')) + " / " + str(round2_result.get('suggested_subtopic')) if not round2_result['agrees'] else ""}
{"- Their reasoning: " + str(round2_result.get('reasoning')) if not round2_result['agrees'] else ""}

FINAL DECISION:
Consider gpt-5.2's feedback. Do you maintain your decision or change it?

Return JSON:
{{
  "decision": "pick_gpt5mini" | "pick_haiku45" | "combine" | "new_concept",
  "final_topic": "Topic from taxonomy",
  "final_subtopic": "Subtopic from taxonomy",
  "additional_concepts": [{{"topic": "...", "subtopic": "..."}}, ...],
  "reasoning": "Final reasoning incorporating feedback (3-4 sentences)",
  "changed_from_round1": true | false,
  "confidence": 0.0-1.0
}}

This is your FINAL decision. Use ONLY taxonomy concepts.
"""
    return prompt

def call_sonnet(prompt: str, max_retries: int = 5) -> Dict[str, Any]:
    """Call claude-sonnet-4-5."""
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

def call_gpt52(prompt: str, max_retries: int = 5) -> Dict[str, Any]:
    """Call gpt-5.2."""
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
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
            return extract_json_robust(content)
            
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                time.sleep(wait_time)
            else:
                raise e

def arbitrate_question(row: pd.Series, taxonomy: Dict[str, List[str]]) -> Dict[str, Any]:
    """Run full arbitration loop for one question."""
    
    result = {
        'id': row['id'],
        'question': row['question'],
        'original_gpt5mini': f"{row['primary_topic_openai']}.{row['primary_subtopic_openai']}",
        'original_haiku45': f"{row['primary_topic_claude']}.{row['primary_subtopic_claude']}",
    }
    
    try:
        # Round 1: Sonnet's initial decision
        round1_prompt = create_round1_prompt(row, taxonomy)
        round1_result = call_sonnet(round1_prompt)
        
        result['round1_decision'] = round1_result['decision']
        result['round1_topic'] = round1_result['final_topic']
        result['round1_subtopic'] = round1_result['final_subtopic']
        result['round1_reasoning'] = round1_result['reasoning']
        result['round1_confidence'] = round1_result.get('confidence', 0.0)
        
        # Round 2: gpt-5.2 review
        round2_prompt = create_round2_prompt(row, round1_result, taxonomy)
        round2_result = call_gpt52(round2_prompt)
        
        result['round2_agrees'] = round2_result['agrees']
        result['round2_feedback'] = round2_result['feedback']
        result['round2_suggested_topic'] = round2_result.get('suggested_topic')
        result['round2_suggested_subtopic'] = round2_result.get('suggested_subtopic')
        result['round2_confidence'] = round2_result.get('confidence', 0.0)
        
        # If gpt-5.2 agrees, we're done
        if round2_result['agrees']:
            result['final_decision'] = round1_result['decision']
            result['final_topic'] = round1_result['final_topic']
            result['final_subtopic'] = round1_result['final_subtopic']
            result['final_reasoning'] = round1_result['reasoning']
            result['agreement_round'] = 2
            result['needs_human_review'] = False
            return result
        
        # Round 3: Sonnet's final decision after feedback
        round3_prompt = create_round3_prompt(row, round1_result, round2_result, taxonomy)
        round3_result = call_sonnet(round3_prompt)
        
        result['round3_decision'] = round3_result['decision']
        result['round3_topic'] = round3_result['final_topic']
        result['round3_subtopic'] = round3_result['final_subtopic']
        result['round3_reasoning'] = round3_result['reasoning']
        result['round3_changed'] = round3_result.get('changed_from_round1', False)
        result['round3_confidence'] = round3_result.get('confidence', 0.0)
        
        # Check if gpt-5.2 would agree with round 3
        # If Sonnet changed to match gpt-5.2's suggestion, call it agreement
        if (round3_result['final_topic'] == round2_result.get('suggested_topic') and 
            round3_result['final_subtopic'] == round2_result.get('suggested_subtopic')):
            result['final_decision'] = round3_result['decision']
            result['final_topic'] = round3_result['final_topic']
            result['final_subtopic'] = round3_result['final_subtopic']
            result['final_reasoning'] = round3_result['reasoning']
            result['agreement_round'] = 3
            result['needs_human_review'] = False
        else:
            # Still disagreement after 3 rounds - flag for human
            result['final_decision'] = round3_result['decision']
            result['final_topic'] = round3_result['final_topic']
            result['final_subtopic'] = round3_result['final_subtopic']
            result['final_reasoning'] = round3_result['reasoning']
            result['agreement_round'] = None
            result['needs_human_review'] = True
        
        return result
        
    except Exception as e:
        result['error'] = str(e)
        result['needs_human_review'] = True
        return result

def main():
    print("="*70)
    print("AGENTIC ARBITRATION WITH FEEDBACK LOOP")
    print("="*70)
    
    # Load data
    print("\n1. Loading data...")
    candidates = load_arbitration_candidates()
    taxonomy = load_taxonomy()
    print(f"   Candidates: {len(candidates)}")
    print(f"   Max rounds: {MAX_ROUNDS}")
    
    # Process questions
    print("\n2. Processing with feedback loop...")
    results = []
    
    for idx, row in tqdm(candidates.iterrows(), total=len(candidates), desc="Arbitrating"):
        result = arbitrate_question(row, taxonomy)
        results.append(result)
        
        # Save incremental
        pd.DataFrame(results).to_csv(OUTPUT_DIR / 'agentic_arbitration_results.csv', index=False)
        
        # Add small delay to avoid rate limits
        time.sleep(0.5)
    
    results_df = pd.DataFrame(results)
    
    # Analysis
    print("\n" + "="*70)
    print("RESULTS SUMMARY")
    print("="*70)
    
    print(f"\nTotal questions: {len(results_df)}")
    
    agreement_r2 = (results_df['agreement_round'] == 2).sum()
    agreement_r3 = (results_df['agreement_round'] == 3).sum()
    needs_human = results_df['needs_human_review'].sum()
    
    print(f"\nAgreement reached in Round 2: {agreement_r2} ({agreement_r2/len(results_df)*100:.1f}%)")
    print(f"Agreement reached in Round 3: {agreement_r3} ({agreement_r3/len(results_df)*100:.1f}%)")
    print(f"Needs human review: {needs_human} ({needs_human/len(results_df)*100:.1f}%)")
    
    print("\nRound 1 decisions:")
    if 'round1_decision' in results_df.columns:
        for decision, count in results_df['round1_decision'].value_counts().items():
            print(f"  {decision}: {count}")
    
    print("\nRound 3 changes:")
    if 'round3_changed' in results_df.columns:
        changed = results_df['round3_changed'].sum()
        print(f"  Sonnet changed decision: {changed} ({changed/len(results_df)*100:.1f}%)")
    
    # Save human review subset
    if needs_human > 0:
        human_review = results_df[results_df['needs_human_review'] == True]
        human_review.to_csv(OUTPUT_DIR / 'needs_human_review.csv', index=False)
        print(f"\n   Saved: needs_human_review.csv ({needs_human} questions)")
    
    print("\n" + "="*70)
    print("COMPLETE!")
    print("="*70)
    print(f"\nResults: {OUTPUT_DIR}")

if __name__ == '__main__':
    import os
    main()
