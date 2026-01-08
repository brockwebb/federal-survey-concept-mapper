#!/usr/bin/env python3
"""
LLM-based categorization of survey questions to Census taxonomy concepts.

Sends questions in batches of 10 to both OpenAI and Claude APIs.
Includes error handling, exponential backoff, and resume capability.
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
CHECKPOINT_FILE = Path('../output/categorization_checkpoint.json')
RESULTS_DIR = Path('../output/results')

# Thread lock for safe checkpoint access
checkpoint_lock = threading.Lock()
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Thread-safe file writing
write_lock = threading.Lock()

def load_taxonomy() -> Dict[str, List[str]]:
    """Load Census taxonomy from JSON file."""
    taxonomy_path = Path('../data/raw/census_survey_explorer_taxonomy.json')
    with open(taxonomy_path, 'r') as f:
        data = json.load(f)
    return data['taxonomy']

def load_questions() -> pd.DataFrame:
    """Load survey questions from CSV."""
    df = pd.read_csv('../data/raw/PublicSurveyQuestionsMap.csv')
    
    # Create question-survey mapping
    questions = []
    for idx, row in df.iterrows():
        question = row['Question']
        # Get all surveys this question appears in
        surveys = [col for col in df.columns if col != 'Question' and pd.notna(row[col])]
        # Use first survey as primary
        survey = surveys[0] if surveys else 'Unknown'
        
        questions.append({
            'id': idx,
            'survey': survey,
            'question': question
        })
    
    return pd.DataFrame(questions)

def create_prompt(batch: List[Dict[str, Any]], taxonomy: Dict[str, List[str]]) -> str:
    """Create categorization prompt for a batch of questions."""
    
    prompt = f"""You are categorizing federal survey questions using the official U.S. Census Bureau taxonomy.

TAXONOMY:
{json.dumps(taxonomy, indent=2)}

TASK:
For each question below, assign:
1. Primary concept: The most relevant Topic and Subtopic
2. Secondary concepts: 0-3 additional relevant subtopics (if applicable)
3. Confidence: 0-1 score for primary assignment
4. Reasoning: Brief explanation (1-2 sentences)

QUESTIONS TO CATEGORIZE:
{json.dumps(batch, indent=2)}

Return a JSON array with one object per question, in the same order. Format:
[
  {{
    "id": 0,
    "primary_topic": "Economic",
    "primary_subtopic": "Income",
    "confidence": 0.95,
    "secondary_concepts": [
      {{"topic": "Economic", "subtopic": "Employment Status"}},
      {{"topic": "Demographic", "subtopic": "Age"}}
    ],
    "reasoning": "Question asks about household income sources."
  }},
  ...
]

