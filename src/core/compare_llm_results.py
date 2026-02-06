#!/usr/bin/env python3
"""
Compare LLM categorization results between OpenAI and Claude.

Analyzes agreement, confidence correlations, and systematic differences.
Generates tables, statistics, and visualizations.
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import cohen_kappa_score, confusion_matrix
from collections import Counter

# Configuration
RESULTS_DIR = Path('../output/results')
OUTPUT_DIR = Path('../output/comparison')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = (14, 10)

def load_results(model: str) -> pd.DataFrame:
    """Load results from JSONL file."""
    results = []
    with open(RESULTS_DIR / f'results_{model}.jsonl', 'r') as f:
        for line in f:
            results.append(json.loads(line))
    return pd.DataFrame(results)

def main():
    print("="*70)
    print("LLM CATEGORIZATION COMPARISON")
    print("="*70)
    
    # Load results
    print("\n1. Loading results...")
    openai_df = load_results('openai')
    claude_df = load_results('claude')
    print(f"   OpenAI: {len(openai_df)} categorizations")
    print(f"   Claude: {len(claude_df)} categorizations")
    
    # Merge on question ID
    print("\n2. Merging results...")
    merged = openai_df.merge(
        claude_df, 
        on='id', 
        suffixes=('_openai', '_claude')
    )
    print(f"   Merged: {len(merged)} questions")
    
    # Filter out any None values
    original_count = len(merged)
    merged = merged[
        merged['primary_topic_openai'].notna() & 
        merged['primary_topic_claude'].notna() &
        merged['primary_subtopic_openai'].notna() & 
        merged['primary_subtopic_claude'].notna()
    ].copy()
    
    if len(merged) < original_count:
        print(f"   Filtered out {original_count - len(merged)} rows with missing values")
        print(f"   Analyzing: {len(merged)} questions")
    
    # === AGREEMENT ANALYSIS ===
    print("\n" + "="*70)
    print("AGREEMENT ANALYSIS")
    print("="*70)
    
    # Topic agreement
    topic_match = (merged['primary_topic_openai'] == merged['primary_topic_claude']).sum()
    topic_agreement = topic_match / len(merged) * 100
    print(f"\nPrimary Topic Agreement: {topic_agreement:.2f}% ({topic_match}/{len(merged)})")
    
    # Subtopic agreement
    subtopic_match = (merged['primary_subtopic_openai'] == merged['primary_subtopic_claude']).sum()
    subtopic_agreement = subtopic_match / len(merged) * 100
    print(f"Primary Subtopic Agreement: {subtopic_agreement:.2f}% ({subtopic_match}/{len(merged)})")
    
    # Cohen's Kappa for topics
    kappa_topic = cohen_kappa_score(merged['primary_topic_openai'], merged['primary_topic_claude'])
    print(f"\nCohen's Kappa (Topics): {kappa_topic:.3f}")
    
    # Cohen's Kappa for subtopics
    kappa_subtopic = cohen_kappa_score(merged['primary_subtopic_openai'], merged['primary_subtopic_claude'])
    print(f"Cohen's Kappa (Subtopics): {kappa_subtopic:.3f}")
    
    # === CONFIDENCE ANALYSIS ===
    print("\n" + "="*70)
    print("CONFIDENCE ANALYSIS")
    print("="*70)
    
    print(f"\nOpenAI Confidence:")
    print(f"  Mean:   {merged['confidence_openai'].mean():.3f}")
    print(f"  Median: {merged['confidence_openai'].median():.3f}")
    print(f"  Std:    {merged['confidence_openai'].std():.3f}")
    print(f"  Min:    {merged['confidence_openai'].min():.3f}")
    print(f"  Max:    {merged['confidence_openai'].max():.3f}")
    
    print(f"\nClaude Confidence:")
    print(f"  Mean:   {merged['confidence_claude'].mean():.3f}")
    print(f"  Median: {merged['confidence_claude'].median():.3f}")
    print(f"  Std:    {merged['confidence_claude'].std():.3f}")
    print(f"  Min:    {merged['confidence_claude'].min():.3f}")
    print(f"  Max:    {merged['confidence_claude'].max():.3f}")
    
    # Confidence correlation
    correlation = merged['confidence_openai'].corr(merged['confidence_claude'])
    print(f"\nConfidence Correlation: {correlation:.3f}")
    
    # === TOPIC DISTRIBUTION ===
    print("\n" + "="*70)
    print("TOPIC DISTRIBUTION")
    print("="*70)
    
    print("\nOpenAI Topic Distribution:")
    openai_topics = merged['primary_topic_openai'].value_counts()
    for topic, count in openai_topics.items():
        print(f"  {topic}: {count} ({count/len(merged)*100:.1f}%)")
    
    print("\nClaude Topic Distribution:")
    claude_topics = merged['primary_topic_claude'].value_counts()
    for topic, count in claude_topics.items():
        print(f"  {topic}: {count} ({count/len(merged)*100:.1f}%)")
    
    # === DISAGREEMENT ANALYSIS ===
    print("\n" + "="*70)
    print("DISAGREEMENT ANALYSIS")
    print("="*70)
    
    disagreements = merged[merged['primary_topic_openai'] != merged['primary_topic_claude']].copy()
    print(f"\nTotal Disagreements: {len(disagreements)} ({len(disagreements)/len(merged)*100:.1f}%)")
    
    if len(disagreements) > 0:
        print("\nTop 10 Disagreement Patterns:")
        disagreement_patterns = disagreements.groupby(['primary_topic_openai', 'primary_topic_claude']).size()
        disagreement_patterns = disagreement_patterns.sort_values(ascending=False).head(10)
        for (openai_topic, claude_topic), count in disagreement_patterns.items():
            print(f"  OpenAI:{openai_topic} vs Claude:{claude_topic} - {count} times")
    
    # === SAVE RESULTS ===
    print("\n" + "="*70)
    print("SAVING RESULTS")
    print("="*70)
    
    # Agreement summary
    agreement_summary = pd.DataFrame({
        'Metric': [
            'Topic Agreement %',
            'Subtopic Agreement %',
            "Cohen's Kappa (Topics)",
            "Cohen's Kappa (Subtopics)",
            'Confidence Correlation'
        ],
        'Value': [
            topic_agreement,
            subtopic_agreement,
            kappa_topic,
            kappa_subtopic,
            correlation
        ]
    })
    agreement_summary.to_csv(OUTPUT_DIR / 'agreement_summary.csv', index=False)
    print(f"   Saved: agreement_summary.csv")
    
    # Confidence statistics
    confidence_stats = pd.DataFrame({
        'Model': ['OpenAI', 'Claude'],
        'Mean': [merged['confidence_openai'].mean(), merged['confidence_claude'].mean()],
        'Median': [merged['confidence_openai'].median(), merged['confidence_claude'].median()],
        'Std': [merged['confidence_openai'].std(), merged['confidence_claude'].std()],
        'Min': [merged['confidence_openai'].min(), merged['confidence_claude'].min()],
        'Max': [merged['confidence_openai'].max(), merged['confidence_claude'].max()]
    })
    confidence_stats.to_csv(OUTPUT_DIR / 'confidence_stats.csv', index=False)
    print(f"   Saved: confidence_stats.csv")
    
    # Topic distributions
    topic_dist = pd.DataFrame({
        'Topic': openai_topics.index,
        'OpenAI_Count': openai_topics.values,
        'OpenAI_Percent': openai_topics.values / len(merged) * 100,
        'Claude_Count': [claude_topics.get(t, 0) for t in openai_topics.index],
        'Claude_Percent': [claude_topics.get(t, 0) / len(merged) * 100 for t in openai_topics.index]
    })
    topic_dist.to_csv(OUTPUT_DIR / 'topic_distribution.csv', index=False)
    print(f"   Saved: topic_distribution.csv")
    
    # Disagreements detail
    if len(disagreements) > 0:
        disagreements_export = disagreements[[
            'id', 
            'primary_topic_openai', 'primary_subtopic_openai', 'confidence_openai',
            'primary_topic_claude', 'primary_subtopic_claude', 'confidence_claude'
        ]].copy()
        disagreements_export.to_csv(OUTPUT_DIR / 'disagreements.csv', index=False)
        print(f"   Saved: disagreements.csv ({len(disagreements)} rows)")
    
    # Full comparison
    merged.to_csv(OUTPUT_DIR / 'full_comparison.csv', index=False)
    print(f"   Saved: full_comparison.csv")
    
    # === GENERATE VISUALIZATIONS ===
    print("\n" + "="*70)
    print("GENERATING VISUALIZATIONS")
    print("="*70)
    
    # Figure 1: Agreement metrics
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Topic confusion matrix
    topics = sorted(set(merged['primary_topic_openai']) | set(merged['primary_topic_claude']))
    cm = confusion_matrix(
        merged['primary_topic_openai'], 
        merged['primary_topic_claude'],
        labels=topics
    )
    
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=topics, yticklabels=topics, ax=axes[0, 0])
    axes[0, 0].set_title('Topic Confusion Matrix')
    axes[0, 0].set_xlabel('Claude')
    axes[0, 0].set_ylabel('OpenAI')
    
    # Confidence scatter
    axes[0, 1].scatter(merged['confidence_openai'], merged['confidence_claude'], 
                      alpha=0.3, s=10)
    axes[0, 1].plot([0, 1], [0, 1], 'r--', alpha=0.5)
    axes[0, 1].set_xlabel('OpenAI Confidence')
    axes[0, 1].set_ylabel('Claude Confidence')
    axes[0, 1].set_title(f'Confidence Correlation (r={correlation:.3f})')
    axes[0, 1].grid(True, alpha=0.3)
    
    # Confidence distributions
    axes[1, 0].hist(merged['confidence_openai'], bins=50, alpha=0.5, label='OpenAI', edgecolor='black')
    axes[1, 0].hist(merged['confidence_claude'], bins=50, alpha=0.5, label='Claude', edgecolor='black')
    axes[1, 0].set_xlabel('Confidence')
    axes[1, 0].set_ylabel('Frequency')
    axes[1, 0].set_title('Confidence Distributions')
    axes[1, 0].legend()
    
    # Topic distribution comparison
    topic_comparison = pd.DataFrame({
        'Topic': openai_topics.index,
        'OpenAI': openai_topics.values,
        'Claude': [claude_topics.get(t, 0) for t in openai_topics.index]
    })
    
    x = np.arange(len(topic_comparison))
    width = 0.35
    axes[1, 1].bar(x - width/2, topic_comparison['OpenAI'], width, label='OpenAI', alpha=0.8)
    axes[1, 1].bar(x + width/2, topic_comparison['Claude'], width, label='Claude', alpha=0.8)
    axes[1, 1].set_xlabel('Topic')
    axes[1, 1].set_ylabel('Count')
    axes[1, 1].set_title('Topic Distribution Comparison')
    axes[1, 1].set_xticks(x)
    axes[1, 1].set_xticklabels(topic_comparison['Topic'], rotation=45, ha='right')
    axes[1, 1].legend()
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'comparison_overview.png', dpi=150, bbox_inches='tight')
    print(f"   Saved: comparison_overview.png")
    
    # Figure 2: Agreement by confidence
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Agreement vs OpenAI confidence
    bins = np.linspace(0, 1, 11)
    merged['confidence_bin_openai'] = pd.cut(merged['confidence_openai'], bins)
    agreement_by_conf = merged.groupby('confidence_bin_openai').apply(
        lambda x: (x['primary_topic_openai'] == x['primary_topic_claude']).mean() * 100
    )
    
    bin_centers = [(b.left + b.right) / 2 for b in agreement_by_conf.index]
    axes[0].plot(bin_centers, agreement_by_conf.values, 'o-', linewidth=2, markersize=8)
    axes[0].set_xlabel('OpenAI Confidence')
    axes[0].set_ylabel('Agreement Rate (%)')
    axes[0].set_title('Agreement vs OpenAI Confidence')
    axes[0].grid(True, alpha=0.3)
    axes[0].set_ylim([0, 105])
    
    # Agreement vs Claude confidence
    merged['confidence_bin_claude'] = pd.cut(merged['confidence_claude'], bins)
    agreement_by_conf_claude = merged.groupby('confidence_bin_claude').apply(
        lambda x: (x['primary_topic_openai'] == x['primary_topic_claude']).mean() * 100
    )
    
    bin_centers_claude = [(b.left + b.right) / 2 for b in agreement_by_conf_claude.index]
    axes[1].plot(bin_centers_claude, agreement_by_conf_claude.values, 'o-', 
                linewidth=2, markersize=8, color='orange')
    axes[1].set_xlabel('Claude Confidence')
    axes[1].set_ylabel('Agreement Rate (%)')
    axes[1].set_title('Agreement vs Claude Confidence')
    axes[1].grid(True, alpha=0.3)
    axes[1].set_ylim([0, 105])
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'agreement_by_confidence.png', dpi=150, bbox_inches='tight')
    print(f"   Saved: agreement_by_confidence.png")
    
    print("\n" + "="*70)
    print("COMPARISON COMPLETE!")
    print("="*70)
    print(f"\nResults saved to: {OUTPUT_DIR}")
    print("\nKey findings:")
    print(f"  - Topic agreement: {topic_agreement:.1f}%")
    print(f"  - Subtopic agreement: {subtopic_agreement:.1f}%")
    print(f"  - Confidence correlation: {correlation:.3f}")
    print(f"  - Disagreements: {len(disagreements)} cases")

if __name__ == '__main__':
    main()
