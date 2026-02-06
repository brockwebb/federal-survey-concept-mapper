#!/usr/bin/env python3
"""
descriptive_stats.py - Generate standardized descriptive statistics

Captures the ad-hoc analyses from conversation into reproducible script.

Analyses performed:
1. L1/L2 barrier distributions (per rater)
2. Agreement rates at L1, L2, feasibility levels
3. Synthesis detection performance (precision/recall)
4. Ground truth rater agreement calculations

Usage:
    python scripts/descriptive_stats.py --stage rater
    python scripts/descriptive_stats.py --stage arbitration
"""

import argparse
import json
import sys
from pathlib import Path
from collections import Counter

import pandas as pd
import numpy as np

# Add lib to path
# Path setup for post-restructure layout
SRC_DIR = Path(__file__).resolve().parent.parent    # .../src/
REPO_ROOT = SRC_DIR.parent                           # repo root
sys.path.insert(0, str(SRC_DIR))                     # enables lib imports
from lib.stats import cohens_kappa, fleiss_kappa, percent_agreement, interpret_kappa
from lib.taxonomy import extract_l1, BARRIER_L1
from lib.io_utils import load_config, ensure_dir


def compute_l1_distribution(df, barrier_col):
    """Compute L1 barrier distribution for a single rater column."""
    l1_codes = df[barrier_col].apply(extract_l1)
    counts = l1_codes.value_counts()
    total = len(df)

    dist = {}
    for code, count in counts.items():
        dist[code] = {
            'count': int(count),
            'percent': round(count / total * 100, 1)
        }
    return dist


def compute_l2_distribution(df, barrier_col, top_n=15):
    """Compute full barrier code distribution (top N)."""
    counts = df[barrier_col].value_counts().head(top_n)
    total = len(df)

    dist = {}
    for code, count in counts.items():
        dist[code] = {
            'count': int(count),
            'percent': round(count / total * 100, 1)
        }
    return dist


def compute_agreement_rates(df, rater_cols):
    """
    Compute agreement rates across raters.

    Returns:
        dict with L1, L2, feasibility agreement stats
    """
    n_raters = len(rater_cols)
    n_pairs = len(df)

    # Extract L1 for each rater
    l1_cols = []
    for col in rater_cols:
        l1_col = f'{col}_l1'
        df[l1_col] = df[col].apply(extract_l1)
        l1_cols.append(l1_col)

    # L1 agreement: all raters match
    l1_match = df.apply(
        lambda row: len(set(row[l1_cols])) == 1,
        axis=1
    )
    l1_agreement = l1_match.sum()

    # L2 agreement: full codes match
    l2_match = df.apply(
        lambda row: len(set(row[rater_cols])) == 1,
        axis=1
    )
    l2_agreement = l2_match.sum()

    return {
        'n_pairs': n_pairs,
        'n_raters': n_raters,
        'l1': {
            'agreement_count': int(l1_agreement),
            'agreement_percent': round(l1_agreement / n_pairs * 100, 1)
        },
        'l2': {
            'agreement_count': int(l2_agreement),
            'agreement_percent': round(l2_agreement / n_pairs * 100, 1)
        }
    }


def compute_synthesis_detection(arb_df, rater_df, arbitrator):
    """
    Evaluate synthesis detection performance for an arbitrator.

    Compares:
    - Ground truth: all 3 raters have same L1
    - Arbitrator's synthesis calls

    Returns precision, recall, F1
    """
    # Merge on pair_id
    merged = arb_df.merge(
        rater_df[['pair_id', 'primary_barrier_openai', 'primary_barrier_anthropic', 'primary_barrier_google']],
        on='pair_id',
        how='left'
    )

    # Ground truth: all 3 L1 match
    merged['l1_openai'] = merged['primary_barrier_openai'].apply(extract_l1)
    merged['l1_anthropic'] = merged['primary_barrier_anthropic'].apply(extract_l1)
    merged['l1_google'] = merged['primary_barrier_google'].apply(extract_l1)

    merged['ground_truth_agreement'] = (
        (merged['l1_openai'] == merged['l1_anthropic']) &
        (merged['l1_anthropic'] == merged['l1_google'])
    )

    # Arbitrator's synthesis calls
    selected_col = f'{arbitrator}_selected_rater'
    if selected_col not in merged.columns:
        return None

    merged['called_synthesis'] = merged[selected_col].str.lower() == 'synthesis'

    # Confusion matrix
    tp = ((merged['ground_truth_agreement']) & (merged['called_synthesis'])).sum()
    fp = ((~merged['ground_truth_agreement']) & (merged['called_synthesis'])).sum()
    fn = ((merged['ground_truth_agreement']) & (~merged['called_synthesis'])).sum()
    tn = ((~merged['ground_truth_agreement']) & (~merged['called_synthesis'])).sum()

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    return {
        'n_pairs': len(merged),
        'ground_truth_agreement_count': int(merged['ground_truth_agreement'].sum()),
        'ground_truth_agreement_percent': round(merged['ground_truth_agreement'].mean() * 100, 1),
        'synthesis_called_count': int(merged['called_synthesis'].sum()),
        'synthesis_called_percent': round(merged['called_synthesis'].mean() * 100, 1),
        'confusion_matrix': {
            'tp': int(tp), 'fp': int(fp),
            'fn': int(fn), 'tn': int(tn)
        },
        'precision': round(precision, 3),
        'recall': round(recall, 3),
        'f1': round(f1, 3)
    }


