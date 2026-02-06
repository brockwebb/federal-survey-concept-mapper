#!/usr/bin/env python3
"""
Create reconciled master dataset and summary visualizations.

Combines:
- Initial categorizations (gpt-5-mini, claude-haiku-4-5)
- Arbitration results (where applicable)
- Agreement flags and decision methods

Outputs:
- master_dataset.csv - One row per question with final categorization
- survey_concept_matrix.csv - Aggregated survey × concept counts
- Summary visualizations
- README.md with key findings
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter

# Configuration
OUTPUT_DIR = Path('../output/final')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = (16, 10)

def load_initial_results() -> pd.DataFrame:
    """Load initial categorization results."""
    openai = []
    with open('../output/results/results_openai.jsonl', 'r') as f:
        for line in f:
            openai.append(json.loads(line))
    
    claude = []
    with open('../output/results/results_claude.jsonl', 'r') as f:
        for line in f:
            claude.append(json.loads(line))
    
    openai_df = pd.DataFrame(openai)
    claude_df = pd.DataFrame(claude)
    
    merged = openai_df.merge(claude_df, on='id', suffixes=('_openai', '_claude'))
    return merged

def load_arbitration_results() -> pd.DataFrame:
    """Load arbitration results if they exist."""
    arb_path = Path('../output/arbitration_final/all_disagreement_resolutions.csv')
    if arb_path.exists():
        return pd.read_csv(arb_path)
    return None

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
            'surveys': ','.join(surveys),
            'survey_count': len(surveys),
            'primary_survey': surveys[0] if surveys else 'Unknown'
        })
    
    return pd.DataFrame(questions)

def reconcile_categorizations(initial_df: pd.DataFrame, arbitration_df: pd.DataFrame = None) -> pd.DataFrame:
    """Create master dataset with reconciled categorizations."""
    
    master = initial_df.copy()
    
    # Add agreement flag
    master['models_agree'] = (
        master['primary_topic_openai'] == master['primary_topic_claude']
    ) & (
        master['primary_subtopic_openai'] == master['primary_subtopic_claude']
    )
    
    # Initialize final categorization columns
    master['final_topic'] = None
    master['final_subtopic'] = None
    master['decision_method'] = None
    master['needs_human_review'] = False
    
    # For agreements, use the agreed-upon categorization
    agreed_mask = master['models_agree'] & master['primary_topic_openai'].notna()
    master.loc[agreed_mask, 'final_topic'] = master.loc[agreed_mask, 'primary_topic_openai']
    master.loc[agreed_mask, 'final_subtopic'] = master.loc[agreed_mask, 'primary_subtopic_openai']
    master.loc[agreed_mask, 'decision_method'] = 'agreement'
    
    # For disagreements, check if arbitration exists
    if arbitration_df is not None:
        # Merge arbitration results
        arb_subset = arbitration_df[[
            'id', 'primary_topic', 'primary_subtopic', 'primary_confidence',
            'secondary_primary_topic', 'secondary_primary_subtopic', 
            'is_dual_modal', 'decision', 'confidence_tier'
        ]].copy()
        arb_subset.columns = [
            'id', 'arb_primary_topic', 'arb_primary_subtopic', 'arb_primary_conf',
            'arb_secondary_topic', 'arb_secondary_subtopic',
            'arb_is_dual_modal', 'arb_decision', 'arb_conf_tier'
        ]
        
        master = master.merge(arb_subset, on='id', how='left')
        
        # Use arbitration results where available
        arbitrated_mask = master['arb_primary_topic'].notna() & ~master['models_agree']
        master.loc[arbitrated_mask, 'final_topic'] = master.loc[arbitrated_mask, 'arb_primary_topic']
        master.loc[arbitrated_mask, 'final_subtopic'] = master.loc[arbitrated_mask, 'arb_primary_subtopic']
        master.loc[arbitrated_mask, 'secondary_primary_topic'] = master.loc[arbitrated_mask, 'arb_secondary_topic']
        master.loc[arbitrated_mask, 'secondary_primary_subtopic'] = master.loc[arbitrated_mask, 'arb_secondary_subtopic']
        master.loc[arbitrated_mask, 'is_dual_modal'] = master.loc[arbitrated_mask, 'arb_is_dual_modal'].fillna(False)
        master.loc[arbitrated_mask, 'confidence_tier'] = master.loc[arbitrated_mask, 'arb_conf_tier']
        
        # Set decision method
        master.loc[arbitrated_mask, 'decision_method'] = master.loc[arbitrated_mask, 'arb_decision']
    
    # For remaining disagreements (no arbitration), mark as needing review
    unresolved_mask = master['final_topic'].isna() & ~master['models_agree']
    master.loc[unresolved_mask, 'needs_human_review'] = True
    master.loc[unresolved_mask, 'decision_method'] = 'unresolved_disagreement'
    
    # Handle failures (both models returned None)
    failure_mask = master['primary_topic_openai'].isna() & master['primary_topic_claude'].isna()
    master.loc[failure_mask, 'needs_human_review'] = True
    master.loc[failure_mask, 'decision_method'] = 'categorization_failed'
    
    return master

def create_survey_concept_matrix(master_df: pd.DataFrame, questions_df: pd.DataFrame) -> pd.DataFrame:
    """Create aggregated survey × concept matrix."""
    
    # Ensure primary_survey exists in master_df (merge if needed)
    if 'primary_survey' not in master_df.columns:
        master_df = master_df.merge(questions_df[['id', 'primary_survey']], on='id', how='left')
    
    # Filter to successfully categorized questions
    valid = master_df[master_df['final_topic'].notna()].copy()
    
    # Create concept column
    valid['concept'] = valid['final_topic'] + '.' + valid['final_subtopic']
    
    # Create pivot table
    matrix = valid.groupby(['primary_survey', 'concept']).size().reset_index(name='count')
    matrix_wide = matrix.pivot(index='primary_survey', columns='concept', values='count').fillna(0)
    
    return matrix_wide

def generate_summary_stats(master_df: pd.DataFrame, questions_df: pd.DataFrame):
    """Generate and print summary statistics."""
    
    total = len(master_df)
    
    print("\n" + "="*70)
    print("SUMMARY STATISTICS")
    print("="*70)
    
    print(f"\nTotal questions: {total:,}")
    
    # Decision methods
    print("\nDecision methods:")
    method_counts = master_df['decision_method'].value_counts()
    for method, count in method_counts.items():
        pct = count / total * 100
        print(f"  {method}: {count:,} ({pct:.1f}%)")
    
    # Human review needed
    review_count = master_df['needs_human_review'].sum()
    print(f"\nNeeds human review: {review_count:,} ({review_count/total*100:.1f}%)")
    
    # Topic distribution
    print("\nFinal topic distribution:")
    valid = master_df[master_df['final_topic'].notna()]
    topic_counts = valid['final_topic'].value_counts()
    for topic, count in topic_counts.items():
        pct = count / len(valid) * 100
        print(f"  {topic}: {count:,} ({pct:.1f}%)")
    
    # Survey coverage (master_df already has primary_survey merged)
    survey_counts = master_df['primary_survey'].value_counts()
    print(f"\nSurveys represented: {len(survey_counts)}")
    print(f"Questions per survey (median): {survey_counts.median():.0f}")
    
    return {
        'total_questions': total,
        'successfully_categorized': len(valid),
        'needs_review': review_count,
        'topics': len(topic_counts),
        'surveys': len(survey_counts)
    }

def create_visualizations(master_df: pd.DataFrame, questions_df: pd.DataFrame, matrix_df: pd.DataFrame):
    """Generate summary visualizations."""
    
    print("\n" + "="*70)
    print("GENERATING VISUALIZATIONS")
    print("="*70)
    
    fig = plt.figure(figsize=(20, 12))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    
    # 1. Decision method breakdown
    ax1 = fig.add_subplot(gs[0, 0])
    method_counts = master_df['decision_method'].value_counts()
    colors = ['#2ecc71', '#3498db', '#e74c3c', '#f39c12', '#95a5a6']
    ax1.pie(method_counts.values, labels=method_counts.index, autopct='%1.1f%%', 
            colors=colors[:len(method_counts)], startangle=90)
    ax1.set_title('Decision Methods', fontsize=14, fontweight='bold')
    
    # 2. Topic distribution
    ax2 = fig.add_subplot(gs[0, 1])
    valid = master_df[master_df['final_topic'].notna()]
    topic_counts = valid['final_topic'].value_counts()
    ax2.barh(range(len(topic_counts)), topic_counts.values, color='steelblue')
    ax2.set_yticks(range(len(topic_counts)))
    ax2.set_yticklabels(topic_counts.index)
    ax2.set_xlabel('Question Count')
    ax2.set_title('Final Topic Distribution', fontsize=14, fontweight='bold')
    ax2.grid(axis='x', alpha=0.3)
    
    # 3. Top 10 subtopics
    ax3 = fig.add_subplot(gs[0, 2])
    valid = valid.copy()  # Avoid SettingWithCopyWarning
    valid['concept'] = valid['final_topic'] + '.' + valid['final_subtopic']
    concept_counts = valid['concept'].value_counts().head(10)
    ax3.barh(range(len(concept_counts)), concept_counts.values, color='coral')
    ax3.set_yticks(range(len(concept_counts)))
    ax3.set_yticklabels([c.replace('.', '\n') for c in concept_counts.index], fontsize=9)
    ax3.set_xlabel('Question Count')
    ax3.set_title('Top 10 Concepts', fontsize=14, fontweight='bold')
    ax3.grid(axis='x', alpha=0.3)
    
    # 4. Survey size distribution
    ax4 = fig.add_subplot(gs[1, 0])
    survey_sizes = master_df['primary_survey'].value_counts()
    ax4.hist(survey_sizes.values, bins=30, color='lightseagreen', edgecolor='black')
    ax4.set_xlabel('Questions per Survey')
    ax4.set_ylabel('Number of Surveys')
    ax4.set_title('Survey Size Distribution', fontsize=14, fontweight='bold')
    ax4.axvline(survey_sizes.median(), color='red', linestyle='--', 
                label=f'Median: {survey_sizes.median():.0f}')
    ax4.legend()
    ax4.grid(alpha=0.3)
    
    # 5. Concept diversity per survey
    ax5 = fig.add_subplot(gs[1, 1])
    master_valid = master_df[master_df['final_topic'].notna()].copy()
    master_valid['concept'] = master_valid['final_topic'] + '.' + master_valid['final_subtopic']
    survey_concepts = master_valid.groupby('primary_survey')['concept'].nunique()
    ax5.hist(survey_concepts.values, bins=20, color='orchid', edgecolor='black')
    ax5.set_xlabel('Unique Concepts per Survey')
    ax5.set_ylabel('Number of Surveys')
    ax5.set_title('Concept Diversity by Survey', fontsize=14, fontweight='bold')
    ax5.axvline(survey_concepts.median(), color='red', linestyle='--',
                label=f'Median: {survey_concepts.median():.0f}')
    ax5.legend()
    ax5.grid(alpha=0.3)
    
    # 6. Top surveys by question count
    ax6 = fig.add_subplot(gs[1, 2])
    top_surveys = survey_sizes.head(15)
    ax6.barh(range(len(top_surveys)), top_surveys.values, color='gold')
    ax6.set_yticks(range(len(top_surveys)))
    ax6.set_yticklabels([s[:40] + '...' if len(s) > 40 else s for s in top_surveys.index], fontsize=8)
    ax6.set_xlabel('Question Count')
    ax6.set_title('Top 15 Surveys by Size', fontsize=14, fontweight='bold')
    ax6.grid(axis='x', alpha=0.3)
    
    # 7. Heatmap of top survey-topic relationships
    ax7 = fig.add_subplot(gs[2, :])
    
    # Get top 15 surveys and all topics
    top_survey_names = survey_sizes.head(15).index
    survey_topic = master_df[master_df['primary_survey'].isin(top_survey_names) & 
                             master_df['final_topic'].notna()].groupby(
        ['primary_survey', 'final_topic']
    ).size().reset_index(name='count')
    
    heatmap_data = survey_topic.pivot(index='primary_survey', columns='final_topic', values='count').fillna(0)
    heatmap_data = heatmap_data.reindex(top_survey_names)
    
    sns.heatmap(heatmap_data, annot=True, fmt='.0f', cmap='YlOrRd', 
                cbar_kws={'label': 'Question Count'}, ax=ax7)
    ax7.set_title('Survey × Topic Heatmap (Top 15 Surveys)', fontsize=14, fontweight='bold')
    ax7.set_xlabel('Topic')
    ax7.set_ylabel('Survey')
    
    plt.savefig(OUTPUT_DIR / 'summary_dashboard.png', dpi=150, bbox_inches='tight')
    print(f"  ✓ Saved: summary_dashboard.png")
    
    plt.close()

def create_readme(stats: dict, master_df: pd.DataFrame):
    """Create summary README."""
    
    readme = f"""# Federal Survey Concept Mapping - Results

