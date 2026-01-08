#!/usr/bin/env python3
"""
Analyze failures and disagreement patterns in LLM categorization.

Investigates:
1. Patterns in None/failed responses
2. Characteristics of disagreements (length, confidence, etc.)
3. Candidates for arbitration
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

# Configuration
RESULTS_DIR = Path('../output/results')
OUTPUT_DIR = Path('../output/analysis')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_results(model: str) -> pd.DataFrame:
    """Load results from JSONL file."""
    results = []
    with open(RESULTS_DIR / f'results_{model}.jsonl', 'r') as f:
        for line in f:
            results.append(json.loads(line))
    return pd.DataFrame(results)

def load_questions() -> pd.DataFrame:
    """Load original questions."""
    df = pd.read_csv('../data/raw/PublicSurveyQuestionsMap.csv')
    
    questions = []
    for idx, row in df.iterrows():
        question = row['Question']
        surveys = [col for col in df.columns if col != 'Question' and pd.notna(row[col])]
        survey = surveys[0] if surveys else 'Unknown'
        
        questions.append({
            'id': idx,
            'survey': survey,
            'question': question,
            'question_length': len(str(question))
        })
    
    return pd.DataFrame(questions)

def main():
    print("="*70)
    print("FAILURE & DISAGREEMENT PATTERN ANALYSIS")
    print("="*70)
    
    # Load data
    print("\n1. Loading data...")
    openai_df = load_results('openai')
    claude_df = load_results('claude')
    questions_df = load_questions()
    
    # Merge all
    merged = openai_df.merge(claude_df, on='id', suffixes=('_openai', '_claude'))
    merged = merged.merge(questions_df, on='id')
    
    print(f"   Total questions: {len(merged)}")
    
    # === ANALYZE FAILURES ===
    print("\n" + "="*70)
    print("FAILURE ANALYSIS (None/Missing Values)")
    print("="*70)
    
    # Identify failures
    openai_failures = merged[merged['primary_topic_openai'].isna()].copy()
    claude_failures = merged[merged['primary_topic_claude'].isna()].copy()
    any_failure = merged[
        merged['primary_topic_openai'].isna() | 
        merged['primary_topic_claude'].isna()
    ].copy()
    
    print(f"\nOpenAI failures: {len(openai_failures)}")
    print(f"Claude failures: {len(claude_failures)}")
    print(f"Total unique failures: {len(any_failure)}")
    
    if len(any_failure) > 0:
        print("\nFailure characteristics:")
        print(f"  Mean question length: {any_failure['question_length'].mean():.1f} chars")
        print(f"  Median question length: {any_failure['question_length'].median():.1f} chars")
        print(f"  Min question length: {any_failure['question_length'].min()}")
        print(f"  Max question length: {any_failure['question_length'].max()}")
        
        # Compare to overall distribution
        print("\nOverall question lengths:")
        print(f"  Mean: {merged['question_length'].mean():.1f} chars")
        print(f"  Median: {merged['question_length'].median():.1f} chars")
        print(f"  Min: {merged['question_length'].min()}")
        print(f"  Max: {merged['question_length'].max()}")
        
        # Save failures
        failures_export = any_failure[['id', 'survey', 'question', 'question_length']].copy()
        failures_export.to_csv(OUTPUT_DIR / 'failures.csv', index=False)
        print(f"\n   Saved: failures.csv")
    
    # === ANALYZE DISAGREEMENTS ===
    print("\n" + "="*70)
    print("DISAGREEMENT ANALYSIS")
    print("="*70)
    
    # Filter to valid comparisons
    valid = merged[
        merged['primary_topic_openai'].notna() & 
        merged['primary_topic_claude'].notna()
    ].copy()
    
    # Add agreement flag
    valid['topic_agrees'] = valid['primary_topic_openai'] == valid['primary_topic_claude']
    valid['subtopic_agrees'] = valid['primary_subtopic_openai'] == valid['primary_subtopic_claude']
    
    # Calculate min confidence
    valid['min_confidence'] = valid[['confidence_openai', 'confidence_claude']].min(axis=1)
    valid['max_confidence'] = valid[['confidence_openai', 'confidence_claude']].max(axis=1)
    valid['confidence_diff'] = abs(valid['confidence_openai'] - valid['confidence_claude'])
    
    disagreements = valid[~valid['topic_agrees']].copy()
    
    print(f"\nTotal disagreements: {len(disagreements)} ({len(disagreements)/len(valid)*100:.1f}%)")
    
    print("\nDisagreement characteristics:")
    print(f"  Mean question length: {disagreements['question_length'].mean():.1f} chars")
    print(f"  Median question length: {disagreements['question_length'].median():.1f} chars")
    print(f"  Mean min confidence: {disagreements['min_confidence'].mean():.3f}")
    print(f"  Mean confidence diff: {disagreements['confidence_diff'].mean():.3f}")
    
    print("\nAgreement characteristics:")
    agreements = valid[valid['topic_agrees']].copy()
    print(f"  Mean question length: {agreements['question_length'].mean():.1f} chars")
    print(f"  Median question length: {agreements['question_length'].median():.1f} chars")
    print(f"  Mean min confidence: {agreements['min_confidence'].mean():.3f}")
    print(f"  Mean confidence diff: {agreements['confidence_diff'].mean():.3f}")
    
    # === ARBITRATION CANDIDATES ===
    print("\n" + "="*70)
    print("ARBITRATION CANDIDATES")
    print("="*70)
    
    # Strategy: Send to arbitrator if min_confidence < 0.8
    arbitration_candidates = disagreements[disagreements['min_confidence'] < 0.8].copy()
    
    print(f"\nCandidates (disagreement + min_confidence < 0.8): {len(arbitration_candidates)}")
    print(f"  This is {len(arbitration_candidates)/len(valid)*100:.1f}% of all questions")
    print(f"  This is {len(arbitration_candidates)/len(disagreements)*100:.1f}% of disagreements")
    
    if len(arbitration_candidates) > 0:
        print("\nArbitration candidate stats:")
        print(f"  Mean min confidence: {arbitration_candidates['min_confidence'].mean():.3f}")
        print(f"  Mean question length: {arbitration_candidates['question_length'].mean():.1f} chars")
        
        # Show top patterns
        print("\nTop disagreement patterns in candidates:")
        patterns = arbitration_candidates.groupby(
            ['primary_topic_openai', 'primary_topic_claude']
        ).size().sort_values(ascending=False).head(10)
        
        for (openai_topic, claude_topic), count in patterns.items():
            print(f"  {openai_topic} vs {claude_topic}: {count}")
        
        # Save candidates
        arb_export = arbitration_candidates[[
            'id', 'survey', 'question', 'question_length',
            'primary_topic_openai', 'primary_subtopic_openai', 'confidence_openai',
            'primary_topic_claude', 'primary_subtopic_claude', 'confidence_claude',
            'min_confidence', 'confidence_diff'
        ]].copy()
        arb_export = arb_export.sort_values('min_confidence')
        arb_export.to_csv(OUTPUT_DIR / 'arbitration_candidates.csv', index=False)
        print(f"\n   Saved: arbitration_candidates.csv ({len(arb_export)} rows)")
    
    # === COMBINED CONCEPTS ANALYSIS ===
    print("\n" + "="*70)
    print("COMBINED CONCEPTS (Multi-perspective approach)")
    print("="*70)
    
    # For each question, collect all unique concepts mentioned
    def collect_concepts(row):
        concepts = set()
        
        # OpenAI primary
        if pd.notna(row['primary_topic_openai']) and pd.notna(row['primary_subtopic_openai']):
            concepts.add(f"{row['primary_topic_openai']}.{row['primary_subtopic_openai']}")
        
        # Claude primary
        if pd.notna(row['primary_topic_claude']) and pd.notna(row['primary_subtopic_claude']):
            concepts.add(f"{row['primary_topic_claude']}.{row['primary_subtopic_claude']}")
        
        # OpenAI secondary
        if 'secondary_concepts_openai' in row.index:
            sec_val = row['secondary_concepts_openai']
            if not (isinstance(sec_val, float) and np.isnan(sec_val)):
                try:
                    sec = eval(sec_val) if isinstance(sec_val, str) else sec_val
                    if isinstance(sec, list):
                        for item in sec:
                            if isinstance(item, dict) and 'topic' in item and 'subtopic' in item:
                                concepts.add(f"{item['topic']}.{item['subtopic']}")
                except:
                    pass
        
        # Claude secondary
        if 'secondary_concepts_claude' in row.index:
            sec_val = row['secondary_concepts_claude']
            if not (isinstance(sec_val, float) and np.isnan(sec_val)):
                try:
                    sec = eval(sec_val) if isinstance(sec_val, str) else sec_val
                    if isinstance(sec, list):
                        for item in sec:
                            if isinstance(item, dict) and 'topic' in item and 'subtopic' in item:
                                concepts.add(f"{item['topic']}.{item['subtopic']}")
                except:
                    pass
        
        return list(concepts)
    
    valid['all_concepts'] = valid.apply(collect_concepts, axis=1)
    valid['concept_count'] = valid['all_concepts'].apply(len)
    
    print(f"\nConcept counts:")
    print(f"  Mean concepts per question: {valid['concept_count'].mean():.2f}")
    print(f"  Median concepts per question: {valid['concept_count'].median():.0f}")
    print(f"  Max concepts per question: {valid['concept_count'].max()}")
    
    print("\nQuestions with multiple perspectives:")
    multi = valid[valid['concept_count'] > 1]
    print(f"  {len(multi)} questions ({len(multi)/len(valid)*100:.1f}%)")
    
    # === VISUALIZATIONS ===
    print("\n" + "="*70)
    print("GENERATING VISUALIZATIONS")
    print("="*70)
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1. Question length distribution: failures vs all
    if len(any_failure) > 0:
        axes[0, 0].hist(merged['question_length'], bins=50, alpha=0.5, 
                       label='All questions', edgecolor='black')
        axes[0, 0].hist(any_failure['question_length'], bins=50, alpha=0.7, 
                       label='Failures', edgecolor='black', color='red')
        axes[0, 0].set_xlabel('Question Length (characters)')
        axes[0, 0].set_ylabel('Frequency')
        axes[0, 0].set_title('Question Length: Failures vs All')
        axes[0, 0].legend()
        axes[0, 0].set_yscale('log')
    
    # 2. Question length: disagreements vs agreements
    axes[0, 1].hist(agreements['question_length'], bins=50, alpha=0.5, 
                   label='Agreements', edgecolor='black')
    axes[0, 1].hist(disagreements['question_length'], bins=50, alpha=0.7, 
                   label='Disagreements', edgecolor='black', color='orange')
    axes[0, 1].set_xlabel('Question Length (characters)')
    axes[0, 1].set_ylabel('Frequency')
    axes[0, 1].set_title('Question Length: Disagreements vs Agreements')
    axes[0, 1].legend()
    axes[0, 1].set_yscale('log')
    
    # 3. Confidence vs agreement
    axes[1, 0].scatter(agreements['min_confidence'], 
                      [1]*len(agreements), alpha=0.1, s=10, label='Agree')
    axes[1, 0].scatter(disagreements['min_confidence'], 
                      [0]*len(disagreements), alpha=0.3, s=10, color='red', label='Disagree')
    axes[1, 0].axvline(x=0.8, color='green', linestyle='--', alpha=0.5, label='Arbitration threshold')
    axes[1, 0].set_xlabel('Minimum Confidence')
    axes[1, 0].set_ylabel('Agreement')
    axes[1, 0].set_title('Confidence vs Agreement')
    axes[1, 0].set_ylim([-0.1, 1.1])
    axes[1, 0].legend()
    
    # 4. Concept count distribution
    axes[1, 1].hist(valid['concept_count'], bins=range(1, valid['concept_count'].max()+2), 
                   edgecolor='black', alpha=0.7)
    axes[1, 1].set_xlabel('Number of Unique Concepts')
    axes[1, 1].set_ylabel('Frequency')
    axes[1, 1].set_title('Concepts per Question (Multi-perspective)')
    axes[1, 1].set_xticks(range(1, valid['concept_count'].max()+1))
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'failure_disagreement_analysis.png', dpi=150, bbox_inches='tight')
    print(f"   Saved: failure_disagreement_analysis.png")
    
    print("\n" + "="*70)
    print("ANALYSIS COMPLETE!")
    print("="*70)
    print(f"\nKey outputs:")
    print(f"  - failures.csv: {len(any_failure)} failed categorizations")
    print(f"  - arbitration_candidates.csv: {len(arbitration_candidates) if len(arbitration_candidates) > 0 else 0} low-confidence disagreements (reference only)")
    print(f"  - failure_disagreement_analysis.png: Visualizations")
    
    print(f"\nNote: Step 5 will arbitrate ALL {len(disagreements)} disagreements using 0.90 threshold.")

if __name__ == '__main__':
    main()
