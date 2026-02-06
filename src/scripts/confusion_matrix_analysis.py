#!/usr/bin/env python3
"""
Confusion Matrix Analysis & Arbitration for Barrier Coding
Report 03: Harmonization Constraints

Analyzes where OpenAI and Claude disagree, generates confusion matrices,
and implements arbitration strategies.

Enhanced 2026-01-29: Added subcategory analysis to understand L1-agree-L2-disagree patterns.
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from collections import Counter
import sys

sys.path.insert(0, str(Path(__file__).parent))
from lib.io_utils import ensure_dir

# Paths
ANALYSIS_DIR = Path(__file__).parent.parent / "output" / "analysis"
MERGED_CSV = ANALYSIS_DIR / "barrier_coding_merged.csv"
OUTPUT_DIR = ANALYSIS_DIR / "confusion_analysis"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_data():
    """Load merged barrier coding results."""
    df = pd.read_csv(MERGED_CSV)
    print(f"Loaded {len(df)} pairs")
    return df

def extract_level1(barrier_code):
    """Extract Level 1 from full barrier code (e.g., 'CC.2' -> 'CC')."""
    if pd.isna(barrier_code) or barrier_code in ['UNKNOWN', 'NONE', '']:
        return 'UNKNOWN'
    return str(barrier_code).split('.')[0]

def extract_level2(barrier_code):
    """Extract Level 2 (subcategory number) from full barrier code (e.g., 'CC.2' -> '2')."""
    if pd.isna(barrier_code) or barrier_code in ['UNKNOWN', 'NONE', '']:
        return 'UNKNOWN'
    parts = str(barrier_code).split('.')
    if len(parts) >= 2:
        return parts[1]
    return 'UNKNOWN'

def create_confusion_matrix(df, col1, col2, labels, title, filename):
    """Create and save a confusion matrix heatmap."""
    # Build matrix
    matrix = pd.DataFrame(0, index=labels, columns=labels)
    for _, row in df.iterrows():
        v1 = row[col1] if row[col1] in labels else 'UNKNOWN'
        v2 = row[col2] if row[col2] in labels else 'UNKNOWN'
        matrix.loc[v1, v2] += 1
    
    # Plot
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(matrix, annot=True, fmt='d', cmap='Blues', ax=ax,
                xticklabels=labels, yticklabels=labels)
    ax.set_xlabel('Claude', fontsize=12)
    ax.set_ylabel('OpenAI', fontsize=12)
    ax.set_title(title, fontsize=14)
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / filename, dpi=150)
    plt.close()
    print(f"Saved: {OUTPUT_DIR / filename}")
    
    return matrix

def create_full_code_confusion_matrix(df, col1, col2, title, filename):
    """Create confusion matrix for full barrier codes (dynamic labels)."""
    # Get all unique codes from both columns
    all_codes = sorted(set(df[col1].dropna().unique()) | set(df[col2].dropna().unique()))
    
    # Filter out UNKNOWN/empty if present, but keep for analysis
    labels = [c for c in all_codes if c and c != 'UNKNOWN' and not pd.isna(c)]
    labels.append('UNKNOWN')  # Add at end
    
    # Build matrix
    matrix = pd.DataFrame(0, index=labels, columns=labels)
    for _, row in df.iterrows():
        v1 = row[col1] if row[col1] in labels else 'UNKNOWN'
        v2 = row[col2] if row[col2] in labels else 'UNKNOWN'
        if pd.isna(v1): v1 = 'UNKNOWN'
        if pd.isna(v2): v2 = 'UNKNOWN'
        matrix.loc[v1, v2] += 1
    
    # Plot - larger figure for more labels
    fig, ax = plt.subplots(figsize=(14, 12))
    sns.heatmap(matrix, annot=True, fmt='d', cmap='Blues', ax=ax,
                xticklabels=labels, yticklabels=labels, annot_kws={'size': 8})
    ax.set_xlabel('Claude', fontsize=12)
    ax.set_ylabel('OpenAI', fontsize=12)
    ax.set_title(title, fontsize=14)
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / filename, dpi=150)
    plt.close()
    print(f"Saved: {OUTPUT_DIR / filename}")
    
    return matrix

def analyze_disagreements(df):
    """Detailed analysis of where models disagree."""
    # Add Level 1 columns
    df['openai_L1'] = df['primary_barrier_openai'].apply(extract_level1)
    df['claude_L1'] = df['primary_barrier_claude'].apply(extract_level1)
    
    # Find disagreements
    l1_disagree = df[df['openai_L1'] != df['claude_L1']].copy()
    full_disagree = df[df['primary_barrier_openai'] != df['primary_barrier_claude']].copy()
    feas_disagree = df[df['feasibility_openai'] != df['feasibility_claude']].copy()
    
    # L1 agrees but full code disagrees (subcategory disagreement)
    l1_agree_full_disagree = df[
        (df['openai_L1'] == df['claude_L1']) & 
        (df['primary_barrier_openai'] != df['primary_barrier_claude'])
    ].copy()
    
    print(f"\n{'='*60}")
    print("DISAGREEMENT ANALYSIS")
    print('='*60)
    print(f"\nLevel 1 Barrier Disagreements: {len(l1_disagree)} ({100*len(l1_disagree)/len(df):.1f}%)")
    print(f"Full Barrier Code Disagreements: {len(full_disagree)} ({100*len(full_disagree)/len(df):.1f}%)")
    print(f"Feasibility Disagreements: {len(feas_disagree)} ({100*len(feas_disagree)/len(df):.1f}%)")
    print(f"\n*** L1 AGREES but Subcategory DISAGREES: {len(l1_agree_full_disagree)} ({100*len(l1_agree_full_disagree)/len(df):.1f}%) ***")
    
    # Most common disagreement patterns (Level 1)
    if len(l1_disagree) > 0:
        patterns = Counter(zip(l1_disagree['openai_L1'], l1_disagree['claude_L1']))
        print("\nTop 10 Level 1 Disagreement Patterns (OpenAI → Claude):")
        for (o, c), count in patterns.most_common(10):
            print(f"  {o} → {c}: {count} cases ({100*count/len(l1_disagree):.1f}%)")
    
    # Full code disagreement patterns
    if len(full_disagree) > 0:
        full_patterns = Counter(zip(full_disagree['primary_barrier_openai'], 
                                    full_disagree['primary_barrier_claude']))
        print("\nTop 15 Full Barrier Code Disagreement Patterns (OpenAI → Claude):")
        for (o, c), count in full_patterns.most_common(15):
            print(f"  {o} → {c}: {count} cases ({100*count/len(full_disagree):.1f}%)")
    
    # Subcategory disagreements when L1 agrees
    if len(l1_agree_full_disagree) > 0:
        print(f"\n{'='*60}")
        print("SUBCATEGORY DISAGREEMENTS (L1 agrees, L2 differs)")
        print('='*60)
        
        # Group by L1 category
        for l1_cat in l1_agree_full_disagree['openai_L1'].unique():
            subset = l1_agree_full_disagree[l1_agree_full_disagree['openai_L1'] == l1_cat]
            print(f"\n{l1_cat} category: {len(subset)} subcategory disagreements")
            sub_patterns = Counter(zip(subset['primary_barrier_openai'], 
                                       subset['primary_barrier_claude']))
            for (o, c), count in sub_patterns.most_common(5):
                print(f"    {o} → {c}: {count} cases")
    
    # Feasibility disagreement patterns
    if len(feas_disagree) > 0:
        feas_patterns = Counter(zip(feas_disagree['feasibility_openai'], 
                                    feas_disagree['feasibility_claude']))
        print(f"\n{'='*60}")
        print("Feasibility Disagreement Patterns (OpenAI → Claude):")
        for (o, c), count in feas_patterns.most_common(10):
            print(f"  {o} → {c}: {count} cases")
    
    return l1_disagree, full_disagree, feas_disagree, l1_agree_full_disagree

def show_disagreement_examples(df, disagree_df, n=5, title="EXAMPLE DISAGREEMENTS"):
    """Show example cases where models disagree."""
    print(f"\n{'='*60}")
    print(f"{title} (first {n})")
    print('='*60)
    
    for i, (_, row) in enumerate(disagree_df.head(n).iterrows()):
        print(f"\n--- Case {i+1}: {row['pair_id']} ---")
        print(f"OpenAI: {row['primary_barrier_openai']} ({row['feasibility_openai']})")
        reasoning_o = row.get('reasoning_openai', 'N/A')
        if pd.notna(reasoning_o):
            print(f"  Reason: {str(reasoning_o)[:150]}...")
        print(f"Claude: {row['primary_barrier_claude']} ({row['feasibility_claude']})")
        reasoning_c = row.get('reasoning_claude', 'N/A')
        if pd.notna(reasoning_c):
            print(f"  Reason: {str(reasoning_c)[:150]}...")

def analyze_subcategory_within_l1(df):
    """Deeper analysis of subcategory patterns within each L1 category."""
    df['openai_L1'] = df['primary_barrier_openai'].apply(extract_level1)
    df['claude_L1'] = df['primary_barrier_claude'].apply(extract_level1)
    
    print(f"\n{'='*60}")
    print("SUBCATEGORY DISTRIBUTION BY L1 CATEGORY")
    print('='*60)
    
    for l1_cat in ['CC', 'TC', 'RS', 'MC', 'PC', 'PM']:
        # Filter to pairs where both models assigned this L1
        both_agree_l1 = df[(df['openai_L1'] == l1_cat) & (df['claude_L1'] == l1_cat)]
        
        if len(both_agree_l1) == 0:
            continue
            
        print(f"\n{l1_cat} Category (n={len(both_agree_l1)} pairs where both agree on L1):")
        
        # OpenAI subcategory distribution
        openai_dist = both_agree_l1['primary_barrier_openai'].value_counts()
        claude_dist = both_agree_l1['primary_barrier_claude'].value_counts()
        
        print(f"  OpenAI subcategory distribution:")
        for code, count in openai_dist.items():
            print(f"    {code}: {count} ({100*count/len(both_agree_l1):.1f}%)")
        
        print(f"  Claude subcategory distribution:")
        for code, count in claude_dist.items():
            print(f"    {code}: {count} ({100*count/len(both_agree_l1):.1f}%)")
        
        # Agreement rate within this L1
        full_agree = (both_agree_l1['primary_barrier_openai'] == both_agree_l1['primary_barrier_claude']).sum()
        print(f"  Full code agreement within {l1_cat}: {full_agree}/{len(both_agree_l1)} ({100*full_agree/len(both_agree_l1):.1f}%)")

def apply_arbitration(df, strategy='conservative'):
    """
    Apply arbitration to resolve disagreements.
    
    Strategies:
    - 'conservative': Default to CC for barriers, F3 for feasibility
    - 'openai': Trust OpenAI when disagreement
    - 'claude': Trust Claude when disagreement
    - 'majority_class': Use per-category majority from agreements
    """
    df = df.copy()
    df['openai_L1'] = df['primary_barrier_openai'].apply(extract_level1)
    df['claude_L1'] = df['primary_barrier_claude'].apply(extract_level1)
    
    # Initialize final columns with OpenAI (arbitrary starting point)
    df['final_barrier_L1'] = df['openai_L1']
    df['final_barrier_full'] = df['primary_barrier_openai']
    df['final_feasibility'] = df['feasibility_openai']
    df['l1_arbitration_needed'] = False
    df['full_arbitration_needed'] = False
    df['feas_arbitration_needed'] = False
    
    # Where they agree, use agreed value
    agree_l1 = df['openai_L1'] == df['claude_L1']
    agree_full = df['primary_barrier_openai'] == df['primary_barrier_claude']
    agree_feas = df['feasibility_openai'] == df['feasibility_claude']
    
    # Mark disagreements
    df.loc[~agree_l1, 'l1_arbitration_needed'] = True
    df.loc[~agree_full, 'full_arbitration_needed'] = True
    df.loc[~agree_feas, 'feas_arbitration_needed'] = True
    
    # Apply strategy for disagreements
    if strategy == 'conservative':
        # For L1 barrier: default to CC (most common)
        df.loc[~agree_l1, 'final_barrier_L1'] = 'CC'
        # For full barrier: default to CC.1 (most common subcategory)
        df.loc[~agree_full, 'final_barrier_full'] = 'CC.1'
        # For feasibility: default to F3 (most restrictive)
        df.loc[~agree_feas, 'final_feasibility'] = 'F3'
    
    elif strategy == 'openai':
        # Already set to OpenAI above
        pass
    
    elif strategy == 'claude':
        df.loc[~agree_l1, 'final_barrier_L1'] = df.loc[~agree_l1, 'claude_L1']
        df.loc[~agree_full, 'final_barrier_full'] = df.loc[~agree_full, 'primary_barrier_claude']
        df.loc[~agree_feas, 'final_feasibility'] = df.loc[~agree_feas, 'feasibility_claude']
    
    # Statistics
    l1_arb = df['l1_arbitration_needed'].sum()
    full_arb = df['full_arbitration_needed'].sum()
    feas_arb = df['feas_arbitration_needed'].sum()
    
    print(f"\n{'='*60}")
    print(f"ARBITRATION RESULTS (strategy: {strategy})")
    print('='*60)
    print(f"L1 pairs requiring arbitration: {l1_arb} ({100*l1_arb/len(df):.1f}%)")
    print(f"Full code pairs requiring arbitration: {full_arb} ({100*full_arb/len(df):.1f}%)")
    print(f"Feasibility pairs requiring arbitration: {feas_arb} ({100*feas_arb/len(df):.1f}%)")
    
    # Final distribution
    print(f"\nFinal L1 Barrier Distribution:")
    for barrier, count in df['final_barrier_L1'].value_counts().items():
        print(f"  {barrier}: {count} ({100*count/len(df):.1f}%)")
    
    print(f"\nFinal Full Barrier Code Distribution (top 10):")
    for barrier, count in df['final_barrier_full'].value_counts().head(10).items():
        print(f"  {barrier}: {count} ({100*count/len(df):.1f}%)")
    
    print(f"\nFinal Feasibility Distribution:")
    for feas, count in df['final_feasibility'].value_counts().items():
        print(f"  {feas}: {count} ({100*count/len(df):.1f}%)")
    
    return df

def main():
    print("="*60)
    print("CONFUSION MATRIX ANALYSIS & ARBITRATION")
    print("Report 03: Harmonization Constraints")
    print("="*60)
    
    # Load data
    df = load_data()
    
    # Add Level 1 extractions
    df['openai_L1'] = df['primary_barrier_openai'].apply(extract_level1)
    df['claude_L1'] = df['primary_barrier_claude'].apply(extract_level1)
    
    # Define labels
    barrier_labels = ['CC', 'TC', 'RS', 'MC', 'PC', 'PM', 'UNKNOWN']
    feasibility_labels = ['F1', 'F2', 'F3']
    
    # Create confusion matrices
    print("\n" + "="*60)
    print("GENERATING CONFUSION MATRICES")
    print("="*60)
    
    barrier_matrix = create_confusion_matrix(
        df, 'openai_L1', 'claude_L1', barrier_labels,
        'Level 1 Barrier Confusion Matrix\n(OpenAI vs Claude)',
        'barrier_L1_confusion_matrix.png'
    )
    
    full_barrier_matrix = create_full_code_confusion_matrix(
        df, 'primary_barrier_openai', 'primary_barrier_claude',
        'Full Barrier Code Confusion Matrix\n(OpenAI vs Claude)',
        'barrier_full_confusion_matrix.png'
    )
    
    feas_matrix = create_confusion_matrix(
        df, 'feasibility_openai', 'feasibility_claude', feasibility_labels,
        'Feasibility Confusion Matrix\n(OpenAI vs Claude)',
        'feasibility_confusion_matrix.png'
    )
    
    # Analyze disagreements
    l1_disagree, full_disagree, feas_disagree, l1_agree_full_disagree = analyze_disagreements(df)
    
    # Subcategory analysis
    analyze_subcategory_within_l1(df)
    
    # Show examples - L1 disagreements
    show_disagreement_examples(df, l1_disagree, n=5, title="L1 DISAGREEMENT EXAMPLES")
    
    # Show examples - subcategory disagreements (L1 agrees)
    if len(l1_agree_full_disagree) > 0:
        show_disagreement_examples(df, l1_agree_full_disagree, n=5, 
                                   title="SUBCATEGORY DISAGREEMENT EXAMPLES (L1 agrees)")
    
    # Apply arbitration (just for preview - not final decision)
    print("\n" + "="*60)
    print("ARBITRATION PREVIEW (conservative strategy - for comparison only)")
    print("="*60)
    df_final = apply_arbitration(df, strategy='conservative')
    
    # Save arbitrated results
    output_file = OUTPUT_DIR / 'barrier_coding_arbitrated.csv'
    df_final.to_csv(output_file, index=False)
    print(f"\nSaved arbitrated results: {output_file}")
    
    # Save confusion matrices as CSV for reference
    barrier_matrix.to_csv(OUTPUT_DIR / 'barrier_L1_confusion_matrix.csv')
    full_barrier_matrix.to_csv(OUTPUT_DIR / 'barrier_full_confusion_matrix.csv')
    feas_matrix.to_csv(OUTPUT_DIR / 'feasibility_confusion_matrix.csv')
    
    # Summary for decision-making
    print("\n" + "="*60)
    print("SUMMARY FOR ARBITRATION DECISION")
    print("="*60)
    print(f"""
Key findings:
1. L1 disagreements: {len(l1_disagree)} pairs ({100*len(l1_disagree)/len(df):.1f}%)
2. Subcategory disagreements (L1 agrees): {len(l1_agree_full_disagree)} pairs ({100*len(l1_agree_full_disagree)/len(df):.1f}%)
3. Feasibility disagreements: {len(feas_disagree)} pairs ({100*len(feas_disagree)/len(df):.1f}%)

Questions for arbitration strategy:
- Are L1 disagreements systematic (same patterns) or random?
- Do subcategory disagreements matter for the analysis goals?
- Is the conservative default acceptable given 79% CC dominance?

See confusion matrices in: {OUTPUT_DIR}/
""")
    
    print("\n" + "="*60)
    print("ANALYSIS COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()