## Overview

This analysis categorized {stats['total_questions']:,} questions from {stats['surveys']} federal surveys using the Census Bureau's official taxonomy.

## Key Findings

### Categorization Success
- **Successfully categorized**: {stats['successfully_categorized']:,} questions ({stats['successfully_categorized']/stats['total_questions']*100:.1f}%)
- **Needs human review**: {stats['needs_review']:,} questions ({stats['needs_review']/stats['total_questions']*100:.1f}%)

### Decision Methods
"""
    
    method_counts = master_df['decision_method'].value_counts()
    for method, count in method_counts.items():
        pct = count / stats['total_questions'] * 100
        readme += f"- **{method}**: {count:,} ({pct:.1f}%)\n"
    
    readme += f"""
### Topic Coverage
- **Total topics**: {stats['topics']}
- **Questions span**: Economic, Social, Housing, Demographic, Government

### Data Quality
- Models achieved strong agreement on most questions
- Agentic arbitration resolved ambiguous cases
- Remaining disagreements flagged for human review

## Files

### Core Datasets
- `master_dataset.csv` - Complete question-level data with final categorizations
- `survey_concept_matrix.csv` - Aggregated survey × concept counts

### Visualizations
- `summary_dashboard.png` - Overview of categorization results

### Source Data
- `../results/` - Raw model outputs
- `../comparison/` - Model agreement analysis
- `../arbitration_agentic/` - Arbitration decisions and reasoning

