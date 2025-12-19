#!/usr/bin/env python3
"""
Re-run ONLY OpenAI categorization (Claude is complete).
"""

import os
import json
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm
import time

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
            result = json.loads(content)
            
            if not isinstance(result, list):
                if isinstance(result, dict) and 'categorizations' in result:
                    result = result['categorizations']
                elif isinstance(result, dict) and len(result) == 1:
                    result = list(result.values())[0]
                else:
                    return []
            
            if not isinstance(result, list):
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

print("Re-running OpenAI ONLY...")
print("(Claude results already complete)")

taxonomy = load_taxonomy()
questions_df = load_questions()

print(f"\nLoaded {len(questions_df)} questions")

# Delete old OpenAI results
openai_file = RESULTS_DIR / 'results_openai.jsonl'
if openai_file.exists():
    openai_file.unlink()
    print("Deleted old OpenAI results")

# Create batches
questions = questions_df.to_dict('records')
batches = [questions[i:i + BATCH_SIZE] for i in range(0, len(questions), BATCH_SIZE)]

print(f"\nProcessing {len(batches)} batches...")

# Sequential processing (no parallel - OpenAI is stalling with parallel)
for batch_idx in tqdm(range(len(batches)), desc="OpenAI"):
    batch = batches[batch_idx]
    results = call_openai(batch, taxonomy)
    
    if results:
        with open(openai_file, 'a') as f:
            for result in results:
                f.write(json.dumps(result) + '\n')

print("\nOpenAI processing complete!")
print(f"Results: {openai_file}")
