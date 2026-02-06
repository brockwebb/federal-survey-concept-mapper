#!/usr/bin/env python3
"""
Post-Arbitration Analysis
Report 03: Harmonization Constraints

Analyzes the final barrier coding results after opus arbitration.
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from lib.io_utils import ensure_dir

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent / 'output' / 'analysis' / 'post_arbitration'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Style settings
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")


def load_data():
    """Load pre and post arbitration data."""
    final = pd.read_csv(str(Path(__file__).parent.parent / 'output' / 'analysis' / 'confusion_analysis' / 'barrier_coding_final.csv'))
    merged = pd.read_csv(str(Path(__file__).parent.parent / 'output' / 'analysis' / 'barrier_coding_merged.csv'))

    # Add survey column based on pair_id prefix
    final['survey'] = final['pair_id'].apply(lambda x: 'CPS' if x.startswith('CPS') else 'FoodAPS')
    merged['survey'] = merged['pair_id'].apply(lambda x: 'CPS' if x.startswith('CPS') else 'FoodAPS')

    print(f"Loaded {len(final)} pairs")
    print(f"  CPS: {(final['survey'] == 'CPS').sum()}")
    print(f"  FoodAPS: {(final['survey'] == 'FoodAPS').sum()}")

    return final, merged


def report_distributions(df: pd.DataFrame, title: str = "Final"):
    """Report barrier and feasibility distributions."""
    print(f"\n{'='*60}")
    print(f"{title.upper()} DISTRIBUTIONS")
    print('='*60)

    # Barrier L1
    print(f"\nBarrier L1 Distribution:")
    barrier_counts = df['final_barrier_L1'].value_counts()
    for code, count in barrier_counts.items():
        print(f"  {code}: {count} ({100*count/len(df):.1f}%)")

    # Feasibility
    print(f"\nFeasibility Distribution:")
    feas_counts = df['final_feasibility'].value_counts()
    for code, count in feas_counts.items():
        print(f"  {code}: {count} ({100*count/len(df):.1f}%)")

    return barrier_counts, feas_counts


def breakdown_by_survey(df: pd.DataFrame):
    """Break down distributions by source survey."""
    print(f"\n{'='*60}")
    print("BREAKDOWN BY SURVEY")
    print('='*60)

    for survey in ['CPS', 'FoodAPS']:
        subset = df[df['survey'] == survey]
        print(f"\n--- {survey} ({len(subset)} pairs) ---")

        print("\nBarrier L1:")
        for code, count in subset['final_barrier_L1'].value_counts().items():
            print(f"  {code}: {count} ({100*count/len(subset):.1f}%)")

        print("\nFeasibility:")
        for code, count in subset['final_feasibility'].value_counts().items():
            print(f"  {code}: {count} ({100*count/len(subset):.1f}%)")


def create_crosstab(df: pd.DataFrame):
    """Create barrier x feasibility crosstab."""
    print(f"\n{'='*60}")
    print("BARRIER × FEASIBILITY CROSSTAB")
    print('='*60)

    # Create crosstab
    ct = pd.crosstab(
        df['final_barrier_L1'],
        df['final_feasibility'],
        margins=True,
        margins_name='Total'
    )

    # Calculate percentages
    ct_pct = pd.crosstab(
        df['final_barrier_L1'],
        df['final_feasibility'],
        normalize='all'
    ) * 100

    print("\nCounts:")
    print(ct)

    print("\nPercentages:")
    print(ct_pct.round(1))

    return ct, ct_pct


def compare_pre_post(final: pd.DataFrame, merged: pd.DataFrame):
    """Compare pre-arbitration vs post-arbitration distributions."""
    print(f"\n{'='*60}")
    print("PRE vs POST ARBITRATION COMPARISON")
    print('='*60)

    # For pre-arbitration, compute what would have been "final" based on agreement
    # Where models agreed, that's the value; where they disagreed, it was undefined

    # Barrier agreement pre-arbitration
    merged['barrier_agreed'] = merged['primary_barrier_openai'] == merged['primary_barrier_claude']
    merged['pre_barrier_L1'] = merged.apply(
        lambda r: str(r['primary_barrier_openai']).split('.')[0] if r['barrier_agreed'] else 'DISAGREED',
        axis=1
    )

    # Feasibility agreement pre-arbitration
    merged['feas_agreed'] = merged['feasibility_openai'] == merged['feasibility_claude']
    merged['pre_feasibility'] = merged.apply(
        lambda r: r['feasibility_openai'] if r['feas_agreed'] else 'DISAGREED',
        axis=1
    )

    print("\nPre-Arbitration Barrier L1 (with disagreements marked):")
    for code, count in merged['pre_barrier_L1'].value_counts().items():
        print(f"  {code}: {count} ({100*count/len(merged):.1f}%)")

    print("\nPost-Arbitration Barrier L1:")
    for code, count in final['final_barrier_L1'].value_counts().items():
        print(f"  {code}: {count} ({100*count/len(final):.1f}%)")

    # Calculate how many disagreements were resolved to each category
    disagreed_pairs = merged[~merged['barrier_agreed']]['pair_id'].tolist()
    resolved = final[final['pair_id'].isin(disagreed_pairs)]

    print(f"\nResolution of {len(resolved)} barrier disagreements:")
    for code, count in resolved['final_barrier_L1'].value_counts().items():
        print(f"  -> {code}: {count} ({100*count/len(resolved):.1f}%)")

    return merged


def analyze_corrections(final: pd.DataFrame):
    """Analyze which barrier types opus corrected most."""
    print(f"\n{'='*60}")
    print("ARBITRATION CORRECTIONS ANALYSIS")
    print('='*60)

    # Only look at arbitrated pairs
    arbitrated = final[final['arbitration_source'].notna()].copy()

    if len(arbitrated) == 0:
        print("No arbitrated pairs found.")
        return None

    print(f"\nTotal arbitrated pairs: {len(arbitrated)}")

    # Where did models disagree and what was the resolution?
    # Reconstruct what each model said
    arbitrated['openai_L1'] = arbitrated['primary_barrier_openai'].apply(
        lambda x: str(x).split('.')[0] if pd.notna(x) else 'UNKNOWN'
    )
    arbitrated['claude_L1'] = arbitrated['primary_barrier_claude'].apply(
        lambda x: str(x).split('.')[0] if pd.notna(x) else 'UNKNOWN'
    )

    # Correction patterns
    print("\nArbitration source distribution:")
    for source, count in arbitrated['arbitration_source'].value_counts().items():
        print(f"  {source}: {count} ({100*count/len(arbitrated):.1f}%)")

    # By barrier type - which categories had most corrections?
    print("\nFinal barrier types after arbitration:")
    for code, count in arbitrated['final_barrier_L1'].value_counts().items():
        print(f"  {code}: {count} ({100*count/len(arbitrated):.1f}%)")

    # Correction matrix: what did models say vs what opus decided
    print("\nCorrection patterns (OpenAI L1 -> Final L1):")
    openai_corrections = pd.crosstab(
        arbitrated['openai_L1'],
        arbitrated['final_barrier_L1'],
        margins=True,
        margins_name='Total'
    )
    print(openai_corrections)

    print("\nCorrection patterns (Claude L1 -> Final L1):")
    claude_corrections = pd.crosstab(
        arbitrated['claude_L1'],
        arbitrated['final_barrier_L1'],
        margins=True,
        margins_name='Total'
    )
    print(claude_corrections)

    # Where opus chose synthesis (neither model)
    synthesis = arbitrated[arbitrated['arbitration_source'] == 'synthesis']
    if len(synthesis) > 0:
        print(f"\nSynthesis cases ({len(synthesis)} pairs) - opus created new coding:")
        for code, count in synthesis['final_barrier_L1'].value_counts().items():
            print(f"  {code}: {count}")

    return arbitrated


def create_visualizations(final: pd.DataFrame, ct: pd.DataFrame, arbitrated: pd.DataFrame):
    """Create and save visualizations."""
    print(f"\n{'='*60}")
    print("CREATING VISUALIZATIONS")
    print('='*60)

    # 1. Barrier L1 distribution by survey
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Overall barrier distribution
    barrier_counts = final['final_barrier_L1'].value_counts()
    colors = sns.color_palette("husl", len(barrier_counts))
    axes[0].pie(barrier_counts.values, labels=barrier_counts.index, autopct='%1.1f%%',
                colors=colors, startangle=90)
    axes[0].set_title('Final Barrier Type Distribution (L1)', fontsize=12, fontweight='bold')

    # By survey
    survey_barrier = final.groupby(['survey', 'final_barrier_L1']).size().unstack(fill_value=0)
    survey_barrier.plot(kind='bar', ax=axes[1], width=0.8)
    axes[1].set_title('Barrier Types by Survey', fontsize=12, fontweight='bold')
    axes[1].set_xlabel('Survey')
    axes[1].set_ylabel('Count')
    axes[1].legend(title='Barrier L1', bbox_to_anchor=(1.02, 1), loc='upper left')
    axes[1].tick_params(axis='x', rotation=0)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'barrier_distribution.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: barrier_distribution.png")

    # 2. Feasibility distribution
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    feas_counts = final['final_feasibility'].value_counts().sort_index()
    feas_colors = {'F1': '#2ecc71', 'F2': '#f39c12', 'F3': '#e74c3c'}
    colors = [feas_colors.get(f, '#95a5a6') for f in feas_counts.index]

    axes[0].bar(feas_counts.index, feas_counts.values, color=colors)
    axes[0].set_title('Feasibility Distribution', fontsize=12, fontweight='bold')
    axes[0].set_xlabel('Feasibility Code')
    axes[0].set_ylabel('Count')

    # Add percentage labels
    for i, (code, count) in enumerate(feas_counts.items()):
        axes[0].text(i, count + 10, f'{100*count/len(final):.1f}%', ha='center', fontsize=10)

    # Feasibility by survey
    survey_feas = final.groupby(['survey', 'final_feasibility']).size().unstack(fill_value=0)
    survey_feas.plot(kind='bar', ax=axes[1], color=[feas_colors.get(c, '#95a5a6') for c in survey_feas.columns], width=0.8)
    axes[1].set_title('Feasibility by Survey', fontsize=12, fontweight='bold')
    axes[1].set_xlabel('Survey')
    axes[1].set_ylabel('Count')
    axes[1].legend(title='Feasibility')
    axes[1].tick_params(axis='x', rotation=0)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'feasibility_distribution.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: feasibility_distribution.png")

    # 3. Barrier x Feasibility heatmap
    fig, ax = plt.subplots(figsize=(10, 6))

    # Remove 'Total' row/col for heatmap
    ct_clean = ct.drop('Total', axis=0).drop('Total', axis=1)

    sns.heatmap(ct_clean, annot=True, fmt='d', cmap='YlOrRd', ax=ax,
                cbar_kws={'label': 'Count'})
    ax.set_title('Barrier × Feasibility Matrix', fontsize=12, fontweight='bold')
    ax.set_xlabel('Feasibility')
    ax.set_ylabel('Barrier L1')

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'barrier_feasibility_heatmap.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: barrier_feasibility_heatmap.png")

    # 4. Arbitration source breakdown
    if arbitrated is not None and len(arbitrated) > 0:
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))

        # Source distribution
        source_counts = arbitrated['arbitration_source'].value_counts()
        source_colors = {'model_a': '#3498db', 'model_b': '#9b59b6', 'synthesis': '#1abc9c'}
        colors = [source_colors.get(s, '#95a5a6') for s in source_counts.index]

        axes[0].pie(source_counts.values, labels=source_counts.index, autopct='%1.1f%%',
                    colors=colors, startangle=90)
        axes[0].set_title('Arbitration Sources\n(model_a=GPT-4o-mini, model_b=Claude-Haiku)',
                         fontsize=11, fontweight='bold')

        # Arbitrated barrier outcomes
        arb_barrier = arbitrated['final_barrier_L1'].value_counts()
        axes[1].barh(arb_barrier.index, arb_barrier.values, color=sns.color_palette("husl", len(arb_barrier)))
        axes[1].set_title('Arbitrated Pairs: Final Barrier Types', fontsize=12, fontweight='bold')
        axes[1].set_xlabel('Count')

        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / 'arbitration_analysis.png', dpi=150, bbox_inches='tight')
        plt.close()
        print(f"  Saved: arbitration_analysis.png")


def save_summary_stats(final: pd.DataFrame, merged: pd.DataFrame, ct: pd.DataFrame):
    """Save summary statistics to JSON."""

    summary = {
        'total_pairs': len(final),
        'surveys': {
            'CPS': int((final['survey'] == 'CPS').sum()),
            'FoodAPS': int((final['survey'] == 'FoodAPS').sum())
        },
        'barrier_L1_distribution': final['final_barrier_L1'].value_counts().to_dict(),
        'feasibility_distribution': final['final_feasibility'].value_counts().to_dict(),
        'arbitration': {
            'total_arbitrated': int(final['arbitration_source'].notna().sum()),
            'agreed_pairs': int(final['arbitration_source'].isna().sum()),
            'source_distribution': final['arbitration_source'].value_counts().to_dict()
        },
        'by_survey': {}
    }

    for survey in ['CPS', 'FoodAPS']:
        subset = final[final['survey'] == survey]
        summary['by_survey'][survey] = {
            'count': len(subset),
            'barrier_L1': subset['final_barrier_L1'].value_counts().to_dict(),
            'feasibility': subset['final_feasibility'].value_counts().to_dict()
        }

    # Crosstab as nested dict
    ct_clean = ct.drop('Total', axis=0).drop('Total', axis=1)
    summary['barrier_feasibility_crosstab'] = ct_clean.to_dict()

    output_file = OUTPUT_DIR / 'summary_stats.json'
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"\nSaved: {output_file}")

    return summary


def main():
    print("="*60)
    print("POST-ARBITRATION ANALYSIS")
    print("Report 03: Harmonization Constraints")
    print("="*60)

    # Load data
    final, merged = load_data()

    # Report distributions
    barrier_counts, feas_counts = report_distributions(final)

    # Breakdown by survey
    breakdown_by_survey(final)

    # Crosstab
    ct, ct_pct = create_crosstab(final)

    # Pre vs post comparison
    merged_with_pre = compare_pre_post(final, merged)

    # Correction analysis
    arbitrated = analyze_corrections(final)

    # Visualizations
    create_visualizations(final, ct, arbitrated)

    # Save summary
    summary = save_summary_stats(final, merged, ct)

    print("\n" + "="*60)
    print("ANALYSIS COMPLETE")
    print(f"Outputs saved to: {OUTPUT_DIR}")
    print("="*60)


if __name__ == "__main__":
    main()
