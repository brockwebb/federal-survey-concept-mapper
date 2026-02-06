#!/usr/bin/env python3
"""
Run ONLY OpenAI categorization.
"""

import os
import json
import re
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()

BATCH_SIZE = 10
MAX_WORKERS = 6
RESULTS_DIR = Path('../output/results')
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def load_taxonomy():
    with open('../data/raw/census_survey_explorer_taxonomy.json', 'r') as f:
        return json.load(f)['taxonomy']

def load_questions():
    df = pd.read_csv('../data/raw/PublicSurveyQuestionsMap.csv')
    questions = []
    for idx, row in df.iterrows():
        question = row['Question']
        surveys = [col for col in df.columns if col != 'Question' and pd.notna(row[col])]
        questions.append({
            'id': idx,
            'survey': surveys[0] if surveys else 'Unknown',
            'question': question
        })
    return pd.DataFrame(questions)

def create_prompt(batch, taxonomy):
    return f"""You are categorizing federal survey questions using the official U.S. Census Bureau taxonomy.

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

def call_openai(batch, taxonomy, max_retries=5):
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
            
            # Aggressive cleaning
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
                if isinstance(result, dict) and 'categorizations' in result:
                    result = result['categorizations']
                elif isinstance(result, dict) and len(result) == 1:
                    result = list(result.values())[0]
                else:
                    return []
            
            return result
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"  Error: {str(e)[:100]}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise Exception(f"Failed after {max_retries} attempts: {e}")
    return []

def process_batch(batch, taxonomy):
    return call_openai(batch, taxonomy)

print("="*70)
print("OPENAI CATEGORIZATION")
print("="*70)

taxonomy = load_taxonomy()
questions_df = load_questions()
print(f"\nLoaded {len(questions_df)} questions")

questions = questions_df.to_dict('records')
batches = [questions[i:i + BATCH_SIZE] for i in range(0, len(questions), BATCH_SIZE)]

output_file = RESULTS_DIR / 'results_openai.jsonl'
if output_file.exists():
    output_file.unlink()

print(f"\nProcessing {len(batches)} batches with {MAX_WORKERS} workers...")

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    future_to_batch = {
        executor.submit(process_batch, batch, taxonomy): idx 
        for idx, batch in enumerate(batches)
    }
    
    failed_batches = []
    
    with tqdm(total=len(batches), desc="OpenAI") as pbar:
        for future in as_completed(future_to_batch):
            batch_idx = future_to_batch[future]
            results = future.result()  # Will raise if failed
            
            if results:
                with open(output_file, 'a') as f:
                    for result in results:
                        f.write(json.dumps(result) + '\n')
            else:
                failed_batches.append(batch_idx)
            
            pbar.update(1)

if failed_batches:
    raise Exception(f"Failed to categorize {len(failed_batches)} batches: {failed_batches[:10]}")

print("\n✓ OpenAI processing complete!")
print(f"Results: {output_file}")