Return ONLY the JSON array, no other text."""
    
    return prompt

def call_openai(batch: List[Dict[str, Any]], taxonomy: Dict[str, List[str]], 
                max_retries: int = 5) -> List[Dict[str, Any]]:
    """Call OpenAI API with exponential backoff."""
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    prompt = create_prompt(batch, taxonomy)
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-5-mini",
                messages=[
                    {"role": "system", "content": "You are a precise data categorization assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.choices[0].message.content
            
            # Aggressive cleaning for OpenAI's malformed JSON
            # Remove control characters
            import re
            content = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', content)
            
            # Try to parse
            try:
                result = json.loads(content)
            except json.JSONDecodeError as e:
                # If it fails, try to extract just the array
                # Find first [ and last ]
                start = content.find('[')
                end = content.rfind(']')
                if start != -1 and end != -1:
                    array_str = content[start:end+1]
                    # Clean again
                    array_str = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', array_str)
                    result = json.loads(array_str)
                else:
                    raise e
            
            # Ensure result is a list
            if not isinstance(result, list):
                if isinstance(result, dict) and 'categorizations' in result:
                    result = result['categorizations']
                elif isinstance(result, dict) and len(result) == 1:
                    result = list(result.values())[0]
                else:
                    print(f"  Unexpected response format: {type(result)}")
                    return []
            
            # Verify it's actually a list now
            if not isinstance(result, list):
                print(f"  Could not extract list from response")
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

def call_claude(batch: List[Dict[str, Any]], taxonomy: Dict[str, List[str]], 
                max_retries: int = 5) -> List[Dict[str, Any]]:
    """Call Claude API with exponential backoff."""
    client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    prompt = create_prompt(batch, taxonomy)
    
    for attempt in range(max_retries):
        try:
            response = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=4096,
                temperature=0,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.content[0].text
            
            # Strip markdown formatting if present
            if content.startswith('```json'):
                content = content.split('```json')[1]
            if content.endswith('```'):
                content = content.rsplit('```', 1)[0]
            content = content.strip()
            
            result = json.loads(content)
            
            # Ensure result is a list
            if not isinstance(result, list):
                # Handle if wrapped in extra object
                if isinstance(result, dict) and 'categorizations' in result:
                    result = result['categorizations']
                elif isinstance(result, dict) and len(result) == 1:
                    result = list(result.values())[0]
                else:
                    print(f"  Unexpected response format: {type(result)}")
                    return []
            
            # Verify it's actually a list now
            if not isinstance(result, list):
                print(f"  Could not extract list from response")
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
    """Load checkpoint if exists (thread-safe with corruption handling)."""
    with checkpoint_lock:
        if CHECKPOINT_FILE.exists():
            try:
                with open(CHECKPOINT_FILE, 'r') as f:
                    content = f.read().strip()
                    if not content:  # Empty file
                        return {'openai_batch': 0, 'claude_batch': 0}
                    return json.loads(content)
            except (json.JSONDecodeError, Exception) as e:
                print(f"  Warning: Corrupted checkpoint file, starting fresh")
                return {'openai_batch': 0, 'claude_batch': 0}
        return {'openai_batch': 0, 'claude_batch': 0}

def save_checkpoint(checkpoint: Dict[str, Any]):
    """Save checkpoint (thread-safe)."""
    with checkpoint_lock:
        CHECKPOINT_FILE.parent.mkdir(parents=True, exist_ok=True)
        # Write to temp file first, then atomic rename
        temp_file = CHECKPOINT_FILE.with_suffix('.tmp')
        with open(temp_file, 'w') as f:
            json.dump(checkpoint, f)
        temp_file.replace(CHECKPOINT_FILE)

def save_results(results: List[Dict[str, Any]], model: str):
    """Append results to JSONL file (thread-safe)."""
    output_file = RESULTS_DIR / f'results_{model}.jsonl'
    with write_lock:
        with open(output_file, 'a') as f:
            for result in results:
                f.write(json.dumps(result) + '\n')

def process_batch(batch_idx: int, batch: List[Dict], taxonomy: Dict, model: str, api_call) -> tuple:
    """Process a single batch (for parallel execution)."""
    results = api_call(batch, taxonomy)
    return (batch_idx, results)

def process_model(questions_df: pd.DataFrame, taxonomy: Dict[str, List[str]], 
                  model: str, start_batch: int = 0):
    """Process all questions for a given model (parallel)."""
    
    print(f"\n{'='*70}")
    print(f"Processing with {model.upper()} ({MAX_WORKERS} workers)")
    print(f"{'='*70}")
    
    # Create batches
    questions = questions_df.to_dict('records')
    batches = [questions[i:i + BATCH_SIZE] for i in range(0, len(questions), BATCH_SIZE)]
    
    # Process from checkpoint
    total_batches = len(batches)
    print(f"Total batches: {total_batches}")
    print(f"Starting from batch: {start_batch}")
    
    api_call = call_openai if model == 'openai' else call_claude
    
    # Parallel processing
    completed_count = start_batch
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all batches
        future_to_batch = {
            executor.submit(process_batch, batch_idx, batches[batch_idx], taxonomy, model, api_call): batch_idx
            for batch_idx in range(start_batch, total_batches)
        }
        
        # Process as they complete
        with tqdm(total=total_batches - start_batch, desc=f"  {model}") as pbar:
            for future in as_completed(future_to_batch):
                batch_idx, results = future.result()
                
                if results:
                    # Save results
                    save_results(results, model)
                    
                    # Update checkpoint
                    completed_count += 1
                    checkpoint = load_checkpoint()
                    checkpoint[f'{model}_batch'] = completed_count
                    save_checkpoint(checkpoint)
                else:
                    print(f"\n  Warning: Batch {batch_idx} failed for {model}")
                
                pbar.update(1)
    
    print(f"\n{model.upper()} processing complete!")

def main():
    """Main execution."""
    import sys
    
    # Check for model argument
    run_openai = True
    run_claude = True
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--openai-only':
            run_claude = False
        elif sys.argv[1] == '--claude-only':
            run_openai = False
    
    print("="*70)
    print("LLM-BASED SURVEY QUESTION CATEGORIZATION")
    print("="*70)
    
    # Load data
    print("\nLoading data...")
    taxonomy = load_taxonomy()
    questions_df = load_questions()
    print(f"  Loaded {len(questions_df)} questions")
    print(f"  Loaded taxonomy: {len(taxonomy)} topics")
    
    # Load checkpoint
    checkpoint = load_checkpoint()
    print(f"\nCheckpoint: OpenAI batch {checkpoint['openai_batch']}, Claude batch {checkpoint['claude_batch']}")
    
    # Run both APIs in parallel
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = []
        
        # Submit OpenAI
        if run_openai and checkpoint['openai_batch'] < len(questions_df) // BATCH_SIZE + 1:
            futures.append(executor.submit(process_model, questions_df, taxonomy, 'openai', checkpoint['openai_batch']))
        elif run_openai:
            print("\nOpenAI processing already complete (skipping)")
        
        # Submit Claude
        if run_claude and checkpoint['claude_batch'] < len(questions_df) // BATCH_SIZE + 1:
            futures.append(executor.submit(process_model, questions_df, taxonomy, 'claude', checkpoint['claude_batch']))
        elif run_claude:
            print("\nClaude processing already complete (skipping)")
        
        # Wait for both to complete
        for future in as_completed(futures):
            future.result()  # This will raise any exceptions that occurred
    
    print("\n" + "="*70)
    print("ALL PROCESSING COMPLETE!")
    print("="*70)
    print(f"\nResults saved to:")
    print(f"  - {RESULTS_DIR}/results_openai.jsonl")
    print(f"  - {RESULTS_DIR}/results_claude.jsonl")

if __name__ == '__main__':
    main()
