#!/usr/bin/env python3
"""
Generate Figure 2: Model Agreement Visualization
Bar chart showing agreement metrics and Cohen's Kappa.

Reads from: output/comparison/agreement_summary.csv
Saves to: output/visualizations/figure_02_model_agreement.png
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Configuration
COMPARISON_DIR = Path('../output/comparison')
VIZ_DIR = Path('../output/visualizations')
VIZ_DIR.mkdir(parents=True, exist_ok=True)

# Set style
sns.set_style('whitegrid')
plt.rcParams['figure.facecolor'] = 'white'


def load_agreement_data():
    """Load agreement metrics from comparison analysis."""
    summary_file = COMPARISON_DIR / 'agreement_summary.csv'
    
    if not summary_file.exists():
        raise FileNotFoundError(f"Agreement summary not found: {summary_file}")
    
    df = pd.read_csv(summary_file)
    
    # Convert to dict for easier access
    metrics = dict(zip(df['Metric'], df['Value']))
    
    return {
        'topic_agreement': metrics['Topic Agreement %'],
        'subtopic_agreement': metrics['Subtopic Agreement %'],
        'kappa_topics': metrics["Cohen's Kappa (Topics)"],
        'kappa_subtopics': metrics["Cohen's Kappa (Subtopics)"],
    }


def create_figure(metrics):
    """Create the agreement visualization figure."""
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Extract values
    topic_pct = metrics['topic_agreement']
    subtopic_pct = metrics['subtopic_agreement']
    kappa_topic = metrics['kappa_topics']
    kappa_subtopic = metrics['kappa_subtopics']
    
    # Left plot: Agreement Rates
    categories = ['Topic\nAgreement', 'Subtopic\nAgreement']
    values = [topic_pct, subtopic_pct]
    colors = ['#4CAF50', '#2196F3']
    
    bars1 = ax1.bar(categories, values, color=colors, alpha=0.8, edgecolor='black', linewidth=2)
    
    # Add value labels on bars
    for bar, val in zip(bars1, values):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 1,
                 f'{val:.1f}%',
                 ha='center', va='bottom', fontsize=14, fontweight='bold')
    
    # Add reference line at 100%
    ax1.axhline(y=100, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    
    ax1.set_ylabel('Agreement Rate (%)', fontsize=13, fontweight='bold')
    ax1.set_title('Model Agreement Rates\n(GPT-5-mini vs Claude Haiku 4.5)', 
                  fontsize=14, fontweight='bold', pad=20)
    ax1.set_ylim(0, 105)
    ax1.grid(axis='y', alpha=0.3)
    
    # Right plot: Cohen's Kappa
    categories2 = [f'Topics\n(κ = {kappa_topic:.3f})', f'Subtopics\n(κ = {kappa_subtopic:.3f})']
    kappa_values = [kappa_topic, kappa_subtopic]
    colors2 = ['#4CAF50', '#2196F3']
    
    bars2 = ax2.bar(categories2, kappa_values, color=colors2, alpha=0.8, edgecolor='black', linewidth=2)
    
    # Add value labels on bars
    for bar, val in zip(bars2, kappa_values):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                 f'{val:.3f}',
                 ha='center', va='bottom', fontsize=14, fontweight='bold')
    
    # Add interpretation zones
    ax2.axhspan(0.81, 1.0, alpha=0.1, color='green', label='Almost Perfect (>0.80)')
    ax2.axhspan(0.61, 0.80, alpha=0.1, color='yellow', label='Substantial (0.61-0.80)')
    ax2.axhspan(0.41, 0.60, alpha=0.1, color='orange', label='Moderate (0.41-0.60)')
    
    # Add horizontal lines for thresholds
    ax2.axhline(y=0.80, color='green', linestyle='--', linewidth=1.5, alpha=0.7)
    ax2.axhline(y=0.60, color='orange', linestyle='--', linewidth=1.5, alpha=0.7)
    
    ax2.set_ylabel('Cohen\'s Kappa (κ)', fontsize=13, fontweight='bold')
    ax2.set_title('Inter-Rater Reliability\n(Beyond-Chance Agreement)', 
                  fontsize=14, fontweight='bold', pad=20)
    ax2.set_ylim(0, 1.0)
    ax2.legend(loc='lower right', fontsize=9, framealpha=0.9)
    ax2.grid(axis='y', alpha=0.3)
    
    # Add interpretation text based on actual values
    if kappa_topic > 0.80:
        ax2.text(0.5, 0.5, '"Almost Perfect"\nAgreement',
                 ha='center', va='center', fontsize=10, style='italic',
                 bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))
    
    if 0.60 < kappa_subtopic <= 0.80:
        ax2.text(1.5, 0.35, '"Substantial"\nAgreement',
                 ha='center', va='center', fontsize=10, style='italic',
                 bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.5))
    
    # Overall title
    fig.suptitle('Dual-Model Agreement Analysis: GPT-5-mini vs Claude Haiku 4.5',
                 fontsize=16, fontweight='bold', y=1.00)
    
    # Add subtitle
    fig.text(0.5, 0.02, 
             'Both models categorized questions independently. High agreement indicates consistent semantic understanding across architectures.',
             ha='center', fontsize=11, style='italic', wrap=True)
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.98])
    
    return fig


def main():
    print("="*70)
    print("FIGURE 2: MODEL AGREEMENT VISUALIZATION")
    print("="*70)
    
    # Load data
    print("\nLoading agreement metrics...")
    metrics = load_agreement_data()
    
    print(f"  Topic Agreement: {metrics['topic_agreement']:.1f}%")
    print(f"  Subtopic Agreement: {metrics['subtopic_agreement']:.1f}%")
    print(f"  Cohen's Kappa (Topics): {metrics['kappa_topics']:.3f}")
    print(f"  Cohen's Kappa (Subtopics): {metrics['kappa_subtopics']:.3f}")
    
    # Create figure
    print("\nGenerating figure...")
    fig = create_figure(metrics)
    
    # Save
    output_path = VIZ_DIR / 'figure_02_model_agreement.png'
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"\n✓ Saved: {output_path}")
    print("\n" + "="*70)


if __name__ == '__main__':
    main()
