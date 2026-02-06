#!/usr/bin/env python3
"""
Inter-Rater Agreement Analysis v2.0
Report 03: Harmonization Constraints

Calculates agreement metrics between raters:
- Cohen's Kappa (pairwise)
- Fleiss' Kappa (multi-rater)
- Percent agreement
- Confusion matrices

Usage:
    Called from run_pipeline.py, not directly.
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import Counter
import warnings
import sys

sys.path.insert(0, str(Path(__file__).parent))


# =============================================================================
# AGREEMENT METRICS
# =============================================================================

def cohens_kappa(y1: List[str], y2: List[str]) -> float:
    """Calculate Cohen's Kappa for two raters."""
    if len(y1) != len(y2):
        raise ValueError("Lists must be same length")

    n = len(y1)
    if n == 0:
        return 0.0

    # Get all categories
    categories = sorted(set(y1) | set(y2))

    # Build confusion matrix
    matrix = {}
    for cat in categories:
        matrix[cat] = {c: 0 for c in categories}

    for a, b in zip(y1, y2):
        matrix[a][b] += 1

    # Calculate observed agreement
    p_o = sum(matrix[c][c] for c in categories) / n

    # Calculate expected agreement
    p_e = 0
    for cat in categories:
        row_sum = sum(matrix[cat].values())
        col_sum = sum(matrix[c][cat] for c in categories)
        p_e += (row_sum / n) * (col_sum / n)

    # Cohen's Kappa
    if p_e == 1:
        return 1.0
    return (p_o - p_e) / (1 - p_e)


def fleiss_kappa(ratings: List[List[str]]) -> float:
    """Calculate Fleiss' Kappa for multiple raters.

    Args:
        ratings: List of lists, where each inner list contains
                 all rater's classifications for one item

    Returns:
        Fleiss' Kappa coefficient
    """
    if not ratings:
        return 0.0

    n_items = len(ratings)
    n_raters = len(ratings[0])

    # Get all categories
    all_categories = set()
    for item_ratings in ratings:
        all_categories.update(item_ratings)
    categories = sorted(all_categories)
    n_categories = len(categories)

    if n_categories < 2:
        return 1.0  # Perfect agreement if only one category

    # Build category counts per item
    counts = []
    for item_ratings in ratings:
        item_counts = Counter(item_ratings)
        counts.append([item_counts.get(cat, 0) for cat in categories])

    counts = np.array(counts)

    # Calculate P_i for each item (proportion of agreeing pairs)
    P_i = (np.sum(counts ** 2, axis=1) - n_raters) / (n_raters * (n_raters - 1))
    P_bar = np.mean(P_i)

    # Calculate p_j for each category (proportion of assignments)
    p_j = np.sum(counts, axis=0) / (n_items * n_raters)

    # Expected agreement
    P_e = np.sum(p_j ** 2)

    # Fleiss' Kappa
    if P_e == 1:
        return 1.0
    return (P_bar - P_e) / (1 - P_e)


def percent_agreement(y1: List[str], y2: List[str]) -> float:
    """Calculate simple percent agreement."""
    if len(y1) != len(y2) or len(y1) == 0:
        return 0.0
    return sum(a == b for a, b in zip(y1, y2)) / len(y1)


def interpret_kappa(kappa: float) -> str:
    """Interpret Kappa value using Landis & Koch scale."""
    if kappa < 0:
        return "Poor (less than chance)"
    elif kappa < 0.21:
        return "Slight"
    elif kappa < 0.41:
        return "Fair"
    elif kappa < 0.61:
        return "Moderate"
    elif kappa < 0.81:
        return "Substantial"
    else:
        return "Almost Perfect"


# =============================================================================
# CONFUSION MATRIX
# =============================================================================

def build_confusion_matrix(y1: List[str], y2: List[str],
                           labels: Optional[List[str]] = None) -> Tuple[pd.DataFrame, List[str]]:
    """Build confusion matrix as DataFrame."""
    if labels is None:
        labels = sorted(set(y1) | set(y2))

    matrix = pd.DataFrame(0, index=labels, columns=labels)

    for a, b in zip(y1, y2):
        if a in labels and b in labels:
            matrix.loc[a, b] += 1

    return matrix, labels


# =============================================================================
# MAIN ANALYSIS FUNCTION
# =============================================================================