def analyze_rater_stage(config, output_dir):
    """
    Analyze rater outputs (Stage 2).
    """
    print("=" * 60)
    print("DESCRIPTIVE STATISTICS: RATER STAGE")
    print("=" * 60)

    # Load merged rater data
    rater_file = output_dir / 'analysis' / 'barrier_coding_merged_3rater.csv'
    if not rater_file.exists():
        # Try alternate filename
        rater_file = output_dir / 'analysis' / 'barrier_coding_merged.csv'

    if not rater_file.exists():
        print(f"ERROR: Rater merged file not found: {rater_file}")
        return None

    df = pd.read_csv(rater_file)
    print(f"Loaded {len(df)} pairs from {rater_file.name}")

    results = {
        'stage': 'rater',
        'n_pairs': len(df),
        'raters': {},
        'agreement': {}
    }

    # Barrier columns
    rater_cols = ['primary_barrier_anthropic', 'primary_barrier_openai', 'primary_barrier_google']
    raters = ['anthropic', 'openai', 'google']

    # Per-rater distributions
    print("\n=== L1 BARRIER DISTRIBUTION (by rater) ===\n")
    for rater, col in zip(raters, rater_cols):
        if col not in df.columns:
            print(f"{rater.upper()}: Column not found")
            continue

        l1_dist = compute_l1_distribution(df, col)
        l2_dist = compute_l2_distribution(df, col)

        results['raters'][rater] = {
            'l1_distribution': l1_dist,
            'l2_distribution': l2_dist
        }

        print(f"{rater.upper()}:")
        for code in sorted(l1_dist.keys()):
            d = l1_dist[code]
            print(f"  {code}:  {d['count']:4d} ({d['percent']:5.1f}%)")
        print()

    # Agreement rates
    print("=== AGREEMENT SUMMARY ===\n")
    agreement = compute_agreement_rates(df, rater_cols)
    results['agreement'] = agreement

    print(f"L1 (category): 3-way agreement = {agreement['l1']['agreement_count']}/{agreement['n_pairs']} ({agreement['l1']['agreement_percent']}%)")
    print(f"L2 (full code): 3-way agreement = {agreement['l2']['agreement_count']}/{agreement['n_pairs']} ({agreement['l2']['agreement_percent']}%)")

    return results


def analyze_arbitration_stage(config, output_dir):
    """
    Analyze arbitration outputs (Stage 5).
    """
    print("=" * 60)
    print("DESCRIPTIVE STATISTICS: ARBITRATION STAGE")
    print("=" * 60)

    # Load files
    arb_file = output_dir / 'analysis' / 'arbitration_merged.csv'
    rater_file = output_dir / 'analysis' / 'barrier_coding_merged_3rater.csv'
    if not rater_file.exists():
        rater_file = output_dir / 'analysis' / 'barrier_coding_merged.csv'

    if not arb_file.exists():
        print(f"ERROR: Arbitration merged file not found: {arb_file}")
        return None

    arb_df = pd.read_csv(arb_file)
    rater_df = pd.read_csv(rater_file) if rater_file.exists() else None

    print(f"Loaded {len(arb_df)} pairs from arbitration_merged.csv")

    results = {
        'stage': 'arbitration',
        'n_pairs': len(arb_df),
        'arbitrators': {},
        'synthesis_detection': {}
    }

    arbitrators = ['anthropic', 'openai', 'google']

    # Synthesis detection analysis
    if rater_df is not None:
        print("\n=== SYNTHESIS DETECTION PERFORMANCE ===\n")
        print("(Comparing arbitrator synthesis calls vs ground truth rater agreement)\n")

        for arb in arbitrators:
            synth_stats = compute_synthesis_detection(arb_df, rater_df, arb)
            if synth_stats is None:
                continue

            results['synthesis_detection'][arb] = synth_stats

            print(f"{arb.upper()}:")
            print(f"  Ground truth (3-way L1 match): {synth_stats['ground_truth_agreement_percent']}%")
            print(f"  Synthesis called: {synth_stats['synthesis_called_percent']}%")
            print(f"  Precision: {synth_stats['precision']:.1%}")
            print(f"  Recall: {synth_stats['recall']:.1%}")
            print(f"  F1: {synth_stats['f1']:.1%}")
            print()

    return results


def main():
    parser = argparse.ArgumentParser(description='Generate descriptive statistics')
    parser.add_argument('--stage', required=True, choices=['rater', 'arbitration', 'all'],
                       help='Pipeline stage to analyze')
    parser.add_argument('--output', type=str, default=None,
                       help='Output JSON file (default: auto-generated)')
    args = parser.parse_args()

    # Find project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    config_path = project_root / 'config.yaml'
    if not config_path.exists():
        print(f"ERROR: config.yaml not found at {config_path}")
        sys.exit(1)

    config = load_config(config_path)
    output_dir = project_root / 'output'

    results = {}

    if args.stage in ['rater', 'all']:
        results['rater'] = analyze_rater_stage(config, output_dir)

    if args.stage in ['arbitration', 'all']:
        results['arbitration'] = analyze_arbitration_stage(config, output_dir)

    # Save results
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = output_dir / 'analysis' / f'descriptive_stats_{args.stage}.json'

    ensure_dir(output_path.parent)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    main()
