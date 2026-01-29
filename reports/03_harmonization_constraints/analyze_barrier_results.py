#!/usr/bin/env python3
"""
Compare and analyze barrier coding results between OpenAI and Claude.

Computes agreement rates, Cohen's kappa, and generates prevalence statistics
for Report 03.
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import cohen_kappa_score
from collections import Counter

# Configuration
RESULTS_DIR = Path('./output/results')
OUTPUT_DIR = Path('./output/analysis')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = (12, 8)

# Taxonomy labels for display
BARRIER_LABELS = {
    'TC': 'Temporal',
    'CC': 'Construct', 
    'PC': 'Population/Coverage',
    'RS': 'Response Scale',
    'MC': 'Mode/Context',
    'PM': 'Processing/Metadata'
}

FEASIBILITY_LABELS = {
    'F1': 'Direct recode',
    'F2': 'Statistical adjustment',
    'F3': 'Incompatible'
}


def load_results(model: str) -> pd.DataFrame:
    """Load results from JSONL file."""
    results = []
    filepath = RESULTS_DIR / f'barrier_results_{model}.jsonl'
    with open(filepath, 'r') as f:
        for line in f:
            results.append(json.loads(line))
    return pd.DataFrame(results)


def extract_level1(barrier_code: str) -> str:
    """Extract Level 1 code from barrier code (e.g., 'TC.1' -> 'TC')."""
    if pd.isna(barrier_code) or not barrier_code:
        return 'UNKNOWN'
    return barrier_code.split('.')[0].upper()


def main():
    print("="*70)
    print("BARRIER CODING COMPARISON & ANALYSIS")
    print("Report 03: Harmonization Constraints")
    print("="*70)
    
    # Load results
    print("\n1. Loading results...")
    try:
        openai_df = load_results('openai')
        claude_df = load_results('claude')
        print(f"   OpenAI: {len(openai_df)} coded pairs")
        print(f"   Claude: {len(claude_df)} coded pairs")
    except FileNotFoundError as e:
        print(f"   Error: {e}")
        print("   Run barrier_coding_pipeline.py first!")
        return
    
    # Merge on pair_id
    print("\n2. Merging results...")
    merged = openai_df.merge(
        claude_df, 
        on='pair_id', 
        suffixes=('_openai', '_claude')
    )
    print(f"   Merged: {len(merged)} pairs")
    
    # Extract Level 1 codes
    merged['barrier_l1_openai'] = merged['primary_barrier_openai'].apply(extract_level1)
    merged['barrier_l1_claude'] = merged['primary_barrier_claude'].apply(extract_level1)
    
    # === AGREEMENT ANALYSIS ===
    print("\n" + "="*70)
    print("AGREEMENT ANALYSIS")
    print("="*70)
    
    # Level 1 barrier agreement
    l1_match = (merged['barrier_l1_openai'] == merged['barrier_l1_claude']).sum()
    l1_agreement = l1_match / len(merged) * 100
    print(f"\nLevel 1 Barrier Agreement: {l1_agreement:.1f}% ({l1_match}/{len(merged)})")
    
    # Full barrier code agreement (with subtype)
    full_match = (merged['primary_barrier_openai'] == merged['primary_barrier_claude']).sum()
    full_agreement = full_match / len(merged) * 100
    print(f"Full Barrier Code Agreement: {full_agreement:.1f}% ({full_match}/{len(merged)})")
    
    # Feasibility agreement
    feas_match = (merged['feasibility_openai'] == merged['feasibility_claude']).sum()
    feas_agreement = feas_match / len(merged) * 100
    print(f"Feasibility Agreement: {feas_agreement:.1f}% ({feas_match}/{len(merged)})")
    
    # Cohen's Kappa
    try:
        kappa_l1 = cohen_kappa_score(merged['barrier_l1_openai'], merged['barrier_l1_claude'])
        print(f"\nCohen's Kappa (Level 1 Barriers): {kappa_l1:.3f}")
    except:
        print("\nCould not compute Kappa for Level 1 barriers")
    
    try:
        kappa_feas = cohen_kappa_score(merged['feasibility_openai'], merged['feasibility_claude'])
        print(f"Cohen's Kappa (Feasibility): {kappa_feas:.3f}")
    except:
        print("Could not compute Kappa for Feasibility")
    
    # === PREVALENCE STATISTICS ===
    print("\n" + "="*70)
    print("BARRIER PREVALENCE (Level 1)")
    print("="*70)
    
    # Combined prevalence (using Claude as primary, following Report 02 convention)
    l1_counts = merged['barrier_l1_claude'].value_counts()
    total = len(merged)
    
    print(f"\n{'Barrier Type':<25} {'Count':>8} {'Percent':>10}")
    print("-" * 45)
    for code, count in l1_counts.items():
        label = BARRIER_LABELS.get(code, code)
        pct = count / total * 100
        print(f"{code} ({label})"[:25].ljust(25) + f"{count:>8}" + f"{pct:>9.1f}%")
    
    # === FEASIBILITY DISTRIBUTION ===
    print("\n" + "="*70)
    print("FEASIBILITY DISTRIBUTION")
    print("="*70)
    
    feas_counts = merged['feasibility_claude'].value_counts()
    
    print(f"\n{'Feasibility':<25} {'Count':>8} {'Percent':>10}")
    print("-" * 45)
    for code, count in feas_counts.items():
        label = FEASIBILITY_LABELS.get(code, code)
        pct = count / total * 100
        print(f"{code} ({label})"[:25].ljust(25) + f"{count:>8}" + f"{pct:>9.1f}%")
    
    # === SAVE ANALYSIS ===
    print("\n" + "="*70)
    print("SAVING OUTPUTS")
    print("="*70)
    
    # Save merged results
    merged.to_csv(OUTPUT_DIR / 'barrier_coding_merged.csv', index=False)
    print(f"   Saved: {OUTPUT_DIR / 'barrier_coding_merged.csv'}")
    
    # Save summary statistics
    summary = {
        'total_pairs': len(merged),
        'agreement': {
            'level1_barrier': l1_agreement,
            'full_barrier': full_agreement,
            'feasibility': feas_agreement
        },
        'level1_prevalence': l1_counts.to_dict(),
        'feasibility_prevalence': feas_counts.to_dict()
    }
    
    with open(OUTPUT_DIR / 'barrier_coding_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"   Saved: {OUTPUT_DIR / 'barrier_coding_summary.json'}")
    
    # === VISUALIZATIONS ===
    print("\n   Generating visualizations...")
    
    # Bar plot of barrier prevalence
    fig, ax = plt.subplots(figsize=(10, 6))
    codes = list(l1_counts.index)
    counts = list(l1_counts.values)
    colors = plt.cm.Set2(np.linspace(0, 1, len(codes)))
    
    bars = ax.bar(codes, counts, color=colors)
    ax.set_xlabel('Barrier Type')
    ax.set_ylabel('Count')
    ax.set_title('Harmonization Barrier Type Prevalence')
    
    # Add value labels
    for bar, count in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
                str(count), ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'barrier_prevalence.png', dpi=150)
    print(f"   Saved: {OUTPUT_DIR / 'barrier_prevalence.png'}")
    plt.close()
    
    # Feasibility pie chart
    fig, ax = plt.subplots(figsize=(8, 8))
    feas_labels = [f"{k} ({FEASIBILITY_LABELS.get(k, k)})" for k in feas_counts.index]
    ax.pie(feas_counts.values, labels=feas_labels, autopct='%1.1f%%',
           colors=plt.cm.RdYlGn(np.linspace(0.2, 0.8, len(feas_counts))))
    ax.set_title('Feasibility Classification Distribution')
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'feasibility_distribution.png', dpi=150)
    print(f"   Saved: {OUTPUT_DIR / 'feasibility_distribution.png'}")
    plt.close()
    
    print("\n" + "="*70)
    print("ANALYSIS COMPLETE!")
    print("="*70)


if __name__ == '__main__':
    main()