def run_agreement_analysis(config: Dict) -> Dict:
    """Run inter-rater agreement analysis.

    Args:
        config: Pipeline configuration dictionary

    Returns:
        Dictionary of agreement metrics
    """

    output_dir = Path(config['paths']['output_dir'])
    analysis_dir = output_dir / config['paths']['analysis_subdir']
    analysis_dir.mkdir(parents=True, exist_ok=True)

    # Load merged results
    merged_path = analysis_dir / 'barrier_coding_merged.csv'
    if not merged_path.exists():
        print(f"ERROR: Merged results not found: {merged_path}")
        print("Run the rating stage first.")
        return {}

    df = pd.read_csv(merged_path)
    rater_keys = list(config['raters'].keys())

    print(f"\nLoaded {len(df)} pairs")
    print(f"Raters: {rater_keys}")

    results = {
        'n_pairs': len(df),
        'raters': rater_keys,
        'pairwise_barrier_kappa': {},
        'pairwise_barrier_agreement': {},
        'pairwise_feasibility_kappa': {},
        'pairwise_feasibility_agreement': {},
    }

    # Pairwise Cohen's Kappa
    print("\n" + "="*50)
    print("PAIRWISE AGREEMENT (Cohen's Kappa)")
    print("="*50)

    for i, r1 in enumerate(rater_keys):
        for r2 in rater_keys[i+1:]:
            barrier_col1 = f'primary_barrier_{r1}'
            barrier_col2 = f'primary_barrier_{r2}'
            feas_col1 = f'feasibility_{r1}'
            feas_col2 = f'feasibility_{r2}'

            # Check columns exist
            if barrier_col1 not in df.columns or barrier_col2 not in df.columns:
                print(f"  Skipping {r1} vs {r2}: missing barrier columns")
                continue

            # Get non-null pairs
            mask = df[barrier_col1].notna() & df[barrier_col2].notna()
            y1_barrier = df.loc[mask, barrier_col1].tolist()
            y2_barrier = df.loc[mask, barrier_col2].tolist()

            if len(y1_barrier) == 0:
                continue

            # Barrier agreement
            kappa_barrier = cohens_kappa(y1_barrier, y2_barrier)
            pct_barrier = percent_agreement(y1_barrier, y2_barrier)

            pair_key = f'{r1}_vs_{r2}'
            results['pairwise_barrier_kappa'][pair_key] = kappa_barrier
            results['pairwise_barrier_agreement'][pair_key] = pct_barrier

            print(f"\n{r1} vs {r2} (Barrier Codes):")
            print(f"  Cohen's Kappa: {kappa_barrier:.3f} ({interpret_kappa(kappa_barrier)})")
            print(f"  Percent Agreement: {pct_barrier*100:.1f}%")
            print(f"  N pairs: {len(y1_barrier)}")

            # Feasibility agreement
            if feas_col1 in df.columns and feas_col2 in df.columns:
                mask_feas = df[feas_col1].notna() & df[feas_col2].notna()
                y1_feas = df.loc[mask_feas, feas_col1].tolist()
                y2_feas = df.loc[mask_feas, feas_col2].tolist()

                if len(y1_feas) > 0:
                    kappa_feas = cohens_kappa(y1_feas, y2_feas)
                    pct_feas = percent_agreement(y1_feas, y2_feas)

                    results['pairwise_feasibility_kappa'][pair_key] = kappa_feas
                    results['pairwise_feasibility_agreement'][pair_key] = pct_feas

                    print(f"\n{r1} vs {r2} (Feasibility):")
                    print(f"  Cohen's Kappa: {kappa_feas:.3f} ({interpret_kappa(kappa_feas)})")
                    print(f"  Percent Agreement: {pct_feas*100:.1f}%")

            # Build confusion matrix for barrier codes (L1 only)
            y1_L1 = [str(x).split('.')[0] for x in y1_barrier]
            y2_L1 = [str(x).split('.')[0] for x in y2_barrier]

            cm, labels = build_confusion_matrix(y1_L1, y2_L1)
            cm_path = analysis_dir / f'confusion_matrix_{r1}_vs_{r2}.csv'
            cm.to_csv(cm_path)
            print(f"  Confusion matrix saved: {cm_path}")

    # Multi-rater Fleiss' Kappa (if 3+ raters)
    if len(rater_keys) >= 3:
        print("\n" + "="*50)
        print("MULTI-RATER AGREEMENT (Fleiss' Kappa)")
        print("="*50)

        # Collect all ratings per pair
        barrier_ratings = []
        feas_ratings = []

        for idx, row in df.iterrows():
            barrier_row = []
            feas_row = []
            for r in rater_keys:
                b_col = f'primary_barrier_{r}'
                f_col = f'feasibility_{r}'
                if b_col in df.columns and pd.notna(row.get(b_col)):
                    # Use L1 code for Fleiss
                    barrier_row.append(str(row[b_col]).split('.')[0])
                if f_col in df.columns and pd.notna(row.get(f_col)):
                    feas_row.append(row[f_col])

            if len(barrier_row) == len(rater_keys):
                barrier_ratings.append(barrier_row)
            if len(feas_row) == len(rater_keys):
                feas_ratings.append(feas_row)

        if barrier_ratings:
            fleiss_barrier = fleiss_kappa(barrier_ratings)
            results['fleiss_barrier_kappa'] = fleiss_barrier
            print(f"\nBarrier Codes (L1):")
            print(f"  Fleiss' Kappa: {fleiss_barrier:.3f} ({interpret_kappa(fleiss_barrier)})")
            print(f"  N complete cases: {len(barrier_ratings)}")

        if feas_ratings:
            fleiss_feas = fleiss_kappa(feas_ratings)
            results['fleiss_feasibility_kappa'] = fleiss_feas
            print(f"\nFeasibility:")
            print(f"  Fleiss' Kappa: {fleiss_feas:.3f} ({interpret_kappa(fleiss_feas)})")
            print(f"  N complete cases: {len(feas_ratings)}")

    # Disagreement analysis
    print("\n" + "="*50)
    print("DISAGREEMENT PATTERNS")
    print("="*50)

    if len(rater_keys) >= 2:
        r1, r2 = rater_keys[0], rater_keys[1]
        barrier_col1 = f'primary_barrier_{r1}'
        barrier_col2 = f'primary_barrier_{r2}'

        if barrier_col1 in df.columns and barrier_col2 in df.columns:
            # L1 disagreements
            df['barrier_L1_1'] = df[barrier_col1].apply(lambda x: str(x).split('.')[0] if pd.notna(x) else None)
            df['barrier_L1_2'] = df[barrier_col2].apply(lambda x: str(x).split('.')[0] if pd.notna(x) else None)

            mask = df['barrier_L1_1'].notna() & df['barrier_L1_2'].notna()
            disagree_L1 = df.loc[mask, 'barrier_L1_1'] != df.loc[mask, 'barrier_L1_2']

            print(f"\nL1 (Category) disagreements: {disagree_L1.sum()} ({100*disagree_L1.mean():.1f}%)")

            # Most common disagreement pairs
            disagree_df = df[mask][disagree_L1]
            if len(disagree_df) > 0:
                disagree_pairs = list(zip(disagree_df['barrier_L1_1'], disagree_df['barrier_L1_2']))
                pair_counts = Counter(disagree_pairs)

                print("\nMost common L1 disagreements:")
                for (a, b), count in pair_counts.most_common(10):
                    print(f"  {a} <-> {b}: {count}")

                results['top_disagreement_pairs'] = [
                    {'pair': f'{a} <-> {b}', 'count': count}
                    for (a, b), count in pair_counts.most_common(10)
                ]

    # Save results
    results_path = analysis_dir / 'agreement_analysis.json'
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved: {results_path}")

    return results


# =============================================================================
# STANDALONE MODE
# =============================================================================

def main():
    """Standalone execution for testing."""
    import yaml

    print("="*60)
    print("INTER-RATER AGREEMENT ANALYSIS v2.0")
    print("="*60)

    config_path = Path(__file__).parent.parent / 'config.yaml'
    if not config_path.exists():
        print(f"ERROR: {config_path} not found")
        return

    with open(config_path) as f:
        config = yaml.safe_load(f)

    results = run_agreement_analysis(config)

    print("\n" + "="*60)
    print("ANALYSIS COMPLETE")
    print("="*60)


if __name__ == '__main__':
    main()