## Next Steps

1. Review questions flagged for human review
2. Analyze survey redundancy and consolidation opportunities
3. Identify concept coverage gaps
4. Generate stakeholder-specific reports

## Methodology

1. **Initial Categorization**: gpt-5-mini and claude-haiku-4-5 independently categorized all questions
2. **Agreement Check**: Questions with model agreement were accepted
3. **Agentic Arbitration**: Disagreements sent through 3-round feedback loop (claude-sonnet-4-5 ↔ gpt-5.2)
4. **Final Reconciliation**: Combined results with decision tracking

Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    with open(OUTPUT_DIR / 'README.md', 'w') as f:
        f.write(readme)
    
    print(f"  ✓ Saved: README.md")

def main():
    print("="*70)
    print("FINAL RECONCILIATION & SUMMARY")
    print("="*70)
    
    # Load all data
    print("\n1. Loading data...")
    initial_df = load_initial_results()
    arbitration_df = load_arbitration_results()
    questions_df = load_questions()
    print(f"   Loaded {len(initial_df):,} initial categorizations")
    if arbitration_df is not None:
        print(f"   Loaded {len(arbitration_df):,} arbitration results")
    
    # Create master dataset
    print("\n2. Reconciling categorizations...")
    master_df = reconcile_categorizations(initial_df, arbitration_df)
    
    # Merge with questions BEFORE other operations
    master_df = master_df.merge(questions_df[['id', 'question', 'primary_survey']], on='id', how='left')
    
    # Save master dataset
    master_df.to_csv(OUTPUT_DIR / 'master_dataset.csv', index=False)
    print(f"   ✓ Saved: master_dataset.csv ({len(master_df):,} rows)")
    
    # Create survey-concept matrix
    print("\n3. Creating survey-concept matrix...")
    matrix_df = create_survey_concept_matrix(master_df, questions_df)
    matrix_df.to_csv(OUTPUT_DIR / 'survey_concept_matrix.csv')
    print(f"   ✓ Saved: survey_concept_matrix.csv ({matrix_df.shape[0]} surveys × {matrix_df.shape[1]} concepts)")
    
    # Generate stats
    stats = generate_summary_stats(master_df, questions_df)
    
    # Create visualizations
    create_visualizations(master_df, questions_df, matrix_df)
    
    # Create README
    print("\n4. Creating summary README...")
    create_readme(stats, master_df)
    
    print("\n" + "="*70)
    print("RECONCILIATION COMPLETE!")
    print("="*70)
    print(f"\nAll outputs saved to: {OUTPUT_DIR}")
    print("\nKey deliverables:")
    print("  - master_dataset.csv - Final categorizations")
    print("  - survey_concept_matrix.csv - Aggregated analysis")
    print("  - summary_dashboard.png - Visual overview")
    print("  - README.md - Summary report")

if __name__ == '__main__':
    main()
