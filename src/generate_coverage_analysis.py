#!/usr/bin/env python3
"""
Generate coverage analysis visualizations.

1. Beeswarm plot - Distribution of question counts across concepts
2. Diverging bar charts - Top 10 vs Bottom 10 for each major topic
3. Long tail analysis - Orphaned and under-sampled concepts
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Configuration
FINAL_DIR = Path('../output/final')
VIZ_DIR = Path('../output/visualizations')
VIZ_DIR.mkdir(parents=True, exist_ok=True)

sns.set_style('whitegrid')
plt.rcParams['figure.facecolor'] = 'white'

def load_data():
    """Load master dataset."""
    master = pd.read_csv(FINAL_DIR / 'master_dataset.csv')
    return master

def load_taxonomy():
    """Load full taxonomy to find orphaned concepts."""
    import json
    taxonomy_path = Path('../data/raw/census_survey_explorer_taxonomy.json')
    with open(taxonomy_path, 'r') as f:
        data = json.load(f)
    
    # Flatten to topic.subtopic
    all_concepts = []
    for topic, subtopics in data['taxonomy'].items():
        for subtopic in subtopics:
            all_concepts.append(f"{topic}.{subtopic}")
    
    return all_concepts

def viz_beeswarm_distribution(master_df):
    """
    Beeswarm plot showing distribution of question counts across concepts.
    """
    print("\n1. BEESWARM PLOT - Question Count Distribution")
    print("="*70)
    
    # Get concept counts (filter out Unknown)
    valid = master_df[
        (master_df['final_topic'].notna()) & 
        (master_df['final_topic'] != 'Unknown')
    ].copy()
    valid['concept'] = valid['final_topic'] + '.' + valid['final_subtopic']
    concept_counts = valid['concept'].value_counts()
    
    # Create dataframe for plotting
    plot_data = pd.DataFrame({
        'concept': concept_counts.index,
        'count': concept_counts.values
    })
    
    # Add topic for coloring
    plot_data['topic'] = plot_data['concept'].str.split('.').str[0]
    
    print(f"   Total concepts with questions: {len(plot_data)}")
    print(f"   Mean questions per concept: {plot_data['count'].mean():.1f}")
    print(f"   Median questions per concept: {plot_data['count'].median():.0f}")
    
    # Create beeswarm
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Use stripplot for beeswarm effect
    sns.stripplot(
        data=plot_data,
        x='topic',
        y='count',
        hue='topic',
        size=8,
        alpha=0.6,
        jitter=True,
        ax=ax,
        legend=False
    )
    
    # Add mean lines for each topic
    for i, topic in enumerate(sorted(plot_data['topic'].unique())):
        topic_mean = plot_data[plot_data['topic'] == topic]['count'].mean()
        ax.plot([i-0.4, i+0.4], [topic_mean, topic_mean], 
                color='red', linestyle='--', linewidth=2, alpha=0.7)
    
    ax.set_xlabel('Census Topic', fontsize=14, fontweight='bold')
    ax.set_ylabel('Question Count', fontsize=14, fontweight='bold')
    ax.set_title('Distribution of Question Coverage Across Census Concepts\n(Each dot = one subtopic, red line = topic mean)', 
                 fontsize=16, fontweight='bold', pad=20)
    
    ax.grid(axis='y', alpha=0.3)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(VIZ_DIR / 'beeswarm_coverage_distribution.png', dpi=300, bbox_inches='tight')
    print(f"   ✓ Saved: beeswarm_coverage_distribution.png")
    plt.close()
    
    return plot_data

def viz_bars_by_topic(master_df):
    """
    Horizontal bar charts - ALL subtopics for each major topic, sorted by count.
    """
    print("\n2. HORIZONTAL BAR CHARTS - All Subtopics per Topic")
    print("="*70)
    
    # Get concept counts (filter out Unknown)
    valid = master_df[
        (master_df['final_topic'].notna()) & 
        (master_df['final_topic'] != 'Unknown')
    ].copy()
    valid['concept'] = valid['final_topic'] + '.' + valid['final_subtopic']
    
    topics = sorted(valid['final_topic'].unique())
    
    fig, axes = plt.subplots(3, 2, figsize=(18, 24))
    axes = axes.flatten()
    
    for idx, topic in enumerate(topics):
        if idx >= len(axes):
            break
            
        ax = axes[idx]
        
        # Get ALL subtopics for this topic
        topic_data = valid[valid['final_topic'] == topic]
        subtopic_counts = topic_data['final_subtopic'].value_counts().sort_values(ascending=True)
        
        # Color gradient from red (low) to green (high)
        colors = plt.cm.RdYlGn(np.linspace(0.2, 0.9, len(subtopic_counts)))
        
        # Plot
        bars = ax.barh(range(len(subtopic_counts)), subtopic_counts.values, 
                       color=colors, edgecolor='black', linewidth=0.5)
        
        # Format
        ax.set_yticks(range(len(subtopic_counts)))
        ax.set_yticklabels(subtopic_counts.index, fontsize=9)
        ax.set_xlabel('Question Count', fontsize=11, fontweight='bold')
        ax.set_title(f'{topic} Coverage\n({len(subtopic_counts)} subtopics)', 
                     fontsize=13, fontweight='bold')
        ax.grid(axis='x', alpha=0.3)
        
        # Add value labels
        for i, val in enumerate(subtopic_counts.values):
            ax.text(val + (max(subtopic_counts.values) * 0.02), i, f'{int(val)}', 
                   va='center', ha='left', fontsize=8, fontweight='bold')
        
        # Add mean line
        mean_val = subtopic_counts.mean()
        ax.axvline(mean_val, color='blue', linestyle='--', linewidth=2, alpha=0.5, label=f'Mean: {mean_val:.1f}')
        ax.legend(loc='lower right', fontsize=9)
        
        print(f"   {topic}: {len(subtopic_counts)} subtopics, mean={mean_val:.1f}, range={subtopic_counts.min()}-{subtopic_counts.max()}")
    
    # Hide unused subplots
    for idx in range(len(topics), len(axes)):
        axes[idx].axis('off')
    
    plt.tight_layout()
    plt.savefig(VIZ_DIR / 'horizontal_bars_all_subtopics.png', dpi=300, bbox_inches='tight')
    print(f"   ✓ Saved: horizontal_bars_all_subtopics.png")
    plt.close()

def viz_unique_orphan_table(master_df, all_taxonomy_concepts):
    """
    Table showing subtopics that appear in 0 or 1 survey (orphans and uniques).
    By major topic with counts.
    """
    print("\n3. UNIQUE & ORPHAN SUBTOPICS - Appearing in 0-1 Surveys")
    print("="*70)
    
    # Get concept counts (filter out Unknown)
    valid = master_df[
        (master_df['final_topic'].notna()) & 
        (master_df['final_topic'] != 'Unknown')
    ].copy()
    valid['concept'] = valid['final_topic'] + '.' + valid['final_subtopic']
    
    # Count which surveys each concept appears in
    concept_survey_counts = valid.groupby('concept')['primary_survey'].nunique()
    
    # Find concepts with ZERO coverage
    covered_concepts = set(concept_survey_counts.index)
    all_concepts_set = set(all_taxonomy_concepts)
    zero_coverage = sorted(list(all_concepts_set - covered_concepts))
    
    # Find concepts in only 1 survey
    one_survey = concept_survey_counts[concept_survey_counts == 1].sort_index()
    
    print(f"   Orphans (0 surveys): {len(zero_coverage)}")
    print(f"   Uniques (1 survey): {len(one_survey)}")
    print(f"   Total exclusive concepts: {len(zero_coverage) + len(one_survey)}")
    
    # Create combined dataframe
    results = []
    
    # Add orphans
    for concept in zero_coverage:
        topic, subtopic = concept.split('.')
        results.append({
            'topic': topic,
            'subtopic': subtopic,
            'survey_count': 0,
            'status': 'Orphan',
            'surveys': 'NONE'
        })
    
    # Add uniques
    for concept in one_survey.index:
        topic, subtopic = concept.split('.')
        # Find which survey has it
        survey = valid[valid['concept'] == concept]['primary_survey'].iloc[0]
        question_count = len(valid[valid['concept'] == concept])
        results.append({
            'topic': topic,
            'subtopic': subtopic,
            'survey_count': 1,
            'status': 'Unique',
            'surveys': survey,
            'questions': question_count
        })
    
    results_df = pd.DataFrame(results)
    results_df.to_csv(VIZ_DIR / 'unique_and_orphan_concepts.csv', index=False)
    print(f"   ✓ Saved: unique_and_orphan_concepts.csv")
    
    # Create visual table by topic
    fig, axes = plt.subplots(3, 2, figsize=(20, 16))
    axes = axes.flatten()
    
    topics = sorted(results_df['topic'].unique())
    
    for idx, topic in enumerate(topics):
        if idx >= len(axes):
            break
        
        ax = axes[idx]
        ax.axis('tight')
        ax.axis('off')
        
        topic_data = results_df[results_df['topic'] == topic].sort_values(['survey_count', 'subtopic'])
        
        orphans = len(topic_data[topic_data['status'] == 'Orphan'])
        uniques = len(topic_data[topic_data['status'] == 'Unique'])
        
        # Create table data
        if len(topic_data) > 0:
            # Limit to top 20 for display
            display_data = topic_data.head(20)
            
            table_data = []
            for _, row in display_data.iterrows():
                if row['status'] == 'Orphan':
                    table_data.append([row['subtopic'][:35], 'NONE', '-'])
                else:
                    survey_short = row['surveys'][:30] if len(row['surveys']) <= 30 else row['surveys'][:27] + '...'
                    table_data.append([row['subtopic'][:35], survey_short, str(int(row['questions']))])
            
            table = ax.table(
                cellText=table_data,
                colLabels=['Subtopic', 'Survey', 'Qs'],
                cellLoc='left',
                loc='center',
                colWidths=[0.5, 0.4, 0.1]
            )
            
            table.auto_set_font_size(False)
            table.set_fontsize(8)
            table.scale(1, 2)
            
            # Color orphans red, uniques yellow
            for i, row in enumerate(display_data.itertuples(), start=1):
                if row.status == 'Orphan':
                    for j in range(3):
                        table[(i, j)].set_facecolor('#ffcccc')
                else:
                    for j in range(3):
                        table[(i, j)].set_facecolor('#ffffcc')
            
            # Header styling
            for j in range(3):
                table[(0, j)].set_facecolor('#4472C4')
                table[(0, j)].set_text_props(weight='bold', color='white')
            
            title = f'{topic}\n{orphans} Orphans (red) | {uniques} Uniques (yellow)'
            if len(topic_data) > 20:
                title += f'\n(Showing 20 of {len(topic_data)})'
        else:
            title = f'{topic}\nNo orphans or uniques!'
        
        ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
        
        print(f"   {topic}: {orphans} orphans, {uniques} uniques")
    
    # Hide unused subplots
    for idx in range(len(topics), len(axes)):
        axes[idx].axis('off')
    
    plt.tight_layout()
    plt.savefig(VIZ_DIR / 'unique_orphan_tables.png', dpi=300, bbox_inches='tight')
    print(f"   ✓ Saved: unique_orphan_tables.png")
    plt.close()
    
    # Summary stats by topic
    print("\n   Summary by Topic:")
    summary = results_df.groupby('topic').agg({
        'subtopic': 'count',
        'survey_count': lambda x: (x == 0).sum()
    })
    summary.columns = ['Total', 'Orphans']
    summary['Uniques'] = results_df.groupby('topic').apply(lambda x: (x['survey_count'] == 1).sum())
    print(summary.to_string())

def main():
    print("="*70)
    print("COVERAGE ANALYSIS VISUALIZATIONS")
    print("="*70)
    
    # Load data
    print("\nLoading data...")
    master_df = load_data()
    all_concepts = load_taxonomy()
    print(f"   Master dataset: {len(master_df)} questions")
    print(f"   Full taxonomy: {len(all_concepts)} concepts")
    
    # Generate visualizations
    viz_beeswarm_distribution(master_df)
    viz_bars_by_topic(master_df)
    viz_unique_orphan_table(master_df, all_concepts)
    
    print("\n" + "="*70)
    print("COVERAGE ANALYSIS COMPLETE!")
    print("="*70)
    print(f"\nOutputs saved to: {VIZ_DIR}")
    print("\nGenerated:")
    print("  - beeswarm_coverage_distribution.png")
    print("  - horizontal_bars_all_subtopics.png")
    print("  - unique_orphan_tables.png")
    print("  - unique_and_orphan_concepts.csv")

if __name__ == '__main__':
    main()
